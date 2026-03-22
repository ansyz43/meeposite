import { useState, useEffect, useCallback } from 'react'
import { Shield, Users, Bot, BarChart3, Search, Trash2, Eye, ToggleLeft, ToggleRight, ChevronLeft, ChevronRight, MessageSquare, X, AlertTriangle } from 'lucide-react'
import api from '../api'

const TABS = [
  { key: 'stats', label: 'Статистика', icon: BarChart3 },
  { key: 'users', label: 'Пользователи', icon: Users },
  { key: 'bots', label: 'Боты', icon: Bot },
]

function StatCard({ label, value, sub, accent }) {
  return (
    <div className={`glass-card p-5 ${accent ? 'border-emerald-500/20' : ''}`}>
      <div className="text-white/40 text-xs font-medium mb-2">{label}</div>
      <div className="text-2xl font-display font-bold text-white">{value}</div>
      {sub && <div className="text-white/30 text-xs mt-1">{sub}</div>}
    </div>
  )
}

function StatsTab() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/admin/stats').then(r => setStats(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center py-20"><div className="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" /></div>
  if (!stats) return null

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard label="Пользователи" value={stats.total_users} sub={`${stats.active_users} активных`} accent />
      <StatCard label="Боты (всего)" value={stats.total_bots} sub={`${stats.assigned_bots} назначены · ${stats.pool_bots} в пуле`} />
      <StatCard label="Контакты" value={stats.total_contacts} />
      <StatCard label="Сообщения" value={stats.total_messages} />
      <StatCard label="Назначенные боты" value={stats.assigned_bots} />
      <StatCard label="Боты в пуле" value={stats.pool_bots} />
      <StatCard label="Рассылки" value={stats.total_broadcasts} />
      <StatCard label="Активные юзеры" value={stats.active_users} />
    </div>
  )
}

function ConfirmModal({ open, onClose, onConfirm, title, message }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="glass-card p-6 max-w-md w-full" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
            <AlertTriangle size={20} className="text-red-400" />
          </div>
          <h3 className="font-display font-semibold text-white">{title}</h3>
        </div>
        <p className="text-white/50 text-sm mb-6">{message}</p>
        <div className="flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm text-white/50 hover:text-white/80 transition-colors">Отмена</button>
          <button onClick={onConfirm} className="px-4 py-2 rounded-lg text-sm bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/20 transition-colors">Удалить</button>
        </div>
      </div>
    </div>
  )
}

function UserDetailModal({ userId, onClose }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!userId) return
    api.get(`/api/admin/users/${userId}`).then(r => setUser(r.data)).finally(() => setLoading(false))
  }, [userId])

  if (!userId) return null

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="glass-card p-6 max-w-lg w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h3 className="font-display font-semibold text-white">Пользователь</h3>
          <button onClick={onClose} className="p-1 text-white/30 hover:text-white transition-colors"><X size={18} /></button>
        </div>
        {loading ? (
          <div className="flex justify-center py-10"><div className="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" /></div>
        ) : user ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="text-white/40">Email:</span> <span className="text-white/80">{user.email}</span></div>
              <div><span className="text-white/40">Имя:</span> <span className="text-white/80">{user.name}</span></div>
              <div><span className="text-white/40">Провайдер:</span> <span className="text-white/80">{user.auth_provider || 'email'}</span></div>
              <div><span className="text-white/40">Активен:</span> <span className={user.is_active ? 'text-emerald-400' : 'text-red-400'}>{user.is_active ? 'Да' : 'Нет'}</span></div>
              <div><span className="text-white/40">Контакты:</span> <span className="text-white/80">{user.contacts_count}</span></div>
              <div><span className="text-white/40">Сообщения:</span> <span className="text-white/80">{user.messages_count}</span></div>
              <div><span className="text-white/40">Кэшбэк:</span> <span className="text-white/80">{user.cashback_balance}</span></div>
              <div><span className="text-white/40">Реф. код:</span> <span className="text-white/80">{user.ref_code || '—'}</span></div>
              <div className="col-span-2"><span className="text-white/40">Регистрация:</span> <span className="text-white/80">{user.created_at ? new Date(user.created_at).toLocaleString('ru') : '—'}</span></div>
            </div>
            {user.bots?.length > 0 && (
              <div>
                <div className="text-white/40 text-xs font-medium mb-2 mt-4">Боты:</div>
                <div className="space-y-2">
                  {user.bots.map(b => (
                    <div key={b.id} className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                      <Bot size={16} className={b.platform === 'vk' ? 'text-blue-400' : 'text-emerald-400'} />
                      <div className="text-sm">
                        <span className="text-white/70">@{b.bot_username || 'no-username'}</span>
                        <span className="text-white/30 ml-2">({b.platform})</span>
                      </div>
                      <div className={`ml-auto text-xs px-2 py-0.5 rounded-full ${b.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-white/5 text-white/30'}`}>
                        {b.is_active ? 'Активен' : 'Неактивен'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : <div className="text-white/40 text-sm">Не найден</div>}
      </div>
    </div>
  )
}

function UsersTab() {
  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [viewUser, setViewUser] = useState(null)
  const limit = 20

  const load = useCallback(() => {
    setLoading(true)
    api.get('/api/admin/users', { params: { search, limit, offset: page * limit } })
      .then(r => { setUsers(r.data.users); setTotal(r.data.total) })
      .finally(() => setLoading(false))
  }, [search, page])

  useEffect(() => { load() }, [load])

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await api.delete(`/api/admin/users/${deleteTarget.id}`)
      setDeleteTarget(null)
      load()
    } catch (e) {
      alert(e.response?.data?.detail || 'Ошибка удаления')
    }
  }

  const handleToggle = async (userId) => {
    try {
      await api.patch(`/api/admin/users/${userId}/toggle`)
      load()
    } catch (e) {
      alert(e.response?.data?.detail || 'Ошибка')
    }
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div>
      {/* Search */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/25" />
        <input
          type="text"
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(0) }}
          placeholder="Поиск по имени или email..."
          className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08] text-sm text-white/80 placeholder:text-white/25 focus:outline-none focus:border-emerald-500/30"
        />
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-10"><div className="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" /></div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-white/30 text-xs border-b border-white/[0.06]">
                <th className="text-left py-3 px-3 font-medium">Имя</th>
                <th className="text-left py-3 px-3 font-medium">Email</th>
                <th className="text-left py-3 px-3 font-medium">Провайдер</th>
                <th className="text-left py-3 px-3 font-medium">Боты</th>
                <th className="text-left py-3 px-3 font-medium">Статус</th>
                <th className="text-left py-3 px-3 font-medium">Дата</th>
                <th className="text-right py-3 px-3 font-medium">Действия</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-3 text-white/70">{u.name}</td>
                  <td className="py-3 px-3 text-white/50">{u.email}</td>
                  <td className="py-3 px-3 text-white/40">{u.auth_provider || 'email'}</td>
                  <td className="py-3 px-3">
                    <div className="flex gap-1">
                      {u.bots?.map(b => (
                        <span key={b.id} className={`text-xs px-1.5 py-0.5 rounded ${b.platform === 'vk' ? 'bg-blue-500/10 text-blue-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                          {b.platform === 'vk' ? 'VK' : 'TG'}
                        </span>
                      ))}
                      {(!u.bots || u.bots.length === 0) && <span className="text-white/20">—</span>}
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                      {u.is_active ? 'Активен' : 'Заблокирован'}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-white/30 text-xs">{u.created_at ? new Date(u.created_at).toLocaleDateString('ru') : '—'}</td>
                  <td className="py-3 px-3">
                    <div className="flex gap-1 justify-end">
                      <button onClick={() => setViewUser(u.id)} className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/70 transition-colors" title="Подробнее">
                        <Eye size={15} />
                      </button>
                      {!u.is_admin && (
                        <>
                          <button onClick={() => handleToggle(u.id)} className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-amber-400 transition-colors" title={u.is_active ? 'Заблокировать' : 'Разблокировать'}>
                            {u.is_active ? <ToggleRight size={15} /> : <ToggleLeft size={15} />}
                          </button>
                          <button onClick={() => setDeleteTarget(u)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-white/30 hover:text-red-400 transition-colors" title="Удалить">
                            <Trash2 size={15} />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <div className="text-xs text-white/30">Всего: {total}</div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/70 disabled:opacity-30 transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-xs text-white/40">{page + 1} / {totalPages}</span>
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/70 disabled:opacity-30 transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      <ConfirmModal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Удалить пользователя?"
        message={`Пользователь ${deleteTarget?.name} (${deleteTarget?.email}) будет удалён. Его боты вернутся в пул. Все контакты и переписки будут удалены.`}
      />

      <UserDetailModal userId={viewUser} onClose={() => setViewUser(null)} />
    </div>
  )
}

function BotsTab() {
  const [bots, setBots] = useState([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const limit = 20

  const load = useCallback(() => {
    setLoading(true)
    api.get('/api/admin/bots', { params: { search, limit, offset: page * limit } })
      .then(r => { setBots(r.data.bots); setTotal(r.data.total) })
      .finally(() => setLoading(false))
  }, [search, page])

  useEffect(() => { load() }, [load])

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await api.delete(`/api/admin/bots/${deleteTarget.id}`)
      setDeleteTarget(null)
      load()
    } catch (e) {
      alert(e.response?.data?.detail || 'Ошибка удаления')
    }
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div>
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/25" />
        <input
          type="text"
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(0) }}
          placeholder="Поиск по username бота..."
          className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08] text-sm text-white/80 placeholder:text-white/25 focus:outline-none focus:border-emerald-500/30"
        />
      </div>

      {loading ? (
        <div className="flex justify-center py-10"><div className="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" /></div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-white/30 text-xs border-b border-white/[0.06]">
                <th className="text-left py-3 px-3 font-medium">Бот</th>
                <th className="text-left py-3 px-3 font-medium">Платформа</th>
                <th className="text-left py-3 px-3 font-medium">Владелец</th>
                <th className="text-left py-3 px-3 font-medium">Контакты</th>
                <th className="text-left py-3 px-3 font-medium">Статус</th>
                <th className="text-right py-3 px-3 font-medium">Действия</th>
              </tr>
            </thead>
            <tbody>
              {bots.map(b => (
                <tr key={b.id} className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-3">
                    <div className="text-white/70">@{b.bot_username || '—'}</div>
                    <div className="text-white/25 text-xs">{b.assistant_name}</div>
                  </td>
                  <td className="py-3 px-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${b.platform === 'vk' ? 'bg-blue-500/10 text-blue-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                      {b.platform === 'vk' ? 'VK' : 'Telegram'}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    {b.owner_email ? (
                      <div>
                        <div className="text-white/60 text-xs">{b.owner_name}</div>
                        <div className="text-white/30 text-xs">{b.owner_email}</div>
                      </div>
                    ) : (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-white/30">Пул</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-white/50">{b.contacts_count}</td>
                  <td className="py-3 px-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${b.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-white/5 text-white/30'}`}>
                      {b.is_active ? 'Активен' : 'Неактивен'}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex justify-end">
                      <button onClick={() => setDeleteTarget(b)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-white/30 hover:text-red-400 transition-colors" title="Удалить бота">
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <div className="text-xs text-white/30">Всего: {total}</div>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
              className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/70 disabled:opacity-30 transition-colors">
              <ChevronLeft size={16} />
            </button>
            <span className="text-xs text-white/40">{page + 1} / {totalPages}</span>
            <button onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page >= totalPages - 1}
              className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/30 hover:text-white/70 disabled:opacity-30 transition-colors">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      <ConfirmModal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Удалить бота?"
        message={`Бот @${deleteTarget?.bot_username || '—'} будет полностью удалён из базы данных вместе со всеми контактами и переписками.`}
      />
    </div>
  )
}

export default function AdminPage() {
  const [tab, setTab] = useState('stats')

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/10 border border-amber-500/20 flex items-center justify-center">
          <Shield size={20} className="text-amber-400" />
        </div>
        <div>
          <h1 className="text-xl font-display font-bold text-white">Админ-панель</h1>
          <p className="text-white/30 text-xs">Управление платформой</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 p-1 rounded-xl bg-white/[0.03] border border-white/[0.06] w-fit">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              tab === t.key
                ? 'bg-emerald-500/10 text-emerald-400 shadow-[inset_0_0_0_1px_rgba(16,185,129,0.2)]'
                : 'text-white/40 hover:text-white/60 hover:bg-white/[0.04]'
            }`}
          >
            <t.icon size={15} />
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="glass-card p-5">
        {tab === 'stats' && <StatsTab />}
        {tab === 'users' && <UsersTab />}
        {tab === 'bots' && <BotsTab />}
      </div>
    </div>
  )
}
