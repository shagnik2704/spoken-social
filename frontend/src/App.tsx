import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
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
import { useEffect } from 'react'
import { useUserStore } from './store/userStore'
import { LoginPage } from './components/auth/LoginPage'
import { useAuthStore } from './store/authStore'
import { Toaster } from '@/components/ui/sonner'

function App() {

  const fetchUser = useUserStore(state => state.fetchUser)
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)
  const user = useUserStore(state => state.user)
  const isUserLoading = useUserStore(state => state.isLoading)

  useEffect(() => {
    if (isAuthenticated) {
      fetchUser()
    }
  }, [isAuthenticated])

  // Wait for user data before rendering authenticated routes
  // This prevents the race condition where navigate('/') fires
  // before fetchUser() completes, causing wrong role-based redirect
  if (isAuthenticated && (!user || isUserLoading)) {
    return (
      <div className="h-screen flex items-center justify-center bg-background text-foreground">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading your profile...</p>
        </div>
      </div>
    )
  }





  return (
    <BrowserRouter>
      <ThemeProvider>
        <ComposeModalProvider>
          {!isAuthenticated ? (
            <Routes>
              <Route path="*" element={<LoginPage />} />
            </Routes>
          ) : (
            <div className="h-screen bg-background text-foreground flex flex-col overflow-hidden">
              {/* Top Bar — fixed, never scrolls */}
              <TopBar />

              <div className="flex flex-1 min-h-0">
                {/* Desktop Sidebar — fixed, never scrolls */}
                <DesktopSidebar />

                {/* Main Content — the ONLY scrollable area */}
                <main className="flex-1 min-w-0 overflow-y-auto overflow-x-hidden p-4 lg:p-6 pb-20 lg:pb-6">
                  <Suspense fallback={<div className="flex h-full items-center justify-center p-8">Loading page...</div>}>
                    <Routes>
                      <Route path="/" element={<Navigate to={user?.role === 'admin' ? '/admin' : user?.role === 'coordinator' ? '/coordinator' : '/dashboard'} replace />} />
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
          )}

          <Toaster
            position="bottom-right"
          />
        </ComposeModalProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default App
