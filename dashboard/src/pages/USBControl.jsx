import { useEffect, useState } from 'react'
import { Shield, Usb } from 'lucide-react'
import Topbar from '../components/Topbar'
import { dashboardAPI } from '../api/client'


const POLICIES = ['allow_all', 'block_all', 'whitelist']


export default function USBControl() {
  const [policy, setPolicy] = useState('allow_all')
  const [devices, setDevices] = useState([])
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchAll = () => {
    Promise.all([
      dashboardAPI.usbPolicy(),
      dashboardAPI.usbWhitelist(),
      dashboardAPI.events({ event_type: 'usb', limit: 80 }),
    ])
      .then(([policyResponse, devicesResponse, eventsResponse]) => {
        setPolicy(policyResponse.data?.policy || 'allow_all')
        setDevices(devicesResponse.data || [])
        setEvents(eventsResponse.data || [])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchAll()
  }, [])

  const updatePolicy = async next => {
    await dashboardAPI.setUsbPolicy(next)
    setPolicy(next)
  }

  const setWhitelist = async (device, isWhitelisted) => {
    await dashboardAPI.upsertUsbWhitelist({
      device_id: device.device_id,
      device_name: device.device_name,
      vendor: device.vendor,
      size: device.size,
      is_whitelisted: isWhitelisted,
    })
    fetchAll()
  }

  return (
    <div>
      <Topbar title="USB Control" subtitle="Control removable media usage across your employee fleet" onRefresh={fetchAll} />
      <div className="page-wrap">
        <div className="panel" style={{ padding: 18, marginBottom: 16 }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>USB Access Policy</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {POLICIES.map(item => (
              <button
                key={item}
                className="btn-secondary"
                onClick={() => updatePolicy(item)}
                style={{
                  padding: '8px 12px',
                  borderColor: policy === item ? 'rgba(0,112,243,0.5)' : undefined,
                  background: policy === item ? 'rgba(0,112,243,0.16)' : undefined,
                  textTransform: 'capitalize',
                }}
              >
                {item.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div className="grid-two">
          <div className="panel" style={{ padding: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <Usb size={17} color="#0070f3" />
              <div style={{ fontWeight: 800 }}>Detected USB Devices</div>
            </div>
            {loading ? (
              <div className="soft-note">Loading USB devices...</div>
            ) : devices.length === 0 ? (
              <div className="soft-note">No USB devices detected yet.</div>
            ) : (
              <div style={{ display: 'grid', gap: 10 }}>
                {devices.map(device => (
                  <div key={device.id} className="soft-note">
                    <div style={{ fontWeight: 700 }}>{device.device_name || device.device_id}</div>
                    <div style={{ color: 'var(--muted)', marginTop: 4, fontSize: 12 }}>{device.vendor || 'Unknown vendor'} | {device.size || 'Unknown size'}</div>
                    <div style={{ color: 'var(--muted)', marginTop: 4, fontSize: 12 }}>{device.device_id}</div>
                    <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                      <button className="btn-secondary" onClick={() => setWhitelist(device, true)} style={{ padding: '7px 10px', color: '#2ed573' }}>Approve</button>
                      <button className="btn-secondary" onClick={() => setWhitelist(device, false)} style={{ padding: '7px 10px', color: '#ff4757' }}>Block</button>
                      <span style={{ marginLeft: 'auto', fontSize: 11, color: device.is_whitelisted ? '#2ed573' : '#ff4757', fontWeight: 700 }}>
                        {device.is_whitelisted ? 'Whitelisted' : 'Not whitelisted'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="panel" style={{ padding: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <Shield size={17} color="#ffa502" />
              <div style={{ fontWeight: 800 }}>Real-time USB Activity</div>
            </div>
            {events.length === 0 ? (
              <div className="soft-note">No USB events found yet.</div>
            ) : (
              <div style={{ display: 'grid', gap: 8, maxHeight: 540, overflow: 'auto' }}>
                {events.map(item => (
                  <div key={item.id} className="soft-note">
                    <div style={{ fontWeight: 700 }}>{(item.payload?.action || 'activity').toUpperCase()}</div>
                    <div style={{ color: 'var(--muted)', marginTop: 4, fontSize: 12 }}>
                      {item.payload?.device_name || item.payload?.device_id || 'USB device'}
                    </div>
                    <div style={{ color: 'var(--muted)', marginTop: 4, fontSize: 12 }}>
                      {new Date(item.created_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
