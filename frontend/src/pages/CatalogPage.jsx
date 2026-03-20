import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import { Bot, ArrowRight } from 'lucide-react'

export default function CatalogPage() {
  const [bots, setBots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [selectedBot, setSelectedBot] = useState(null)
  const [sellerLink, setSellerLink] = useState('')
  const [creating, setCreating] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadCatalog()
  }, [])

  async function loadCatalog() {
    try {
      const { data } = await api.get('/api/referral/catalog')
      setBots(data)
    } catch { /* ignore */ }
    setLoading(false)
  }

  async function becomePartner(e) {
    e.preventDefault()
    if (!selectedBot || !sellerLink) return
    setCreating(true)
    setError('')
    try {
      await api.post('/api/referral/partner', {
        bot_id: selectedBot.id,
        seller_link: sellerLink,
      })
      setSuccess('Вы стали партнёром!')
      setTimeout(() => navigate('/dashboard/partner'), 1500)
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка')
    }
    setCreating(false)
  }

  useEffect(() => {
    if (success) { const t = setTimeout(() => setSuccess(''), 3000); return () => clearTimeout(t) }
  }, [success])

  if (loading) return (
    <div className="flex items-center gap-3 text-white/40">
      <div className="w-5 h-5 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" />
      Загрузка...
    </div>
  )

  return (
    <div>
      <h1 className="text-2xl font-display font-bold mb-2">Каталог ботов</h1>
      <p className="text-white/50 mb-8">Выберите бота, чтобы стать его партнёром и получить реферальную ссылку</p>

      {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}

      {bots.length === 0 ? (
        <div className="glass-card p-8 text-center">
          <Bot size={40} className="text-white/20 mx-auto mb-4" />
          <p className="text-white/50">Пока нет доступных ботов для партнёрства</p>
        </div>
      ) : (
        <div className="grid gap-4 mb-8">
          {bots.map(bot => (
            <div
              key={bot.id}
              onClick={() => setSelectedBot(bot)}
              className={`glass-card p-5 cursor-pointer transition-all ${
                selectedBot?.id === bot.id
                  ? 'border-emerald-500/50 bg-emerald-500/5'
                  : 'hover:bg-white/5'
              }`}
            >
              <div className="flex items-center gap-4">
                {bot.avatar_url ? (
                  <img src={bot.avatar_url} alt="" className="w-12 h-12 rounded-xl object-cover" />
                ) : (
                  <div className="w-12 h-12 rounded-xl bg-white/[0.06] flex items-center justify-center">
                    <Bot size={24} className="text-white/30" />
                  </div>
                )}
                <div className="flex-1">
                  <div className="font-medium">{bot.assistant_name}</div>
                  {bot.bot_username && (
                    <div className="text-sm text-white/40">@{bot.bot_username}</div>
                  )}
                </div>
                {selectedBot?.id === bot.id && (
                  <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center">
                    <div className="w-2 h-2 rounded-full bg-white" />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedBot && (
        <form onSubmit={becomePartner} className="glass-card p-6 space-y-5">
          <h2 className="font-semibold">Стать партнёром — {selectedBot.assistant_name}</h2>
          <div>
            <label className="block text-sm text-white/60 mb-1.5">Ваша ссылка продавца</label>
            <input
              type="url"
              value={sellerLink}
              onChange={e => setSellerLink(e.target.value)}
              className="input-field"
              placeholder="https://your-seller-link.com"
              required
            />
            <p className="text-xs text-white/30 mt-1">Бот будет давать эту ссылку вашим клиентам</p>
          </div>
          <button type="submit" disabled={creating} className="btn-primary flex items-center gap-2 disabled:opacity-50">
            <ArrowRight size={18} /> {creating ? 'Создание...' : 'Стать партнёром'}
          </button>
        </form>
      )}
    </div>
  )
}
