import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { Bot, MessageSquare, Users, ArrowRight, Sparkles } from 'lucide-react'

export default function Dashboard() {
  const [bot, setBot] = useState(null)
  const [stats, setStats] = useState({ contacts: 0, conversations: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [botRes, contactsRes, convRes] = await Promise.all([
          api.get('/api/bot'),
          api.get('/api/contacts?per_page=1').catch(() => ({ data: { total: 0 } })),
          api.get('/api/conversations?per_page=1').catch(() => ({ data: { total: 0 } })),
        ])
        setBot(botRes.data)
        setStats({
          contacts: contactsRes.data?.total || 0,
          conversations: convRes.data?.total || 0,
        })
      } catch { /* ignore */ }
      setLoading(false)
    }
    load()
  }, [])

  if (loading) return (
    <div className="flex items-center gap-3 text-white/40">
      <div className="w-5 h-5 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" />
      Загрузка...
    </div>
  )

  return (
    <div>
      <h1 className="text-2xl font-display font-bold mb-8">Панель управления</h1>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <StatCard icon={Bot} label="Бот" value={bot ? (bot.is_active ? 'Активен' : 'Неактивен') : 'Не подключён'}
          color={bot?.is_active ? 'green' : 'yellow'} />
        <StatCard icon={Users} label="Контакты" value={stats.contacts} color="emerald" />
        <StatCard icon={MessageSquare} label="Диалоги" value={stats.conversations} color="teal" />
      </div>

      {/* Empty state */}
      {!bot && (
        <div className="glass-card p-10 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/[0.04] to-transparent pointer-events-none" />
          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-5">
              <Bot size={32} className="text-emerald-400" />
            </div>
            <h2 className="text-xl font-display font-semibold mb-2">У вас пока нет бота</h2>
            <p className="text-white/40 mb-6 max-w-sm mx-auto text-sm">Нажмите кнопку — система автоматически назначит вам персонального ИИ-бота</p>
            <Link to="/dashboard/bot" className="btn-primary inline-flex items-center gap-2">
              <span className="relative z-10 flex items-center gap-2">
                Подключить <ArrowRight size={18} />
              </span>
            </Link>
          </div>
        </div>
      )}

      {/* Quick actions */}
      {bot && (
        <div className="glass-card p-6">
          <h2 className="font-display font-semibold mb-4 flex items-center gap-2">
            <Sparkles size={16} className="text-emerald-400" />
            Быстрые действия
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { to: '/dashboard/bot', icon: Bot, label: 'Настройки бота' },
              { to: '/dashboard/conversations', icon: MessageSquare, label: 'Переписки' },
              { to: '/dashboard/contacts', icon: Users, label: 'Контакты' },
            ].map(item => (
              <Link key={item.to} to={item.to}
                className="flex items-center gap-3 p-4 rounded-xl border border-white/[0.06] bg-white/[0.02]
                hover:border-emerald-500/20 hover:bg-emerald-500/[0.04] transition-all duration-300 group">
                <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center group-hover:shadow-glow transition-shadow">
                  <item.icon size={17} className="text-emerald-400" />
                </div>
                <span className="text-sm text-white/60 group-hover:text-white/80 transition-colors">{item.label}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    green: 'text-green-400 bg-green-500/10 border-green-500/20',
    yellow: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    teal: 'text-teal-400 bg-teal-500/10 border-teal-500/20',
  }
  return (
    <div className="stat-card p-6">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${colors[color]}`}>
          <Icon size={20} />
        </div>
        <span className="text-white/40 text-sm">{label}</span>
      </div>
      <div className="text-2xl font-display font-bold">{value}</div>
    </div>
  )
}
