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

  // Expose callback for Telegram widget
  useEffect(() => {
    window.__onTelegramAuth = async (tgUser) => {
      try {
        await authRef.current.loginWithTelegram(tgUser)
      } catch (err) {
        // error will show on next render
      }
    }
    return () => { delete window.__onTelegramAuth }
  }, [])

  // Load Telegram widget
  useEffect(() => {
    const botName = import.meta.env.VITE_TELEGRAM_BOT_NAME
    if (!botName) return
    const container = document.getElementById('telegram-login-btn')
    if (!container) return
    container.innerHTML = ''
    const script = document.createElement('script')
    script.src = 'https://telegram.org/js/telegram-widget.js?22'
    script.setAttribute('data-telegram-login', botName)
    script.setAttribute('data-size', 'large')
    script.setAttribute('data-radius', '12')
    script.setAttribute('data-onauth', '__onTelegramAuth(user)')
    script.setAttribute('data-request-access', 'write')
    script.async = true
    container.appendChild(script)
  }, [])

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

  const showSocial = import.meta.env.VITE_TELEGRAM_BOT_NAME || import.meta.env.VITE_GOOGLE_CLIENT_ID

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <Link to="/" className="text-2xl font-bold text-accent-400 block text-center mb-8">Meepo</Link>
        <div className="glass-card p-8">
          <h1 className="text-2xl font-bold mb-6 text-center">Вход</h1>
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
                {import.meta.env.VITE_TELEGRAM_BOT_NAME && (
                  <div id="telegram-login-btn" className="flex justify-center"></div>
                )}
                {import.meta.env.VITE_GOOGLE_CLIENT_ID && (
                  <div id="google-login-btn" className="flex justify-center"></div>
                )}
              </div>
            </>
          )}

          <p className="text-center text-white/40 text-sm mt-4">
            <Link to="/reset-password" className="text-white/50 hover:text-accent-400 hover:underline">Забыли пароль?</Link>
          </p>
          <p className="text-center text-white/40 text-sm mt-2">
            Нет аккаунта? <Link to="/register" className="text-accent-400 hover:underline">Зарегистрироваться</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
