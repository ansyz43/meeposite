import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Bot, MessageSquare, Users, User, LogOut, LayoutDashboard, Handshake, Menu, X, Megaphone, Shield, FileText } from 'lucide-react'
import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'

const SIDEBAR_COLLAPSED = 64
const SIDEBAR_EXPANDED = 256

export default function DashboardLayout() {
  const { user, logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [hovered, setHovered] = useState(false)
  const location = useLocation()

  useEffect(() => { setSidebarOpen(false) }, [location.pathname])

  // Glass-card mouse glow — delegate from document
  useEffect(() => {
    function handleMouseMove(e) {
      const card = e.target.closest('.glass-card')
      if (!card) return
      const rect = card.getBoundingClientRect()
      card.style.setProperty('--mouse-x', (e.clientX - rect.left) + 'px')
      card.style.setProperty('--mouse-y', (e.clientY - rect.top) + 'px')
    }
    document.addEventListener('mousemove', handleMouseMove)
    return () => document.removeEventListener('mousemove', handleMouseMove)
  }, [])

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Главная', end: true },
    ...(user?.has_bot ? [
      { to: '/dashboard/bot', icon: Bot, label: 'Мой бот' },
      { to: '/dashboard/conversations', icon: MessageSquare, label: 'Переписки' },
      { to: '/dashboard/contacts', icon: Users, label: 'Контакты' },
      { to: '/dashboard/broadcast', icon: Megaphone, label: 'Рассылка' },
    ] : []),
    { to: '/dashboard/partner', icon: Handshake, label: 'Рефералы' },
    { to: '/dashboard/content-plan', icon: FileText, label: 'Контент-план' },
    { to: '/dashboard/profile', icon: User, label: 'Профиль' },
    ...(user?.is_admin ? [
      { to: '/dashboard/admin', icon: Shield, label: 'Админ' },
    ] : []),
  ]

  const expanded = hovered

  return (
    <div className="min-h-screen flex bg-[#060B11]">
      {/* Mobile header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 bg-[#0C1219]/90 backdrop-blur-2xl border-b border-white/[0.06] flex items-center px-4 h-14">
        <button onClick={() => setSidebarOpen(true)} className="p-2 text-white/50 hover:text-white transition-colors">
          <Menu size={20} />
        </button>
        <div className="ml-3 flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center">
            <Bot size={14} className="text-white" />
          </div>
          <span className="font-display font-bold gradient-text">Meepo</span>
        </div>
      </div>

      {/* Overlay — mobile */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{ width: expanded ? SIDEBAR_EXPANDED : SIDEBAR_COLLAPSED }}
        className={`bg-[#0C1219]/95 backdrop-blur-2xl border-r border-white/[0.06] flex flex-col fixed h-full z-50 transition-all duration-300 ease-in-out overflow-hidden ${sidebarOpen ? 'translate-x-0 !w-64' : '-translate-x-full'} md:translate-x-0`}
      >
        {/* Logo */}
        <div className="p-3 border-b border-white/[0.06] flex items-center justify-between h-14">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-glow shrink-0 ml-1">
              <Bot size={18} className="text-white" />
            </div>
            <div className={`font-display font-bold text-sm gradient-text whitespace-nowrap transition-opacity duration-200 ${expanded ? 'opacity-100' : 'opacity-0 md:opacity-0'}`}>Meepo</div>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden p-1 text-white/30 hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto overflow-x-hidden">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              title={!expanded ? item.label : undefined}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-200 group relative whitespace-nowrap ${
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-400 shadow-[inset_0_0_0_1px_rgba(16,185,129,0.2)]'
                    : 'text-white/45 hover:text-white/80 hover:bg-white/[0.04]'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-emerald-400" />
                  )}
                  <item.icon size={17} className={`flex-shrink-0 ${isActive ? 'text-emerald-400' : 'text-white/35 group-hover:text-white/60'} transition-colors`} />
                  <span className={`transition-opacity duration-200 ${expanded ? 'opacity-100' : 'opacity-0'}`}>{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User info + Logout */}
        <div className="p-2 border-t border-white/[0.06] space-y-1">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 text-xs font-bold shrink-0">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className={`min-w-0 transition-opacity duration-200 ${expanded ? 'opacity-100' : 'opacity-0'}`}>
              <div className="text-[13px] font-medium text-white/70 truncate">{user?.name || 'Пользователь'}</div>
              <div className="text-[11px] text-white/25 truncate">{user?.email}</div>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2 rounded-xl text-[13px] text-white/30 hover:text-red-400 hover:bg-red-500/[0.06] transition-all duration-200 w-full cursor-pointer whitespace-nowrap"
          >
            <LogOut size={17} className="shrink-0" />
            <span className={`transition-opacity duration-200 ${expanded ? 'opacity-100' : 'opacity-0'}`}>Выйти</span>
          </button>
        </div>
      </aside>

      {/* Main content — left margin matches collapsed sidebar on desktop */}
      <main className="flex-1 p-4 md:p-8 pt-18 md:pt-8 min-h-screen transition-[margin] duration-300 md:ml-16">
        <Outlet />
      </main>
    </div>
  )
}
