# PRD — NEMESYS TRAFFIC SENTINEL
### Real-Time Network Traffic Anomaly Detection (Wireshark + Scikit-learn) — Kali Linux

Version 1.0 | Owner: Monish | Status: Build-ready

---

## 1. Problem & Goal

Security analysts staring at raw `tshark`/Wireshark captures can't spot anomalies in real time without manual filtering. The goal is a self-hosted SOC-style dashboard on Kali Linux that:

1. Captures live packets via `tshark` (Wireshark CLI engine) on a chosen interface.
2. Extracts flow-level features in near-real-time.
3. Scores each flow/window with a scikit-learn anomaly model (Isolation Forest, unsupervised — no labeled attack data needed).
4. Streams results to a web dashboard with live charts, an anomaly feed, and packet-level drill-down.

This is a single-host tool (runs on the same Kali box doing the capture), not a distributed SIEM.

---

## 2. System Architecture

```
┌─────────────────────┐
│   Kali Linux Host    │
│                       │
│  ┌─────────────┐     │      ┌────────────────────┐      ┌──────────────────┐
│  │  tshark      │     │      │  Python Backend      │      │  React Dashboard   │
│  │  (capture)   │ ───▶│ ───▶ │  FastAPI + asyncio    │ ───▶ │  (this frontend)   │
│  │  -i eth0 -T  │     │      │                       │ WS   │                    │
│  │  ek/json     │     │      │  • PacketReader        │      │  Recharts/SVG     │
│  └─────────────┘     │      │  • FeatureExtractor    │      │  Live updates      │
│        capture.pcap  │      │  • IsolationForest      │      │  Alert feed        │
│        (rotating)    │      │    (scikit-learn)       │      └──────────────────┘
│                       │      │  • AlertEngine          │
│                       │      │  • REST + WebSocket API │
└──────────────────────┘      └────────────────────────┘
```

**Why this split:** `tshark` needs root/cap_net_raw and is the only piece tightly coupled to Kali/Wireshark. Everything else (feature engineering, ML inference, serving) is plain Python + a normal web frontend, so the frontend you're given here can be developed/tested completely independent of packet capture, against a mock WebSocket feed.

---

## 3. Backend Design (build this next, frontend already contracts against it)

### 3.1 Packet Capture Layer
- Use `tshark -i <iface> -l -T ek` (line-buffered JSON, one packet object per line) piped into Python via `subprocess.Popen(..., stdout=PIPE)`, OR use `pyshark` (LiveCapture) which wraps the same tshark process.
- Run with `setcap cap_net_raw,cap_net_admin=eip $(which dumpcap)` once, so the backend doesn't need to run as root.
- Each packet parsed for: timestamp, src_ip, dst_ip, src_port, dst_port, protocol, length, tcp_flags.

### 3.2 Feature Extraction (sliding window, e.g. 2s buckets per flow 5-tuple)
Per flow-window, compute the features the IsolationForest is trained on:
- `packet_count`, `byte_count`, `avg_packet_size`, `packet_rate` (pkts/sec)
- `unique_dst_ports` (port-scan signal), `syn_count`, `syn_without_ack_ratio`
- `protocol_entropy` (mix of TCP/UDP/ICMP in window)
- `duration`, `bytes_per_second`

### 3.3 Model
- `sklearn.ensemble.IsolationForest(n_estimators=200, contamination=0.02)`.
- Train once offline on a baseline "normal" capture (e.g. 30–60 min of your own clean traffic), serialize with `joblib`.
- At inference time: `score = model.decision_function(features)`; flag anomaly if `score < threshold` (or use `model.predict()` → `-1`).
- Severity bucket: map `score` into `low / medium / high / critical` via percentile thresholds — this maps directly onto the severity badges in the frontend's `AnomalyFeed`.
- Retrain periodically (cron / button-triggered) as traffic patterns drift — surfaced in UI via a "Model trained: Xh ago" indicator (already stubbed in `Header.jsx`).

### 3.4 API Contract (the frontend in this delivery is built exactly to this contract)

**REST**
| Method | Path | Returns |
|---|---|---|
| GET | `/api/status` | `{capturing: bool, interface: str, model_age_minutes: int, packets_total: int}` |
| GET | `/api/interfaces` | `[{name, description}]` — populate interface selector |
| POST | `/api/capture/start` | `{interface: str}` body → starts tshark subprocess |
| POST | `/api/capture/stop` | stops capture |
| GET | `/api/stats/protocols?window=5m` | `[{protocol, count, bytes}]` — feeds `ProtocolDonut` |
| GET | `/api/stats/top-talkers?window=5m&limit=10` | `[{ip, packets, bytes, country?}]` — feeds `TopTalkers` |
| GET | `/api/alerts?limit=50&severity=` | paginated historical alerts — feeds `AnomalyFeed` on load |
| GET | `/api/packets?limit=100` | recent raw packets — feeds `PacketTable` |
| POST | `/api/model/retrain` | triggers offline retrain job |

**WebSocket** — `ws://<host>:8000/ws/live`
Single multiplexed stream, message envelope:
```json
{ "type": "metric_tick",  "payload": { "timestamp": 169..., "pps": 1423, "bps": 8820213, "active_flows": 87 } }
{ "type": "anomaly",      "payload": { "id": "uuid", "timestamp": 169..., "severity": "high", "src_ip": "10.0.0.5", "dst_ip": "8.8.8.8", "reason": "port_scan", "score": -0.41, "details": {...} } }
{ "type": "packet",       "payload": { "timestamp":..., "src_ip":..., "dst_ip":..., "proto":"TCP", "length": 1500, "flags":"SYN" } }
{ "type": "status",       "payload": { "capturing": true, "packets_total": 102934 } }
```
`type` is the dispatch key the frontend's `useSocket` hook switches on — extend the `switch` block in that hook when adding new message types, nothing else in the component tree needs to change.

### 3.5 Tech Stack (backend, to be built)
- Python 3.11, FastAPI, `uvicorn[standard]` (native WS support), `pyshark`/`tshark`, `scikit-learn`, `pandas`, `joblib`, `pydantic`.
- Optional: SQLite (via `sqlmodel`) for alert/packet history instead of in-memory ring buffers.

---

## 4. Frontend Requirements (delivered in this package)

- **Stack**: React 18 + Vite, Tailwind CSS, Recharts for charting, lucide-react for icons. Zero backend dependency to run in demo mode (ships with a mock WebSocket data generator so you can develop/style without the Python side running yet).
- **Views / Components**:
  1. **Header** — interface selector, capture start/stop toggle, live connection-status pill, model-age indicator.
  2. **Stat strip** — packets/sec, throughput (bps), active flows, anomalies (last hour) as 4 KPI cards.
  3. **Traffic Chart** — live area/line chart of packets-per-second over a rolling 60s window.
  4. **Protocol Donut** — live protocol mix (TCP/UDP/ICMP/Other).
  5. **Top Talkers** — ranked table of IPs by bytes, with mini sparkbar.
  6. **Anomaly Feed** — real-time scrolling list of flagged events, color-coded by severity, expandable for raw feature detail.
  7. **Packet Table** — recent raw packets, filterable by protocol/IP, virtualized-style scroll.
- **Connection layer**: a single `useSocket` hook owns the WebSocket connection, auto-reconnect with backoff, and exposes typed state (`metrics`, `anomalies`, `packets`, `connectionStatus`). Swapping the mock generator for a real socket is a one-line change (`VITE_WS_URL` env var + flip `USE_MOCK`).
- **Design direction**: dark "SOC ops room" theme — near-black base, signal-green/amber/red severity language (matches the threat-tooling aesthetic of your other NEMESYS/SHIELD projects), monospace for IPs/hex/timestamps, sans for UI chrome.

---

## 5. Integration Steps (once backend is built)

1. `cd backend && uvicorn main:app --host 0.0.0.0 --port 8000`
2. In `nemesys-traffic-dashboard/.env`: set `VITE_WS_URL=ws://localhost:8000/ws/live` and `VITE_API_URL=http://localhost:8000/api`.
3. In `src/hooks/useSocket.js` set `USE_MOCK = false`.
4. `npm run dev` (or `npm run build` + serve `dist/` via the FastAPI app itself / nginx for a single-binary deploy on Kali).
5. Run capture as non-root via the `cap_net_raw` setcap step above; start capture either via the dashboard's Start button (`POST /api/capture/start`) or a systemd unit.

---

## 6. Non-functional requirements
- Dashboard must stay responsive with feed rates up to ~2,000 pps (throttle packet table to last 100 rows, batch chart updates to 1/sec).
- WebSocket reconnect within 3s of drop, with visible "reconnecting…" state — never a silent stale UI.
- All ML inference stays local — no traffic data leaves the host.
- Works on a single Kali VM with 4GB RAM; backend ring-buffers (not unbounded growth) for in-memory packet/alert history.

---

## 7. Milestones
1. ✅ Frontend dashboard (mock-data driven) — delivered here.
2. Backend skeleton: FastAPI + WS + mock metric emitter (validate contract against this frontend with zero ML).
3. tshark capture + feature extraction pipeline (no ML yet — just feed real packets into the same WS contract).
4. Train IsolationForest baseline, wire in scoring + alert emission.
5. Polish: retrain endpoint, persistence (SQLite), packet/alert filtering on backend.
