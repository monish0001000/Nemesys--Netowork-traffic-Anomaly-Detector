import subprocess
import json
import time
import requests
import argparse
import sys
import threading
import queue

def capture_traffic(interface, pkt_queue):
    print(f"Starting TShark capture on interface: {interface}")
    cmd = ["tshark", "-i", interface, "-l", "-T", "ek"]
    
    try:
        # bufsize=1 for line-buffered reading
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        for line in process.stdout:
            try:
                data = json.loads(line)
                if "index" in data:
                    continue # Skip elasticsearch index metadata lines
                    
                layers = data.get("layers", {})
                
                # Parse packet
                ip = layers.get("ip", {})
                tcp = layers.get("tcp", {})
                udp = layers.get("udp", {})
                frame = layers.get("frame", {})
                
                if not ip:
                    continue
                    
                src_ip = ip.get("ip_ip_src", "unknown")
                dst_ip = ip.get("ip_ip_dst", "unknown")
                
                proto = "Other"
                src_port = 0
                dst_port = 0
                flags_list = []
                
                if tcp:
                    proto = "TCP"
                    src_port = int(tcp.get("tcp_tcp_srcport", 0))
                    dst_port = int(tcp.get("tcp_tcp_dstport", 0))
                    if tcp.get("tcp_flags_tcp_flags_syn") == "1": flags_list.append("SYN")
                    if tcp.get("tcp_flags_tcp_flags_ack") == "1": flags_list.append("ACK")
                    if tcp.get("tcp_flags_tcp_flags_fin") == "1": flags_list.append("FIN")
                elif udp:
                    proto = "UDP"
                    src_port = int(udp.get("udp_udp_srcport", 0))
                    dst_port = int(udp.get("udp_udp_dstport", 0))
                    
                length = int(frame.get("frame_frame_len", 0))
                flags = ",".join(flags_list)
                timestamp = int(time.time() * 1000)
                
                import socket
                pkt = {
                    "node_id": socket.gethostname(),
                    "timestamp": timestamp,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "proto": proto,
                    "length": length,
                    "flags": flags
                }
                
                pkt_queue.put(pkt)
                
            except json.JSONDecodeError:
                pass
                
    except FileNotFoundError:
        print("ERROR: tshark not found in PATH! Make sure Wireshark/tshark is installed.")
        print("Note: On Termux, you may need root access to run tshark.")
        sys.exit(1)
    except Exception as e:
        print(f"Capture error: {e}")

def send_telemetry(target_url, pkt_queue):
    endpoint = f"{target_url.rstrip('/')}/api/telemetry/packet"
    session = requests.Session()
    
    print(f"Streaming parsed telemetry to {endpoint} for anomaly analysis...")
    
    while True:
        try:
            pkt = pkt_queue.get()
            # Send to the central NEMESYS backend where the Isolation Forest model 
            # analyzes the flow window for anomalies.
            session.post(endpoint, json=pkt, timeout=1.0)
        except requests.RequestException:
            # Drop packets silently if backend is unreachable to prevent memory buildup
            pass
        except Exception as e:
            print(f"Sender error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NEMESYS TShark Telemetry Agent")
    parser.add_argument("--url", default="http://localhost:8000", help="Target NEMESYS backend URL")
    parser.add_argument("-i", "--interface", required=True, help="Network interface to capture (e.g., eth0, wlan0)")
    args = parser.parse_args()
    
    # Use a thread-safe queue to pass packets from capture thread to sender thread
    packet_queue = queue.Queue(maxsize=1000)
    
    capture_thread = threading.Thread(target=capture_traffic, args=(args.interface, packet_queue), daemon=True)
    sender_thread = threading.Thread(target=send_telemetry, args=(args.url, packet_queue), daemon=True)
    
    capture_thread.start()
    sender_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping agent...")
        sys.exit(0)
