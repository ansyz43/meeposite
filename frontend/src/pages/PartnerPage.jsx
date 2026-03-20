import { useEffect, useState } from 'react'
import api from '../api'
import { useAuth } from '../hooks/useAuth'
import { Copy, Check, Link, Users, TrendingUp, Wallet, Clock } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Loader from '../components/ui/Loader'
import StatCard from '../components/ui/StatCard'
import ReferralTree from '../components/ReferralTree'

export default function PartnerPage() {
  const { user } = useAuth()
  const [partner, setPartner] = useState(null)
  const [sessions, setSessions] = useState([])
  const [tree, setTree] = useState([])
  const [cashback, setCashback] = useState([])
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [refCopied, setRefCopied] = useState(false)
  const [sellerLink, setSellerLink] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [tab, setTab] = useState(user?.has_bot ? 'tree' : 'sessions')

  useEffect(() => { loadData() }, [])

  async function loadData() {
    try {
      const requests = [
        api.get('/api/referral/partner'),
        api.get('/api/referral/sessions'),
      ]
      if (user?.has_bot) {
        requests.push(api.get('/api/referral/my-tree'))
        requests.push(api.get('/api/referral/my-cashback'))
      }
      const results = await Promise.allSettled(requests)
      const partnerData = results[0]?.status === 'fulfilled' ? results[0].value.data : null
      const sessionsData = results[1]?.status === 'fulfilled' ? results[1].value.data : []
      const treeData = results[2]?.status === 'fulfilled' ? results[2].value.data : []
      const cashbackData = results[3]?.status === 'fulfilled' ? results[3].value.data : []
      setPartner(partnerData)
      setSessions(Array.isArray(sessionsData) ? sessionsData : [])
      setTree(Array.isArray(treeData) ? treeData : [])
      setCashback(Array.isArray(cashbackData) ? cashbackData : [])
      if (partnerData) {
        setSellerLink(partnerData.seller_link || '')
      }
    } catch { /* ignore */ }
    setLoading(false)
  }

  function copyRefLink() {
    if (user?.ref_link) {
      navigator.clipboard.writeText(user.ref_link)
      setRefCopied(true)
      setTimeout(() => setRefCopied(false), 2000)
    }
  }

  function copyBotRefLink() {
    if (partner?.ref_link) {
      navigator.clipboard.writeText(partner.ref_link)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  async function saveSellerLink(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const { data } = await api.put('/api/referral/partner', { seller_link: sellerLink })
      setPartner(data)
      setSuccess('Ссылка обновлена!')
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка')
    }
    setSaving(false)
  }

  useEffect(() => {
    if (success) { const t = setTimeout(() => setSuccess(''), 3000); return () => clearTimeout(t) }
  }, [success])

  if (loading) return <Loader />

  const totalReferrals = countNodes(tree)
  const totalCashback = user?.cashback_balance || 0
  const monthCashback = cashback
    .filter(tx => {
      const d = new Date(tx.created_at)
      const now = new Date()
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
    })
    .reduce((sum, tx) => sum + tx.amount, 0)

  const tabs = [
    ...(user?.has_bot ? [
      { key: 'tree', label: 'Дерево', icon: Users },
      { key: 'cashback', label: 'Кэшбек', icon: Wallet },
    ] : []),
    ...(partner ? [{ key: 'sessions', label: 'Сессии', icon: Clock }] : []),
  ]

  return (
    <div>
      <PageHeader title="Партнёрство" />

      {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}

      {/* Stats */}
      {user?.has_bot && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <StatCard icon={Wallet} label="Баланс кэшбека" value={totalCashback.toFixed(2)} color="green" />
          <StatCard icon={Users} label="В команде" value={totalReferrals} color="emerald" />
          <StatCard icon={TrendingUp} label="Доход за месяц" value={monthCashback.toFixed(2)} color="yellow" />
        </div>
      )}

      {/* Referral link */}
      {user?.has_bot && user?.ref_link && (
        <div className="glass-card p-4 mb-4">
          <div className="text-xs text-white/40 mb-2">Ваша ссылка для приглашения на платформу</div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <Link size={16} className="text-green-400 shrink-0" />
              <span className="text-white/70 text-sm truncate">{user.ref_link}</span>
            </div>
            <button onClick={copyRefLink} className="flex items-center gap-2 text-sm text-green-400 hover:text-green-300 shrink-0 ml-3 transition-colors">
              {refCopied ? <Check size={16} /> : <Copy size={16} />}
              {refCopied ? 'Скопировано' : 'Скопировать'}
            </button>
          </div>
        </div>
      )}

      {/* Bot partner link */}
      {partner && (
        <div className="glass-card p-4 mb-6">
          <div className="text-xs text-white/40 mb-2">Реферальная ссылка бота @{partner.bot_username} (кредитов: {partner.credits})</div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <Link size={16} className="text-emerald-400 shrink-0" />
              <span className="text-white/70 text-sm truncate">{partner.ref_link}</span>
            </div>
            <button onClick={copyBotRefLink} className="flex items-center gap-2 text-sm text-emerald-400 hover:text-emerald-300 shrink-0 ml-3 transition-colors">
              {copied ? <Check size={16} /> : <Copy size={16} />}
              {copied ? 'Скопировано' : 'Скопировать'}
            </button>
          </div>
        </div>
      )}

      {/* Tabs */}
      {tabs.length > 0 && (
        <div className="flex gap-1 mb-4 bg-white/[0.03] rounded-xl p-1">
          {tabs.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm flex-1 justify-center transition-all duration-200 ${
                tab === t.key ? 'bg-white/[0.06] text-white shadow-sm' : 'text-white/40 hover:text-white/60'
              }`}
            >
              <t.icon size={14} /> {t.label}
            </button>
          ))}
        </div>
      )}

      {/* Tab content */}
      {user?.has_bot && tab === 'tree' && <ReferralTree tree={tree} userName={user?.name} />}

      {user?.has_bot && tab === 'cashback' && (
        <div className="glass-card overflow-hidden">
          <div className="p-5 border-b border-white/[0.06]">
            <h2 className="font-display font-semibold flex items-center gap-2">
              <Wallet size={18} className="text-green-400" />
              История кэшбека
            </h2>
          </div>
          {cashback.length === 0 ? (
            <div className="p-8 text-center text-white/40 text-sm">Пока нет начислений</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="glass-table">
                <thead>
                  <tr>
                    <th>От кого</th>
                    <th>Уровень</th>
                    <th>Тип</th>
                    <th>Исходная сумма</th>
                    <th className="text-right">Ваш доход</th>
                    <th className="text-right">Дата</th>
                  </tr>
                </thead>
                <tbody>
                  {cashback.map(tx => (
                    <tr key={tx.id}>
                      <td className="font-medium text-white/80">{tx.from_user_name}</td>
                      <td>{tx.level}</td>
                      <td>{tx.source_type === 'credits' ? 'Кредиты' : 'Подписка'}</td>
                      <td>{tx.source_amount.toFixed(1)} кр.</td>
                      <td className="text-right text-green-400 font-medium">+{tx.amount.toFixed(2)}</td>
                      <td className="text-right text-white/40">{new Date(tx.created_at).toLocaleDateString('ru-RU')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'sessions' && partner && (
        <div className="space-y-6">
          <div className="glass-card overflow-hidden">
            <div className="p-5 border-b border-white/[0.06]">
              <h2 className="font-display font-semibold flex items-center gap-2">
                <Clock size={18} className="text-emerald-400" />
                Сессии клиентов ({sessions.length})
              </h2>
            </div>
            {sessions.length === 0 ? (
              <div className="p-8 text-center text-white/40 text-sm">Пока нет клиентов</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="glass-table">
                  <thead>
                    <tr>
                      <th>Статус</th>
                      <th>Клиент</th>
                      <th>Username</th>
                      <th className="text-right">Действует до</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessions.map(s => (
                      <tr key={s.id}>
                        <td>
                          <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full ${s.is_active ? 'bg-green-500/10 text-green-400' : 'bg-white/5 text-white/30'}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${s.is_active ? 'bg-green-400' : 'bg-white/20'}`} />
                            {s.is_active ? 'Активна' : 'Завершена'}
                          </span>
                        </td>
                        <td className="font-medium text-white/80">{s.first_name || 'Пользователь'}</td>
                        <td>{s.telegram_username ? <span className="text-white/40">@{s.telegram_username}</span> : <span className="text-white/20">—</span>}</td>
                        <td className="text-right text-white/40">
                          {new Date(s.expires_at).toLocaleString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Seller link form — separate card */}
          <div className="glass-card p-5">
            <h3 className="font-display font-semibold text-sm mb-4">Ваша ссылка продавца</h3>
            <form onSubmit={saveSellerLink} className="flex gap-3">
              <input
                type="url"
                value={sellerLink}
                onChange={e => setSellerLink(e.target.value)}
                className="input-field flex-1 !py-2.5"
                placeholder="https://your-seller-link.com"
                required
              />
              <button type="submit" disabled={saving} className="btn-primary !px-5 !py-2.5 disabled:opacity-50 shrink-0">
                <span className="relative z-10">{saving ? '...' : 'Сохранить'}</span>
              </button>
            </form>
          </div>
        </div>
      )}

      {/* CTA for non-partners */}
      {!partner && (
        <div className="glass-card p-8 text-center mt-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/[0.03] to-transparent pointer-events-none" />
          <div className="relative">
            <p className="text-white/50 mb-4">Хотите также зарабатывать с ботом?</p>
            <a href="/dashboard/catalog" className="btn-primary inline-flex items-center gap-2 text-sm">
              <span className="relative z-10">Стать партнёром бота</span>
            </a>
          </div>
        </div>
      )}
    </div>
  )
}

function countNodes(nodes) {
  let count = 0
  for (const n of nodes) {
    count += 1
    if (n.children) count += countNodes(n.children)
  }
  return count
}
