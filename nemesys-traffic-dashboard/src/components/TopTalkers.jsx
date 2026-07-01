import React from 'react'

function fmtBytes(b) {
  if (b > 1e6) return (b / 1e6).toFixed(2) + ' MB'
  if (b > 1e3) return (b / 1e3).toFixed(1) + ' KB'
  return b + ' B'
}

export default function TopTalkers({ data }) {
  const max = Math.max(...data.map(d => d.bytes), 1)
  return (
    <div className="rounded-lg border border-line bg-panel2 p-4 h-[300px] flex flex-col">
      <h2 className="font-mono text-xs tracking-wider text-muted uppercase mb-3">Top Talkers</h2>
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {data.map((t, i) => (
          <div key={t.ip} className="font-mono text-xs">
            <div className="flex items-center justify-between mb-1">
              <span className="text-d8e2e6">{i + 1}. {t.ip}</span>
              <span className="text-cyan">{fmtBytes(t.bytes)}</span>
            </div>
            <div className="h-1.5 rounded-full bg-line overflow-hidden">
              <div className="h-full bg-gradient-to-r from-signal to-cyan" style={{ width: `${(t.bytes / max) * 100}%` }} />
            </div>
          </div>
        ))}
        {data.length === 0 && <p className="text-muted font-mono text-xs">awaiting flow data…</p>}
      </div>
    </div>
  )
}
