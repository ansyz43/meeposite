import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api'
import { Mail, KeyRound, Lock } from 'lucide-react'

export default function ResetPassword() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1) // 1=email, 2=code, 3=newPassword
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [token, setToken] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState('')

  async function handleSendCode(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/api/auth/reset-password', { email })
      setStep(2)
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка')
    }
    setLoading(false)
  }

  async function handleVerifyCode(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/api/auth/verify-code', { email, code })
      setToken(data.token)
      setStep(3)
    } catch (err) {
      setError(err.response?.data?.detail || 'Неверный код')
    }
    setLoading(false)
  }

  async function handleSetPassword(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/api/auth/set-password', { token, password })
      setSuccess('Пароль обновлён!')
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 relative overflow-hidden bg-[#060B11]">
      <div className="absolute inset-0 mesh-gradient" />
      <div className="absolute top-[30%] right-[20%] w-[400px] h-[400px] bg-emerald-500/[0.06] rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute inset-0 noise" />
      <div className="w-full max-w-md relative">
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center">
            <Lock size={16} className="text-white" />
          </div>
          <span className="text-2xl font-display font-bold gradient-text">Meepo</span>
        </Link>
        <div className="glass-card p-8">
          <h1 className="text-2xl font-display font-bold mb-6 text-center">Восстановление пароля</h1>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>
          )}
          {success && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>
          )}

          {/* Step 1: Enter email */}
          {step === 1 && (
            <form onSubmit={handleSendCode} className="space-y-4">
              <p className="text-sm text-white/50 mb-2">Введите email, на который зарегистрирован аккаунт</p>
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Email</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                  className="input-field" placeholder="you@example.com" required />
              </div>
              <button type="submit" disabled={loading}
                className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
                <Mail size={18} />
                {loading ? 'Отправка...' : 'Отправить код'}
              </button>
            </form>
          )}

          {/* Step 2: Enter code */}
          {step === 2 && (
            <form onSubmit={handleVerifyCode} className="space-y-4">
              <p className="text-sm text-white/50 mb-2">Введите 6-значный код, отправленный на {email}</p>
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Код</label>
                <input type="text" value={code} onChange={e => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="input-field text-center text-2xl tracking-[0.5em]" placeholder="------" required
                  maxLength={6} inputMode="numeric" autoComplete="one-time-code" />
              </div>
              <button type="submit" disabled={loading || code.length !== 6}
                className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
                <KeyRound size={18} />
                {loading ? 'Проверка...' : 'Подтвердить'}
              </button>
              <button type="button" onClick={() => { setStep(1); setError('') }}
                className="text-sm text-white/40 hover:text-white/60 w-full text-center">
                Отправить код повторно
              </button>
            </form>
          )}

          {/* Step 3: New password */}
          {step === 3 && (
            <form onSubmit={handleSetPassword} className="space-y-4">
              <p className="text-sm text-white/50 mb-2">Введите новый пароль</p>
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Новый пароль</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                  className="input-field" placeholder="••••••••" required minLength={6} />
              </div>
              <button type="submit" disabled={loading}
                className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
                <Lock size={18} />
                {loading ? 'Сохранение...' : 'Сохранить пароль'}
              </button>
            </form>
          )}

          <p className="text-center text-white/40 text-sm mt-6">
            <Link to="/login" className="text-emerald-400 hover:underline">Вернуться к входу</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
