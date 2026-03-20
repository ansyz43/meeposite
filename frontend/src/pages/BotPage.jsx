import { useEffect, useState, useRef } from 'react'
import api from '../api'
import { Bot, Copy, Check, Save, Trash2, Plus, Camera, Users, PlusCircle, Link2, ExternalLink, Settings, MessageCircle, Handshake } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import PageHeader from '../components/ui/PageHeader'
import Loader from '../components/ui/Loader'
import EmptyState from '../components/ui/EmptyState'
import Modal from '../components/ui/Modal'

export default function BotPage() {
  const { loadProfile } = useAuth()
  const [bot, setBot] = useState(null)
  const [loading, setLoading] = useState(true)
  const [claiming, setClaiming] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [copied, setCopied] = useState(false)
  const [avatarUploading, setAvatarUploading] = useState(false)
  const [showDisconnect, setShowDisconnect] = useState(false)
  const fileInputRef = useRef(null)

  // Partners
  const [partners, setPartners] = useState([])
  const [addingCredits, setAddingCredits] = useState(null)
  const [creditsAmount, setCreditsAmount] = useState(5)

  // Editable fields
  const [assistantName, setAssistantName] = useState('')
  const [sellerLink, setSellerLink] = useState('')
  const [greeting, setGreeting] = useState('')
  const [botDescription, setBotDescription] = useState('')
  const [allowPartners, setAllowPartners] = useState(false)

  useEffect(() => { loadBot() }, [])

  async function loadBot() {
    try {
      const { data } = await api.get('/api/bot')
      setBot(data)
      if (data) {
        setAssistantName(data.assistant_name || '')
        setSellerLink(data.seller_link || '')
        setGreeting(data.greeting_message || '')
        setBotDescription(data.bot_description || '')
        setAllowPartners(data.allow_partners || false)
        if (data.allow_partners) loadPartners()
      }
    } catch { /* ignore */ }
    setLoading(false)
  }

  async function loadPartners() {
    try {
      const { data } = await api.get('/api/referral/my-partners')
      setPartners(data)
    } catch { /* ignore */ }
  }

  async function addCredits(partnerId) {
    try {
      await api.post('/api/referral/credits', { partner_id: partnerId, credits: creditsAmount })
      setSuccess(`Добавлено ${creditsAmount} кредитов`)
      setAddingCredits(null)
      setCreditsAmount(5)
      loadPartners()
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка')
    }
  }

  async function claimBot() {
    setError('')
    setClaiming(true)
    try {
      await api.post('/api/bot/claim')
      setSuccess('Бот создан! Заполните настройки.')
      await loadBot()
      await loadProfile()
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка создания бота')
    }
    setClaiming(false)
  }

  async function saveSettings(e) {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await api.put('/api/bot', {
        assistant_name: assistantName,
        seller_link: sellerLink || null,
        greeting_message: greeting || null,
        bot_description: botDescription || null,
        allow_partners: allowPartners,
      })
      setSuccess('Настройки сохранены!')
      await loadBot()
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка сохранения')
    }
    setSaving(false)
  }

  async function disconnectBot() {
    try {
      await api.delete('/api/bot')
      setBot(null)
      setSuccess('Бот отключён')
      setShowDisconnect(false)
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка')
      setShowDisconnect(false)
    }
  }

  function copyLink() {
    if (bot?.bot_username) {
      navigator.clipboard.writeText(`https://t.me/${bot.bot_username}`)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  async function handleAvatarChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setError('Только JPEG, PNG или WEBP')
      return
    }
    if (file.size > 2 * 1024 * 1024) {
      setError('Максимум 2 МБ')
      return
    }
    setAvatarUploading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await api.post('/api/bot/avatar', formData)
      setBot(data)
      setSuccess('Аватарка загружена!')
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка загрузки аватарки')
    }
    setAvatarUploading(false)
  }

  useEffect(() => {
    if (success) { const t = setTimeout(() => setSuccess(''), 3000); return () => clearTimeout(t) }
  }, [success])

  if (loading) return <Loader />

  // No bot — show create button
  if (!bot) {
    return (
      <div>
        <PageHeader title="Мой бот" />
        {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
        {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}
        <EmptyState
          icon={Bot}
          title="У вас пока нет бота"
          description="Нажмите кнопку ниже — система автоматически назначит вам персонального Telegram-бота с ИИ"
          action={
            <button onClick={claimBot} disabled={claiming}
              className="btn-primary inline-flex items-center gap-2 text-lg px-8 py-3 disabled:opacity-50">
              <span className="relative z-10 flex items-center gap-2">
                <Plus size={20} /> {claiming ? 'Создание...' : 'Создать бота'}
              </span>
            </button>
          }
        />
      </div>
    )
  }

  // Bot connected — show settings
  return (
    <div>
      <PageHeader title="Мой бот" actions={
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${bot.is_active ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.4)]' : 'bg-red-400'}`} />
          <span className="text-sm text-white/60">{bot.is_active ? 'Активен' : 'Неактивен'}</span>
        </div>
      } />

      {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}

      {/* Bot link card */}
      {bot.bot_username && (
        <div className="glass-card p-5 mb-6 border-l-4 border-l-emerald-500">
          <div className="flex items-center gap-2 mb-3">
            <Link2 size={18} className="text-emerald-400" />
            <span className="text-sm font-medium text-white/60">Ваша ссылка на бота</span>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-lg font-semibold text-emerald-400 break-all">
              https://t.me/{bot.bot_username}
            </span>
            <div className="flex items-center gap-2">
              <button onClick={copyLink}
                className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors">
                {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                {copied ? 'Скопировано' : 'Копировать'}
              </button>
              <a href={`https://t.me/${bot.bot_username}`} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors">
                <ExternalLink size={14} /> Открыть
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Settings form */}
      <form onSubmit={saveSettings} className="glass-card p-6 space-y-6">
        {/* Section: Основные */}
        <div>
          <h2 className="font-display font-semibold flex items-center gap-2 mb-5">
            <Settings size={18} className="text-emerald-400" />
            Основные настройки
          </h2>

          {/* Avatar */}
          <div className="flex items-center gap-4 mb-5">
            <div className="relative group cursor-pointer" onClick={() => fileInputRef.current?.click()}>
              {bot.avatar_url ? (
                <img src={bot.avatar_url + (bot.avatar_url.includes('?') ? '&' : '?') + 't=' + Date.now()} alt="Аватар" className="w-20 h-20 rounded-2xl object-cover" />
              ) : (
                <div className="w-20 h-20 rounded-2xl bg-white/[0.06] flex items-center justify-center">
                  <Bot size={32} className="text-white/30" />
                </div>
              )}
              <div className="absolute inset-0 bg-black/50 rounded-2xl flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <Camera size={20} className="text-white" />
              </div>
              {avatarUploading && (
                <div className="absolute inset-0 bg-black/60 rounded-2xl flex items-center justify-center">
                  <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                </div>
              )}
            </div>
            <div>
              <p className="text-sm text-white/60">Аватарка бота</p>
              <p className="text-xs text-white/30">Нажмите для загрузки (JPEG, PNG, WEBP, до 2 МБ)</p>
            </div>
            <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp"
              className="hidden" onChange={handleAvatarChange} />
          </div>

          <div>
            <label className="block text-sm text-white/60 mb-1.5">Имя ассистента</label>
            <input type="text" value={assistantName} onChange={e => setAssistantName(e.target.value)}
              className="input-field" placeholder="Ассистент Анны" required />
            <p className="text-xs text-white/30 mt-1">Как бот будет представляться пользователям</p>
          </div>
        </div>

        <div className="border-t border-white/[0.06]" />

        {/* Section: Контент */}
        <div className="space-y-5">
          <h2 className="font-display font-semibold flex items-center gap-2">
            <MessageCircle size={18} className="text-emerald-400" />
            Контент
          </h2>

          <div>
            <label className="block text-sm text-white/60 mb-1.5">Описание бота</label>
            <textarea value={botDescription} onChange={e => setBotDescription(e.target.value)}
              className="input-field min-h-[80px] resize-y" placeholder="Персональный помощник по продукции FitLine" maxLength={512} />
            <p className="text-xs text-white/30 mt-1">Видно в Telegram до нажатия /start (макс. 512 символов)</p>
          </div>

          <div>
            <label className="block text-sm text-white/60 mb-1.5">Приветственное сообщение</label>
            <textarea value={greeting} onChange={e => setGreeting(e.target.value)}
              className="input-field min-h-[100px] resize-y" placeholder="Привет! Я ассистент..." />
            <p className="text-xs text-white/30 mt-1">Отправляется при нажатии /start</p>
          </div>

          <div>
            <label className="block text-sm text-white/60 mb-1.5">Ваша ссылка</label>
            <input type="url" value={sellerLink} onChange={e => setSellerLink(e.target.value)}
              className="input-field" placeholder="https://your-link.com" />
            <p className="text-xs text-white/30 mt-1">Бот будет давать эту ссылку заинтересованным клиентам</p>
          </div>
        </div>

        <div className="border-t border-white/[0.06]" />

        {/* Section: Партнёры */}
        <div>
          <h2 className="font-display font-semibold flex items-center gap-2 mb-4">
            <Handshake size={18} className="text-emerald-400" />
            Партнёрская программа
          </h2>
          <div className="flex items-center justify-between py-2 px-1">
            <div>
              <div className="text-sm text-white/80">Разрешить партнёров</div>
              <div className="text-xs text-white/30">Другие пользователи смогут стать партнёрами вашего бота</div>
            </div>
            <button type="button" onClick={() => setAllowPartners(!allowPartners)}
              className={`toggle-switch ${allowPartners ? 'active' : ''}`} />
          </div>
        </div>

        <div className="border-t border-white/[0.06]" />

        {/* Actions */}
        <div className="flex flex-col-reverse sm:flex-row items-start sm:items-center justify-between gap-3">
          <button type="button" onClick={() => setShowDisconnect(true)}
            className="flex items-center gap-2 text-sm text-red-400 hover:text-red-300 transition-colors">
            <Trash2 size={16} /> Отключить бота
          </button>
          <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2 disabled:opacity-50 w-full sm:w-auto justify-center">
            <Save size={18} /> {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </form>

      {/* Partners section */}
      {allowPartners && (
        <div className="mt-6">
          <div className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Users size={20} className="text-emerald-400" />
              <h2 className="font-display font-semibold">Партнёры ({partners.length})</h2>
            </div>

            {partners.length === 0 ? (
              <p className="text-white/40 text-sm">Пока нет партнёров</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="glass-table">
                  <thead>
                    <tr>
                      <th>Имя</th>
                      <th>Email</th>
                      <th>Ссылка</th>
                      <th className="text-center">Кредиты</th>
                      <th className="text-center">Сессии</th>
                      <th className="text-center">Активные</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {partners.map(p => (
                      <tr key={p.id} className="border-b border-white/[0.06]">
                        <td className="py-2.5 text-white/80">{p.user_name}</td>
                        <td className="py-2.5 text-white/50">{p.user_email}</td>
                        <td className="py-2.5">
                          {p.seller_link ? (
                            <a href={p.seller_link} target="_blank" rel="noopener noreferrer"
                              className="text-emerald-400 hover:underline truncate block max-w-[200px]">
                              {p.seller_link.replace(/^https?:\/\//, '')}
                            </a>
                          ) : <span className="text-white/30">—</span>}
                        </td>
                        <td className="py-2.5 text-center">{p.credits}</td>
                        <td className="py-2.5 text-center">{p.total_sessions}</td>
                        <td className="py-2.5 text-center">
                          {p.active_sessions > 0
                            ? <span className="text-green-400">{p.active_sessions}</span>
                            : <span className="text-white/30">0</span>}
                        </td>
                        <td className="py-2.5 text-right">
                          {addingCredits === p.id ? (
                            <div className="flex items-center gap-2 justify-end">
                              <input type="number" min="1" max="1000" value={creditsAmount}
                                onChange={e => setCreditsAmount(parseInt(e.target.value) || 1)}
                                className="w-16 bg-white/[0.06] border border-white/[0.08] rounded px-2 py-1 text-sm text-white text-center" />
                              <button onClick={() => addCredits(p.id)}
                                className="text-green-400 hover:text-green-300 text-xs font-medium">
                                OK
                              </button>
                              <button onClick={() => setAddingCredits(null)}
                                className="text-white/30 hover:text-white/50 text-xs">
                                ✕
                              </button>
                            </div>
                          ) : (
                            <button onClick={() => { setAddingCredits(p.id); setCreditsAmount(5) }}
                              className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 text-xs ml-auto">
                              <PlusCircle size={14} /> Кредиты
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Disconnect Modal */}
      <Modal
        open={showDisconnect}
        onClose={() => setShowDisconnect(false)}
        title="Отключить бота?"
        actions={
          <>
            <button onClick={() => setShowDisconnect(false)} className="btn-secondary !py-2 !px-5 text-sm">Отмена</button>
            <button onClick={disconnectBot} className="bg-red-500/20 hover:bg-red-500/30 text-red-400 font-medium py-2 px-5 rounded-xl text-sm transition-colors">
              Отключить
            </button>
          </>
        }
      >
        Все переписки и контакты будут удалены. Это действие нельзя отменить.
      </Modal>
    </div>
  )
}
