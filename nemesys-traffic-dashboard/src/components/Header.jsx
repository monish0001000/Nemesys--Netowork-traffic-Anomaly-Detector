import React from 'react'
import { Shield, Radio, Cpu, ChevronDown } from 'lucide-react'

const STATUS_MAP = {
  live: { label: 'LIVE', color: 'text-signal', dot: 'bg-signal' },
  connecting: { label: 'CONNECTING', color: 'text-amber', dot: 'bg-amber' },
  reconnecting: { label: 'RECONNECTING', color: 'text-amber', dot: 'bg-amber' },
  offline: { label: 'OFFLINE', color: 'text-crimson', dot: 'bg-crimson' }
}

export default function Header({ connectionStatus, status, nodes, selectedNode, setSelectedNode }) {
  const s = STATUS_MAP[connectionStatus] || STATUS_MAP.offline

  return (
    <header className="border-b border-line bg-panel/80 backdrop-blur sticky top-0 z-20">
      <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between gap-6 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded border border-signal/40 flex items-center justify-center shadow-glow">
            <Shield size={18} className="text-signal" />
          </div>
          <div>
            <h1 className="font-mono text-sm tracking-[0.25em] text-d8e2e6 font-semibold">
              NEMESYS <span className="text-signal">// TRAFFIC SENTINEL</span>
            </h1>
            <p className="text-[11px] text-muted font-mono tracking-wide">Real-time anomaly detection — Wireshark + scikit-learn</p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded border border-line bg-panel2 font-mono text-xs relative group cursor-pointer">
            <Cpu size={13} className="text-purple-400" />
            <span className="text-muted">NODE</span>
            <span className="text-purple-400">{selectedNode}</span>
            <ChevronDown size={12} className="text-muted" />
            <div className="absolute top-full mt-2 left-0 min-w-full bg-panel border border-line rounded hidden group-hover:block z-50 shadow-xl overflow-hidden">
              <div 
                className={`px-4 py-2 hover:bg-line/50 whitespace-nowrap ${selectedNode === "All Nodes" ? "text-signal bg-line/20" : "text-muted"}`}
                onClick={() => setSelectedNode("All Nodes")}
              >
                All Nodes
              </div>
              {nodes.map(n => (
                <div 
                  key={n} 
                  className={`px-4 py-2 hover:bg-line/50 whitespace-nowrap ${selectedNode === n ? "text-signal bg-line/20" : "text-muted"}`}
                  onClick={() => setSelectedNode(n)}
                >
                  {n}
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded border border-line bg-panel2 font-mono text-xs">
            <Radio size={13} className={s.color} />
            <span className={`w-1.5 h-1.5 rounded-full ${s.dot} animate-pulseDot`} />
            <span className={s.color}>{s.label}</span>
          </div>
        </div>
      </div>
    </header>
  )
}
