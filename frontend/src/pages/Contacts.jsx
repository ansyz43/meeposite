import { useEffect, useState } from 'react'
import api from '../api'
import { Users, Search, Download } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Loader from '../components/ui/Loader'

function VkBadge() {
  return (
    <svg width={14} height={14} viewBox="0 0 24 24" fill="currentColor" className="text-blue-400">
      <path d="M12.785 16.241s.288-.032.436-.194c.136-.148.132-.427.132-.427s-.02-1.304.587-1.496c.598-.188 1.368 1.259 2.184 1.814.616.42 1.084.328 1.084.328l2.178-.03s1.14-.07.6-.964c-.044-.073-.316-.662-1.624-1.872-1.37-1.268-1.186-1.062.464-3.254.764-1.012 1.542-2.122 1.404-2.476-.132-.33-.944-.244-.944-.244l-2.45.016s-.182-.024-.316.056c-.132.078-.216.262-.216.262s-.388 1.032-.904 1.91c-1.092 1.862-1.528 1.96-1.708 1.846-.418-.268-.314-1.076-.314-1.65 0-1.792.272-2.54-.528-2.734-.266-.064-.462-.106-1.14-.112-.87-.01-1.606.002-2.024.206-.278.136-.492.438-.362.456.162.022.528.098.722.362.25.342.242 1.11.242 1.11s.144 2.11-.336 2.372c-.33.18-.782-.188-1.754-1.874-.498-.864-.874-1.818-.874-1.818s-.072-.178-.202-.274c-.156-.116-.376-.152-.376-.152l-2.328.016s-.35.01-.478.162c-.114.136-.01.416-.01.416s1.82 4.258 3.882 6.404c1.888 1.966 4.034 1.836 4.034 1.836h.972z"/>
    </svg>
  )
}

function TgBadge() {
  return (
    <svg width={14} height={14} viewBox="0 0 24 24" fill="currentColor" className="text-sky-400">
      <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
    </svg>
  )
}

const platformTabs = [
  { key: '', label: 'Все' },
  { key: 'telegram', label: 'Telegram', icon: <TgBadge /> },
  { key: 'vk', label: 'ВКонтакте', icon: <VkBadge /> },
]

export default function Contacts() {
  const [contacts, setContacts] = useState([])
  const [search, setSearch] = useState('')
  const [platform, setPlatform] = useState('')
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)

  useEffect(() => { loadContacts() }, [search, page, platform])

  async function loadContacts() {
    setLoading(true)
    try {
      const params = { search, page, per_page: 50 }
      if (platform) params.platform = platform
      const { data } = await api.get('/api/contacts', { params })
      setContacts(data.contacts)
      setTotal(data.total)
    } catch { /* ignore */ }
    setLoading(false)
  }

  async function exportCSV() {
    try {
      const { data } = await api.get('/api/contacts/export', { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([data]))
      const a = document.createElement('a')
      a.href = url
      a.download = 'contacts.csv'
      a.click()
      window.URL.revokeObjectURL(url)
    } catch { /* ignore */ }
  }

  function profileLink(c) {
    if (c.platform === 'vk' && c.vk_id) {
      return <a href={`https://vk.com/id${c.vk_id}`} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 transition-colors">id{c.vk_id}</a>
    }
    if (c.telegram_username) {
      return <a href={`https://t.me/${c.telegram_username}`} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:text-emerald-300 transition-colors">@{c.telegram_username}</a>
    }
    return <span className="text-white/20">—</span>
  }

  const totalPages = Math.ceil(total / 50)

  return (
    <div>
      <PageHeader title="Контакты" subtitle={total > 0 ? `${total} контактов` : undefined} actions={
        <button onClick={exportCSV} className="btn-secondary flex items-center gap-2 !py-2 !px-4 text-sm">
          <Download size={16} /> Экспорт CSV
        </button>
      } />

      {/* Platform filter tabs */}
      <div className="flex gap-1 mb-4 p-1 bg-white/[0.03] rounded-xl w-fit border border-white/[0.06]">
        {platformTabs.map(t => (
          <button key={t.key} onClick={() => { setPlatform(t.key); setPage(1) }}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
              platform === t.key
                ? 'bg-white/[0.1] text-white shadow-sm'
                : 'text-white/40 hover:text-white/60 hover:bg-white/[0.04]'
            }`}>
            {t.icon}{t.label}
          </button>
        ))}
      </div>

      <div className="glass-card overflow-hidden">
        {/* Search */}
        <div className="p-4 border-b border-white/[0.06]">
          <div className="relative max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
            <input type="text" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }}
              placeholder="Поиск по имени, username, телефону..." className="input-field pl-9 !py-2 text-sm" />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="glass-table">
            <thead>
              <tr>
                <th className="w-8"></th>
                <th>Имя</th>
                <th>Профиль</th>
                <th>Телефон</th>
                <th>Первое сообщение</th>
                <th>Последняя активность</th>
                <th className="text-right">Сообщений</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan="7" className="!py-8 text-center"><Loader /></td></tr>
              )}
              {!loading && contacts.length === 0 && (
                <tr><td colSpan="7" className="!py-12 text-center">
                  <div className="w-12 h-12 rounded-2xl bg-white/[0.04] flex items-center justify-center mx-auto mb-3">
                    <Users size={24} className="text-white/20" />
                  </div>
                  <span className="text-white/30 text-sm">Пока нет контактов</span>
                </td></tr>
              )}
              {contacts.map(c => (
                <tr key={c.id}>
                  <td className="!px-3">{c.platform === 'vk' ? <VkBadge /> : <TgBadge />}</td>
                  <td className="font-medium text-white/80">{[c.first_name, c.last_name].filter(Boolean).join(' ') || '—'}</td>
                  <td>{profileLink(c)}</td>
                  <td>{c.phone || <span className="text-white/20">—</span>}</td>
                  <td className="text-white/40">{c.first_message_at ? new Date(c.first_message_at).toLocaleDateString('ru') : '—'}</td>
                  <td className="text-white/40">{c.last_message_at ? new Date(c.last_message_at).toLocaleDateString('ru') : '—'}</td>
                  <td className="text-right font-mono">{c.message_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-white/[0.06] flex items-center justify-between">
            <span className="text-xs text-white/30 font-mono">Стр. {page} из {totalPages}</span>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="text-sm px-3 py-1.5 rounded-lg border border-white/[0.08] bg-white/[0.02] hover:bg-white/[0.06] text-white/60 disabled:opacity-30 disabled:hover:bg-white/[0.02] transition-colors">
                Назад
              </button>
              <button onClick={() => setPage(p => p + 1)} disabled={page >= totalPages}
                className="text-sm px-3 py-1.5 rounded-lg border border-white/[0.08] bg-white/[0.02] hover:bg-white/[0.06] text-white/60 disabled:opacity-30 disabled:hover:bg-white/[0.02] transition-colors">
                Далее
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
