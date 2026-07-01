import React from 'react'
import { Activity, Gauge, Network, AlertOctagon } from 'lucide-react'
import Header from './components/Header'
import StatCard from './components/StatCard'
import TrafficChart from './components/TrafficChart'
import ProtocolDonut from './components/ProtocolDonut'
import TopTalkers from './components/TopTalkers'
import AnomalyFeed from './components/AnomalyFeed'
import PacketTable from './components/PacketTable'
import { useSocket } from './hooks/useSocket'

function fmtBps(bps) {
  if (bps > 1e6) return [(bps / 1e6).toFixed(2), 'Mbps']
  if (bps > 1e3) return [(bps / 1e3).toFixed(1), 'Kbps']
  return [bps, 'bps']
}

export default function App() {
  const [selectedNode, setSelectedNode] = React.useState("All Nodes")
  const [nodes, setNodes] = React.useState([])
  const [protocolStats, setProtocolStats] = React.useState([])
  const [topTalkers, setTopTalkers] = React.useState([])
  
  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const resNodes = await fetch(`http://localhost:8000/api/nodes`)
        if (resNodes.ok) setNodes(await resNodes.json())
        
        const q = selectedNode === "All Nodes" ? "" : `?node_id=${selectedNode}`
        const resProto = await fetch(`http://localhost:8000/api/stats/protocols${q}`)
        if (resProto.ok) setProtocolStats(await resProto.json())
        
        const resTalkers = await fetch(`http://localhost:8000/api/stats/top-talkers${q}`)
        if (resTalkers.ok) setTopTalkers(await resTalkers.json())
      } catch (e) {}
    }
    fetchData()
    const int = setInterval(fetchData, 3000)
    return () => clearInterval(int)
  }, [selectedNode])

  const { connectionStatus, metrics, chartData, packets, anomalies, status } = useSocket(selectedNode)
  const [bpsVal, bpsUnit] = fmtBps(metrics.bps || 0)
  const criticalCount = anomalies.filter(a => a.severity === 'critical' || a.severity === 'high').length

  return (
    <div className="min-h-screen grid-overlay">
      <Header 
        connectionStatus={connectionStatus} 
        status={status} 
        nodes={nodes}
        selectedNode={selectedNode}
        setSelectedNode={setSelectedNode}
      />

      <main className="max-w-[1600px] mx-auto px-6 py-6 space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={Gauge} label="Packets / sec" value={metrics.pps?.toLocaleString() ?? 0} accent="signal" />
          <StatCard icon={Activity} label="Throughput" value={bpsVal} suffix={bpsUnit} accent="cyan" />
          <StatCard icon={Network} label="Active Flows" value={metrics.active_flows ?? 0} accent="signal" />
          <StatCard icon={AlertOctagon} label="High/Critical (session)" value={criticalCount} accent={criticalCount > 0 ? 'crimson' : 'amber'} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <TrafficChart data={chartData} />
          </div>
          <ProtocolDonut data={protocolStats} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <TopTalkers data={topTalkers} />
          <div className="lg:col-span-2">
            <AnomalyFeed anomalies={anomalies} />
          </div>
        </div>

        <PacketTable packets={packets} />

        <footer className="text-center font-mono text-[10px] text-muted py-4 tracking-wider">
          NEMESYS TRAFFIC SENTINEL — demo mode runs on synthetic data · wire up FastAPI backend per PRD section 3 &amp; 5
        </footer>
      </main>
    </div>
  )
}
