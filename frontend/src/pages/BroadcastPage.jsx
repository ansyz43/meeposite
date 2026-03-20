import { useEffect, useState, useRef } from 'react'
import api from '../api'
import { Send, Image, Clock, CheckCircle, AlertCircle, Megaphone } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import Loader from '../components/ui/Loader'
import Modal from '../components/ui/Modal'

export default function BroadcastPage() {
  const [broadcasts, setBroadcasts] = useState([])
  const [loading, setLoading] = useState(true)
  const [bcText, setBcText] = useState('')
  const [bcImage, setBcImage] = useState(null)
  const [bcSending, setBcSending] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showConfirm, setShowConfirm] = useState(false)
  const bcFileRef = useRef(null)

  useEffect(() => { loadBroadcasts() }, [])

  async function loadBroadcasts() {
    try {
      const { data } = await api.get('/api/bot/broadcasts')
      setBroadcasts(data)
    } catch { /* ignore */ }
    setLoading(false)
  }

  async function sendBroadcast() {
    setShowConfirm(false)
    setBcSending(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('message_text', bcText.trim())
      if (bcImage) formData.append('image', bcImage)
      await api.post('/api/bot/broadcast', formData)
      setSuccess('Рассылка запущена!')
      setBcText('')
      setBcImage(null)
      if (bcFileRef.current) bcFileRef.current.value = ''
      loadBroadcasts()
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : 'Ошибка отправки рассылки')
    }
    setBcSending(false)
  }

  useEffect(() => {
    if (success) { const t = setTimeout(() => setSuccess(''), 3000); return () => clearTimeout(t) }
  }, [success])

  // Auto-refresh while any broadcast is sending
  useEffect(() => {
    if (!broadcasts.some(bc => bc.status === 'sending' || bc.status === 'pending')) return
    const t = setInterval(loadBroadcasts, 3000)
    return () => clearInterval(t)
  }, [broadcasts])

  if (loading) return <Loader />

  return (
    <div>
      <PageHeader title="Рассылка" subtitle="Отправьте сообщение всем контактам бота" />

      {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}

      {/* Create broadcast */}
      <div className="glass-card p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Send size={20} className="text-emerald-400" />
          <h2 className="font-semibold">Новая рассылка</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-white/60 mb-1.5">Текст сообщения</label>
            <textarea value={bcText} onChange={e => setBcText(e.target.value)}
              className="input-field min-h-[140px] resize-y" placeholder="Текст рассылки для всех контактов..." maxLength={4096} />
            <p className="text-xs text-white/30 mt-1">Поддерживается HTML: &lt;b&gt;жирный&lt;/b&gt;, &lt;i&gt;курсив&lt;/i&gt;, &lt;a href="..."&gt;ссылка&lt;/a&gt;</p>
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-1.5">Картинка (не обязательно)</label>
            <div className="flex items-center gap-3">
              <button type="button" onClick={() => bcFileRef.current?.click()}
                className="flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.08] text-white/70 hover:text-white transition-colors">
                <Image size={16} /> {bcImage ? bcImage.name : 'Выбрать файл'}
              </button>
              {bcImage && (
                <button onClick={() => { setBcImage(null); if (bcFileRef.current) bcFileRef.current.value = '' }}
                  className="text-red-400 hover:text-red-300 text-xs">✕ Убрать</button>
              )}
            </div>
            <input ref={bcFileRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden"
              onChange={e => setBcImage(e.target.files?.[0] || null)} />
          </div>
          <div className="pt-2">
            <button onClick={() => setShowConfirm(true)} disabled={bcSending || !bcText.trim()}
              className="btn-primary flex items-center gap-2 disabled:opacity-50">
              <span className="relative z-10 flex items-center gap-2">
                <Send size={18} /> {bcSending ? 'Отправка...' : 'Отправить всем'}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Broadcast history */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Megaphone size={20} className="text-emerald-400" />
          <h2 className="font-display font-semibold">История рассылок</h2>
        </div>

        {broadcasts.length === 0 ? (
          <p className="text-white/30 text-sm">Рассылок пока не было</p>
        ) : (
          <div className="space-y-3">
            {broadcasts.map(bc => (
              <div key={bc.id} className="p-4 rounded-xl bg-white/5 border border-white/[0.06]">
                <div className="flex flex-col sm:flex-row sm:items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white/80 whitespace-pre-wrap break-words">{bc.message_text.length > 200 ? bc.message_text.substring(0, 200) + '...' : bc.message_text}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-white/30">
                      <span>{new Date(bc.created_at).toLocaleString('ru-RU')}</span>
                      {bc.image_url && <span>📷 с картинкой</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-sm shrink-0">
                    <div className="text-center">
                      <div className="text-green-400 font-medium">{bc.sent_count}</div>
                      <div className="text-[10px] text-white/30">отправлено</div>
                    </div>
                    {bc.failed_count > 0 && (
                      <div className="text-center">
                        <div className="text-red-400 font-medium">{bc.failed_count}</div>
                        <div className="text-[10px] text-white/30">ошибок</div>
                      </div>
                    )}
                    <div className="text-center">
                      <div className="text-white/50 font-medium">{bc.total_contacts}</div>
                      <div className="text-[10px] text-white/30">всего</div>
                    </div>
                    <div className="ml-1">
                      {bc.status === 'sending' && (
                        <span className="flex items-center gap-1 text-yellow-400 text-xs">
                          <Clock size={14} className="animate-spin" /> Отправка
                        </span>
                      )}
                      {bc.status === 'completed' && (
                        <span className="flex items-center gap-1 text-green-400 text-xs">
                          <CheckCircle size={14} /> Готово
                        </span>
                      )}
                      {bc.status === 'pending' && (
                        <span className="flex items-center gap-1 text-white/40 text-xs">
                          <Clock size={14} /> Ожидание
                        </span>
                      )}
                      {bc.status === 'failed' && (
                        <span className="flex items-center gap-1 text-red-400 text-xs">
                          <AlertCircle size={14} /> Ошибка
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Confirm Modal */}
      <Modal
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        title="Отправить рассылку?"
        actions={
          <>
            <button onClick={() => setShowConfirm(false)} className="btn-secondary !py-2 !px-5 text-sm">Отмена</button>
            <button onClick={sendBroadcast} className="btn-primary !py-2 !px-5 text-sm">
              <span className="relative z-10 flex items-center gap-2">
                <Send size={14} /> Отправить
              </span>
            </button>
          </>
        }
      >
        <div className="space-y-3">
          <p>Сообщение будет отправлено всем контактам бота.</p>
          <div className="bg-white/[0.04] rounded-xl p-3 text-white/70 text-sm max-h-32 overflow-y-auto whitespace-pre-wrap">
            {bcText.trim().substring(0, 300)}{bcText.trim().length > 300 ? '...' : ''}
          </div>
          {bcImage && <p className="text-xs text-white/40">📷 С картинкой: {bcImage.name}</p>}
        </div>
      </Modal>
    </div>
  )
}
