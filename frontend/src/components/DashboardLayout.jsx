import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Bot, MessageSquare, Users, User, LogOut, LayoutDashboard, Handshake, Store, Menu, X } from 'lucide-react'
import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'

export default function DashboardLayout() {
  const { user, logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  // Close sidebar on navigation (mobile)
  useEffect(() => { setSidebarOpen(false) }, [location.pathname])

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Главная', end: true },
    ...(user?.has_bot ? [
      { to: '/dashboard/bot', icon: Bot, label: 'Мой бот' },
      { to: '/dashboard/conversations', icon: MessageSquare, label: 'Переписки' },
      { to: '/dashboard/contacts', icon: Users, label: 'Контакты' },
    ] : []),
    { to: '/dashboard/catalog', icon: Store, label: 'Каталог ботов' },
    { to: '/dashboard/partner', icon: Handshake, label: 'Партнёрство' },
    { to: '/dashboard/profile', icon: User, label: 'Профиль' },
  ]

  return (
    <div className="min-h-screen flex">
      {/* Mobile header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 bg-dark-800 border-b border-white/5 flex items-center px-4 h-14">
        <button onClick={() => setSidebarOpen(true)} className="p-2 text-white/60 hover:text-white">
          <Menu size={22} />
        </button>
        <div className="ml-3 text-lg font-bold text-accent-400">Meepo</div>
      </div>

      {/* Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`w-64 bg-dark-800 border-r border-white/5 flex flex-col fixed h-full z-50 transition-transform duration-200 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0`}>
        <div className="p-6 border-b border-white/5 flex items-center justify-between">
          <div>
            <div className="text-xl font-bold text-accent-400">Meepo</div>
            <div className="text-sm text-white/40 mt-1">{user?.name}</div>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden p-1 text-white/40 hover:text-white">
            <X size={20} />
          </button>
        </div>
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-accent-500/10 text-accent-400 border border-accent-500/20'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-white/5">
          <button
            onClick={logout}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-white/40 hover:text-red-400 hover:bg-red-500/5 transition-colors w-full"
          >
            <LogOut size={18} />
            Выйти
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 md:ml-64 p-4 md:p-8 pt-18 md:pt-8">
        <Outlet />
      </main>
    </div>
  )
}
