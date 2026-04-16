import { useState, useEffect, useCallback } from 'react'
import { FileText, Plus, Trash2, RefreshCw, Sparkles, Calendar, Clock, Hash, ChevronDown, ChevronUp, Send, Instagram, Loader2, AlertCircle, Check, Eye, Heart, Wand2 } from 'lucide-react'
import api from '../api'

const PLATFORMS = [
  { value: 'instagram', label: 'Instagram', icon: Instagram },
  { value: 'telegram', label: 'Telegram', icon: Send },
]

const TONES = [
  { value: 'friendly', label: 'Дружелюбный' },
  { value: 'professional', label: 'Профессиональный' },
  { value: 'expert', label: 'Экспертный' },
  { value: 'casual', label: 'Неформальный' },
  { value: 'motivational', label: 'Мотивирующий' },
]

export default function ContentPlanPage() {
  const [tab, setTab] = useState('profile')  // profile | competitors | plans
  const [profile, setProfile] = useState(null)
  const [plans, setPlans] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [profRes, plansRes] = await Promise.all([
        api.get('/api/content/profile'),
        api.get('/api/content/plans'),
      ])
      setProfile(profRes.data)
      setPlans(plansRes.data || [])
    } catch (e) {
      setError('Ошибка загрузки данных')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
      </div>
    )
  }

  const tabs = [
    { id: 'profile', label: 'Профиль', icon: FileText },
    { id: 'competitors', label: 'Конкуренты', icon: Eye, disabled: !profile },
    { id: 'plans', label: 'Контент-планы', icon: Calendar, disabled: !profile },
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-white">Контент-план</h1>
        <p className="text-white/40 text-sm mt-1">AI-генерация контента на основе анализа конкурентов</p>
      </div>

      {error && (
        <div className="glass-card p-3 border border-red-500/20 flex items-center gap-2 text-red-400 text-sm">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-white/[0.03] rounded-xl p-1">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => !t.disabled && setTab(t.id)}
            disabled={t.disabled}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
              tab === t.id
                ? 'bg-emerald-500/15 text-emerald-400 shadow-[inset_0_0_0_1px_rgba(16,185,129,0.2)]'
                : t.disabled
                  ? 'text-white/20 cursor-not-allowed'
                  : 'text-white/50 hover:text-white/70 hover:bg-white/[0.04]'
            }`}
          >
            <t.icon size={16} />
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'profile' && <ProfileTab profile={profile} onUpdate={loadData} />}
      {tab === 'competitors' && profile && <CompetitorsTab profile={profile} onUpdate={loadData} />}
      {tab === 'plans' && profile && <PlansTab plans={plans} onUpdate={loadData} />}
    </div>
  )
}


// ── Profile Tab ──────────────────────────────────────────────

function ProfileTab({ profile, onUpdate }) {
  const [form, setForm] = useState({
    niche: profile?.niche || '',
    platforms: profile?.platforms || ['instagram', 'telegram'],
    tone: profile?.tone || 'friendly',
    target_audience: profile?.target_audience || '',
    topics: profile?.topics?.join(', ') || '',
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  // Auto-detect
  const [detectPlatform, setDetectPlatform] = useState('telegram')
  const [detectUsername, setDetectUsername] = useState('')
  const [detecting, setDetecting] = useState(false)
  const [detectError, setDetectError] = useState('')
  const [detectSuccess, setDetectSuccess] = useState(false)

  const handleAutoDetect = async () => {
    if (!detectUsername.trim()) return
    setDetecting(true)
    setDetectError('')
    setDetectSuccess(false)
    try {
      const { data } = await api.post('/api/content/profile/auto-detect', {
        platform: detectPlatform,
        username: detectUsername.trim(),
      })
      setForm(f => ({
        ...f,
        niche: data.niche || f.niche,
        target_audience: data.target_audience || f.target_audience,
        tone: data.tone || f.tone,
        topics: Array.isArray(data.topics) ? data.topics.join(', ') : f.topics,
      }))
      setDetectSuccess(true)
      setTimeout(() => setDetectSuccess(false), 3000)
    } catch (e) {
      setDetectError(e.response?.data?.detail || 'Ошибка анализа')
    } finally {
      setDetecting(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.post('/api/content/profile', {
        ...form,
        topics: form.topics.split(',').map(t => t.trim()).filter(Boolean),
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
      onUpdate()
    } catch (e) {
      alert(e.response?.data?.detail || 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  const togglePlatform = (p) => {
    setForm(f => ({
      ...f,
      platforms: f.platforms.includes(p)
        ? f.platforms.filter(x => x !== p)
        : [...f.platforms, p],
    }))
  }

  return (
    <div className="space-y-5">
      {/* Auto-detect block */}
      <div className="glass-card p-5 border border-emerald-500/20">
        <div className="flex items-center gap-2 mb-3">
          <Wand2 size={18} className="text-emerald-400" />
          <h3 className="text-sm font-semibold text-white">Заполнить автоматически</h3>
        </div>
        <p className="text-xs text-white/40 mb-3">
          Укажите ваш Telegram-канал или Instagram — система проанализирует посты и заполнит профиль
        </p>
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="flex gap-1 bg-white/[0.04] rounded-lg p-0.5">
            {PLATFORMS.map(p => (
              <button key={p.value} onClick={() => setDetectPlatform(p.value)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-xs transition-all ${
                  detectPlatform === p.value
                    ? 'bg-emerald-500/15 text-emerald-400'
                    : 'text-white/40 hover:text-white/60'
                }`}>
                <p.icon size={14} /> {p.label}
              </button>
            ))}
          </div>
          <input
            value={detectUsername}
            onChange={e => setDetectUsername(e.target.value)}
            placeholder={detectPlatform === 'telegram' ? '@username канала' : '@username в Instagram'}
            className="flex-1 bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-white text-sm placeholder-white/20 focus:border-emerald-500/40 focus:outline-none"
          />
          <button
            onClick={handleAutoDetect}
            disabled={detecting || !detectUsername.trim()}
            className="btn-primary flex items-center gap-2 text-sm px-4 py-2 disabled:opacity-50 whitespace-nowrap"
          >
            <span className="relative z-10 flex items-center gap-2">
              {detecting ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
              {detecting ? 'Анализ...' : 'Определить'}
            </span>
          </button>
        </div>
        {detectError && <p className="text-red-400 text-xs mt-2">{detectError}</p>}
        {detectSuccess && <p className="text-emerald-400 text-xs mt-2">Профиль заполнен! Проверьте и сохраните.</p>}
      </div>

    <div className="glass-card p-6 space-y-5">
      <h2 className="text-lg font-semibold text-white">Профиль для контента</h2>

      <div>
        <label className="block text-sm text-white/50 mb-1.5">Ниша</label>
        <input
          value={form.niche}
          onChange={e => setForm(f => ({ ...f, niche: e.target.value }))}
          placeholder="Например: wellness, фитнес, красота"
          className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2.5 text-white text-sm placeholder-white/20 focus:border-emerald-500/40 focus:outline-none"
        />
      </div>

      <div>
        <label className="block text-sm text-white/50 mb-1.5">Платформы</label>
        <div className="flex gap-2">
          {PLATFORMS.map(p => (
            <button
              key={p.value}
              onClick={() => togglePlatform(p.value)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all ${
                form.platforms.includes(p.value)
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'bg-white/[0.04] text-white/40 border border-white/[0.08] hover:border-white/20'
              }`}
            >
              <p.icon size={16} />
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm text-white/50 mb-1.5">Тон общения</label>
        <div className="flex flex-wrap gap-2">
          {TONES.map(t => (
            <button
              key={t.value}
              onClick={() => setForm(f => ({ ...f, tone: t.value }))}
              className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
                form.tone === t.value
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'bg-white/[0.04] text-white/40 border border-white/[0.08] hover:border-white/20'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm text-white/50 mb-1.5">Целевая аудитория</label>
        <textarea
          value={form.target_audience}
          onChange={e => setForm(f => ({ ...f, target_audience: e.target.value }))}
          placeholder="Опишите вашу ЦА: возраст, интересы, боли..."
          rows={3}
          className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2.5 text-white text-sm placeholder-white/20 focus:border-emerald-500/40 focus:outline-none resize-none"
        />
      </div>

      <div>
        <label className="block text-sm text-white/50 mb-1.5">Темы (через запятую)</label>
        <input
          value={form.topics}
          onChange={e => setForm(f => ({ ...f, topics: e.target.value }))}
          placeholder="здоровье, БАДы, спорт, питание"
          className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2.5 text-white text-sm placeholder-white/20 focus:border-emerald-500/40 focus:outline-none"
        />
      </div>

      <button
        onClick={handleSave}
        disabled={saving || !form.niche}
        className="btn-primary flex items-center gap-2"
      >
        {saving ? <Loader2 size={16} className="animate-spin" /> : saved ? <Check size={16} /> : null}
        {saved ? 'Сохранено!' : 'Сохранить профиль'}
      </button>
    </div>
    </div>
  )
}


// ── Competitors Tab ──────────────────────────────────────────

function CompetitorsTab({ profile, onUpdate }) {
  const [adding, setAdding] = useState(false)
  const [form, setForm] = useState({ platform: 'telegram', channel_username: '' })
  const [submitting, setSubmitting] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [posts, setPosts] = useState({})
  const [loadingPosts, setLoadingPosts] = useState(null)

  const handleAdd = async () => {
    if (!form.channel_username.trim()) return
    setSubmitting(true)
    try {
      await api.post('/api/content/competitors', form)
      setForm({ platform: 'telegram', channel_username: '' })
      setAdding(false)
      onUpdate()
    } catch (e) {
      alert(e.response?.data?.detail || 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Удалить конкурента?')) return
    try {
      await api.delete(`/api/content/competitors/${id}`)
      onUpdate()
    } catch (e) {
      alert('Ошибка удаления')
    }
  }

  const handleParse = async (id) => {
    try {
      await api.post(`/api/content/competitors/${id}/parse`)
      alert('Парсинг запущен. Обновите через минуту.')
    } catch (e) {
      alert(e.response?.data?.detail || 'Ошибка')
    }
  }

  const loadPosts = async (id) => {
    if (expandedId === id) {
      setExpandedId(null)
      return
    }
    setLoadingPosts(id)
    try {
      const res = await api.get(`/api/content/competitors/${id}/posts`)
      setPosts(p => ({ ...p, [id]: res.data }))
      setExpandedId(id)
    } catch {
      alert('Ошибка загрузки постов')
    } finally {
      setLoadingPosts(null)
    }
  }

  const competitors = profile?.competitors || []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Конкуренты ({competitors.length}/10)</h2>
        <button onClick={() => setAdding(!adding)} className="btn-primary text-sm flex items-center gap-1.5">
          <Plus size={15} /> Добавить
        </button>
      </div>

      {adding && (
        <div className="glass-card p-4 space-y-3">
          <div className="flex gap-2">
            {PLATFORMS.map(p => (
              <button
                key={p.value}
                onClick={() => setForm(f => ({ ...f, platform: p.value }))}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
                  form.platform === p.value
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                    : 'bg-white/[0.04] text-white/40 border border-white/[0.08]'
                }`}
              >
                <p.icon size={14} /> {p.label}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              value={form.channel_username}
              onChange={e => setForm(f => ({ ...f, channel_username: e.target.value }))}
              placeholder={form.platform === 'telegram' ? '@channel_name' : 'username'}
              className="flex-1 bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-white text-sm placeholder-white/20 focus:border-emerald-500/40 focus:outline-none"
            />
            <button onClick={handleAdd} disabled={submitting} className="btn-primary text-sm px-4">
              {submitting ? <Loader2 size={14} className="animate-spin" /> : 'Добавить'}
            </button>
          </div>
        </div>
      )}

      {competitors.length === 0 ? (
        <div className="glass-card p-8 text-center text-white/30 text-sm">
          Добавьте конкурентов для анализа их контента
        </div>
      ) : (
        <div className="space-y-2">
          {competitors.map(comp => (
            <div key={comp.id} className="glass-card overflow-hidden">
              <div className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    comp.platform === 'telegram' ? 'bg-blue-500/15 text-blue-400' : 'bg-pink-500/15 text-pink-400'
                  }`}>
                    {comp.platform === 'telegram' ? <Send size={15} /> : <Instagram size={15} />}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-white truncate">@{comp.channel_username}</div>
                    <div className="text-xs text-white/30">
                      {comp.channel_title || comp.platform}
                      {comp.post_count > 0 && ` · ${comp.post_count} постов`}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <button onClick={() => loadPosts(comp.id)} className="p-2 text-white/30 hover:text-white/60 transition-colors" title="Посмотреть посты">
                    {loadingPosts === comp.id ? <Loader2 size={15} className="animate-spin" /> : expandedId === comp.id ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                  </button>
                  <button onClick={() => handleParse(comp.id)} className="p-2 text-white/30 hover:text-emerald-400 transition-colors" title="Обновить">
                    <RefreshCw size={15} />
                  </button>
                  <button onClick={() => handleDelete(comp.id)} className="p-2 text-white/30 hover:text-red-400 transition-colors" title="Удалить">
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>

              {expandedId === comp.id && posts[comp.id] && (
                <div className="border-t border-white/[0.06] max-h-80 overflow-y-auto">
                  {posts[comp.id].length === 0 ? (
                    <div className="p-4 text-center text-white/20 text-sm">Посты не загружены. Нажмите ↻ для парсинга.</div>
                  ) : posts[comp.id].map(post => (
                    <div key={post.id} className="p-3 border-b border-white/[0.04] last:border-0">
                      <p className="text-xs text-white/60 leading-relaxed">{post.text}</p>
                      <div className="flex gap-3 mt-1.5 text-[10px] text-white/25">
                        {post.views != null && <span className="flex items-center gap-1"><Eye size={10} /> {post.views}</span>}
                        {post.reactions != null && <span className="flex items-center gap-1"><Heart size={10} /> {post.reactions}</span>}
                        {post.posted_at && <span>{new Date(post.posted_at).toLocaleDateString()}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


// ── Plans Tab ────────────────────────────────────────────────

function PlansTab({ plans, onUpdate }) {
  const [generating, setGenerating] = useState(false)
  const [genForm, setGenForm] = useState({ platform: 'instagram', period_days: 7 })
  const [showGen, setShowGen] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [planDetail, setPlanDetail] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const res = await api.post('/api/content/plans/generate', genForm)
      setPlanDetail(res.data)
      setSelectedPlan(res.data.id)
      setShowGen(false)
      onUpdate()
    } catch (e) {
      alert(e.response?.data?.detail || 'Ошибка генерации')
    } finally {
      setGenerating(false)
    }
  }

  const loadDetail = async (id) => {
    if (selectedPlan === id && planDetail) {
      setSelectedPlan(null)
      setPlanDetail(null)
      return
    }
    setLoadingDetail(true)
    setSelectedPlan(id)
    try {
      const res = await api.get(`/api/content/plans/${id}`)
      setPlanDetail(res.data)
    } catch {
      alert('Ошибка загрузки')
    } finally {
      setLoadingDetail(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Удалить план?')) return
    try {
      await api.delete(`/api/content/plans/${id}`)
      if (selectedPlan === id) {
        setSelectedPlan(null)
        setPlanDetail(null)
      }
      onUpdate()
    } catch {
      alert('Ошибка удаления')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Контент-планы</h2>
        <button onClick={() => setShowGen(!showGen)} className="btn-primary text-sm flex items-center gap-1.5">
          <Sparkles size={15} /> Сгенерировать
        </button>
      </div>

      {showGen && (
        <div className="glass-card p-4 space-y-3">
          <div className="flex gap-2">
            {PLATFORMS.map(p => (
              <button
                key={p.value}
                onClick={() => setGenForm(f => ({ ...f, platform: p.value }))}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
                  genForm.platform === p.value
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                    : 'bg-white/[0.04] text-white/40 border border-white/[0.08]'
                }`}
              >
                <p.icon size={14} /> {p.label}
              </button>
            ))}
          </div>
          <div className="flex gap-2 items-center">
            <span className="text-sm text-white/50">Период:</span>
            {[7, 14, 30].map(d => (
              <button
                key={d}
                onClick={() => setGenForm(f => ({ ...f, period_days: d }))}
                className={`px-3 py-1.5 rounded-lg text-sm ${
                  genForm.period_days === d
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                    : 'bg-white/[0.04] text-white/40 border border-white/[0.08]'
                }`}
              >
                {d} дней
              </button>
            ))}
          </div>
          <button onClick={handleGenerate} disabled={generating} className="btn-primary flex items-center gap-2">
            {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            {generating ? 'Генерация...' : 'Создать контент-план'}
          </button>
          {generating && <p className="text-xs text-white/30">Это может занять 20-40 секунд...</p>}
        </div>
      )}

      {plans.length === 0 && !showGen ? (
        <div className="glass-card p-8 text-center text-white/30 text-sm">
          У вас пока нет контент-планов. Нажмите «Сгенерировать» для создания.
        </div>
      ) : (
        <div className="space-y-2">
          {plans.map(plan => (
            <div key={plan.id}>
              <div className="glass-card p-4 flex items-center justify-between cursor-pointer hover:bg-white/[0.02] transition-colors" onClick={() => loadDetail(plan.id)}>
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    plan.platform === 'telegram' ? 'bg-blue-500/15 text-blue-400' : 'bg-pink-500/15 text-pink-400'
                  }`}>
                    {plan.platform === 'telegram' ? <Send size={15} /> : <Instagram size={15} />}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{plan.title}</div>
                    <div className="text-xs text-white/30">
                      {new Date(plan.created_at).toLocaleDateString()} · {plan.item_count} постов ·{' '}
                      <span className={plan.status === 'ready' ? 'text-emerald-400' : plan.status === 'error' ? 'text-red-400' : 'text-yellow-400'}>
                        {plan.status === 'ready' ? 'Готов' : plan.status === 'error' ? 'Ошибка' : 'Генерация...'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <button onClick={(e) => { e.stopPropagation(); handleDelete(plan.id) }} className="p-2 text-white/30 hover:text-red-400 transition-colors">
                    <Trash2 size={15} />
                  </button>
                  {selectedPlan === plan.id ? <ChevronUp size={15} className="text-white/30" /> : <ChevronDown size={15} className="text-white/30" />}
                </div>
              </div>

              {selectedPlan === plan.id && planDetail && (
                <PlanDetail plan={planDetail} loading={loadingDetail} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


// ── Plan Detail ──────────────────────────────────────────────

function PlanDetail({ plan, loading }) {
  const [editingId, setEditingId] = useState(null)
  const [editText, setEditText] = useState('')
  const [saving, setSaving] = useState(false)

  if (loading) {
    return <div className="py-4 text-center"><Loader2 className="w-5 h-5 text-emerald-400 animate-spin mx-auto" /></div>
  }

  if (plan.status === 'error') {
    return (
      <div className="glass-card mt-1 p-4 text-red-400 text-sm flex items-center gap-2">
        <AlertCircle size={16} /> {plan.error_message || 'Ошибка генерации'}
      </div>
    )
  }

  const handleSave = async (itemId) => {
    setSaving(true)
    try {
      await api.put(`/api/content/plans/${plan.id}/items/${itemId}`, { text: editText })
      plan.items = plan.items.map(i => i.id === itemId ? { ...i, text: editText, is_edited: true } : i)
      setEditingId(null)
    } catch {
      alert('Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  const postTypeColors = {
    'пост': 'bg-blue-500/15 text-blue-400',
    'сторис': 'bg-purple-500/15 text-purple-400',
    'рилс': 'bg-pink-500/15 text-pink-400',
    'карусель': 'bg-amber-500/15 text-amber-400',
  }

  return (
    <div className="mt-1 space-y-1.5">
      {plan.items?.map(item => (
        <div key={item.id} className="glass-card p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-white/25">День {item.day_number}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${postTypeColors[item.post_type] || 'bg-white/10 text-white/50'}`}>
                {item.post_type}
              </span>
              {item.is_edited && <span className="text-[10px] text-emerald-400/50">изменено</span>}
            </div>
            <div className="flex items-center gap-2 text-xs text-white/25">
              {item.best_time && <span className="flex items-center gap-1"><Clock size={10} /> {item.best_time}</span>}
            </div>
          </div>

          <div className="text-xs font-medium text-white/70 mb-1.5">{item.topic}</div>

          {editingId === item.id ? (
            <div className="space-y-2">
              <textarea
                value={editText}
                onChange={e => setEditText(e.target.value)}
                rows={6}
                className="w-full bg-white/[0.04] border border-emerald-500/30 rounded-lg px-3 py-2 text-white text-xs focus:outline-none resize-none"
              />
              <div className="flex gap-2">
                <button onClick={() => handleSave(item.id)} disabled={saving} className="btn-primary text-xs px-3 py-1.5">
                  {saving ? <Loader2 size={12} className="animate-spin" /> : 'Сохранить'}
                </button>
                <button onClick={() => setEditingId(null)} className="text-xs text-white/30 hover:text-white/60">Отмена</button>
              </div>
            </div>
          ) : (
            <div
              onClick={() => { setEditingId(item.id); setEditText(item.text) }}
              className="text-xs text-white/50 leading-relaxed whitespace-pre-wrap cursor-pointer hover:bg-white/[0.02] rounded p-1 -m-1 transition-colors"
              title="Нажмите для редактирования"
            >
              {item.text}
            </div>
          )}

          {item.hashtags && (
            <div className="mt-2 flex items-center gap-1 text-[10px] text-emerald-400/40">
              <Hash size={10} /> {item.hashtags}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
