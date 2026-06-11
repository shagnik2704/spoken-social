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
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from './lib/queryClient'
import { ImpersonationBanner } from '@/components/layout/ImpersonationBanner'
import { LandingPage } from './components/auth/LandingPage'
import { ProgrammeSelector } from './components/auth/ProgrammeSelector'

function App() {

  const fetchUser = useUserStore(state => state.fetchUser)
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)
  const user = useUserStore(state => state.user)
  const isUserLoading = useUserStore(state => state.isLoading)
  const activeProgrammeId = useUserStore(state => state.activeProgrammeId)

  useEffect(() => {
    if (isAuthenticated) {
      fetchUser()
    }
  }, [isAuthenticated])

  return (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <ThemeProvider>
        <ComposeModalProvider>
          {!isAuthenticated ? (
            <Routes>
              <Route path="*" element={<LoginPage />} />
            </Routes>
          ) : isUserLoading || !user ? (
            /* Loading guard is INSIDE BrowserRouter so the router never unmounts.
               This keeps navigate() functions valid across impersonation transitions. */
            <div className="h-screen flex items-center justify-center bg-background text-foreground">
              <div className="flex flex-col items-center gap-3">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                <p className="text-sm text-muted-foreground">Loading your profile...</p>
              </div>
            </div>
          ) : !activeProgrammeId ? (
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
          ) : (
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
          )}

          <Toaster
            position="bottom-right"
          />
        </ComposeModalProvider>
      </ThemeProvider>
    </BrowserRouter>
    <ReactQueryDevtools initialIsOpen={false}/>
  </QueryClientProvider>
  )
}

export default App
