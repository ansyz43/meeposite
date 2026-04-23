import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { Component, Suspense, lazy } from 'react'

const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const BotPage = lazy(() => import('./pages/BotPage'))
const Conversations = lazy(() => import('./pages/Conversations'))
const Contacts = lazy(() => import('./pages/Contacts'))
const Profile = lazy(() => import('./pages/Profile'))
const PartnerPage = lazy(() => import('./pages/PartnerPage'))
const BroadcastPage = lazy(() => import('./pages/BroadcastPage'))
const ResetPassword = lazy(() => import('./pages/ResetPassword'))
const AdminPage = lazy(() => import('./pages/AdminPage'))
const ContentPlanPage = lazy(() => import('./pages/ContentPlanPage'))
const DashboardLayout = lazy(() => import('./components/DashboardLayout'))

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
  if (loading) return <div className="flex items-center justify-center h-screen bg-background"><div className="w-6 h-6 border-2 border-sky-500/30 border-t-sky-400 rounded-full animate-spin" /></div>
  return user ? children : <Navigate to="/login" />
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  return user ? <Navigate to="/dashboard" /> : children
}

function RouteFallback() {
  return (
    <div className="flex items-center justify-center h-screen bg-background">
      <div className="w-6 h-6 border-2 border-sky-500/30 border-t-sky-400 rounded-full animate-spin" />
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
    <AuthProvider>
      <Suspense fallback={<RouteFallback />}>
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
            <Route path="partner" element={<PartnerPage />} />
            <Route path="broadcast" element={<BroadcastPage />} />
            <Route path="profile" element={<Profile />} />
            <Route path="content-plan" element={<ContentPlanPage />} />
            <Route path="admin" element={<AdminPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Suspense>
    </AuthProvider>
    </ErrorBoundary>
  )
}
