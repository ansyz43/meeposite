import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import api from '../api'
import { Save } from 'lucide-react'

export default function Profile() {
  const { user, loadProfile } = useAuth()
  const [name, setName] = useState(user?.name || '')
  const [curPass, setCurPass] = useState('')
  const [newPass, setNewPass] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

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
      <h1 className="text-2xl font-bold mb-8">Профиль</h1>

      {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}

      {/* Profile info */}
      <form onSubmit={saveName} className="glass-card p-6 mb-6 space-y-4">
        <h2 className="font-semibold">Личные данные</h2>
        <div>
          <label className="block text-sm text-white/60 mb-1.5">Email</label>
          <input type="email" value={user?.email || ''} disabled className="input-field opacity-50 cursor-not-allowed" />
        </div>
        <div>
          <label className="block text-sm text-white/60 mb-1.5">Имя</label>
          <input type="text" value={name} onChange={e => setName(e.target.value)} className="input-field" required />
        </div>
        <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2 disabled:opacity-50">
          <Save size={16} /> Сохранить
        </button>
      </form>

      {/* Change password */}
      <form onSubmit={changePassword} className="glass-card p-6 space-y-4">
        <h2 className="font-semibold">Смена пароля</h2>
        <div>
          <label className="block text-sm text-white/60 mb-1.5">Текущий пароль</label>
          <input type="password" value={curPass} onChange={e => setCurPass(e.target.value)} className="input-field" required />
        </div>
        <div>
          <label className="block text-sm text-white/60 mb-1.5">Новый пароль</label>
          <input type="password" value={newPass} onChange={e => setNewPass(e.target.value)}
            className="input-field" placeholder="Минимум 6 символов" required />
        </div>
        <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2 disabled:opacity-50">
          <Save size={16} /> Изменить пароль
        </button>
      </form>
    </div>
  )
}
