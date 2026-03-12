import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { Bot, MessageSquare, Users, ArrowRight } from 'lucide-react'

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

  if (loading) return <div className="text-white/50">Загрузка...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-8">Панель управления</h1>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard icon={Bot} label="Бот" value={bot ? (bot.is_active ? 'Активен' : 'Неактивен') : 'Не подключён'}
          color={bot?.is_active ? 'green' : 'yellow'} />
        <StatCard icon={Users} label="Контакты" value={stats.contacts} color="blue" />
        <StatCard icon={MessageSquare} label="Диалоги" value={stats.conversations} color="purple" />
      </div>

      {/* Quick actions */}
      {!bot && (
        <div className="glass-card p-8 text-center">
          <Bot size={48} className="text-accent-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">У вас пока нет бота</h2>
          <p className="text-white/50 mb-6">Нажмите кнопку — система автоматически назначит вам персонального ИИ-бота</p>
          <Link to="/dashboard/bot" className="btn-primary inline-flex items-center gap-2">
            Подключить <ArrowRight size={18} />
          </Link>
        </div>
      )}

      {bot && (
        <div className="glass-card p-6">
          <h2 className="font-semibold mb-4">Быстрые действия</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Link to="/dashboard/bot" className="flex items-center gap-3 p-4 rounded-xl border border-white/5 hover:border-accent-500/30 transition-colors">
              <Bot size={20} className="text-accent-400" />
              <span className="text-sm">Настройки бота</span>
            </Link>
            <Link to="/dashboard/conversations" className="flex items-center gap-3 p-4 rounded-xl border border-white/5 hover:border-accent-500/30 transition-colors">
              <MessageSquare size={20} className="text-accent-400" />
              <span className="text-sm">Переписки</span>
            </Link>
            <Link to="/dashboard/contacts" className="flex items-center gap-3 p-4 rounded-xl border border-white/5 hover:border-accent-500/30 transition-colors">
              <Users size={20} className="text-accent-400" />
              <span className="text-sm">Контакты</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    green: 'text-green-400 bg-green-500/10',
    yellow: 'text-yellow-400 bg-yellow-500/10',
    blue: 'text-blue-400 bg-blue-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
  }
  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colors[color]}`}>
          <Icon size={20} />
        </div>
        <span className="text-white/50 text-sm">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  )
}
