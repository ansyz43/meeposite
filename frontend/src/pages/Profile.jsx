import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import api from '../api'
import { Save, User, Lock, Mail } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'

export default function Profile() {
  const { user, loadProfile } = useAuth()
  const [name, setName] = useState(user?.name || '')
  const [curPass, setCurPass] = useState('')
  const [newPass, setNewPass] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (success) { const t = setTimeout(() => setSuccess(''), 3000); return () => clearTimeout(t) }
  }, [success])

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
              <User size={18} className="text-emerald-400" />
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
              <Lock size={18} className="text-emerald-400" />
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
    </div>
  )
}
