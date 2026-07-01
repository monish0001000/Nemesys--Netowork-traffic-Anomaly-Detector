import subprocess
import json
import time
import asyncio
import random
from state import state

async def run_tshark(interface="eth0"):
    cmd = [
        "tshark", "-i", interface, "-l", "-T", "ek"
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"Started tshark capture on {interface}")
        while state.capturing:
            line = await process.stdout.readline()
            if not line:
                break
                
            try:
                data = json.loads(line.decode('utf-8'))
                if "index" in data:
                    continue # ElasticSearch bulk index lines
                    
                layers = data.get("layers", {})
                
                # Parse packet
                ip = layers.get("ip", {})
                tcp = layers.get("tcp", {})
                udp = layers.get("udp", {})
                frame = layers.get("frame", {})
                
                if not ip: # Ignore non-IP packets for simplicity
                    continue
                    
                src_ip = ip.get("ip_ip_src", "unknown")
                dst_ip = ip.get("ip_ip_dst", "unknown")
                
                proto = "Other"
                src_port = 0
                dst_port = 0
                flags = ""
                
                if tcp:
                    proto = "TCP"
                    src_port = int(tcp.get("tcp_tcp_srcport", 0))
                    dst_port = int(tcp.get("tcp_tcp_dstport", 0))
                    flags_list = []
                    if tcp.get("tcp_flags_tcp_flags_syn") == "1": flags_list.append("SYN")
                    if tcp.get("tcp_flags_tcp_flags_ack") == "1": flags_list.append("ACK")
                    if tcp.get("tcp_flags_tcp_flags_fin") == "1": flags_list.append("FIN")
                    flags = ",".join(flags_list)
                elif udp:
                    proto = "UDP"
                    src_port = int(udp.get("udp_udp_srcport", 0))
                    dst_port = int(udp.get("udp_udp_dstport", 0))
                    
                length = int(frame.get("frame_frame_len", 0))
                
                timestamp = int(time.time() * 1000)
                
                pkt = {
                    "timestamp": timestamp,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "proto": proto,
                    "length": length,
                    "flags": flags
                }
                
                await state.add_packet(pkt)
                
                # Broadcast packet
                msg = json.dumps({"type": "packet", "payload": pkt})
                for q in list(state.clients):
                    try:
                        q.put_nowait(msg)
                    except asyncio.QueueFull:
                        pass
                
            except json.JSONDecodeError:
                pass
                
        # If we stop capturing, terminate process
        process.terminate()
        await process.wait()
        
    except FileNotFoundError:
        print("tshark not found in PATH! Make sure Wireshark is installed.")
        state.capturing = False

async def mock_capture():
    print("Starting mock capture generator...")
    ips = ["10.0.0.5", "10.0.0.12", "192.168.1.1", "8.8.8.8", "1.1.1.1", "10.0.0.100"]
    
    while state.capturing:
        await asyncio.sleep(random.uniform(0.01, 0.05)) # ~20-100 pps
        
        src_ip = random.choice(ips)
        dst_ip = random.choice(ips)
        while src_ip == dst_ip:
            dst_ip = random.choice(ips)
            
        proto = random.choices(["TCP", "UDP", "ICMP"], weights=[0.8, 0.15, 0.05])[0]
        
        pkt = {
            "timestamp": int(time.time() * 1000),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": random.randint(1024, 65535),
            "dst_port": random.choice([80, 443, 53, 22, 8080]),
            "proto": proto,
            "length": random.randint(64, 1500),
            "flags": random.choice(["SYN", "ACK", "SYN,ACK", ""]) if proto == "TCP" else ""
        }
        
        # Introduce a deliberate anomaly occasionally (simulating a port scan or flood)
        if random.random() < 0.05:
            # Port scan scenario
            pkt["src_ip"] = "192.168.1.99"
            pkt["dst_port"] = random.randint(1, 1024)
            pkt["flags"] = "SYN"
            pkt["length"] = 64
            
        await state.add_packet(pkt)
        
        msg = json.dumps({"type": "packet", "payload": pkt})
        for q in list(state.clients):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass
                
async def start_capture_loop(interface):
    state.capturing = True
    state.interface = interface
    
    msg = json.dumps({"type": "status", "payload": {"capturing": True, "packets_total": state.packets_total}})
    for q in list(state.clients):
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            pass
            
    if interface.startswith("mock"):
        asyncio.create_task(mock_capture())
    else:
        asyncio.create_task(run_tshark(interface))
