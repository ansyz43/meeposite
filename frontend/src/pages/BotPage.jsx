import { useEffect, useState, useRef } from 'react'
import api from '../api'
import { Bot, Copy, Check, Save, Trash2, Plus, Camera, Users, PlusCircle, Link2, ExternalLink, Settings, MessageCircle, Handshake, ZoomIn } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import PageHeader from '../components/ui/PageHeader'
import Loader from '../components/ui/Loader'
import EmptyState from '../components/ui/EmptyState'
import Modal from '../components/ui/Modal'
import TelegramGroupPopup from '../components/ui/TelegramGroupPopup'
import ImageGallery, { InstructionStep } from '../components/ui/ImageGallery'

// VK icon as inline SVG
function VkIcon({ size = 18, className = '' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M12.785 16.241s.288-.032.436-.194c.136-.148.132-.427.132-.427s-.02-1.304.587-1.496c.598-.188 1.368 1.259 2.184 1.814.616.42 1.084.328 1.084.328l2.178-.03s1.14-.07.6-.964c-.044-.073-.316-.662-1.624-1.872-1.37-1.268-1.186-1.062.464-3.254.764-1.012 1.542-2.122 1.404-2.476-.132-.33-.944-.244-.944-.244l-2.45.016s-.182-.024-.316.056c-.132.078-.216.262-.216.262s-.388 1.032-.904 1.91c-1.092 1.862-1.528 1.96-1.708 1.846-.418-.268-.314-1.076-.314-1.65 0-1.792.272-2.54-.528-2.734-.266-.064-.462-.106-1.14-.112-.87-.01-1.606.002-2.024.206-.278.136-.492.438-.362.456.162.022.528.098.722.362.25.342.242 1.11.242 1.11s.144 2.11-.336 2.372c-.33.18-.782-.188-1.754-1.874-.498-.864-.874-1.818-.874-1.818s-.072-.178-.202-.274c-.156-.116-.376-.152-.376-.152l-2.328.016s-.35.01-.478.162c-.114.136-.01.416-.01.416s1.82 4.258 3.882 6.404c1.888 1.966 4.034 1.836 4.034 1.836h.972z"/>
    </svg>
  )
}

// Telegram icon
function TgIcon({ size = 18, className = '' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
    </svg>
  )
}

export default function BotPage() {
  const { loadProfile } = useAuth()
  const [tab, setTab] = useState('telegram')
  const [tgBot, setTgBot] = useState(null)
  const [vkBot, setVkBot] = useState(null)
  const [loading, setLoading] = useState(true)
  const [claiming, setClaiming] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [copied, setCopied] = useState(false)
  const [avatarUploading, setAvatarUploading] = useState(false)
  const [showDisconnect, setShowDisconnect] = useState(false)
  const [showTgGroup, setShowTgGroup] = useState(false)
  const [showVkGuide, setShowVkGuide] = useState(false)
  const [vkGuideStart, setVkGuideStart] = useState(0)
  const fileInputRef = useRef(null)

  // Partners
  const [partners, setPartners] = useState([])
  const [addingCredits, setAddingCredits] = useState(null)
  const [creditsAmount, setCreditsAmount] = useState(5)

  // TG editable fields
  const [assistantName, setAssistantName] = useState('')
  const [sellerLink, setSellerLink] = useState('')
  const [greeting, setGreeting] = useState('')
  const [botDescription, setBotDescription] = useState('')
  const [allowPartners, setAllowPartners] = useState(false)

  // VK editable fields
  const [vkAssistantName, setVkAssistantName] = useState('')
  const [vkSellerLink, setVkSellerLink] = useState('')
  const [vkGreeting, setVkGreeting] = useState('')
  const [vkBotDescription, setVkBotDescription] = useState('')

  // VK connect form
  const [vkGroupId, setVkGroupId] = useState('')
  const [vkGroupToken, setVkGroupToken] = useState('')
  const [vkConnectName, setVkConnectName] = useState('')
  const [vkConnecting, setVkConnecting] = useState(false)

  useEffect(() => { loadBots() }, [])

  async function loadBots() {
    try {
      const [tgRes, vkRes] = await Promise.all([
        api.get('/api/bot'),
        api.get('/api/bot/vk'),
      ])
      setTgBot(tgRes.data)
      setVkBot(vkRes.data)
      if (tgRes.data) {
        setAssistantName(tgRes.data.assistant_name || '')
        setSellerLink(tgRes.data.seller_link || '')
        setGreeting(tgRes.data.greeting_message || '')
        setBotDescription(tgRes.data.bot_description || '')
        setAllowPartners(tgRes.data.allow_partners || false)
        if (tgRes.data.allow_partners) loadPartners()
      }
      if (vkRes.data) {
        setVkAssistantName(vkRes.data.assistant_name || '')
        setVkSellerLink(vkRes.data.seller_link || '')
        setVkGreeting(vkRes.data.greeting_message || '')
        setVkBotDescription(vkRes.data.bot_description || '')
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

  // Managed bot creation
  const [creationLink, setCreationLink] = useState(null)
  const [creationPolling, setCreationPolling] = useState(false)
  const [termsAccepted, setTermsAccepted] = useState(false)
  const pollingRef = useRef(null)

  // ── Telegram actions ──

  async function createManagedBot() {
    setError('')
    if (!termsAccepted) {
      setError('Необходимо принять условия Оферты и Политики обработки данных')
      return
    }
    setClaiming(true)
    try {
      const { data } = await api.post('/api/bot/create', { terms_accepted: true })
      setCreationLink(data.link)
      // Start polling for creation status
      setCreationPolling(true)
    } catch (err) {
      const d = err.response?.data?.detail
      if (d === 'У вас уже есть Telegram-бот') {
        await loadBots()
        await loadProfile()
      } else {
        setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка создания бота')
      }
    }
    setClaiming(false)
  }

  // Poll creation status
  useEffect(() => {
    if (!creationPolling) return
    pollingRef.current = setInterval(async () => {
      try {
        const { data } = await api.get('/api/bot/creation-status')
        if (data.status === 'created') {
          clearInterval(pollingRef.current)
          setCreationPolling(false)
          setCreationLink(null)
          setSuccess('Бот создан! Заполните настройки.')
          setShowTgGroup(true)
          await loadBots()
          await loadProfile()
        } else if (data.status === 'failed') {
          clearInterval(pollingRef.current)
          setCreationPolling(false)
          setCreationLink(null)
          setError('Ошибка создания бота. Попробуйте ещё раз.')
        }
      } catch { /* ignore */ }
    }, 3000)
    return () => clearInterval(pollingRef.current)
  }, [creationPolling])

  async function saveTgSettings(e) {
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
      setShowTgGroup(true)
      await loadBots()
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка сохранения')
    }
    setSaving(false)
  }

  async function disconnectTgBot() {
    try {
      await api.delete('/api/bot')
      setTgBot(null)
      setSuccess('Telegram-бот отключён')
      setShowDisconnect(false)
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка')
      setShowDisconnect(false)
    }
  }

  function copyLink() {
    if (tgBot?.bot_username) {
      navigator.clipboard.writeText(`https://t.me/${tgBot.bot_username}`)
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
      setTgBot(data)
      setSuccess('Аватарка загружена!')
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка загрузки аватарки')
    }
    setAvatarUploading(false)
  }

  // ── VK actions ──

  async function connectVk(e) {
    e.preventDefault()
    setError('')
    setVkConnecting(true)
    try {
      const { data } = await api.post('/api/bot/vk/connect', {
        group_id: parseInt(vkGroupId),
        group_token: vkGroupToken,
        assistant_name: vkConnectName || 'Ассистент',
      })
      setVkBot(data)
      setVkAssistantName(data.assistant_name || '')
      setVkSellerLink(data.seller_link || '')
      setVkGreeting(data.greeting_message || '')
      setVkBotDescription(data.bot_description || '')
      setShowTgGroup(true)
      setSuccess('VK-бот подключён!')
      setVkGroupId('')
      setVkGroupToken('')
      setVkConnectName('')
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка подключения VK-бота')
    }
    setVkConnecting(false)
  }

  async function saveVkSettings(e) {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await api.put('/api/bot/vk', {
        assistant_name: vkAssistantName,
        seller_link: vkSellerLink || null,
        greeting_message: vkGreeting || null,
        bot_description: vkBotDescription || null,
      })
      setSuccess('Настройки VK-бота сохранены!')
      await loadBots()
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка сохранения')
    }
    setSaving(false)
  }

  async function disconnectVk() {
    try {
      await api.delete('/api/bot/vk')
      setVkBot(null)
      setSuccess('VK-бот отключён')
      setShowDisconnect(false)
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка')
      setShowDisconnect(false)
    }
  }

  useEffect(() => {
    if (success) { const t = setTimeout(() => setSuccess(''), 3000); return () => clearTimeout(t) }
  }, [success])

  if (loading) return <Loader />

  // ── Platform tabs ──
  const tabBar = (
    <div className="flex gap-1 p-1 bg-white/[0.04] rounded-xl mb-6">
      <button onClick={() => { setTab('telegram'); setError('') }}
        className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
          tab === 'telegram'
            ? 'bg-white/[0.08] text-white shadow-sm'
            : 'text-white/40 hover:text-white/60'
        }`}>
        <TgIcon size={16} /> Telegram
      </button>
      <button onClick={() => { setTab('vk'); setError('') }}
        className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
          tab === 'vk'
            ? 'bg-white/[0.08] text-white shadow-sm'
            : 'text-white/40 hover:text-white/60'
        }`}>
        <VkIcon size={16} /> ВКонтакте
      </button>
    </div>
  )

  // ── TELEGRAM TAB ──
  if (tab === 'telegram') {
    if (!tgBot) {
      return (
        <div>
          <PageHeader title="Мой бот" />
          {tabBar}
          {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
          {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}

          {creationPolling ? (
            <EmptyState
              icon={Bot}
              title="Создайте бота в Telegram"
              description="Нажмите кнопку ниже — откроется Telegram, подтвердите создание бота. Страница обновится автоматически."
              action={
                <div className="flex flex-col items-center gap-4">
                  {creationLink && (
                    <a href={creationLink} target="_blank" rel="noopener noreferrer"
                      className="btn-primary inline-flex items-center gap-2 text-lg px-8 py-3">
                      <span className="relative z-10 flex items-center gap-2">
                        <ExternalLink size={20} /> Открыть в Telegram
                      </span>
                    </a>
                  )}
                  <div className="flex items-center gap-2 text-white/60">
                    <div className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
                    <span className="text-sm">Ожидание создания бота...</span>
                  </div>
                </div>
              }
            />
          ) : (
            <EmptyState
              icon={Bot}
              title="У вас пока нет Telegram-бота"
              description="Нажмите кнопку ниже — система автоматически назначит вам персонального Telegram-бота с ИИ"
              action={
                <div className="flex flex-col items-center gap-3">
                  <label className="flex items-start gap-2 max-w-md text-sm text-white/70 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={termsAccepted}
                      onChange={(e) => setTermsAccepted(e.target.checked)}
                      className="mt-0.5 w-4 h-4 rounded border-white/20 bg-white/[0.04] accent-sky-500"
                    />
                    <span>
                      Я принимаю{' '}
                      <a href="/offer" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Публичную оферту</a>{' '}
                      и{' '}
                      <a href="/privacy" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Политику обработки персональных данных</a>
                    </span>
                  </label>
                  <button onClick={createManagedBot} disabled={claiming || !termsAccepted}
                    className="btn-primary inline-flex items-center gap-2 text-lg px-8 py-3 disabled:opacity-50 disabled:cursor-not-allowed">
                    <span className="relative z-10 flex items-center gap-2">
                      <Plus size={20} /> {claiming ? 'Создание...' : 'Создать бота'}
                    </span>
                  </button>
                </div>
              }
            />
          )}
        </div>
      )
    }

    return (
      <div>
        <PageHeader title="Мой бот" actions={
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${tgBot.is_active ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.4)]' : 'bg-red-400'}`} />
            <span className="text-sm text-white/60">{tgBot.is_active ? 'Активен' : 'Неактивен'}</span>
          </div>
        } />
        {tabBar}

        {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
        {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}

        {/* Bot link card */}
        {tgBot.bot_username && (
          <div className="glass-card p-5 mb-6 border-l-4 border-l-blue-500">
            <div className="flex items-center gap-2 mb-3">
              <Link2 size={18} className="text-sky-400" />
              <span className="text-sm font-medium text-white/60">Ваша ссылка на бота</span>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-lg font-semibold text-sky-400 break-all">
                https://t.me/{tgBot.bot_username}
              </span>
              <div className="flex items-center gap-2">
                <button onClick={copyLink}
                  className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors">
                  {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                  {copied ? 'Скопировано' : 'Копировать'}
                </button>
                <a href={`https://t.me/${tgBot.bot_username}`} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors">
                  <ExternalLink size={14} /> Открыть
                </a>
              </div>
            </div>
          </div>
        )}

        {/* TG Settings form */}
        <form onSubmit={saveTgSettings} className="glass-card p-6 space-y-6">
          <div>
            <h2 className="font-display font-semibold flex items-center gap-2 mb-5">
              <Settings size={18} className="text-sky-400" />
              Основные настройки
            </h2>

            {/* Avatar */}
            <div className="flex items-center gap-4 mb-5">
              <div className="relative group cursor-pointer" onClick={() => fileInputRef.current?.click()}>
                {tgBot.avatar_url ? (
                  <img src={tgBot.avatar_url + (tgBot.avatar_url.includes('?') ? '&' : '?') + 't=' + Date.now()} alt="Аватар" className="w-20 h-20 rounded-2xl object-cover" />
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

          <div className="space-y-5">
            <h2 className="font-display font-semibold flex items-center gap-2">
              <MessageCircle size={18} className="text-sky-400" />
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
              <input type="text" value={sellerLink} onChange={e => setSellerLink(e.target.value)}
                className="input-field" placeholder="https://your-link.com" />
              <p className="text-xs text-white/30 mt-1">Бот будет давать эту ссылку заинтересованным клиентам</p>
            </div>
          </div>

          <div className="border-t border-white/[0.06]" />

          <div>
            <h2 className="font-display font-semibold flex items-center gap-2 mb-4">
              <Handshake size={18} className="text-sky-400" />
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
                <Users size={20} className="text-sky-400" />
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
                                className="text-sky-400 hover:underline truncate block max-w-[200px]">
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
                                className="flex items-center gap-1 text-sky-400 hover:text-sky-300 text-xs ml-auto">
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
          title="Отключить Telegram-бота?"
          actions={
            <>
              <button onClick={() => setShowDisconnect(false)} className="btn-secondary !py-2 !px-5 text-sm">Отмена</button>
              <button onClick={disconnectTgBot} className="bg-red-500/20 hover:bg-red-500/30 text-red-400 font-medium py-2 px-5 rounded-xl text-sm transition-colors">
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

  // ── VK TAB ──
  if (!vkBot) {
    return (
      <div>
        <PageHeader title="Мой бот" />
        {tabBar}
        {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
        {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}

        <div className="glass-card p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
              <VkIcon size={24} className="text-blue-400" />
            </div>
            <div>
              <h2 className="font-display font-semibold">Подключить VK-бота</h2>
              <p className="text-sm text-white/40">Подключите сообщество ВКонтакте для автоматических ответов</p>
            </div>
          </div>

          <form onSubmit={connectVk} className="space-y-5">
            <div>
              <label className="block text-sm text-white/60 mb-1.5">ID сообщества</label>
              <input type="number" value={vkGroupId} onChange={e => setVkGroupId(e.target.value)}
                className="input-field" placeholder="123456789" required />
              <p className="text-xs text-white/30 mt-1">Числовой ID вашего сообщества ВКонтакте</p>
            </div>

            <div>
              <label className="block text-sm text-white/60 mb-1.5">Токен сообщества</label>
              <input type="password" value={vkGroupToken} onChange={e => setVkGroupToken(e.target.value)}
                className="input-field" placeholder="vk1.a.xxxxx..." required />
              <p className="text-xs text-white/30 mt-1">Настройки → Работа с API → Ключи доступа → Создать ключ</p>
            </div>

            <div>
              <label className="block text-sm text-white/60 mb-1.5">Имя ассистента</label>
              <input type="text" value={vkConnectName} onChange={e => setVkConnectName(e.target.value)}
                className="input-field" placeholder="Ассистент Анны" required />
            </div>

            <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
              <p className="text-sm text-blue-400 font-medium mb-3">Перед подключением:</p>
              <div className="space-y-3">
                {[
                  { n: 1, title: 'Откройте сообщество → Управление', desc: 'Нажмите шестерёнку справа от названия', img: '/vk-guide/1.png' },
                  { n: 2, title: 'Сообщения → включите «Сообщения сообщества»', desc: null, img: '/vk-guide/2.png' },
                  { n: 3, title: 'Настройки для бота → включите возможности бота', desc: 'Добавьте кнопку «Начать» и сохраните', imgs: ['/vk-guide/3.png', '/vk-guide/4.png'] },
                  { n: 4, title: 'Работа с API → Создать ключ доступа', desc: null, img: '/vk-guide/5.png' },
                  { n: 5, title: 'Выберите все разрешения при создании ключа', desc: null, img: '/vk-guide/6.png' },
                  { n: 6, title: 'Скопируйте созданный ключ → вставьте в поле «Токен сообщества»', desc: null, img: '/vk-guide/7.png' },
                  { n: 7, title: 'Вкладка Long Poll API → включите', desc: null, img: '/vk-guide/8.png' },
                  { n: 8, title: 'Типы событий → отметьте «Входящее сообщение»', desc: null, imgs: ['/vk-guide/9.png', '/vk-guide/10.png'] },
                  { n: 9, title: 'Скопируйте цифры после «club» на странице настроек', desc: 'Вставьте их в поле «ID сообщества»', imgs: ['/vk-guide/11.png', '/vk-guide/12.png', '/vk-guide/13.png'] },
                ].map(step => (
                  <InstructionStep
                    key={step.n}
                    number={step.n}
                    title={step.title}
                    description={step.desc}
                    image={step.img || (step.imgs && step.imgs[0])}
                    onImageClick={() => {
                      const allImages = [1,2,3,4,5,6,7,8,9,10,11,12,13].map(i => ({
                        src: `/vk-guide/${i}.png`,
                        alt: `Шаг ${i}`,
                      }))
                      const idx = step.img
                        ? parseInt(step.img.match(/(\d+)\.png/)[1]) - 1
                        : parseInt(step.imgs[0].match(/(\d+)\.png/)[1]) - 1
                      setVkGuideStart(idx)
                      setShowVkGuide(true)
                    }}
                  />
                ))}
              </div>
              <button type="button" onClick={() => { setVkGuideStart(0); setShowVkGuide(true) }}
                className="mt-4 w-full flex items-center justify-center gap-2 text-sm text-blue-400 hover:text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 rounded-xl py-2.5 transition-colors cursor-pointer">
                <ZoomIn size={16} /> Открыть все скриншоты
              </button>
            </div>

            <button type="submit" disabled={vkConnecting}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
              <span className="relative z-10 flex items-center gap-2">
                <VkIcon size={18} /> {vkConnecting ? 'Подключение...' : 'Подключить VK-бота'}
              </span>
            </button>
          </form>
        </div>

        <ImageGallery
          open={showVkGuide}
          onClose={() => setShowVkGuide(false)}
          startIndex={vkGuideStart}
          images={[1,2,3,4,5,6,7,8,9,10,11,12,13].map(i => ({
            src: `/vk-guide/${i}.png`,
            alt: `Шаг ${i}`,
            caption: [
              'Откройте сообщество → Управление',
              'Сообщения → включите сообщения сообщества',
              'Настройки для бота → возможности бота',
              'Добавьте кнопку «Начать» и сохраните',
              'Работа с API → Создать ключ доступа',
              'Выберите все разрешения',
              'Скопируйте созданный ключ → вставьте в поле «Токен»',
              'Long Poll API → включите',
              'Типы событий → входящее сообщение',
              'Отметьте нужные события',
              'Найдите цифры после «club»',
              'Скопируйте ID сообщества',
              'Вставьте ID на сайте и нажмите «Подключить»',
            ][i - 1],
          }))}
        />
      </div>
    )
  }

  // VK connected — show settings
  return (
    <div>
      <PageHeader title="Мой бот" actions={
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${vkBot.is_active ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.4)]' : 'bg-red-400'}`} />
          <span className="text-sm text-white/60">{vkBot.is_active ? 'Активен' : 'Неактивен'}</span>
        </div>
      } />
      {tabBar}

      {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}

      {/* VK Bot info card */}
      {vkBot.bot_username && (
        <div className="glass-card p-5 mb-6 border-l-4 border-l-blue-500">
          <div className="flex items-center gap-2 mb-3">
            <VkIcon size={18} className="text-blue-400" />
            <span className="text-sm font-medium text-white/60">Сообщество ВКонтакте</span>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-lg font-semibold text-blue-400 break-all">
              vk.com/{vkBot.bot_username}
            </span>
            <a href={`https://vk.com/${vkBot.bot_username}`} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors">
              <ExternalLink size={14} /> Открыть
            </a>
            {vkBot.vk_group_id && (
              <a href={`https://vk.com/im?sel=-${vkBot.vk_group_id}`} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 hover:text-blue-300 border border-blue-500/20 transition-colors">
                <MessageCircle size={14} /> Написать боту
              </a>
            )}
          </div>
        </div>
      )}

      {/* VK Settings form */}
      <form onSubmit={saveVkSettings} className="glass-card p-6 space-y-6">
        <div>
          <h2 className="font-display font-semibold flex items-center gap-2 mb-5">
            <Settings size={18} className="text-blue-400" />
            Настройки VK-бота
          </h2>

          <div>
            <label className="block text-sm text-white/60 mb-1.5">Имя ассистента</label>
            <input type="text" value={vkAssistantName} onChange={e => setVkAssistantName(e.target.value)}
              className="input-field" placeholder="Ассистент Анны" required />
            <p className="text-xs text-white/30 mt-1">Как бот будет представляться пользователям</p>
          </div>
        </div>

        <div className="border-t border-white/[0.06]" />

        <div className="space-y-5">
          <h2 className="font-display font-semibold flex items-center gap-2">
            <MessageCircle size={18} className="text-blue-400" />
            Контент
          </h2>

          <div>
            <label className="block text-sm text-white/60 mb-1.5">Описание бота</label>
            <textarea value={vkBotDescription} onChange={e => setVkBotDescription(e.target.value)}
              className="input-field min-h-[80px] resize-y" placeholder="Персональный помощник по продукции FitLine" maxLength={512} />
          </div>

          <div>
            <label className="block text-sm text-white/60 mb-1.5">Приветственное сообщение</label>
            <textarea value={vkGreeting} onChange={e => setVkGreeting(e.target.value)}
              className="input-field min-h-[100px] resize-y" placeholder="Привет! Я ассистент..." />
          </div>

          <div>
            <label className="block text-sm text-white/60 mb-1.5">Ваша ссылка</label>
            <input type="text" value={vkSellerLink} onChange={e => setVkSellerLink(e.target.value)}
              className="input-field" placeholder="https://your-link.com" />
            <p className="text-xs text-white/30 mt-1">Бот будет давать эту ссылку заинтересованным клиентам</p>
          </div>
        </div>

        <div className="border-t border-white/[0.06]" />

        <div className="flex flex-col-reverse sm:flex-row items-start sm:items-center justify-between gap-3">
          <button type="button" onClick={() => setShowDisconnect(true)}
            className="flex items-center gap-2 text-sm text-red-400 hover:text-red-300 transition-colors">
            <Trash2 size={16} /> Отключить VK-бота
          </button>
          <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2 disabled:opacity-50 w-full sm:w-auto justify-center">
            <Save size={18} /> {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </form>

      {/* VK Disconnect Modal */}
      <Modal
        open={showDisconnect}
        onClose={() => setShowDisconnect(false)}
        title="Отключить VK-бота?"
        actions={
          <>
            <button onClick={() => setShowDisconnect(false)} className="btn-secondary !py-2 !px-5 text-sm">Отмена</button>
            <button onClick={disconnectVk} className="bg-red-500/20 hover:bg-red-500/30 text-red-400 font-medium py-2 px-5 rounded-xl text-sm transition-colors">
              Отключить
            </button>
          </>
        }
      >
        VK-бот будет полностью удалён вместе с контактами и переписками. Это действие нельзя отменить.
      </Modal>

      <TelegramGroupPopup open={showTgGroup} onClose={() => setShowTgGroup(false)} />
    </div>
  )
}
