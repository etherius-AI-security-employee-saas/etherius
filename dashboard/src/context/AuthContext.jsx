import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('etherius_user')) } catch { return null }
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('etherius_token')
    if (token) {
      authAPI.me()
        .then(r => { setUser(r.data); localStorage.setItem('etherius_user', JSON.stringify(r.data)) })
        .catch(() => { localStorage.clear(); setUser(null) })
        .finally(() => setLoading(false))
    } else setLoading(false)
  }, [])

  const login = async (email, password) => {
    const r = await authAPI.login(email, password)
    localStorage.setItem('etherius_token', r.data.access_token)
    const me = await authAPI.me()
    setUser(me.data)
    localStorage.setItem('etherius_user', JSON.stringify(me.data))
    return me.data
  }

  const logout = () => {
    localStorage.removeItem('etherius_token')
    localStorage.removeItem('etherius_user')
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, login, logout, loading }}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
