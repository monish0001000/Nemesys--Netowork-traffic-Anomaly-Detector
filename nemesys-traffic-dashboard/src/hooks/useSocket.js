import { useEffect, useRef, useState, useCallback } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live'

const MAX_PACKETS = 120
const MAX_ANOMALIES = 60
const MAX_CHART_POINTS = 60

export function useSocket(selectedNode = "All Nodes") {
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  
  // Store all data keyed by node_id
  const [metricsByNode, setMetricsByNode] = useState({})
  const [chartByNode, setChartByNode] = useState({})
  const [packetsByNode, setPacketsByNode] = useState({})
  const [anomaliesByNode, setAnomaliesByNode] = useState({})
  const [status, setStatus] = useState({ capturing: false, interface: '—' })

  const wsRef = useRef(null)
  const retryRef = useRef(0)

  const handleMessage = useCallback((msg) => {
    switch (msg.type) {
      case 'metric_tick': {
        const p = msg.payload;
        const nid = p.node_id;
        
        setMetricsByNode(prev => ({ ...prev, [nid]: p }))
        setChartByNode(prev => {
          const arr = prev[nid] || [];
          const next = [...arr, {
            t: new Date(p.timestamp).toLocaleTimeString('en-GB'),
            pps: p.pps,
            bps: Math.round(p.bps / 1024)
          }]
          return { ...prev, [nid]: next.slice(-MAX_CHART_POINTS) }
        })
        break
      }
      case 'packet': {
        const p = msg.payload;
        const nid = p.node_id || "local";
        setPacketsByNode(prev => {
          const arr = prev[nid] || [];
          const nextNid = [p, ...arr].slice(0, MAX_PACKETS);
          const arrAll = prev["All Nodes"] || [];
          const nextAll = [p, ...arrAll].slice(0, MAX_PACKETS);
          return { ...prev, [nid]: nextNid, "All Nodes": nextAll }
        })
        break
      }
      case 'anomaly': {
        const p = msg.payload;
        const nid = p.node_id || "local";
        setAnomaliesByNode(prev => {
          const arr = prev[nid] || [];
          const nextNid = [p, ...arr].slice(0, MAX_ANOMALIES);
          const arrAll = prev["All Nodes"] || [];
          const nextAll = [p, ...arrAll].slice(0, MAX_ANOMALIES);
          return { ...prev, [nid]: nextNid, "All Nodes": nextAll }
        })
        break
      }
      case 'status':
        setStatus(prev => ({ ...prev, ...msg.payload }))
        break
      default:
        break
    }
  }, [])

  useEffect(() => {
    function connect() {
      setConnectionStatus(retryRef.current === 0 ? 'connecting' : 'reconnecting')
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        retryRef.current = 0
        setConnectionStatus('live')
      }
      ws.onmessage = (evt) => {
        try {
          handleMessage(JSON.parse(evt.data))
        } catch (e) {
          console.error('Bad WS payload', e)
        }
      }
      ws.onclose = () => {
        setConnectionStatus('reconnecting')
        retryRef.current += 1
        const backoff = Math.min(1000 * 2 ** retryRef.current, 10000)
        setTimeout(connect, backoff)
      }
      ws.onerror = () => ws.close()
    }

    connect()
    return () => wsRef.current?.close()
  }, [handleMessage])

  return {
    connectionStatus,
    status,
    metrics: metricsByNode[selectedNode] || { pps: 0, bps: 0, active_flows: 0 },
    chartData: chartByNode[selectedNode] || [],
    packets: packetsByNode[selectedNode] || [],
    anomalies: anomaliesByNode[selectedNode] || []
  }
}
