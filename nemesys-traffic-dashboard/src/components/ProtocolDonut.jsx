import React from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

const COLORS = ['#39ff8f', '#3ad6ff', '#ffb648', '#ff4d5e', '#9b7cff', '#5d6b73']

export default function ProtocolDonut({ data }) {
  const total = data.reduce((s, d) => s + d.count, 0) || 1
  return (
    <div className="rounded-lg border border-line bg-panel2 p-4 h-[300px] flex flex-col">
      <h2 className="font-mono text-xs tracking-wider text-muted uppercase mb-2">Protocol Mix</h2>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="count" nameKey="protocol" innerRadius={55} outerRadius={85} paddingAngle={3} isAnimationActive={false}>
            {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="#0b0f12" strokeWidth={2} />)}
          </Pie>
          <Tooltip
            contentStyle={{ background: '#0b0f12', border: '1px solid #1c2329', borderRadius: 6, fontFamily: 'JetBrains Mono', fontSize: 12 }}
            formatter={(value, name) => [`${value} (${((value / total) * 100).toFixed(1)}%)`, name]}
          />
          <Legend
            verticalAlign="bottom"
            height={28}
            formatter={(value) => <span className="font-mono text-[11px] text-muted">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
