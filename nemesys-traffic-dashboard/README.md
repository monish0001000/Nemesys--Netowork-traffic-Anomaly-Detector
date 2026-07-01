# NEMESYS Traffic Sentinel — Dashboard

Frontend for real-time network traffic anomaly detection (Wireshark + scikit-learn backend). Ships in **mock mode** out of the box — runs and looks fully alive with zero backend.

## Run (Kali Linux or any Linux/macOS/WSL)

```bash
npm install
npm run dev
```
Open http://localhost:5173

## Connect to the real backend

1. Build the FastAPI backend per `PRD_NEMESYS_TRAFFIC_SENTINEL.md` (sections 3 & 5).
2. `cp .env.example .env` and point `VITE_WS_URL` / `VITE_API_URL` at your backend.
3. In `src/hooks/useSocket.js` set `const USE_MOCK = false`.
4. `npm run dev` again — the dashboard now drives off live `tshark` + IsolationForest output.

## Production build

```bash
npm run build       # outputs to dist/
npm run preview     # serve the build locally
```
Serve `dist/` via the FastAPI backend itself (StaticFiles mount) or nginx for a single-box Kali deployment.

## Structure
```
src/
  components/   UI pieces (Header, charts, feed, table)
  hooks/        useSocket.js — the ONE integration point with the backend
  lib/          mockData.js — synthetic live feed for dev/demo
```
