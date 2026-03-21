import { useEffect, useState, useRef } from 'react'
import api from '../api'
import { MessageSquare, Search, Download, ArrowLeft, ArrowDown, User } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Loader from '../components/ui/Loader'

function VkBadge() {
  return (
    <svg width={14} height={14} viewBox="0 0 24 24" fill="currentColor" className="text-blue-400 shrink-0">
      <path d="M12.785 16.241s.288-.032.436-.194c.136-.148.132-.427.132-.427s-.02-1.304.587-1.496c.598-.188 1.368 1.259 2.184 1.814.616.42 1.084.328 1.084.328l2.178-.03s1.14-.07.6-.964c-.044-.073-.316-.662-1.624-1.872-1.37-1.268-1.186-1.062.464-3.254.764-1.012 1.542-2.122 1.404-2.476-.132-.33-.944-.244-.944-.244l-2.45.016s-.182-.024-.316.056c-.132.078-.216.262-.216.262s-.388 1.032-.904 1.91c-1.092 1.862-1.528 1.96-1.708 1.846-.418-.268-.314-1.076-.314-1.65 0-1.792.272-2.54-.528-2.734-.266-.064-.462-.106-1.14-.112-.87-.01-1.606.002-2.024.206-.278.136-.492.438-.362.456.162.022.528.098.722.362.25.342.242 1.11.242 1.11s.144 2.11-.336 2.372c-.33.18-.782-.188-1.754-1.874-.498-.864-.874-1.818-.874-1.818s-.072-.178-.202-.274c-.156-.116-.376-.152-.376-.152l-2.328.016s-.35.01-.478.162c-.114.136-.01.416-.01.416s1.82 4.258 3.882 6.404c1.888 1.966 4.034 1.836 4.034 1.836h.972z"/>
    </svg>
  )
}

function TgBadge() {
  return (
    <svg width={14} height={14} viewBox="0 0 24 24" fill="currentColor" className="text-sky-400 shrink-0">
      <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
    </svg>
  )
}

const platformTabs = [
  { key: '', label: 'Все' },
  { key: 'telegram', label: 'Telegram', icon: <TgBadge /> },
  { key: 'vk', label: 'ВКонтакте', icon: <VkBadge /> },
]

export default function Conversations() {
  const [conversations, setConversations] = useState([])
  const [selected, setSelected] = useState(null)
  const [messages, setMessages] = useState([])
  const [search, setSearch] = useState('')
  const [platform, setPlatform] = useState('')
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const messagesEndRef = useRef(null)
  const chatRef = useRef(null)
  const [showScrollBtn, setShowScrollBtn] = useState(false)

  useEffect(() => { loadConversations() }, [search, platform])

  async function loadConversations() {
    setLoading(true)
    try {
      const params = { search, per_page: 100 }
      if (platform) params.platform = platform
      const { data } = await api.get('/api/conversations', { params })
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

      {/* Platform filter tabs */}
      <div className="flex gap-1 mb-4 p-1 bg-white/[0.03] rounded-xl w-fit border border-white/[0.06]">
        {platformTabs.map(t => (
          <button key={t.key} onClick={() => { setPlatform(t.key); setSelected(null) }}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
              platform === t.key
                ? 'bg-white/[0.1] text-white shadow-sm'
                : 'text-white/40 hover:text-white/60 hover:bg-white/[0.04]'
            }`}>
            {t.icon}{t.label}
          </button>
        ))}
      </div>

      <div className="glass-card overflow-hidden h-[calc(100vh-14rem)]">
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
                    <div className="w-9 h-9 rounded-xl bg-white/[0.06] flex items-center justify-center shrink-0 relative">
                      <User size={16} className="text-white/30" />
                      <span className="absolute -bottom-0.5 -right-0.5">
                        {c.platform === 'vk' ? <VkBadge /> : <TgBadge />}
                      </span>
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
