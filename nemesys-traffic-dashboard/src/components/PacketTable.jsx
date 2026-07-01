import React, { useState, useMemo } from 'react'
import { ListFilter } from 'lucide-react'

export default function PacketTable({ packets }) {
  const [filter, setFilter] = useState('ALL')
  const protocols = ['ALL', ...Array.from(new Set(packets.map(p => p.proto)))]

  const rows = useMemo(
    () => (filter === 'ALL' ? packets : packets.filter(p => p.proto === filter)).slice(0, 40),
    [packets, filter]
  )

  return (
    <div className="rounded-lg border border-line bg-panel2 flex flex-col h-[460px]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-line">
        <h2 className="font-mono text-xs tracking-wider text-muted uppercase">Live Packet Stream</h2>
        <div className="flex items-center gap-1.5">
          <ListFilter size={12} className="text-muted" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-panel border border-line rounded text-[11px] font-mono text-d8e2e6 px-2 py-1 outline-none"
          >
            {protocols.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-[11px] font-mono">
          <thead className="sticky top-0 bg-panel2 text-muted">
            <tr className="text-left">
              <th className="px-3 py-2 font-medium">TIME</th>
              <th className="px-3 py-2 font-medium">NODE</th>
              <th className="px-3 py-2 font-medium">SRC</th>
              <th className="px-3 py-2 font-medium">DST</th>
              <th className="px-3 py-2 font-medium">PROTO</th>
              <th className="px-3 py-2 font-medium">LEN</th>
              <th className="px-3 py-2 font-medium">FLAGS</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id} className="border-t border-line/60 hover:bg-panel transition-colors">
                <td className="px-3 py-1.5 text-muted">{new Date(p.timestamp).toLocaleTimeString('en-GB')}</td>
                <td className="px-3 py-1.5 text-amber opacity-80">{p.node_id || 'local'}</td>
                <td className="px-3 py-1.5 text-d8e2e6">{p.src_ip}:{p.src_port}</td>
                <td className="px-3 py-1.5 text-d8e2e6">{p.dst_ip}:{p.dst_port}</td>
                <td className="px-3 py-1.5 text-cyan">{p.proto}</td>
                <td className="px-3 py-1.5 text-muted">{p.length}B</td>
                <td className="px-3 py-1.5 text-amber">{p.flags}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={6} className="px-3 py-6 text-center text-muted">awaiting packets…</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
