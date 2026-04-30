import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import api from '../api'
import { Save, User, Lock, Mail, CreditCard, Crown, CheckCircle2, Clock } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'

export default function Profile() {
  const { user, loadProfile } = useAuth()
  const [name, setName] = useState(user?.name || '')
  const [curPass, setCurPass] = useState('')
  const [newPass, setNewPass] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [paying, setPaying] = useState(false)
  const [subInfo, setSubInfo] = useState(null) // { has_active_subscription, payments }
  const [polling, setPolling] = useState(false)

  async function refreshSubscription() {
    try {
      const { data } = await api.get('/api/payments/me')
      setSubInfo(data)
      return data
    } catch { return null }
  }

  useEffect(() => { refreshSubscription() }, [])

  useEffect(() => {
    if (success) { const t = setTimeout(() => setSuccess(''), 3000); return () => clearTimeout(t) }
  }, [success])

  // If returning from Tochka redirect, poll status until terminal
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const paid = params.get('paid')
    if (paid !== '1' && paid !== '0') return
    setPolling(true)
    let cancelled = false
    let attempts = 0
    async function tick() {
      if (cancelled) return
      attempts += 1
      const info = await refreshSubscription()
      const pending = info?.payments?.some(p => p.status === 'pending')
      if (info?.has_active_subscription) {
        setSuccess('Подписка активирована!')
        setPolling(false)
        // clean URL
        window.history.replaceState({}, '', '/dashboard/profile')
        return
      }
      if (!pending || attempts >= 20) {
        setPolling(false)
        if (paid === '0') setError('Оплата не прошла')
        window.history.replaceState({}, '', '/dashboard/profile')
        return
      }
      setTimeout(tick, 3000)
    }
    tick()
    return () => { cancelled = true }
  }, [])

  async function saveName(e) {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await api.put('/api/profile', { name })
      await loadProfile()
      setSuccess('Имя обновлено')
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка')
    }
    setSaving(false)
  }

  async function changePassword(e) {
    e.preventDefault()
    setError('')
    if (newPass.length < 6) { setError('Минимум 6 символов'); return }
    setSaving(true)
    try {
      await api.put('/api/profile/password', { current_password: curPass, new_password: newPass })
      setCurPass('')
      setNewPass('')
      setSuccess('Пароль изменён')
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка')
    }
    setSaving(false)
  }

  async function buyPro() {
    setError('')
    setPaying(true)
    try {
      const { data } = await api.post('/api/payments/subscription')
      if (data?.payment_link) {
        window.location.href = data.payment_link
        return
      }
      setError('Сервер не вернул ссылку на оплату')
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : 'Не удалось создать платёж')
    }
    setPaying(false)
  }

  return (
    <div>
      <PageHeader title="Профиль" />

      {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4 animate-fade-in-up">{success}</div>}

      <div className="glass-card overflow-hidden">
        {/* Personal info section */}
        <form onSubmit={saveName}>
          <div className="p-6 border-b border-white/[0.06]">
            <h2 className="font-display font-semibold flex items-center gap-2 mb-5">
              <User size={18} className="text-sky-400" />
              Личные данные
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Email</label>
                <div className="relative">
                  <input type="email" value={user?.email || ''} disabled className="input-field opacity-50 cursor-not-allowed pr-36" />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-white/20 bg-white/[0.04] px-2 py-0.5 rounded-md flex items-center gap-1">
                    <Mail size={10} /> Изменить нельзя
                  </span>
                </div>
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Имя</label>
                <input type="text" value={name} onChange={e => setName(e.target.value)} className="input-field" required />
              </div>
            </div>
          </div>
          <div className="px-6 py-4 bg-white/[0.02] flex justify-end">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2 disabled:opacity-50 !py-2.5 !px-5">
              <span className="relative z-10 flex items-center gap-2"><Save size={16} /> Сохранить</span>
            </button>
          </div>
        </form>

        {/* Divider */}
        <div className="border-t border-white/[0.06]" />

        {/* Password section */}
        <form onSubmit={changePassword}>
          <div className="p-6 border-b border-white/[0.06]">
            <h2 className="font-display font-semibold flex items-center gap-2 mb-5">
              <Lock size={18} className="text-sky-400" />
              Смена пароля
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Текущий пароль</label>
                <input type="password" value={curPass} onChange={e => setCurPass(e.target.value)} className="input-field" required />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Новый пароль</label>
                <input type="password" value={newPass} onChange={e => setNewPass(e.target.value)}
                  className="input-field" placeholder="Минимум 6 символов" required />
              </div>
            </div>
          </div>
          <div className="px-6 py-4 bg-white/[0.02] flex justify-end">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2 disabled:opacity-50 !py-2.5 !px-5">
              <span className="relative z-10 flex items-center gap-2"><Save size={16} /> Изменить пароль</span>
            </button>
          </div>
        </form>
      </div>

      {/* Pro subscription */}
      <div className="glass-card overflow-hidden mt-6">
        <div className="p-6">
          <h2 className="font-display font-semibold flex items-center gap-2 mb-3">
            <Crown size={18} className="text-amber-400" />
            Подписка Meepo Pro
          </h2>
          {subInfo?.has_active_subscription && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4 flex items-center gap-2">
              <CheckCircle2 size={16} /> Подписка активна
            </div>
          )}
          {polling && (
            <div className="bg-sky-500/10 border border-sky-500/30 rounded-xl px-4 py-3 text-sky-300 text-sm mb-4 flex items-center gap-2">
              <Clock size={16} className="animate-pulse" /> Проверяем статус оплаты...
            </div>
          )}
          <p className="text-sm text-white/60 mb-4">
            Полный доступ к CRM, рассылкам, контент-плану и расширенной аналитике.
            Оплата через банк «Точка» — банковской картой или СБП.
          </p>
          <div className="flex items-baseline gap-2 mb-5">
            <span className="text-3xl font-display font-bold text-white">1 ₽</span>
            <span className="text-sm text-amber-300/80">тестовый режим</span>
          </div>
          <button onClick={buyPro} disabled={paying || subInfo?.has_active_subscription}
            className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
            <span className="relative z-10 flex items-center gap-2">
              <CreditCard size={16} /> {paying ? 'Создание платежа...' : (subInfo?.has_active_subscription ? 'Оплачено' : 'Оплатить подписку')}
            </span>
          </button>
          <p className="text-[11px] text-white/30 mt-3">
            Нажимая «Оплатить», вы принимаете{' '}
            <a href="/offer" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">условия Оферты</a>.
          </p>
        </div>
      </div>
    </div>
  )
}
