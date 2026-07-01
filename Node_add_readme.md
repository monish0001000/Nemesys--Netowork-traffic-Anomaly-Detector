# NEMESYS TRAFFIC SENTINEL: How to Add a New Node

This guide explains how to connect a new remote device (Windows, Linux, or Android via Termux) to your NEMESYS Traffic Sentinel dashboard so that its network telemetry can be monitored and analyzed for anomalies.

The backend acts as the central brain. It receives traffic from multiple devices, analyzes them using scikit-learn, and broadcasts the data to the React dashboard. Each device you connect will automatically appear in the dashboard's **NODE** dropdown based on its hostname.

---

## Prerequisites
Before you start, make sure the NEMESYS backend is running on your main host machine.
You must know the IP address of your host machine (e.g., `192.168.1.5`).

---

## Option 1: Lightweight Telemetry Agent (Cross-Platform)

This is the recommended agent. It uses `psutil` to observe actual active network connections. It does not require Wireshark, making it incredibly easy to run on almost any device (including mobile).

**Supported Platforms:** Windows, Linux, macOS, Android (via Termux)

### 1. Setup
Copy the `telemetry_agent.py` file from the main project to your target device. Then install the requirements:

```bash
pip install requests psutil
```

### 2. Run the Agent
Run the script, replacing `<HOST_IP>` with the IP address of the machine running the NEMESYS backend:

```bash
python telemetry_agent.py --url http://<HOST_IP>:8000
```

> **Note for Android/Termux:** If Android permissions block `psutil` from reading the socket tables natively, the script will automatically fallback to generating realistic mock traffic telemetry so you can still verify the connection to the dashboard.

---

## Option 2: TShark Telemetry Agent (Advanced Packet Capture)

This agent uses the `tshark` command-line tool (the engine behind Wireshark) to capture raw packets in real-time. It provides higher fidelity data but requires Wireshark to be installed.

**Supported Platforms:** Windows, Linux (requires root/sudo for capture capabilities).

### 1. Setup
Make sure `tshark` is installed on the target device:
- **Windows:** Install Wireshark (ensure TShark is checked during installation).
- **Linux:** `sudo apt install tshark`

Copy the `tshark_agent.py` file from the main project to the target device. Install requirements:

```bash
pip install requests
```

### 2. Run the Agent
You need to specify the network interface you want to monitor (e.g., `eth0`, `wlan0`, or `"Wi-Fi"` on Windows).

**On Linux:**
```bash
sudo python tshark_agent.py -i wlan0 --url http://<HOST_IP>:8000
```

**On Windows (Run as Administrator):**
```bash
python tshark_agent.py -i "Wi-Fi" --url http://<HOST_IP>:8000
```

---

## Verifying the Connection

1. Open your NEMESYS web dashboard (`http://<HOST_IP>:5173/`).
2. Look at the top right of the header for the **NODE** selector.
3. Click the dropdown. You should see the hostname of your newly connected device appear alongside "All Nodes".
4. Select the new node to filter the dashboard and view its traffic exclusively!
