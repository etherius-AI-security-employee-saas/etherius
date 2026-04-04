import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, KeyRound, ShieldCheck, User, Users } from 'lucide-react'
import { authAPI, licenseAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'
import Topbar from '../components/Topbar'

const emptyUser = { email: '', password: '', full_name: '', role: 'viewer' }
const emptyEmployeeLicense = { label: '', max_activations: 1, valid_days: 365 }

export default function Settings() {
  const { user } = useAuth()
  const [users, setUsers] = useState([])
  const [newUser, setNewUser] = useState(emptyUser)
  const [newEmployeeLicense, setNewEmployeeLicense] = useState(emptyEmployeeLicense)
  const [employeeLicenses, setEmployeeLicenses] = useState([])
  const [subscription, setSubscription] = useState(null)
  const [msg, setMsg] = useState(null)
  const [licenseMsg, setLicenseMsg] = useState(null)
  const canManageUsers = ['admin', 'superadmin'].includes(user?.role)
  const canManageEmployeeKeys = ['admin', 'superadmin', 'manager'].includes(user?.role)

  const maskedSubscriptionKey = useMemo(() => {
    if (!subscription?.key_value) return '-'
    if (subscription.key_value.length < 10) return subscription.key_value
    return `${subscription.key_value.slice(0, 8)}...${subscription.key_value.slice(-6)}`
  }, [subscription])

  const loadUsers = () => {
    if (canManageUsers) authAPI.listUsers().then(r => setUsers(r.data)).catch(console.error)
  }

  const loadLicenses = () => {
    if (!canManageEmployeeKeys) return
    licenseAPI.subscription().then(r => setSubscription(r.data)).catch(console.error)
    licenseAPI.listEmployeeKeys().then(r => setEmployeeLicenses(r.data)).catch(console.error)
  }

  useEffect(() => {
    loadUsers()
    loadLicenses()
  }, [canManageUsers, canManageEmployeeKeys])

  const createUser = async () => {
    if (!newUser.email || !newUser.password) {
      setMsg({ type: 'error', text: 'Email and password are required.' })
      return
    }

    try {
      await authAPI.createUser(newUser)
      setMsg({ type: 'success', text: `User ${newUser.email} created successfully.` })
      setNewUser(emptyUser)
      loadUsers()
    } catch (error) {
      setMsg({ type: 'error', text: error.response?.data?.detail || 'Unable to create user.' })
    }
  }

  const createEmployeeLicense = async () => {
    try {
      await licenseAPI.createEmployeeKey({
        label: newEmployeeLicense.label || null,
        max_activations: Number(newEmployeeLicense.max_activations) || 1,
        valid_days: Number(newEmployeeLicense.valid_days) || 365,
      })
      setLicenseMsg({ type: 'success', text: 'Employee key generated successfully.' })
      setNewEmployeeLicense(emptyEmployeeLicense)
      loadLicenses()
    } catch (error) {
      setLicenseMsg({ type: 'error', text: error.response?.data?.detail || 'Unable to generate employee key.' })
    }
  }

  const revokeEmployeeKey = async licenseId => {
    try {
      await licenseAPI.revokeEmployeeKey(licenseId)
      setLicenseMsg({ type: 'success', text: 'Employee key revoked.' })
      loadLicenses()
    } catch (error) {
      setLicenseMsg({ type: 'error', text: error.response?.data?.detail || 'Unable to revoke employee key.' })
    }
  }

  const copyText = async (text, label) => {
    try {
      await navigator.clipboard.writeText(text)
      setLicenseMsg({ type: 'success', text: `${label} copied to clipboard.` })
    } catch {
      setLicenseMsg({ type: 'error', text: 'Clipboard access failed. Copy manually.' })
    }
  }

  return (
    <div>
      <Topbar title="Settings & Access" subtitle="Manage admins, subscriptions, and employee deployment keys" />
      <div className="page-wrap">
        <div className="grid-two">
          <div>
            <div className="panel" style={{ padding: 22, marginBottom: 18 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <User size={18} color="#5cc8ff" />
                <strong>Your account</strong>
              </div>
              {[
                ['Email', user?.email],
                ['Full name', user?.full_name || '-'],
                ['Role', user?.role],
                ['Company ID', user?.company_id || '-'],
                ['Company Enrollment Code', user?.company_code || '-'],
              ].map(([label, value]) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, padding: '12px 0', borderBottom: '1px solid rgba(100, 181, 246, 0.08)' }}>
                  <span style={{ color: 'var(--muted)' }}>{label}</span>
                  <span style={{ color: 'var(--muted-strong)', fontFamily: label === 'Company ID' ? '"JetBrains Mono", monospace' : undefined }}>{value}</span>
                </div>
              ))}
            </div>

            <div className="panel" style={{ padding: 22, marginBottom: 18 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <ShieldCheck size={18} color="#51d0a1" />
                <strong>Subscription & License Policy</strong>
              </div>

              <div className="soft-note" style={{ marginBottom: 10 }}>
                Subscription status: <strong style={{ color: subscription?.is_active ? '#7ee0b9' : '#ff9a9a' }}>{subscription?.status || 'Unknown'}</strong>
              </div>
              <div className="soft-note" style={{ marginBottom: 10 }}>
                Subscription key: <span className="kbd-box">{maskedSubscriptionKey}</span>
              </div>
              <div className="soft-note" style={{ marginBottom: 10 }}>
                Expires: <strong>{subscription?.expires_at ? new Date(subscription.expires_at).toLocaleString() : '-'}</strong>
              </div>
              <div className="soft-note" style={{ marginBottom: 10 }}>
                Employee seats: <strong>{subscription?.employees_used ?? 0}/{subscription?.employee_limit ?? 0}</strong>
                {' '}({subscription?.employee_seats_remaining ?? 0} remaining)
              </div>
              <div className="soft-note" style={{ marginBottom: 10 }}>
                Customer installation policy: employees must activate with a company enrollment code and an employee license key.
              </div>
              <div className="soft-note">
                Managers can generate employee keys from this page and share only with approved employees.
              </div>
            </div>

            <div className="panel" style={{ padding: 22 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <KeyRound size={18} color="#51d0a1" />
                <strong>Employee software rollout</strong>
              </div>
              <div className="soft-note" style={{ marginBottom: 10 }}>
                Employee software is in the <span className="kbd-box">agent</span> folder. Share both the <strong>Company Enrollment Code</strong> and one employee key from this page.
              </div>
              <div className="soft-note" style={{ marginBottom: 10 }}>
                The app auto-captures hostname, OS, IP, and MAC then registers to the manager dashboard.
              </div>
              <div className="soft-note">
                No employee needs dashboard access. They install Etherius Shield, paste keys, and start protection.
              </div>
            </div>
          </div>

          <div>
            {canManageEmployeeKeys ? (
              <>
                {canManageUsers ? (
                <div className="panel" style={{ padding: 22, marginBottom: 18 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                    <Users size={18} color="#ffb347" />
                    <strong>Add team member</strong>
                  </div>
                  {msg ? (
                    <div className="soft-note" style={{ marginBottom: 16, borderColor: msg.type === 'success' ? 'rgba(81, 208, 161, 0.22)' : 'rgba(255, 107, 107, 0.22)', color: msg.type === 'success' ? '#7ee0b9' : '#ff9a9a' }}>
                      {msg.text}
                    </div>
                  ) : null}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 16 }}>
                    {[
                      ['Email', 'email', 'email', 'manager@company.com'],
                      ['Password', 'password', 'password', 'SecurePass123!'],
                      ['Full Name', 'full_name', 'text', 'Aisha Verma'],
                    ].map(([label, key, type, placeholder]) => (
                      <div key={key}>
                        <label className="field-label">{label}</label>
                        <input className="field-input" type={type} value={newUser[key]} onChange={event => setNewUser({ ...newUser, [key]: event.target.value })} placeholder={placeholder} />
                      </div>
                    ))}
                    <div>
                      <label className="field-label">Role</label>
                      <select className="field-input" value={newUser.role} onChange={event => setNewUser({ ...newUser, role: event.target.value })}>
                        {['viewer', 'manager', 'admin'].map(role => <option key={role} value={role}>{role}</option>)}
                      </select>
                    </div>
                  </div>
                  <button className="btn-primary" onClick={createUser} style={{ padding: '12px 16px' }}>Create Team Member</button>
                </div>
                ) : null}

                <div className="panel" style={{ padding: 22, marginBottom: 18 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                    <KeyRound size={18} color="#5cc8ff" />
                    <strong>Employee License Keys</strong>
                  </div>

                  {licenseMsg ? (
                    <div className="soft-note" style={{ marginBottom: 16, borderColor: licenseMsg.type === 'success' ? 'rgba(81, 208, 161, 0.22)' : 'rgba(255, 107, 107, 0.22)', color: licenseMsg.type === 'success' ? '#7ee0b9' : '#ff9a9a' }}>
                      {licenseMsg.text}
                    </div>
                  ) : null}

                  <div style={{ display: 'grid', gap: 12, marginBottom: 14 }}>
                    <div>
                      <label className="field-label">Label</label>
                      <input className="field-input" value={newEmployeeLicense.label} onChange={event => setNewEmployeeLicense({ ...newEmployeeLicense, label: event.target.value })} placeholder="Finance Team Laptop" />
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      <div>
                        <label className="field-label">Max Activations</label>
                        <input className="field-input" type="number" min="1" value={newEmployeeLicense.max_activations} onChange={event => setNewEmployeeLicense({ ...newEmployeeLicense, max_activations: event.target.value })} />
                      </div>
                      <div>
                        <label className="field-label">Valid Days</label>
                        <input className="field-input" type="number" min="1" value={newEmployeeLicense.valid_days} onChange={event => setNewEmployeeLicense({ ...newEmployeeLicense, valid_days: event.target.value })} />
                      </div>
                    </div>
                    <button className="btn-primary" onClick={createEmployeeLicense} style={{ padding: '12px 16px' }}>Generate Employee Key</button>
                  </div>

                  <div className="soft-note">
                    Share generated keys only with approved employees. Revoke keys immediately if a device is retired or compromised.
                  </div>
                </div>

                <div className="panel data-table" style={{ marginBottom: 18 }}>
                  <div className="data-table-header" style={{ gridTemplateColumns: '1.4fr 0.8fr 0.8fr 1.1fr' }}>
                    <div>Employee Key</div>
                    <div>Usage</div>
                    <div>Expiry</div>
                    <div>Actions</div>
                  </div>
                  {employeeLicenses.length === 0 ? (
                    <div style={{ padding: '28px 20px', color: 'var(--muted)', textAlign: 'center' }}>No employee keys yet.</div>
                  ) : employeeLicenses.map(item => (
                    <div key={item.id} className="data-table-row" style={{ gridTemplateColumns: '1.4fr 0.8fr 0.8fr 1.1fr' }}>
                      <div>
                        <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 12, color: 'var(--muted-strong)' }}>{item.key_value}</div>
                        <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>{item.label || 'No label'}</div>
                      </div>
                      <div style={{ color: 'var(--muted-strong)' }}>{item.current_activations}/{item.max_activations}</div>
                      <div style={{ color: 'var(--muted-strong)' }}>{item.expires_at ? new Date(item.expires_at).toLocaleDateString() : '-'}</div>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        <button className="btn-secondary" onClick={() => copyText(item.key_value, 'Employee key')} style={{ padding: '8px 10px', fontSize: 12 }}>Copy</button>
                        <button className="btn-secondary" onClick={() => revokeEmployeeKey(item.id)} style={{ padding: '8px 10px', fontSize: 12, color: '#ffb8b8' }} disabled={!item.is_active}>Revoke</button>
                      </div>
                    </div>
                  ))}
                </div>

                {canManageUsers ? (
                <div className="panel data-table">
                  <div className="data-table-header" style={{ gridTemplateColumns: '1.3fr 1fr 0.8fr' }}>
                    <div>User</div>
                    <div>Role</div>
                    <div>Status</div>
                  </div>
                  {users.length === 0 ? (
                    <div style={{ padding: '40px 24px', color: 'var(--muted)', textAlign: 'center' }}>No users found.</div>
                  ) : users.map(teamUser => (
                    <div key={teamUser.id} className="data-table-row" style={{ gridTemplateColumns: '1.3fr 1fr 0.8fr' }}>
                      <div>
                        <div style={{ fontWeight: 700 }}>{teamUser.full_name || teamUser.email}</div>
                        <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>{teamUser.email}</div>
                      </div>
                      <div style={{ textTransform: 'uppercase', color: 'var(--accent)', fontWeight: 700, fontSize: 12 }}>{teamUser.role}</div>
                      <div style={{ color: teamUser.is_active ? '#7ee0b9' : '#ff9a9a' }}>{teamUser.is_active ? 'Active' : 'Disabled'}</div>
                    </div>
                  ))}
                </div>
                ) : null}
              </>
            ) : (
              <div className="panel" style={{ padding: 22 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                  <AlertTriangle size={18} color="#ffb347" />
                  <strong>Restricted settings</strong>
                </div>
                <div className="soft-note">Only admins and superadmins can create users, issue employee keys, and manage subscription policy.</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
