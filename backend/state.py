from collections import deque, defaultdict
import time
import asyncio

class AppState:
    def __init__(self):
        self.packets = deque(maxlen=1000)
        self.alerts = deque(maxlen=1000)
        self.capturing = False
        self.interface = "mock0"
        
        self.packets_total = 0
        self.bytes_total = 0
        
        self.nodes_last_seen = {} # node_id -> timestamp
        
        # Stats per node
        self.node_window_packets = defaultdict(int)
        self.node_window_bytes = defaultdict(int)
        
        self.last_tick_time = time.time()
        
        # Top talkers and protocols per node: ip_stats[node_id][ip]
        self.ip_stats = defaultdict(lambda: defaultdict(lambda: {"packets": 0, "bytes": 0}))
        self.protocol_stats = defaultdict(lambda: defaultdict(lambda: {"count": 0, "bytes": 0}))
        
        # Active flows for sliding window
        self.active_flows = {} # (node_id, src_ip, dst_ip, src_port, dst_port, proto) -> list of packets
        self.flow_last_seen = {} # flow_tuple -> timestamp
        
        # Clients for websockets
        self.clients = set()
        self.lock = asyncio.Lock()
        
    async def add_packet(self, pkt):
        async with self.lock:
            node_id = pkt.get('node_id', 'local')
            self.nodes_last_seen[node_id] = time.time()
            
            self.packets_total += 1
            self.bytes_total += pkt['length']
            
            self.node_window_packets[node_id] += 1
            self.node_window_bytes[node_id] += pkt['length']
            
            self.packets.append(pkt)
            
            # IP stats
            src_ip = pkt.get('src_ip', 'unknown')
            dst_ip = pkt.get('dst_ip', 'unknown')
            self.ip_stats[node_id][src_ip]["packets"] += 1
            self.ip_stats[node_id][src_ip]["bytes"] += pkt['length']
            self.ip_stats[node_id][dst_ip]["packets"] += 1
            self.ip_stats[node_id][dst_ip]["bytes"] += pkt['length']
            
            # Proto stats
            proto = pkt.get('proto', 'Other')
            self.protocol_stats[node_id][proto]["count"] += 1
            self.protocol_stats[node_id][proto]["bytes"] += pkt['length']
            
            # Flow tracking
            flow_key = (node_id, src_ip, dst_ip, pkt.get('src_port', 0), pkt.get('dst_port', 0), proto)
            if flow_key not in self.active_flows:
                self.active_flows[flow_key] = deque(maxlen=1000)
                
            self.active_flows[flow_key].append(pkt)
            self.flow_last_seen[flow_key] = pkt['timestamp']

state = AppState()
