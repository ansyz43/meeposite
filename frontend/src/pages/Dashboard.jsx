import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { Bot, MessageSquare, Users, ArrowRight, Sparkles, Megaphone, User, Settings, CheckCircle2 } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Loader from '../components/ui/Loader'
import EmptyState from '../components/ui/EmptyState'
import StatCard from '../components/ui/StatCard'

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

  if (loading) return <Loader />

  // Setup progress
  const setupSteps = [
    { label: 'Бот подключён', done: !!bot },
    { label: 'Имя ассистента', done: !!bot?.assistant_name },
    { label: 'Ссылка продавца', done: !!bot?.seller_link },
    { label: 'Аватарка загружена', done: !!bot?.avatar_url },
  ]
  const setupDone = setupSteps.filter(s => s.done).length
  const setupTotal = setupSteps.length

  return (
    <div className="dashboard-page">
      <PageHeader title="Панель управления" />

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <StatCard icon={Bot} label="Бот" value={bot ? (bot.is_active ? 'Активен' : 'Неактивен') : 'Не подключён'}
          color={bot?.is_active ? 'green' : 'yellow'} />
        <StatCard icon={Users} label="Контакты" value={stats.contacts} color="emerald" />
        <StatCard icon={MessageSquare} label="Диалоги" value={stats.conversations} color="teal" />
      </div>

      {/* Empty state */}
      {!bot && (
        <EmptyState
          icon={Bot}
          title="У вас пока нет бота"
          description="Нажмите кнопку — система автоматически назначит вам персонального ИИ-бота"
          action={
            <Link to="/dashboard/bot" className="btn-primary inline-flex items-center gap-2">
              <span className="relative z-10 flex items-center gap-2">
                Подключить <ArrowRight size={18} />
              </span>
            </Link>
          }
        />
      )}

      {/* Setup progress + Quick actions */}
      {bot && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quick actions — bento grid */}
          <div className="lg:col-span-2 glass-card p-6">
            <h2 className="font-display font-semibold mb-5 flex items-center gap-2">
              <Sparkles size={16} className="text-sky-400" />
              Быстрые действия
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { to: '/dashboard/bot', icon: Settings, label: 'Настройки бота', desc: 'Имя, аватар, приветствие' },
                { to: '/dashboard/conversations', icon: MessageSquare, label: 'Переписки', desc: 'Диалоги с клиентами' },
                { to: '/dashboard/contacts', icon: Users, label: 'Контакты', desc: 'База клиентов' },
                { to: '/dashboard/broadcast', icon: Megaphone, label: 'Рассылка', desc: 'Отправить сообщение всем' },
              ].map(item => (
                <Link key={item.to} to={item.to}
                  className="flex items-center gap-4 p-4 rounded-xl border border-white/[0.06] bg-white/[0.02]
                  hover:border-sky-500/20 hover:bg-sky-500/[0.04] transition-all duration-300 group">
                  <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center group-hover:shadow-[0_0_20px_rgba(16,185,129,0.15)] transition-shadow shrink-0">
                    <item.icon size={18} className="text-sky-400" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white/80 group-hover:text-white transition-colors">{item.label}</div>
                    <div className="text-xs text-white/30">{item.desc}</div>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Setup progress */}
          <div className="glass-card p-6">
            <h2 className="font-display font-semibold mb-5 flex items-center gap-2">
              <CheckCircle2 size={16} className="text-sky-400" />
              Настройка
            </h2>
            <div className="mb-4">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-white/40">{setupDone} из {setupTotal}</span>
                <span className="text-sky-400 font-mono text-xs">{Math.round(setupDone / setupTotal * 100)}%</span>
              </div>
              <div className="h-2 bg-white/[0.06] rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full transition-all duration-700"
                  style={{ width: `${(setupDone / setupTotal) * 100}%` }}
                />
              </div>
            </div>
            <div className="space-y-3">
              {setupSteps.map((step, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
                    step.done ? 'bg-sky-500/20 text-sky-400' : 'bg-white/[0.06] text-white/20'
                  }`}>
                    {step.done ? <CheckCircle2 size={14} /> : <div className="w-2 h-2 rounded-full bg-white/20" />}
                  </div>
                  <span className={`text-sm ${step.done ? 'text-white/60' : 'text-white/30'}`}>{step.label}</span>
                </div>
              ))}
            </div>
            {setupDone < setupTotal && (
              <Link to="/dashboard/bot" className="mt-5 text-sm text-sky-400 hover:text-sky-300 flex items-center gap-1 transition-colors">
                Завершить настройку <ArrowRight size={14} />
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
