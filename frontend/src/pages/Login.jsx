import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { LogIn } from 'lucide-react'

export default function Login() {
  const { login, loginWithTelegram, loginWithGoogle } = useAuth()
  const authRef = useRef({ loginWithTelegram, loginWithGoogle })
  authRef.current = { loginWithTelegram, loginWithGoogle }
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Handle Telegram auth result (redirect fallback — mobile or popup)
  useEffect(() => {
    const hash = window.location.hash
    if (hash.startsWith('#tgAuthResult=')) {
      const raw = hash.substring(14)
      let data
      try {
        data = JSON.parse(atob(raw))
      } catch {
        try { data = JSON.parse(decodeURIComponent(raw)) } catch { /* ignore */ }
      }
      if (data) {
        window.history.replaceState(null, '', window.location.pathname + window.location.search)
        authRef.current.loginWithTelegram(data).catch(() => {})
      }
    }
  }, [])

  function openTelegramAuth() {
    const botId = import.meta.env.VITE_TELEGRAM_BOT_ID
    if (!botId) return
    const origin = window.location.origin
    const returnUrl = origin + '/login'
    const url = `https://oauth.telegram.org/auth?bot_id=${botId}&origin=${encodeURIComponent(origin)}&request_access=write&return_to=${encodeURIComponent(returnUrl)}`

    // On mobile, redirect directly instead of popup (popups often blocked)
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
    if (isMobile) {
      window.location.href = url
      return
    }

    const w = 550, h = 470
    const left = Math.round(screen.width / 2 - w / 2)
    const top = Math.round(screen.height / 2 - h / 2)
    const popup = window.open(url, 'telegram_auth', `width=${w},height=${h},left=${left},top=${top}`)

    function handleAuth(tgUser) {
      cleanup()
      if (popup && !popup.closed) popup.close()
      setError('')
      setLoading(true)
      authRef.current.loginWithTelegram(tgUser)
        .catch(err => setError(err.response?.data?.detail || 'Ошибка входа через Telegram'))
        .finally(() => setLoading(false))
    }

    function onMessage(e) {
      if (e.origin !== 'https://oauth.telegram.org') return
      let msg
      try { msg = typeof e.data === 'string' ? JSON.parse(e.data) : e.data } catch { return }
      if (!msg || msg.event !== 'auth_result') return
      if (msg.result) handleAuth(msg.result)
    }
    window.addEventListener('message', onMessage)

    const pollTimer = setInterval(() => {
      try {
        if (!popup || popup.closed) { cleanup(); return }
        const loc = popup.location
        if (loc.origin === origin && loc.hash.startsWith('#tgAuthResult=')) {
          const raw = loc.hash.substring(14)
          let data
          try { data = JSON.parse(atob(raw)) } catch { data = JSON.parse(decodeURIComponent(raw)) }
          handleAuth(data)
        }
      } catch { /* cross-origin */ }
    }, 50)

    function cleanup() {
      clearInterval(pollTimer)
      window.removeEventListener('message', onMessage)
    }
  }

  // Load Google Sign-In (once)
  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
    if (!clientId) return
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.onload = () => {
      window.google?.accounts.id.initialize({
        client_id: clientId,
        auto_select: false,
        callback: async (response) => {
          setError('')
          setLoading(true)
          try {
            await authRef.current.loginWithGoogle(response.credential)
          } catch (err) {
            setError(err.response?.data?.detail || 'Ошибка входа через Google')
          } finally {
            setLoading(false)
          }
        },
      })
      window.google?.accounts.id.renderButton(
        document.getElementById('google-login-btn'),
        { theme: 'filled_black', size: 'large', width: '100%', shape: 'pill', text: 'signin_with' }
      )
    }
    document.head.appendChild(script)
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка входа')
    } finally {
      setLoading(false)
    }
  }

  const showSocial = import.meta.env.VITE_TELEGRAM_BOT_ID || import.meta.env.VITE_GOOGLE_CLIENT_ID

  return (
    <div className="min-h-screen flex items-center justify-center px-6 relative overflow-hidden bg-[#060B11]">
      <div className="absolute inset-0 mesh-gradient" />
      <div className="absolute top-[20%] left-[30%] w-[400px] h-[400px] bg-emerald-500/[0.06] rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute inset-0 noise" />
      <div className="w-full max-w-md relative">
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center">
            <LogIn size={16} className="text-white" />
          </div>
          <span className="text-2xl font-display font-bold gradient-text">Meepo</span>
        </Link>
        <div className="glass-card p-8">
          <h1 className="text-2xl font-display font-bold mb-6 text-center">Вход</h1>
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-white/60 mb-1.5">Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="input-field" placeholder="you@example.com" required />
            </div>
            <div>
              <label className="block text-sm text-white/60 mb-1.5">Пароль</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                className="input-field" placeholder="••••••••" required />
            </div>
            <button type="submit" disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
              <LogIn size={18} />
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </form>

          {showSocial && (
            <>
              <div className="flex items-center gap-3 my-5">
                <div className="flex-1 h-px bg-white/10"></div>
                <span className="text-white/30 text-xs uppercase">или</span>
                <div className="flex-1 h-px bg-white/10"></div>
              </div>
              <div className="space-y-3">
                {import.meta.env.VITE_TELEGRAM_BOT_ID && (
                  <button onClick={openTelegramAuth} type="button"
                    className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-white font-medium"
                    style={{ background: '#54a9eb' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.12.03-1.99 1.27-5.62 3.72-.53.36-1.01.54-1.44.53-.47-.01-1.38-.27-2.06-.49-.83-.27-1.49-.42-1.43-.88.03-.24.37-.49 1.02-.75 3.98-1.73 6.64-2.87 7.97-3.44 3.8-1.58 4.59-1.86 5.1-1.87.11 0 .37.03.54.17.14.12.18.28.2.47-.01.06.01.24 0 .37z"/>
                    </svg>
                    Войти через Telegram
                  </button>
                )}
                {import.meta.env.VITE_GOOGLE_CLIENT_ID && (
                  <div id="google-login-btn" className="flex justify-center"></div>
                )}
              </div>
            </>
          )}

          <p className="text-center text-white/40 text-sm mt-4">
            <Link to="/reset-password" className="text-white/50 hover:text-emerald-400 hover:underline transition-colors">Забыли пароль?</Link>
          </p>
          <p className="text-center text-white/40 text-sm mt-2">
            Нет аккаунта? <Link to="/register" className="text-emerald-400 hover:underline">Зарегистрироваться</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
