import { useEffect, useState } from 'react'
import api from '../api'
import { MessageSquare, Search, Download, ArrowLeft } from 'lucide-react'

export default function Conversations() {
  const [conversations, setConversations] = useState([])
  const [selected, setSelected] = useState(null)
  const [messages, setMessages] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)

  useEffect(() => { loadConversations() }, [search])

  async function loadConversations() {
    setLoading(true)
    try {
      const { data } = await api.get('/api/conversations', { params: { search, per_page: 100 } })
      setConversations(data.conversations)
      setTotal(data.total)
    } catch { /* ignore */ }
    setLoading(false)
  }

  async function selectConversation(contactId) {
    setSelected(contactId)
    try {
      const { data } = await api.get(`/api/conversations/${contactId}`, { params: { per_page: 100 } })
      setMessages(data.messages)
    } catch { /* ignore */ }
  }

  async function exportConversation() {
    try {
      const { data } = await api.get(`/api/conversations/${selected}/export`, { responseType: 'blob' })
      const url = URL.createObjectURL(data)
      const a = document.createElement('a')
      a.href = url
      a.download = `chat_${selected}.txt`
      a.click()
      URL.revokeObjectURL(url)
    } catch { /* ignore */ }
  }

  function displayName(c) {
    if (c.first_name) return `${c.first_name}${c.last_name ? ' ' + c.last_name : ''}`
    if (c.telegram_username) return '@' + c.telegram_username
    return 'Пользователь'
  }

  return (
    <div>
      <h1 className="text-2xl font-display font-bold mb-8">Переписки</h1>
      <div className="glass-card overflow-hidden" style={{ height: 'calc(100vh - 200px)' }}>
        <div className="flex h-full relative">
          {/* Left panel — conversation list */}
          <div className={`w-full md:w-80 border-r border-white/[0.06] flex flex-col ${selected ? 'hidden md:flex' : 'flex'}`}>
            <div className="p-3 border-b border-white/[0.06]">
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
                <input type="text" value={search} onChange={e => setSearch(e.target.value)}
                  placeholder="Поиск..." className="input-field pl-9 !py-2 text-sm" />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto">
              {loading && <div className="p-4 text-white/40 text-sm">Загрузка...</div>}
              {!loading && conversations.length === 0 && (
                <div className="p-8 text-center text-white/30 text-sm">
                  <MessageSquare size={32} className="mx-auto mb-2 opacity-50" />
                  Пока нет переписок
                </div>
              )}
              {conversations.map(c => (
                <button
                  key={c.contact_id}
                  onClick={() => selectConversation(c.contact_id)}
                  className={`w-full text-left p-4 border-b border-white/[0.06] hover:bg-white/5 transition-colors ${
                    selected === c.contact_id ? 'bg-emerald-500/10 border-l-2 border-l-emerald-500'
                    : c.link_sent ? 'bg-green-500/5 border-l-2 border-l-green-500/50'
                    : ''
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm truncate">
                      {displayName(c)}
                      {c.link_sent && <span className="ml-2 text-[10px] text-green-400">✓ ссылка</span>}
                    </span>
                    <span className="text-xs text-white/30">
                      {c.last_message_at ? new Date(c.last_message_at).toLocaleDateString('ru') : ''}
                    </span>
                  </div>
                  <p className="text-xs text-white/40 truncate">{c.last_message}</p>
                </button>
              ))}
            </div>
            <div className="p-3 border-t border-white/[0.06] text-xs text-white/30">
              Всего: {total}
            </div>
          </div>

          {/* Right panel — messages */}
          <div className={`flex-1 flex flex-col ${!selected ? 'hidden md:flex' : 'flex'}`}>
            {!selected ? (
              <div className="flex-1 flex items-center justify-center text-white/30 text-sm">
                Выберите переписку
              </div>
            ) : (
              <>
              <div className="flex items-center justify-between p-3 border-b border-white/[0.06]">
                <button onClick={() => setSelected(null)} className="md:hidden flex items-center gap-1 text-sm text-white/50 hover:text-white">
                  <ArrowLeft size={16} />
                  Назад
                </button>
                <button
                  onClick={exportConversation}
                  className="flex items-center gap-1.5 text-xs text-white/40 hover:text-emerald-400 transition-colors"
                >
                  <Download size={14} />
                  Скачать переписку
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-3">
                {messages.map(m => (
                  <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-start' : 'justify-end'}`}>
                    <div className={`max-w-[70%] rounded-2xl px-4 py-2.5 text-sm ${
                      m.role === 'user'
                        ? 'bg-white/[0.05] text-white/80 rounded-tl-md border border-white/[0.04]'
                        : 'bg-gradient-to-r from-emerald-500/20 to-emerald-600/20 text-white/90 rounded-tr-md border border-emerald-500/10'
                    }`}>
                      <p>{m.content}</p>
                      <div className="text-[10px] text-white/30 mt-1">
                        {new Date(m.created_at).toLocaleString('ru')}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
