import React, { useState } from 'react'
import { AlertTriangle, ChevronDown } from 'lucide-react'

const SEVERITY_STYLE = {
  low: { bar: 'bg-cyan', text: 'text-cyan', label: 'LOW' },
  medium: { bar: 'bg-amber', text: 'text-amber', label: 'MEDIUM' },
  high: { bar: 'bg-amber', text: 'text-amber', label: 'HIGH' },
  critical: { bar: 'bg-crimson', text: 'text-crimson', label: 'CRITICAL' }
}

function timeAgo(ts) {
  const s = Math.floor((Date.now() - ts) / 1000)
  if (s < 60) return `${s}s ago`
  return `${Math.floor(s / 60)}m ago`
}

export default function AnomalyFeed({ anomalies }) {
  const [openId, setOpenId] = useState(null)

  return (
    <div className="rounded-lg border border-line bg-panel2 flex flex-col h-[460px]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-line">
        <h2 className="font-mono text-xs tracking-wider text-muted uppercase flex items-center gap-2">
          <AlertTriangle size={14} className="text-amber" /> Anomaly Feed
        </h2>
        <span className="font-mono text-[11px] px-2 py-0.5 rounded border border-line text-muted">{anomalies.length} flagged</span>
      </div>

      <div className="flex-1 overflow-y-auto divide-y divide-line">
        {anomalies.length === 0 && (
          <p className="font-mono text-xs text-muted p-4">No anomalies detected — baseline traffic nominal.</p>
        )}
        {anomalies.map((a) => {
          const s = SEVERITY_STYLE[a.severity] || SEVERITY_STYLE.low
          const open = openId === a.id
          return (
            <div key={a.id} className="px-4 py-3">
              <button onClick={() => setOpenId(open ? null : a.id)} className="w-full flex items-start gap-3 text-left">
                <span className={`mt-1 w-2 h-2 rounded-full shrink-0 ${s.bar}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`font-mono text-[11px] tracking-wider font-semibold ${s.text}`}>{s.label}</span>
                    <span className="font-mono text-[10px] text-muted shrink-0">{timeAgo(a.timestamp)}</span>
                  </div>
                  <p className="font-mono text-xs text-d8e2e6 mt-0.5 truncate">{a.reason.replaceAll('_', ' ')}</p>
                  <p className="font-mono text-[11px] text-muted truncate">{a.src_ip} → {a.dst_ip} · score {a.score}</p>
                </div>
                <ChevronDown size={14} className={`text-muted shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
              </button>
              {open && (
                <div className="mt-2 ml-5 p-3 rounded border border-line bg-panel font-mono text-[11px] text-muted space-y-1">
                  {Object.entries(a.details || {}).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span>{k}</span><span className="text-d8e2e6">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
