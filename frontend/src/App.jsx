import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { Component } from 'react'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import BotPage from './pages/BotPage'
import Conversations from './pages/Conversations'
import Contacts from './pages/Contacts'
import Profile from './pages/Profile'
import CatalogPage from './pages/CatalogPage'
import PartnerPage from './pages/PartnerPage'
import BroadcastPage from './pages/BroadcastPage'
import ResetPassword from './pages/ResetPassword'
import AdminPage from './pages/AdminPage'
import DashboardLayout from './components/DashboardLayout'

class ErrorBoundary extends Component {
  state = { hasError: false, error: null }
  static getDerivedStateFromError(error) { return { hasError: true, error } }
  componentDidCatch(error, info) { console.error('React crash:', error, info) }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen">
          <div className="glass-card p-8 text-center max-w-md">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-bold text-white mb-2">Произошла ошибка</h2>
            <p className="text-white/50 text-sm mb-4">{this.state.error?.message}</p>
            <button onClick={() => { this.setState({ hasError: false }); window.location.href = '/dashboard' }}
              className="btn-primary">Вернуться</button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen bg-[#060B11]"><div className="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" /></div>
  return user ? children : <Navigate to="/login" />
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  return user ? <Navigate to="/dashboard" /> : children
}

export default function App() {
  return (
    <ErrorBoundary>
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
        <Route path="/reset-password" element={<PublicRoute><ResetPassword /></PublicRoute>} />
        <Route path="/dashboard" element={<PrivateRoute><DashboardLayout /></PrivateRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="bot" element={<BotPage />} />
          <Route path="conversations" element={<Conversations />} />
          <Route path="contacts" element={<Contacts />} />
          <Route path="catalog" element={<CatalogPage />} />
          <Route path="partner" element={<PartnerPage />} />
          <Route path="broadcast" element={<BroadcastPage />} />
          <Route path="profile" element={<Profile />} />
          <Route path="admin" element={<AdminPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </AuthProvider>
    </ErrorBoundary>
  )
}
