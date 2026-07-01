# NEMESYS: In-Depth Architecture and Technical Explanation

NEMESYS (Network Traffic Sentinel) is a distributed, real-time network traffic analysis and anomaly detection platform. It is engineered to provide Security Operations Center (SOC) capabilities on a self-hosted environment, leveraging Unsupervised Machine Learning to detect malicious or anomalous network behaviors without relying on static signature databases.

This document serves as a deep dive into how NEMESYS works under the hood.

---

## 1. System Architecture

The NEMESYS architecture is strictly divided into three decoupled tiers:

1. **Telemetry Agents (Data Collection)**
2. **FastAPI Backend (Data Processing & Machine Learning)**
3. **React Dashboard (Data Visualization)**

### Data Flow Pipeline
1. **Agents** capture live network traffic on edge devices (Nodes).
2. Packets are parsed into a lightweight JSON schema and POSTed to the **Backend** via HTTP.
3. The Backend receives the packets, maintains a sliding window of state (Packets Per Second, Bytes Per Second, Active Flows), and extracts mathematical features.
4. An **Isolation Forest** ML model evaluates these features every few seconds to score the traffic.
5. High-risk scores trigger Anomalies.
6. The Backend routes raw packets, metrics, and anomalies through a **WebSocket** directly to the **Frontend Dashboard**.
7. The Dashboard dynamically renders the data in real-time, allowing users to filter by specific edge nodes.

---

## 2. Telemetry Agents (The Edge)

Agents run on the target devices you want to monitor. They are responsible for reading network traffic and forwarding it. NEMESYS provides two types of agents depending on the device's capabilities:

### A. TShark Agent (`tshark_agent.py`)
- **Technology**: Subprocesses Wireshark's `tshark` binary.
- **Use Case**: Deep packet inspection on Linux/Windows desktops.
- **How it works**: It spawns a `tshark` process listening on a specific interface (e.g., `eth0`), outputting raw packet data in JSON format (`-T json`). It parses fields like `ip.src`, `ip.dst`, `tcp.flags`, and `frame.len`.

### B. Lightweight Cross-Platform Agent (`telemetry_agent.py`)
- **Technology**: `psutil` and `socket`.
- **Use Case**: Mobile devices (Termux on Android), restricted environments, or systems without Wireshark.
- **How it works**: It rapidly polls the OS for active network connections (`psutil.net_connections`). By observing established sockets, it calculates traffic flow.
- **Fallback Mechanism**: Mobile operating systems (like Android) strictly restrict access to network socket tables. If `psutil` encounters an `AccessDenied` exception, the agent gracefully falls back to a **Mock Traffic Generator**, which mathematically simulates realistic packet bursts, TCP handshakes, and UDP streams so the dashboard can still be tested and demonstrated.

Both agents dynamically inject their machine's hostname (`socket.gethostname()`) as a `node_id` into every packet.

---

## 3. The Backend (Brain & ML Engine)

Written in Python using **FastAPI**, the backend is asynchronous and highly concurrent.

### State Management (`state.py`)
Because network traffic is high-velocity, NEMESYS does not rely on a slow database. It maintains an **in-memory sliding window** using Python `deque` and `defaultdict`s. 
- It tracks Top Talkers (IPs transferring the most bytes).
- It breaks down protocol distributions (TCP vs. UDP vs. ICMP).
- It groups all of these metrics by the specific `node_id` that sent them.

### Machine Learning: Isolation Forest (`model.py` & `features.py`)
Traditional firewalls use "Signatures" (e.g., "Block IP if payload contains XYZ"). NEMESYS uses **Unsupervised Machine Learning**.
- **The Algorithm**: Scikit-learn's `Isolation Forest`.
- **Why?**: Isolation Forests are exceptionally good at identifying anomalies without needing a labeled dataset of "hacks". It builds random decision trees. Normal traffic takes many splits to isolate, while anomalous traffic (like a sudden DDoS burst or port scan) looks drastically different and is isolated quickly.
- **Feature Extraction**: Every 2 seconds, the backend computes aggregate features across active flows:
  - Total flow duration
  - Bytes transferred (forward/backward)
  - Packet size variance
  - TCP Flag ratios (e.g., too many SYN flags = SYN Flood attack)
- **Scoring**: If the Isolation Forest returns a score below a certain threshold (e.g., `-0.05`), it triggers an Anomaly Event, assigning a severity (Medium, High, Critical) based on how negative the score is.

### WebSocket Broadcaster
FastAPI maintains an active WebSocket pool. As soon as a metric is calculated or an anomaly is flagged, a JSON payload is instantly pushed to all connected web browsers.

---

## 4. The Dashboard (Visualization)

The frontend is a modern Single Page Application (SPA) built with **React** and **Vite**.

- **Aesthetic**: It utilizes a dark, cyberpunk/hacker-themed UI (Glassmorphism, vibrant cyans, and crimsons) to emulate high-end SOC environments.
- **Real-Time Hook (`useSocket.js`)**: A custom React Hook maintains a persistent WebSocket connection to the backend. It automatically buffers the last 120 packets and 60 metrics, managing state updates at 60 FPS without crashing the browser.
- **Multi-Node Filtering**: The dashboard reads the `node_id` from incoming streams. The user can use the header dropdown to instantly pivot the entire UI—switching from a global network overview to inspecting the specific traffic and anomalies of a single Kali Linux or Android device.

---

## Conclusion
NEMESYS successfully combines low-level OS network hooks, modern asynchronous Python, unsupervised machine learning, and reactive UI design into a cohesive, real-time threat detection system.
