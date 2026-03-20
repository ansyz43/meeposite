import { useEffect, useState, useRef } from 'react'
import api from '../api'
import { MessageSquare, Search, Download, ArrowLeft, ArrowDown, User } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Loader from '../components/ui/Loader'

export default function Conversations() {
  const [conversations, setConversations] = useState([])
  const [selected, setSelected] = useState(null)
  const [messages, setMessages] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const messagesEndRef = useRef(null)
  const chatRef = useRef(null)
  const [showScrollBtn, setShowScrollBtn] = useState(false)

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
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
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

  function handleChatScroll() {
    if (!chatRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = chatRef.current
    setShowScrollBtn(scrollHeight - scrollTop - clientHeight > 100)
  }

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div>
      <PageHeader title="Переписки" subtitle={total > 0 ? `${total} диалогов` : undefined} />
      <div className="glass-card overflow-hidden h-[calc(100vh-12rem)]">
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
              {loading && <div className="p-6"><Loader /></div>}
              {!loading && conversations.length === 0 && (
                <div className="p-8 text-center">
                  <div className="w-12 h-12 rounded-2xl bg-white/[0.04] flex items-center justify-center mx-auto mb-3">
                    <MessageSquare size={24} className="text-white/20" />
                  </div>
                  <p className="text-white/30 text-sm">Пока нет переписок</p>
                </div>
              )}
              {conversations.map(c => (
                <button
                  key={c.contact_id}
                  onClick={() => selectConversation(c.contact_id)}
                  className={`w-full text-left p-4 border-b border-white/[0.04] hover:bg-white/[0.03] transition-all duration-200 ${
                    selected === c.contact_id ? 'bg-emerald-500/10 border-l-2 border-l-emerald-500'
                    : c.link_sent ? 'bg-green-500/[0.03] border-l-2 border-l-green-500/50'
                    : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-white/[0.06] flex items-center justify-center shrink-0">
                      <User size={16} className="text-white/30" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="font-medium text-sm truncate">
                          {displayName(c)}
                        </span>
                        <span className="text-[11px] text-white/25 shrink-0 ml-2">
                          {c.last_message_at ? new Date(c.last_message_at).toLocaleDateString('ru') : ''}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {c.link_sent && <span className="text-[10px] text-green-400 shrink-0">✓</span>}
                        <p className="text-xs text-white/35 truncate">{c.last_message}</p>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
            <div className="p-3 border-t border-white/[0.06] text-xs text-white/25 font-mono">
              Всего: {total}
            </div>
          </div>

          {/* Right panel — messages */}
          <div className={`flex-1 flex flex-col ${!selected ? 'hidden md:flex' : 'flex'}`}>
            {!selected ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6">
                <div className="w-16 h-16 rounded-2xl bg-white/[0.04] flex items-center justify-center mx-auto mb-4">
                  <MessageSquare size={28} className="text-white/15" />
                </div>
                <p className="text-white/30 text-sm">Выберите переписку из списка слева</p>
              </div>
            ) : (
              <>
              <div className="flex items-center justify-between p-3 border-b border-white/[0.06]">
                <button onClick={() => setSelected(null)} className="md:hidden flex items-center gap-1 text-sm text-white/50 hover:text-white transition-colors">
                  <ArrowLeft size={16} />
                  Назад
                </button>
                <div />
                <button
                  onClick={exportConversation}
                  className="flex items-center gap-1.5 text-xs text-white/40 hover:text-emerald-400 transition-colors"
                >
                  <Download size={14} />
                  Скачать
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-3 relative" ref={chatRef} onScroll={handleChatScroll}>
                {messages.map(m => (
                  <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-start' : 'justify-end'}`}>
                    <div className={`max-w-[70%] rounded-2xl px-4 py-2.5 text-sm ${
                      m.role === 'user'
                        ? 'bg-white/[0.05] text-white/80 rounded-tl-md border border-white/[0.04]'
                        : 'bg-gradient-to-r from-emerald-500/20 to-emerald-600/20 text-white/90 rounded-tr-md border border-emerald-500/10'
                    }`}>
                      <p className="whitespace-pre-wrap">{m.content}</p>
                      <div className="text-[10px] text-white/25 mt-1.5 text-right">
                        {new Date(m.created_at).toLocaleString('ru', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })}
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
              {showScrollBtn && (
                <button onClick={scrollToBottom}
                  className="absolute bottom-4 right-4 w-9 h-9 rounded-full bg-[#0C1219]/90 border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white hover:border-emerald-500/30 transition-all shadow-lg z-10">
                  <ArrowDown size={16} />
                </button>
              )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
