import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Bot, MessageSquare, Users, User, LogOut, LayoutDashboard, Handshake, Store } from 'lucide-react'

export default function DashboardLayout() {
  const { user, logout } = useAuth()

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
      {/* Sidebar */}
      <aside className="w-64 bg-dark-800 border-r border-white/5 flex flex-col fixed h-full">
        <div className="p-6 border-b border-white/5">
          <div className="text-xl font-bold text-accent-400">Meepo</div>
          <div className="text-sm text-white/40 mt-1">{user?.name}</div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
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
      <main className="flex-1 ml-64 p-8">
        <Outlet />
      </main>
    </div>
  )
}
