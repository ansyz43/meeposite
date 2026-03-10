import { useEffect, useState, useRef, useCallback } from 'react'
import api from '../api'
import { useAuth } from '../hooks/useAuth'
import { Copy, Check, Link, Users, TrendingUp, Wallet, Clock, ChevronDown, ChevronRight } from 'lucide-react'

// --- SVG Visual Tree ---

const NODE_W = 140
const NODE_H = 56
const H_GAP = 24
const V_GAP = 70
const TRUNK_H = 40

function layoutTree(nodes, startX = 0, depth = 0) {
  const laid = []
  let x = startX
  for (const node of nodes) {
    const children = node.children && node.children.length > 0 ? node.children : []
    const childLayouts = layoutTree(children, x, depth + 1)
    const childWidth = childLayouts.reduce((s, c) => Math.max(s, c.maxX), x) 
    const subtreeWidth = children.length > 0
      ? childWidth - x
      : NODE_W
    const nodeX = x + subtreeWidth / 2 - NODE_W / 2
    const nodeY = TRUNK_H + depth * (NODE_H + V_GAP)
    laid.push({
      ...node,
      x: nodeX,
      y: nodeY,
      depth,
      childLayouts,
      maxX: x + subtreeWidth,
    })
    x = x + subtreeWidth + H_GAP
  }
  return laid
}

function getMaxExtents(nodes) {
  let maxX = 0, maxY = 0
  for (const n of nodes) {
    maxX = Math.max(maxX, n.x + NODE_W)
    maxY = Math.max(maxY, n.y + NODE_H)
    if (n.childLayouts.length > 0) {
      const { mx, my } = n.childLayouts.reduce(
        (acc, c) => {
          const ce = getMaxExtents([c])
          return { mx: Math.max(acc.mx, ce.maxX), my: Math.max(acc.my, ce.maxY) }
        },
        { mx: 0, my: 0 }
      )
      maxX = Math.max(maxX, mx)
      maxY = Math.max(maxY, my)
    }
  }
  return { maxX, maxY }
}

function SvgBranch({ x1, y1, x2, y2, delay, isActive }) {
  const midY = (y1 + y2) / 2
  const color = isActive ? '#34d399' : '#374151'
  const glow = isActive ? '#34d39940' : 'none'
  return (
    <path
      d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
      fill="none"
      stroke={color}
      strokeWidth={isActive ? 2.5 : 1.5}
      strokeLinecap="round"
      className="tree-branch"
      style={{
        animationDelay: `${delay}ms`,
        filter: isActive ? `drop-shadow(0 0 4px ${glow})` : 'none',
      }}
    />
  )
}

function SvgNode({ node, delay, onHover, hoveredId }) {
  const isActive = node.total_spent > 0
  const isHovered = hoveredId === node.id
  return (
    <g
      className="tree-node-g"
      style={{ animationDelay: `${delay}ms` }}
      onMouseEnter={() => onHover(node.id)}
      onMouseLeave={() => onHover(null)}
    >
      {/* Node bg */}
      <rect
        x={node.x}
        y={node.y}
        width={NODE_W}
        height={NODE_H}
        rx={12}
        fill={isHovered ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.04)'}
        stroke={isActive ? 'rgba(52,211,153,0.3)' : 'rgba(255,255,255,0.08)'}
        strokeWidth={isHovered ? 1.5 : 1}
        className="transition-all duration-200"
      />
      {/* Status dot */}
      <circle
        cx={node.x + 16}
        cy={node.y + NODE_H / 2}
        r={4}
        fill={isActive ? '#34d399' : '#374151'}
      >
        {isActive && (
          <animate attributeName="r" values="4;5;4" dur="2s" repeatCount="indefinite" />
        )}
      </circle>
      {/* Name */}
      <text
        x={node.x + 28}
        y={node.y + 22}
        fill="rgba(255,255,255,0.85)"
        fontSize="12"
        fontWeight="500"
        fontFamily="Inter, system-ui, sans-serif"
      >
        {node.name.length > 12 ? node.name.slice(0, 11) + '…' : node.name}
      </text>
      {/* Level badge */}
      <text
        x={node.x + 28}
        y={node.y + 40}
        fill="rgba(255,255,255,0.25)"
        fontSize="10"
        fontFamily="Inter, system-ui, sans-serif"
      >
        ур. {node.level}
        {node.total_spent > 0 ? ` · ${node.total_spent.toFixed(0)} кр.` : ''}
      </text>
      {/* Cashback earned indicator */}
      {node.cashback_earned > 0 && (
        <text
          x={node.x + NODE_W - 8}
          y={node.y + 22}
          fill="#34d399"
          fontSize="10"
          fontWeight="600"
          textAnchor="end"
          fontFamily="Inter, system-ui, sans-serif"
        >
          +{node.cashback_earned.toFixed(1)}
        </text>
      )}
    </g>
  )
}

function renderNodes(nodes, delay = 0, lines = [], svgNodes = [], onHover, hoveredId) {
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i]
    const d = delay + i * 150
    svgNodes.push(
      <SvgNode key={`n-${n.id}`} node={n} delay={d} onHover={onHover} hoveredId={hoveredId} />
    )
    // Draw branches to children
    for (let j = 0; j < n.childLayouts.length; j++) {
      const child = n.childLayouts[j]
      const isActive = child.total_spent > 0
      lines.push(
        <SvgBranch
          key={`b-${n.id}-${child.id}`}
          x1={n.x + NODE_W / 2}
          y1={n.y + NODE_H}
          x2={child.x + NODE_W / 2}
          y2={child.y}
          delay={d + 100 + j * 80}
          isActive={isActive}
        />
      )
      renderNodes([child], d + 200, lines, svgNodes, onHover, hoveredId)
    }
  }
}

function VisualTree({ tree, userName }) {
  const [hoveredId, setHoveredId] = useState(null)
  const containerRef = useRef(null)

  // Build root node representing the current user
  const rootNode = {
    id: 'root',
    name: userName || 'Вы',
    email: '',
    level: 0,
    total_spent: 1, // always active
    cashback_earned: 0,
    children: tree,
  }

  const layout = layoutTree([rootNode])
  const { maxX, maxY } = getMaxExtents(layout)
  const svgW = maxX + 40
  const svgH = maxY + 40

  const lines = []
  const svgNodes = []
  renderNodes(layout, 0, lines, svgNodes, setHoveredId, hoveredId)

  // Tooltip
  const hovered = hoveredId ? findNode(tree, hoveredId) : null

  return (
    <div ref={containerRef} className="relative overflow-x-auto">
      <svg
        width={Math.max(svgW, 300)}
        height={svgH}
        viewBox={`0 0 ${Math.max(svgW, 300)} ${svgH}`}
        className="mx-auto"
      >
        {/* Background glow */}
        <defs>
          <radialGradient id="treeGlow">
            <stop offset="0%" stopColor="rgba(99,102,241,0.08)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
        </defs>
        <rect x="0" y="0" width="100%" height="100%" fill="url(#treeGlow)" rx="16" />

        {/* Branches first (behind nodes) */}
        {lines}
        {/* Nodes */}
        {svgNodes}
      </svg>

      {/* Tooltip */}
      {hovered && (
        <div className="absolute top-2 right-2 bg-dark-800/95 border border-white/10 rounded-xl p-3 text-xs backdrop-blur-sm z-10 min-w-[160px]">
          <div className="font-medium text-white/90 mb-1">{hovered.name}</div>
          <div className="text-white/30 mb-2">{hovered.email}</div>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-white/40">Уровень</span>
              <span className="text-white/70">{hovered.level}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/40">Потратил</span>
              <span className="text-accent-400">{(hovered.total_spent || 0).toFixed(1)} кр.</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/40">Ваш доход</span>
              <span className="text-green-400">+{(hovered.cashback_earned || 0).toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/40">Дата</span>
              <span className="text-white/50">{new Date(hovered.joined_at).toLocaleDateString('ru-RU')}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function findNode(nodes, id) {
  for (const n of nodes) {
    if (n.id === id) return n
    if (n.children) {
      const found = findNode(n.children, id)
      if (found) return found
    }
  }
  return null
}

function ReferralTree({ tree, userName }) {
  if (!tree || tree.length === 0) {
    return (
      <div className="glass-card p-8 text-center">
        <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Users size={28} className="text-white/20" />
        </div>
        <p className="text-white/40 mb-2">Пока нет рефералов</p>
        <p className="text-sm text-white/20">Отправьте вашу реферальную ссылку друзьям и партнёрам</p>
      </div>
    )
  }

  return (
    <div className="glass-card p-5 overflow-hidden">
      <h2 className="font-semibold mb-4 flex items-center gap-2">
        <Users size={18} className="text-accent-400" />
        Ваше дерево
      </h2>
      <VisualTree tree={tree} userName={userName} />
    </div>
  )
}

// --- Main Page ---

export default function PartnerPage() {
  const { user } = useAuth()
  const [partner, setPartner] = useState(null)
  const [sessions, setSessions] = useState([])
  const [tree, setTree] = useState([])
  const [cashback, setCashback] = useState([])
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [refCopied, setRefCopied] = useState(false)
  const [sellerLink, setSellerLink] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [tab, setTab] = useState(user?.has_bot ? 'tree' : 'sessions') // 'tree' | 'cashback' | 'sessions'

  useEffect(() => { loadData() }, [])

  async function loadData() {
    try {
      const requests = [
        api.get('/api/referral/partner'),
        api.get('/api/referral/sessions'),
      ]
      if (user?.has_bot) {
        requests.push(api.get('/api/referral/my-tree'))
        requests.push(api.get('/api/referral/my-cashback'))
      }
      const results = await Promise.allSettled(requests)
      const partnerData = results[0]?.status === 'fulfilled' ? results[0].value.data : null
      const sessionsData = results[1]?.status === 'fulfilled' ? results[1].value.data : []
      const treeData = results[2]?.status === 'fulfilled' ? results[2].value.data : []
      const cashbackData = results[3]?.status === 'fulfilled' ? results[3].value.data : []
      setPartner(partnerData)
      setSessions(Array.isArray(sessionsData) ? sessionsData : [])
      setTree(Array.isArray(treeData) ? treeData : [])
      setCashback(Array.isArray(cashbackData) ? cashbackData : [])
      if (partnerData) {
        setSellerLink(partnerData.seller_link || '')
      }
    } catch { /* ignore */ }
    setLoading(false)
  }

  function copyRefLink() {
    if (user?.ref_link) {
      navigator.clipboard.writeText(user.ref_link)
      setRefCopied(true)
      setTimeout(() => setRefCopied(false), 2000)
    }
  }

  function copyBotRefLink() {
    if (partner?.ref_link) {
      navigator.clipboard.writeText(partner.ref_link)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  async function saveSellerLink(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const { data } = await api.put('/api/referral/partner', { seller_link: sellerLink })
      setPartner(data)
      setSuccess('Ссылка обновлена!')
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка')
    }
    setSaving(false)
  }

  useEffect(() => {
    if (success) { const t = setTimeout(() => setSuccess(''), 3000); return () => clearTimeout(t) }
  }, [success])

  if (loading) return <div className="text-white/50">Загрузка...</div>

  // Count totals
  const totalReferrals = countNodes(tree)
  const totalCashback = user?.cashback_balance || 0
  const monthCashback = cashback
    .filter(tx => {
      const d = new Date(tx.created_at)
      const now = new Date()
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
    })
    .reduce((sum, tx) => sum + tx.amount, 0)

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Партнёрство</h1>

      {error && <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-500/10 border border-green-500/30 rounded-xl px-4 py-3 text-green-400 text-sm mb-4">{success}</div>}

      {/* Stats cards — only for bot owners */}
      {user?.has_bot && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="glass-card p-5 text-center">
            <Wallet size={22} className="text-green-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-green-400">{totalCashback.toFixed(2)}</div>
            <div className="text-xs text-white/40 mt-1">Баланс кэшбека</div>
          </div>
          <div className="glass-card p-5 text-center">
            <Users size={22} className="text-accent-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-accent-400">{totalReferrals}</div>
            <div className="text-xs text-white/40 mt-1">В команде</div>
          </div>
          <div className="glass-card p-5 text-center">
            <TrendingUp size={22} className="text-yellow-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-yellow-400">{monthCashback.toFixed(2)}</div>
            <div className="text-xs text-white/40 mt-1">Доход за месяц</div>
          </div>
        </div>
      )}

      {/* Referral link (for inviting to platform) — only for bot owners */}
      {user?.has_bot && user?.ref_link && (
        <div className="glass-card p-4 mb-4">
          <div className="text-xs text-white/40 mb-2">Ваша ссылка для приглашения на платформу</div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <Link size={16} className="text-green-400 shrink-0" />
              <span className="text-white/70 text-sm truncate">{user.ref_link}</span>
            </div>
            <button onClick={copyRefLink} className="flex items-center gap-2 text-sm text-green-400 hover:text-green-300 shrink-0 ml-3">
              {refCopied ? <Check size={16} /> : <Copy size={16} />}
              {refCopied ? 'Скопировано' : 'Скопировать'}
            </button>
          </div>
        </div>
      )}

      {/* Bot partner section */}
      {partner && (
        <div className="glass-card p-4 mb-6">
          <div className="text-xs text-white/40 mb-2">Реферальная ссылка бота @{partner.bot_username} (кредитов: {partner.credits})</div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <Link size={16} className="text-accent-400 shrink-0" />
              <span className="text-white/70 text-sm truncate">{partner.ref_link}</span>
            </div>
            <button onClick={copyBotRefLink} className="flex items-center gap-2 text-sm text-accent-400 hover:text-accent-300 shrink-0 ml-3">
              {copied ? <Check size={16} /> : <Copy size={16} />}
              {copied ? 'Скопировано' : 'Скопировать'}
            </button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-dark-700/50 rounded-xl p-1">
        {[
          ...(user?.has_bot ? [
            { key: 'tree', label: 'Дерево', icon: Users },
            { key: 'cashback', label: 'Кэшбек', icon: Wallet },
          ] : []),
          ...(partner ? [{ key: 'sessions', label: 'Сессии', icon: Clock }] : []),
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm flex-1 justify-center transition-colors ${
              tab === t.key ? 'bg-dark-600 text-white' : 'text-white/40 hover:text-white/60'
            }`}
          >
            <t.icon size={14} /> {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {user?.has_bot && tab === 'tree' && <ReferralTree tree={tree} userName={user?.name} />}

      {user?.has_bot && tab === 'cashback' && (
        <div className="glass-card p-5">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <Wallet size={18} className="text-green-400" />
            История кэшбека
          </h2>
          {cashback.length === 0 ? (
            <p className="text-white/40 text-sm">Пока нет начислений</p>
          ) : (
            <div className="space-y-2">
              {cashback.map(tx => (
                <div key={tx.id} className="flex items-center justify-between py-2.5 border-b border-white/5 last:border-0">
                  <div>
                    <div className="text-sm text-white/80">{tx.from_user_name}</div>
                    <div className="text-xs text-white/30">
                      Уровень {tx.level} · {tx.source_type === 'credits' ? 'Кредиты' : 'Подписка'} · {tx.source_amount.toFixed(1)} кр.
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-green-400">+{tx.amount.toFixed(2)}</div>
                    <div className="text-xs text-white/20">
                      {new Date(tx.created_at).toLocaleDateString('ru-RU')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'sessions' && partner && (
        <div className="glass-card p-5">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <Clock size={18} /> Сессии клиентов ({sessions.length})
          </h2>
          {sessions.length === 0 ? (
            <p className="text-white/40 text-sm">Пока нет клиентов</p>
          ) : (
            <div className="space-y-2">
              {sessions.map(s => (
                <div key={s.id} className="flex items-center justify-between py-2.5 border-b border-white/5 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${s.is_active ? 'bg-green-400' : 'bg-white/20'}`} />
                    <div>
                      <div className="text-sm font-medium">
                        {s.first_name || 'Пользователь'}{' '}
                        {s.telegram_username && <span className="text-white/40">@{s.telegram_username}</span>}
                      </div>
                      <div className="text-xs text-white/30">
                        до {new Date(s.expires_at).toLocaleString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${s.is_active ? 'bg-green-500/10 text-green-400' : 'bg-white/5 text-white/30'}`}>
                    {s.is_active ? 'Активна' : 'Завершена'}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Seller link form */}
          <form onSubmit={saveSellerLink} className="mt-6 pt-4 border-t border-white/10 space-y-3">
            <h3 className="text-sm font-medium text-white/60">Ваша ссылка продавца</h3>
            <div className="flex gap-2">
              <input
                type="url"
                value={sellerLink}
                onChange={e => setSellerLink(e.target.value)}
                className="input-field flex-1"
                placeholder="https://your-seller-link.com"
                required
              />
              <button type="submit" disabled={saving} className="btn-primary px-4 disabled:opacity-50">
                {saving ? '...' : 'Сохранить'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* No partner — show catalog link */}
      {!partner && (
        <div className="glass-card p-6 text-center mt-6">
          <p className="text-white/50 mb-3">Хотите также зарабатывать с ботом?</p>
          <a href="/dashboard/catalog" className="btn-primary inline-flex items-center gap-2 text-sm">
            Стать партнёром бота
          </a>
        </div>
      )}
    </div>
  )
}

function countNodes(nodes) {
  let count = 0
  for (const n of nodes) {
    count += 1
    if (n.children) count += countNodes(n.children)
  }
  return count
}
