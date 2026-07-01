// Simulates the real backend's WebSocket feed described in the PRD (/ws/live).
// Swap out by setting USE_MOCK=false in useSocket.js once the FastAPI backend is live.

const PROTOCOLS = ['TCP', 'UDP', 'ICMP', 'DNS', 'TLS', 'ARP']
const SEVERITIES = ['low', 'medium', 'high', 'critical']
const REASONS = [
  'port_scan_pattern', 'syn_flood_burst', 'unusual_payload_entropy',
  'beaconing_interval', 'dns_tunneling_suspected', 'rare_destination_port',
  'protocol_anomaly', 'data_exfil_volume_spike'
]

const randIp = () => `${10 + Math.floor(Math.random() * 200)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)]

let packetsTotal = 184213
const baseIps = Array.from({ length: 6 }, randIp)

export function createMockEngine(onMessage) {
  let alive = true

  const metricTimer = setInterval(() => {
    if (!alive) return
    const pps = Math.round(800 + Math.random() * 1400 + Math.sin(Date.now() / 4000) * 300)
    packetsTotal += pps
    onMessage({
      type: 'metric_tick',
      payload: {
        timestamp: Date.now(),
        pps,
        bps: Math.round(pps * (400 + Math.random() * 800)),
        active_flows: Math.round(40 + Math.random() * 90),
        packets_total: packetsTotal
      }
    })
  }, 1000)

  const packetTimer = setInterval(() => {
    if (!alive) return
    onMessage({
      type: 'packet',
      payload: {
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        src_ip: pick(baseIps),
        dst_ip: randIp(),
        src_port: Math.round(1024 + Math.random() * 64000),
        dst_port: pick([22, 80, 443, 53, 8080, 3389, 445, 21]),
        proto: pick(PROTOCOLS),
        length: Math.round(64 + Math.random() * 1440),
        flags: pick(['SYN', 'ACK', 'SYN-ACK', 'PSH-ACK', 'FIN', '-'])
      }
    })
  }, 350)

  const protocolTimer = setInterval(() => {
    if (!alive) return
    onMessage({
      type: 'protocol_stats',
      payload: PROTOCOLS.map(p => ({
        protocol: p,
        count: Math.round(20 + Math.random() * 400),
        bytes: Math.round(2000 + Math.random() * 900000)
      }))
    })
  }, 2500)

  const talkerTimer = setInterval(() => {
    if (!alive) return
    onMessage({
      type: 'top_talkers',
      payload: baseIps
        .map(ip => ({
          ip,
          packets: Math.round(100 + Math.random() * 5000),
          bytes: Math.round(50000 + Math.random() * 4000000)
        }))
        .sort((a, b) => b.bytes - a.bytes)
    })
  }, 3000)

  const anomalyTimer = setInterval(() => {
    if (!alive) return
    if (Math.random() > 0.62) {
      const severity = pick(SEVERITIES)
      onMessage({
        type: 'anomaly',
        payload: {
          id: crypto.randomUUID(),
          timestamp: Date.now(),
          severity,
          src_ip: pick(baseIps),
          dst_ip: randIp(),
          reason: pick(REASONS),
          score: -(Math.random() * 0.6 + 0.05).toFixed(3),
          details: {
            packet_count: Math.round(10 + Math.random() * 900),
            unique_dst_ports: Math.round(1 + Math.random() * 40),
            syn_ratio: (Math.random()).toFixed(2),
            window_s: 2
          }
        }
      })
    }
  }, 2200)

  onMessage({ type: 'status', payload: { capturing: true, packets_total: packetsTotal, interface: 'eth0 (mock)' } })

  return () => {
    alive = false
    clearInterval(metricTimer)
    clearInterval(packetTimer)
    clearInterval(protocolTimer)
    clearInterval(talkerTimer)
    clearInterval(anomalyTimer)
  }
}
