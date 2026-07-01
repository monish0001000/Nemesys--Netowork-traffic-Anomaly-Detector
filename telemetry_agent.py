import time
import requests
import psutil
import socket
import random
import argparse
import sys

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generate_telemetry(target_url):
    local_ip = get_local_ip()
    print(f"Starting telemetry agent. Local IP: {local_ip}")
    print(f"Sending telemetry to: {target_url}")
    
    endpoint = f"{target_url.rstrip('/')}/api/telemetry/packet"
    
    session = requests.Session()
    
    while True:
        try:
            # Cross-platform way to get active connections without root
            # Note: psutil might need elevated privileges to see all connections on some platforms,
            # but it will return at least the current user's connections.
            conns = psutil.net_connections(kind='inet')
            
            # Filter for established or active listening connections to simulate traffic
            active_conns = [c for c in conns if c.status == 'ESTABLISHED' or c.status == 'NONE']
            
            if not active_conns:
                time.sleep(1)
                continue
                
            # Pick a random connection to simulate a packet for
            conn = random.choice(active_conns)
            
            if not conn.laddr or not conn.raddr:
                continue
                
            src_ip = conn.laddr.ip
            src_port = conn.laddr.port
            dst_ip = conn.raddr.ip
            dst_port = conn.raddr.port
            
            # Map psutil protocol
            proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
            
            # Simulate length and flags
            length = random.randint(64, 1500)
            flags = "ACK" if proto == "TCP" else ""
            if random.random() < 0.1 and proto == "TCP":
                flags = "SYN"
                length = 64
                
            pkt = {
                "node_id": socket.gethostname(),
                "timestamp": int(time.time() * 1000),
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_port,
                "dst_port": dst_port,
                "proto": proto,
                "length": length,
                "flags": flags
            }
            
            try:
                session.post(endpoint, json=pkt, timeout=1.0)
            except requests.RequestException as e:
                print(f"[!] Failed to send to {endpoint} - Check IP/Firewall ({e})")
                time.sleep(2)
                
            # Pace the packets
            time.sleep(random.uniform(0.01, 0.1))
            
        except psutil.AccessDenied:
            # On some platforms, net_connections needs root. Fallback to purely simulated traffic.
            print("Access denied getting real connections. Falling back to mock generator.")
            fallback_generator(session, endpoint, local_ip)
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

def fallback_generator(session, endpoint, local_ip):
    ips = [local_ip, "8.8.8.8", "1.1.1.1", "10.0.0.1", "192.168.1.254"]
    while True:
        src_ip = random.choice(ips)
        dst_ip = random.choice(ips)
        while src_ip == dst_ip:
            dst_ip = random.choice(ips)
            
        proto = random.choices(["TCP", "UDP", "ICMP"], weights=[0.8, 0.15, 0.05])[0]
        
        pkt = {
            "node_id": socket.gethostname(),
            "timestamp": int(time.time() * 1000),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": random.randint(1024, 65535),
            "dst_port": random.choice([80, 443, 53, 22]),
            "proto": proto,
            "length": random.randint(64, 1500),
            "flags": random.choice(["SYN", "ACK", "SYN,ACK", ""]) if proto == "TCP" else ""
        }
        
        try:
            session.post(endpoint, json=pkt, timeout=1.0)
        except requests.RequestException as e:
            print(f"[!] Failed to send to {endpoint} - Check IP/Firewall ({e})")
            time.sleep(2)
            
        time.sleep(random.uniform(0.01, 0.1))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NEMESYS Telemetry Agent")
    parser.add_argument("--url", default="http://localhost:8000", help="Target NEMESYS backend URL")
    args = parser.parse_args()
    
    try:
        generate_telemetry(args.url)
    except KeyboardInterrupt:
        print("Stopped.")
        sys.exit(0)
