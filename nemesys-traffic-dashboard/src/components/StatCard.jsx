import React from 'react'

export default function StatCard({ icon: Icon, label, value, suffix, accent = 'signal', trend }) {
  const colorMap = {
    signal: 'text-signal border-signal/30 shadow-glow',
    amber: 'text-amber border-amber/30 shadow-glowAmber',
    crimson: 'text-crimson border-crimson/30 shadow-glowRed',
    cyan: 'text-cyan border-cyan/30'
  }
  return (
    <div className="relative overflow-hidden rounded-lg border border-line bg-panel2 p-4 flex items-center gap-4">
      <div className={`w-10 h-10 shrink-0 rounded border flex items-center justify-center ${colorMap[accent]}`}>
        <Icon size={18} />
      </div>
      <div className="min-w-0">
        <p className="text-[11px] font-mono text-muted tracking-wider uppercase">{label}</p>
        <p className="font-mono text-2xl font-semibold text-d8e2e6 leading-tight truncate">
          {value}<span className="text-sm text-muted ml-1">{suffix}</span>
        </p>
        {trend && <p className="text-[11px] font-mono text-muted">{trend}</p>}
      </div>
    </div>
  )
}
