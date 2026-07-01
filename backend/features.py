import time
import math
from collections import Counter
import uuid
import asyncio
import json

from state import state
from model import anomaly_model

def entropy(labels):
    total = len(labels)
    if total <= 1:
        return 0.0
    counts = Counter(labels)
    ent = 0.0
    for k, v in counts.items():
        p = v / total
        ent -= p * math.log2(p)
    return ent

async def process_flows_window():
    # Called periodically
    while True:
        await asyncio.sleep(2.0)
        
        now = time.time()
        
        alerts_to_send = []
        
        async with state.lock:
            # We want to process flows that had activity in the last few seconds
            # In a real app we might clean up stale flows here too.
            stale_keys = []
            
            for flow_key, packets in list(state.active_flows.items()):
                last_seen = state.flow_last_seen.get(flow_key, 0)
                
                if now - last_seen > 10.0:
                    stale_keys.append(flow_key)
                    continue
                
                # Only score if active recently
                if now - last_seen > 2.0:
                    continue
                    
                if len(packets) < 5:
                    continue # Too few packets to be meaningful
                    
                # Compute features
                node_id, src_ip, dst_ip, src_port, dst_port, proto_flow = flow_key
                
                packet_count = len(packets)
                byte_count = sum(p.get('length', 0) for p in packets)
                avg_packet_size = byte_count / packet_count
                
                t_start = packets[0]['timestamp'] / 1000.0 # assume packet timestamp is in ms
                t_end = packets[-1]['timestamp'] / 1000.0
                duration = t_end - t_start
                if duration < 0.001:
                    duration = 0.001
                    
                packet_rate = packet_count / duration
                bytes_per_second = byte_count / duration
                
                syn_count = sum(1 for p in packets if 'SYN' in p.get('flags', ''))
                ack_count = sum(1 for p in packets if 'ACK' in p.get('flags', ''))
                syn_without_ack_ratio = 0
                if syn_count > 0:
                    syn_without_ack_ratio = max(0.0, (syn_count - ack_count) / syn_count)
                    
                unique_dst_ports = 1
                
                protos = [p.get('proto', 'TCP') for p in packets]
                protocol_entropy = entropy(protos)
                
                features = {
                    'packet_count': packet_count,
                    'byte_count': byte_count,
                    'avg_packet_size': avg_packet_size,
                    'packet_rate': packet_rate,
                    'unique_dst_ports': unique_dst_ports,
                    'syn_count': syn_count,
                    'syn_without_ack_ratio': syn_without_ack_ratio,
                    'protocol_entropy': protocol_entropy,
                    'duration': duration,
                    'bytes_per_second': bytes_per_second
                }
                
                # Score with model
                score, severity = anomaly_model.score(features)
                
                if score < 0:
                    alert = {
                        "id": str(uuid.uuid4()),
                        "node_id": node_id,
                        "timestamp": int(now * 1000),
                        "severity": severity,
                        "src_ip": src_ip,
                        "dst_ip": dst_ip,
                        "reason": f"Anomaly score {score:.2f}",
                        "score": score,
                        "details": features
                    }
                    state.alerts.append(alert)
                    alerts_to_send.append(alert)
            
            # Cleanup stale flows
            for k in stale_keys:
                del state.active_flows[k]
                del state.flow_last_seen[k]
                
        # Broadcast outside the lock
        for alert in alerts_to_send:
            msg = json.dumps({"type": "anomaly", "payload": alert})
            for q in list(state.clients):
                await q.put(msg)
