import { useState, useEffect } from 'react'
import { Filter, Search } from 'lucide-react'
import { dashboardAPI } from '../api/client'
import AlertCard from '../components/AlertCard'
import Topbar from '../components/Topbar'

const SEVS = ['all','critical','high','medium','low']
const STATS = ['all','open','investigating','resolved']

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [sev, setSev] = useState('all')
  const [sta, setSta] = useState('open')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  const fetch = () => {
    const p = {}
    if (sev !== 'all') p.severity = sev
    if (sta !== 'all') p.status = sta
    dashboardAPI.alerts(p).then(r => setAlerts(r.data)).catch(console.error).finally(() => setLoading(false))
  }
  useEffect(() => { fetch() }, [sev, sta])

  const update = async (id, data) => { await dashboardAPI.updateAlert(id, data); fetch() }

  const filtered = alerts.filter(a =>
    !search || a.title.toLowerCase().includes(search.toLowerCase()) || a.description.toLowerCase().includes(search.toLowerCase())
  )

  const Chip = ({ opts, cur, set }) => (
    <div style={{ display:'flex', gap:6, flexWrap:'wrap' }}>
      {opts.map(o => (
        <button key={o} onClick={() => set(o)} style={{
          padding:'4px 12px', borderRadius:20, fontSize:11, cursor:'pointer',
          border: cur===o ? '1px solid #0070f3' : '1px solid rgba(30,58,95,0.5)',
          background: cur===o ? 'rgba(0,112,243,0.15)' : 'transparent',
          color: cur===o ? '#4a9eff' : '#4a6fa5', fontWeight: cur===o ? 600 : 400,
          textTransform:'capitalize', transition:'all 0.15s'
        }}>{o}</button>
      ))}
    </div>
  )

  return (
    <div>
      <Topbar title="Alerts" subtitle={`${filtered.length} alerts`} onRefresh={fetch} />
      <div style={{ padding:28 }}>
        {/* Filters */}
        <div style={{ background:'linear-gradient(135deg,#0d1321,#0a0f1e)', border:'1px solid rgba(30,58,95,0.5)', borderRadius:12, padding:18, marginBottom:20 }}>
          <div style={{ display:'flex', gap:24, flexWrap:'wrap', alignItems:'flex-start' }}>
            <div>
              <div style={{ fontSize:10, color:'#4a6fa5', marginBottom:6, textTransform:'uppercase', letterSpacing:1, fontWeight:600 }}>Severity</div>
              <Chip opts={SEVS} cur={sev} set={setSev} />
            </div>
            <div>
              <div style={{ fontSize:10, color:'#4a6fa5', marginBottom:6, textTransform:'uppercase', letterSpacing:1, fontWeight:600 }}>Status</div>
              <Chip opts={STATS} cur={sta} set={setSta} />
            </div>
            <div style={{ marginLeft:'auto' }}>
              <div style={{ fontSize:10, color:'#4a6fa5', marginBottom:6, textTransform:'uppercase', letterSpacing:1, fontWeight:600 }}>Search</div>
              <div style={{ position:'relative' }}>
                <Search size={12} style={{ position:'absolute', left:10, top:'50%', transform:'translateY(-50%)', color:'#4a6fa5' }} />
                <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search alerts..."
                  style={{ padding:'6px 12px 6px 28px', background:'rgba(13,19,33,0.8)', border:'1px solid rgba(30,58,95,0.5)',
                    borderRadius:8, color:'#e2e8f0', fontSize:12, outline:'none', width:200 }} />
              </div>
            </div>
          </div>
        </div>

        {loading ? <div style={{ color:'#4a6fa5', padding:40, textAlign:'center' }}>Loading alerts...</div>
         : filtered.length === 0 ? (
          <div style={{ background:'linear-gradient(135deg,#0d1321,#0a0f1e)', border:'1px solid rgba(30,58,95,0.5)',
            borderRadius:12, padding:'60px 40px', textAlign:'center' }}>
            <Filter size={32} style={{ color:'#2a3f5f', margin:'0 auto 12px', display:'block' }} />
            <div style={{ color:'#4a6fa5', fontSize:14 }}>No alerts match your filters</div>
          </div>
        ) : filtered.map(a => <AlertCard key={a.id} alert={a} onUpdate={update} />)}
      </div>
    </div>
  )
}
