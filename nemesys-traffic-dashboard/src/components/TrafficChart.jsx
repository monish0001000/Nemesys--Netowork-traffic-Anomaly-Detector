import React from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function TrafficChart({ data }) {
  return (
    <div className="rounded-lg border border-line bg-panel2 p-4 h-[300px] flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <h2 className="font-mono text-xs tracking-wider text-muted uppercase">Live Traffic — packets/sec</h2>
        <span className="font-mono text-[11px] text-signal">rolling 60s</span>
      </div>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="ppsFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#39ff8f" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#39ff8f" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#1c2329" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="t" tick={{ fill: '#5d6b73', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={{ stroke: '#1c2329' }} tickLine={false} minTickGap={40} />
          <YAxis tick={{ fill: '#5d6b73', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} width={45} />
          <Tooltip
            contentStyle={{ background: '#0b0f12', border: '1px solid #1c2329', borderRadius: 6, fontFamily: 'JetBrains Mono', fontSize: 12 }}
            labelStyle={{ color: '#5d6b73' }}
            itemStyle={{ color: '#39ff8f' }}
          />
          <Area type="monotone" dataKey="pps" stroke="#39ff8f" strokeWidth={2} fill="url(#ppsFill)" isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
