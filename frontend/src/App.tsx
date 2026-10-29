import { Suspense, lazy, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { TopBar, DesktopSidebar, MobileBottomNav } from '@/components/layout/Navbar'
import { ThemeProvider } from '@/hooks/useTheme'
import { ComposeModalProvider } from '@/hooks/useComposeModal'
import { ComposeModal } from '@/components/compose/ComposeModal'
// const Feed = lazy(() => import('@/components/feed/Feed'))
const Profile = lazy(() => import('@/components/profile/Profile'))
const Dashboard = lazy(() => import('@/components/dashboard/Dashboard'))
const Leaderboard = lazy(() => import('@/components/leaderboard/Leaderboard'))
const CoordinatorDashboard = lazy(() => import('@/components/coordinator/CoordinatorDashboard'))
const AdminDashboard = lazy(() => import('@/components/admin/AdminDashboard'))
import { useUserStore } from './store/userStore'
import { LoginPage } from './components/auth/LoginPage'
import { SSOCallbackPage } from './components/auth/SSOCallbackPage'
import { useAuthStore } from './store/authStore'
import { Toaster } from '@/components/ui/sonner'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from './lib/queryClient'
import { ImpersonationBanner } from '@/components/layout/ImpersonationBanner'
import { LandingPage } from './components/auth/LandingPage'
import { ProgrammeSelector } from './components/auth/ProgrammeSelector'

function AppContent() {
  const location = useLocation()
  const navigate = useNavigate()
  const fetchUser = useUserStore(state => state.fetchUser)
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)
  const user = useUserStore(state => state.user)
  const isUserLoading = useUserStore(state => state.isLoading)
  const activeProgrammeId = useUserStore(state => state.activeProgrammeId)

  // Redirect any URL with ?token= or ?sso_token= to /sso
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    if ((params.get('token') || params.get('sso_token')) && !location.pathname.startsWith('/sso') && !location.pathname.startsWith('/auth/sso')) {
      navigate(`/sso${location.search}`, { replace: true })
    }
  }, [location.pathname, location.search, navigate])

  useEffect(() => {
    if (isAuthenticated) {
      fetchUser()
    }
  }, [isAuthenticated, fetchUser])

  // SSO Callback routes take precedence regardless of previous authentication state
  if (location.pathname === '/sso' || location.pathname === '/auth/sso') {
    return (
      <Routes>
        <Route path="/sso" element={<SSOCallbackPage />} />
        <Route path="/auth/sso" element={<SSOCallbackPage />} />
      </Routes>
    )
  }

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    )
  }

  if (isUserLoading || !user) {
    return (
      <div className="h-screen flex items-center justify-center bg-background text-foreground">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading your profile...</p>
        </div>
      </div>
    )
  }

  if (!activeProgrammeId) {
    return (
      <Suspense fallback={
        <div className="h-screen flex items-center justify-center bg-background text-foreground">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            <p className="text-sm text-muted-foreground">Loading programmes...</p>
          </div>
        </div>
      }>
        <Routes>
          <Route path="/programmes" element={<ProgrammeSelector />} />
          <Route path="*" element={<Navigate to="/programmes" replace />} />
        </Routes>
      </Suspense>
    )
  }

  return (
    <div className="h-screen bg-background text-foreground flex flex-col overflow-hidden">
      {/* Impersonation Banner */}
      <ImpersonationBanner />

      {/* Top Bar — fixed, never scrolls */}
      <TopBar />

      <div className="flex flex-1 min-h-0">
        {/* Desktop Sidebar — fixed, never scrolls */}
        <DesktopSidebar />

        {/* Main Content — the ONLY scrollable area */}
        <main className="flex-1 min-w-0 overflow-y-auto overflow-x-hidden p-4 lg:p-6 pb-20 lg:pb-6">
          <Suspense fallback={<div className="flex h-full items-center justify-center p-8">Loading page...</div>}>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/landing" element={<LandingPage />} />
              <Route path="/programmes" element={<Navigate to="/" replace />} />
              {/* <Route path="/feed" element={<Feed />} /> */}
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/leaderboard" element={<Leaderboard />} />
              <Route path="/coordinator" element={<CoordinatorDashboard />} />
              <Route path="/admin" element={<AdminDashboard />} />
            </Routes>
          </Suspense>
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileBottomNav />

      {/* Compose Modal — renders on top of everything */}
      <ComposeModal />
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider>
          <ComposeModalProvider>
            <AppContent />
            <Toaster position="bottom-right" />
          </ComposeModalProvider>
        </ThemeProvider>
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false}/>
    </QueryClientProvider>
  )
}

export default App
