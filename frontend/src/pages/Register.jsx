import { useState, useEffect, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { UserPlus } from 'lucide-react'

export default function Register() {
  const { register, loginWithTelegram, loginWithGoogle } = useAuth()
  const authRef = useRef({ loginWithTelegram, loginWithGoogle })
  authRef.current = { loginWithTelegram, loginWithGoogle }
  const [searchParams] = useSearchParams()
  const refCode = searchParams.get('ref') || ''
  const refCodeRef = useRef(refCode)
  refCodeRef.current = refCode
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    window.__onTelegramAuth = async (tgUser) => {
      try {
        await authRef.current.loginWithTelegram({ ...tgUser, ref_code: refCodeRef.current || undefined })
      } catch (err) {
        // error handled by auth
      }
    }
    return () => { delete window.__onTelegramAuth }
  }, [])

  useEffect(() => {
    const botName = import.meta.env.VITE_TELEGRAM_BOT_NAME
    if (!botName) return
    const container = document.getElementById('telegram-register-btn')
    if (!container) return
    container.innerHTML = ''
    const script = document.createElement('script')
    script.src = 'https://telegram.org/js/telegram-widget.js?23'
    script.setAttribute('data-telegram-login', botName)
    script.setAttribute('data-size', 'large')
    script.setAttribute('data-radius', '12')
    script.setAttribute('data-onauth', '__onTelegramAuth(user)')
    script.setAttribute('data-request-access', 'write')
    container.appendChild(script)
  }, [])

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
            await authRef.current.loginWithGoogle(response.credential, refCodeRef.current || undefined)
          } catch (err) {
            setError(err.response?.data?.detail || 'Ошибка регистрации через Google')
          } finally {
            setLoading(false)
          }
        },
      })
      window.google?.accounts.id.renderButton(
        document.getElementById('google-register-btn'),
        { theme: 'filled_black', size: 'large', width: '100%', shape: 'pill', text: 'signup_with' }
      )
    }
    document.head.appendChild(script)
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (password.length < 6) {
      setError('Пароль должен быть не менее 6 символов')
      return
    }
    setLoading(true)
    try {
      await register(email, password, name, refCode || undefined)
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка регистрации')
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
          <h1 className="text-2xl font-bold mb-6 text-center">Регистрация</h1>
          {refCode && (
            <div className="bg-accent-500/10 border border-accent-500/30 rounded-xl px-4 py-3 text-accent-400 text-sm mb-4 text-center">
              Вас пригласили! После регистрации вы будете привязаны к реферальной сети
            </div>
          )}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>
          )}

          {showSocial && (
            <>
              <div className="space-y-3 mb-5">
                {import.meta.env.VITE_TELEGRAM_BOT_NAME && (
                  <div id="telegram-register-btn" className="flex justify-center"></div>
                )}
                {import.meta.env.VITE_GOOGLE_CLIENT_ID && (
                  <div id="google-register-btn" className="flex justify-center"></div>
                )}
              </div>
              <div className="flex items-center gap-3 mb-5">
                <div className="flex-1 h-px bg-white/10"></div>
                <span className="text-white/30 text-xs uppercase">или</span>
                <div className="flex-1 h-px bg-white/10"></div>
              </div>
            </>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-white/60 mb-1.5">Ваше имя</label>
              <input type="text" value={name} onChange={e => setName(e.target.value)}
                className="input-field" placeholder="Анна Иванова" required />
            </div>
            <div>
              <label className="block text-sm text-white/60 mb-1.5">Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="input-field" placeholder="you@example.com" required />
            </div>
            <div>
              <label className="block text-sm text-white/60 mb-1.5">Пароль</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                className="input-field" placeholder="Минимум 6 символов" required />
            </div>
            <button type="submit" disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
              <UserPlus size={18} />
              {loading ? 'Создание...' : 'Создать аккаунт'}
            </button>
          </form>
          <p className="text-center text-white/40 text-sm mt-6">
            Уже есть аккаунт? <Link to="/login" className="text-accent-400 hover:underline">Войти</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
