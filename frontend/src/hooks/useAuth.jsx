import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react'
import api, { initTokenFunctions } from '../api'

const AuthContext = createContext(null)

// In-memory token storage (not accessible via XSS unlike localStorage)
let _accessToken = null

export function getAccessToken() { return _accessToken }
export function setAccessToken(token) { _accessToken = token }

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Wire up api.js token functions
    initTokenFunctions(getAccessToken, setAccessToken)

    // Migrate from localStorage if exists (one-time)
    const stored = localStorage.getItem('access_token')
    if (stored) {
      _accessToken = stored
      localStorage.removeItem('access_token')
    }
    if (_accessToken) {
      loadProfile()
    } else {
      // Try silent refresh via httpOnly cookie
      silentRefresh()
    }
  }, [])

  async function silentRefresh() {
    try {
      const { data } = await api.post('/api/auth/refresh', {}, { withCredentials: true })
      _accessToken = data.access_token
      await loadProfile()
    } catch {
      setLoading(false)
    }
  }

  const loadProfile = useCallback(async () => {
    try {
      const { data } = await api.get('/api/profile')
      setUser(data)
    } catch {
      _accessToken = null
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const { data } = await api.post('/api/auth/login', { email, password })
    _accessToken = data.access_token
    await loadProfile()
  }, [loadProfile])

  const register = useCallback(async (email, password, name, ref_code) => {
    const payload = { email, password, name }
    if (ref_code) payload.ref_code = ref_code
    const { data } = await api.post('/api/auth/register', payload)
    _accessToken = data.access_token
    await loadProfile()
  }, [loadProfile])

  const loginWithTelegram = useCallback(async (telegramData) => {
    const { data } = await api.post('/api/auth/telegram', telegramData)
    _accessToken = data.access_token
    await loadProfile()
  }, [loadProfile])

  const loginWithGoogle = useCallback(async (credential, ref_code) => {
    const payload = { credential }
    if (ref_code) payload.ref_code = ref_code
    const { data } = await api.post('/api/auth/google', payload)
    _accessToken = data.access_token
    await loadProfile()
  }, [loadProfile])

  const logout = useCallback(async () => {
    try {
      await api.post('/api/auth/logout')
    } catch { /* ignore */ }
    _accessToken = null
    setUser(null)
  }, [])

  const value = useMemo(() => ({
    user, loading, login, register, loginWithTelegram, loginWithGoogle, logout, loadProfile
  }), [user, loading, login, register, loginWithTelegram, loginWithGoogle, logout, loadProfile])

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
