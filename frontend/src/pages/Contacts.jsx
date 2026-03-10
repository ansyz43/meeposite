import { useEffect, useState } from 'react'
import api from '../api'
import { Users, Search, Download } from 'lucide-react'

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

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">Контакты</h1>
        <button onClick={exportCSV} className="btn-secondary flex items-center gap-2 !py-2 text-sm">
          <Download size={16} /> Экспорт CSV
        </button>
      </div>

      <div className="glass-card overflow-hidden">
        {/* Search */}
        <div className="p-4 border-b border-white/5">
          <div className="relative max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
            <input type="text" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }}
              placeholder="Поиск по имени, username, телефону..." className="input-field pl-9 !py-2 text-sm" />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-white/40 text-left">
                <th className="px-4 py-3 font-medium">Имя</th>
                <th className="px-4 py-3 font-medium">Username</th>
                <th className="px-4 py-3 font-medium">Телефон</th>
                <th className="px-4 py-3 font-medium">Первое сообщение</th>
                <th className="px-4 py-3 font-medium">Последняя активность</th>
                <th className="px-4 py-3 font-medium text-right">Сообщений</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan="6" className="px-4 py-8 text-center text-white/40">Загрузка...</td></tr>
              )}
              {!loading && contacts.length === 0 && (
                <tr><td colSpan="6" className="px-4 py-12 text-center">
                  <Users size={32} className="mx-auto mb-2 text-white/20" />
                  <span className="text-white/30">Пока нет контактов</span>
                </td></tr>
              )}
              {contacts.map(c => (
                <tr key={c.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="px-4 py-3">{[c.first_name, c.last_name].filter(Boolean).join(' ') || '—'}</td>
                  <td className="px-4 py-3 text-white/60">{c.telegram_username ? '@' + c.telegram_username : '—'}</td>
                  <td className="px-4 py-3 text-white/60">{c.phone || '—'}</td>
                  <td className="px-4 py-3 text-white/40">{c.first_message_at ? new Date(c.first_message_at).toLocaleDateString('ru') : '—'}</td>
                  <td className="px-4 py-3 text-white/40">{c.last_message_at ? new Date(c.last_message_at).toLocaleDateString('ru') : '—'}</td>
                  <td className="px-4 py-3 text-right">{c.message_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > 50 && (
          <div className="p-4 border-t border-white/5 flex items-center justify-between">
            <span className="text-sm text-white/40">Всего: {total}</span>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="btn-secondary !py-1.5 !px-3 text-sm disabled:opacity-30">Назад</button>
              <button onClick={() => setPage(p => p + 1)} disabled={page * 50 >= total}
                className="btn-secondary !py-1.5 !px-3 text-sm disabled:opacity-30">Далее</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
