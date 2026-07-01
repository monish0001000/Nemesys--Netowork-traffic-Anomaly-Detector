import asyncio
import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from state import state
from model import anomaly_model
from capture import start_capture_loop
from features import process_flows_window

app = FastAPI(title="NEMESYS Traffic Sentinel Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CaptureRequest(BaseModel):
    interface: str

class PacketModel(BaseModel):
    node_id: str = "local"
    timestamp: int
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    proto: str
    length: int
    flags: str

@app.post("/api/telemetry/packet")
async def receive_telemetry_packet(packet: PacketModel):
    pkt = packet.model_dump()
    await state.add_packet(pkt)
    
    # Broadcast packet
    msg = json.dumps({"type": "packet", "payload": pkt})
    for q in list(state.clients):
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            pass
            
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    # Start background task for feature extraction and anomaly scoring
    asyncio.create_task(process_flows_window())
    
    # Background task for metrics ticking
    asyncio.create_task(metrics_ticker())

async def metrics_ticker():
    while True:
        await asyncio.sleep(1.0)
        
        now = time.time()
        
        async with state.lock:
            dt = now - state.last_tick_time
            if dt < 0.001: dt = 0.001
            
            payloads = []
            
            total_pkts = sum(state.node_window_packets.values())
            total_bytes = sum(state.node_window_bytes.values())
            
            global_pps = total_pkts / dt
            global_bps = (total_bytes * 8) / dt
            
            payloads.append({
                "node_id": "All Nodes",
                "timestamp": int(now * 1000),
                "pps": int(global_pps),
                "bps": int(global_bps),
                "active_flows": len(state.active_flows)
            })
            
            for node_id in list(state.nodes_last_seen.keys()):
                pkts = state.node_window_packets.get(node_id, 0)
                byts = state.node_window_bytes.get(node_id, 0)
                
                pps = pkts / dt
                bps = (byts * 8) / dt
                node_flows = sum(1 for flow_key in state.active_flows if flow_key[0] == node_id)
                
                payloads.append({
                    "node_id": node_id,
                    "timestamp": int(now * 1000),
                    "pps": int(pps),
                    "bps": int(bps),
                    "active_flows": node_flows
                })
            
            state.node_window_packets.clear()
            state.node_window_bytes.clear()
            state.last_tick_time = now
            
        for p in payloads:
            msg = json.dumps({"type": "metric_tick", "payload": p})
            for q in list(state.clients):
                try:
                    q.put_nowait(msg)
                except asyncio.QueueFull:
                    pass

@app.get("/api/status")
async def get_status():
    model_age_minutes = 0
    if anomaly_model.last_trained > 0:
        model_age_minutes = int((time.time() - anomaly_model.last_trained) / 60)
        
    return {
        "capturing": state.capturing,
        "interface": state.interface,
        "model_age_minutes": model_age_minutes,
        "packets_total": state.packets_total
    }

@app.get("/api/interfaces")
async def get_interfaces():
    # Return some dummy interfaces + mock
    return [
        {"name": "mock0", "description": "Mock Packet Generator"},
        {"name": "eth0", "description": "Ethernet 0"},
        {"name": "wlan0", "description": "Wireless 0"},
        {"name": "lo", "description": "Loopback"}
    ]

@app.post("/api/capture/start")
async def start_capture(req: CaptureRequest):
    if state.capturing:
        return {"status": "already capturing"}
        
    await start_capture_loop(req.interface)
    return {"status": "started", "interface": req.interface}

@app.post("/api/capture/stop")
async def stop_capture():
    state.capturing = False
    
    msg = json.dumps({"type": "status", "payload": {"capturing": False, "packets_total": state.packets_total}})
    for q in list(state.clients):
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            pass
            
    return {"status": "stopped"}

@app.get("/api/nodes")
async def get_nodes():
    return list(state.nodes_last_seen.keys())

@app.get("/api/stats/protocols")
async def get_protocols(node_id: str = None, window: str = "5m"):
    async with state.lock:
        res = []
        # Aggregate across nodes if no node_id, else specific
        agg = {}
        for nid, pstats in state.protocol_stats.items():
            if node_id and node_id != "All Nodes" and nid != node_id:
                continue
            for proto, stats in pstats.items():
                if proto not in agg:
                    agg[proto] = {"count": 0, "bytes": 0}
                agg[proto]["count"] += stats["count"]
                agg[proto]["bytes"] += stats["bytes"]
                
        for proto, stats in agg.items():
            res.append({
                "protocol": proto,
                "count": stats["count"],
                "bytes": stats["bytes"]
            })
        return res

@app.get("/api/stats/top-talkers")
async def get_top_talkers(node_id: str = None, window: str = "5m", limit: int = 10):
    async with state.lock:
        agg = {}
        for nid, istats in state.ip_stats.items():
            if node_id and node_id != "All Nodes" and nid != node_id:
                continue
            for ip, stats in istats.items():
                if ip not in agg:
                    agg[ip] = {"packets": 0, "bytes": 0}
                agg[ip]["packets"] += stats["packets"]
                agg[ip]["bytes"] += stats["bytes"]
                
        sorted_ips = sorted(agg.items(), key=lambda x: x[1]["bytes"], reverse=True)
        res = []
        for ip, stats in sorted_ips[:limit]:
            res.append({
                "ip": ip,
                "packets": stats["packets"],
                "bytes": stats["bytes"]
            })
        return res

@app.get("/api/alerts")
async def get_alerts(node_id: str = None, limit: int = 50, severity: str = ""):
    async with state.lock:
        alerts = list(state.alerts)
        if node_id and node_id != "All Nodes":
            alerts = [a for a in alerts if a.get("node_id") == node_id]
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        # return newest first
        alerts.reverse()
        return alerts[:limit]

@app.get("/api/packets")
async def get_packets(node_id: str = None, limit: int = 100):
    async with state.lock:
        packets = list(state.packets)
        if node_id and node_id != "All Nodes":
            packets = [p for p in packets if p.get("node_id") == node_id]
        packets.reverse() # newest first
        return packets[:limit]

@app.post("/api/model/retrain")
async def retrain_model():
    # In a real scenario we would fetch historical features from a DB
    # For now, we'll just re-run the baseline training to simulate
    anomaly_model.train_baseline()
    return {"status": "retrained"}

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    q = asyncio.Queue(maxsize=100)
    state.clients.add(q)
    
    # Send initial status
    await websocket.send_text(json.dumps({
        "type": "status",
        "payload": {"capturing": state.capturing, "packets_total": state.packets_total}
    }))
    
    try:
        while True:
            msg = await q.get()
            await websocket.send_text(msg)
    except WebSocketDisconnect:
        state.clients.remove(q)
    except Exception as e:
        print(f"WS error: {e}")
        if q in state.clients:
            state.clients.remove(q)
