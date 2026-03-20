import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import { Bot, ArrowRight, Store } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Loader from '../components/ui/Loader'
import EmptyState from '../components/ui/EmptyState'

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

  if (loading) return <Loader />

  return (
    <div>
      <PageHeader title="Каталог ботов" subtitle="Выберите бота, чтобы стать его партнёром" />

      {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}

      {bots.length === 0 ? (
        <EmptyState icon={Store} title="Нет доступных ботов" description="Пока нет ботов, которые принимают партнёров" />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {bots.map(bot => (
            <div
              key={bot.id}
              onClick={() => setSelectedBot(selectedBot?.id === bot.id ? null : bot)}
              className={`glass-card p-5 cursor-pointer transition-all duration-300 ${
                selectedBot?.id === bot.id
                  ? 'border-emerald-500/50 bg-emerald-500/[0.06] shadow-[0_0_30px_rgba(16,185,129,0.08)]'
                  : 'hover:bg-white/[0.04]'
              }`}
            >
              <div className="flex items-center gap-4">
                {bot.avatar_url ? (
                  <img src={bot.avatar_url} alt="" className="w-12 h-12 rounded-xl object-cover" />
                ) : (
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 flex items-center justify-center">
                    <Bot size={24} className="text-emerald-400" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{bot.assistant_name}</div>
                  {bot.bot_username && (
                    <div className="text-sm text-white/35">@{bot.bot_username}</div>
                  )}
                </div>
                {selectedBot?.id === bot.id && (
                  <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center shrink-0">
                    <div className="w-2 h-2 rounded-full bg-white" />
                  </div>
                )}
              </div>

              {/* Inline form */}
              {selectedBot?.id === bot.id && (
                <form onSubmit={becomePartner} className="mt-5 pt-5 border-t border-white/[0.06] space-y-4" onClick={e => e.stopPropagation()}>
                  <div>
                    <label className="block text-sm text-white/60 mb-1.5">Ваша ссылка продавца</label>
                    <input
                      type="url"
                      value={sellerLink}
                      onChange={e => setSellerLink(e.target.value)}
                      className="input-field !py-2.5"
                      placeholder="https://your-seller-link.com"
                      required
                    />
                    <p className="text-xs text-white/30 mt-1">Бот будет давать эту ссылку вашим клиентам</p>
                  </div>
                  <button type="submit" disabled={creating} className="btn-primary flex items-center gap-2 disabled:opacity-50 w-full justify-center">
                    <span className="relative z-10 flex items-center gap-2">
                      <ArrowRight size={16} /> {creating ? 'Создание...' : 'Стать партнёром'}
                    </span>
                  </button>
                </form>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
