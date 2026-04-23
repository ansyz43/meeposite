import { useState, useRef } from 'react'
import { Users } from 'lucide-react'

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

function VisualTreeSvg({ tree, userName }) {
  const [hoveredId, setHoveredId] = useState(null)

  const rootNode = {
    id: 'root',
    name: userName || 'Вы',
    email: '',
    level: 0,
    total_spent: 1,
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

  const hovered = hoveredId ? findNode(tree, hoveredId) : null

  return (
    <div className="relative overflow-x-auto">
      <svg
        width={Math.max(svgW, 300)}
        height={svgH}
        viewBox={`0 0 ${Math.max(svgW, 300)} ${svgH}`}
        className="mx-auto"
      >
        <defs>
          <radialGradient id="treeGlow">
            <stop offset="0%" stopColor="rgba(59,130,246,0.12)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
        </defs>
        <rect x="0" y="0" width="100%" height="100%" fill="url(#treeGlow)" rx="16" />
        {lines}
        {svgNodes}
      </svg>

      {hovered && (
        <div className="absolute top-2 right-2 bg-[#0C1219]/95 border border-white/[0.08] rounded-xl p-3 text-xs backdrop-blur-sm z-10 min-w-[160px]">
          <div className="font-medium text-white/90 mb-1">{hovered.name}</div>
          <div className="text-white/30 mb-2">{hovered.email}</div>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-white/40">Уровень</span>
              <span className="text-white/70">{hovered.level}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/40">Потратил</span>
              <span className="text-sky-400">{(hovered.total_spent || 0).toFixed(1)} кр.</span>
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

export default function ReferralTree({ tree, userName }) {
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
      <h2 className="font-display font-semibold mb-4 flex items-center gap-2">
        <Users size={18} className="text-sky-400" />
        Ваше дерево
      </h2>
      <VisualTreeSvg tree={tree} userName={userName} />
    </div>
  )
}
