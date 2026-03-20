import { useEffect, useState } from 'react'
import api from '../api'
import { Users, Search, Download } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Loader from '../components/ui/Loader'

export default function Contacts() {
  const [contacts, setContacts] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)

  useEffect(() => { loadContacts() }, [search, page])

  async function loadContacts() {
    setLoading(true)
    try {
      const { data } = await api.get('/api/contacts', { params: { search, page, per_page: 50 } })
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

  const totalPages = Math.ceil(total / 50)

  return (
    <div>
      <PageHeader title="Контакты" subtitle={total > 0 ? `${total} контактов` : undefined} actions={
        <button onClick={exportCSV} className="btn-secondary flex items-center gap-2 !py-2 !px-4 text-sm">
          <Download size={16} /> Экспорт CSV
        </button>
      } />

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
                <th>Имя</th>
                <th>Username</th>
                <th>Телефон</th>
                <th>Первое сообщение</th>
                <th>Последняя активность</th>
                <th className="text-right">Сообщений</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan="6" className="!py-8 text-center"><Loader /></td></tr>
              )}
              {!loading && contacts.length === 0 && (
                <tr><td colSpan="6" className="!py-12 text-center">
                  <div className="w-12 h-12 rounded-2xl bg-white/[0.04] flex items-center justify-center mx-auto mb-3">
                    <Users size={24} className="text-white/20" />
                  </div>
                  <span className="text-white/30 text-sm">Пока нет контактов</span>
                </td></tr>
              )}
              {contacts.map(c => (
                <tr key={c.id}>
                  <td className="font-medium text-white/80">{[c.first_name, c.last_name].filter(Boolean).join(' ') || '—'}</td>
                  <td>{c.telegram_username ? <a href={`https://t.me/${c.telegram_username}`} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:text-emerald-300 transition-colors">@{c.telegram_username}</a> : <span className="text-white/20">—</span>}</td>
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
