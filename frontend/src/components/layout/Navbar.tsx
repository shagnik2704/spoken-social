import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useUserStore } from '@/store/userStore'
import { useTheme } from '@/hooks/useTheme'
import { useComposeModal } from '@/hooks/useComposeModal'
import {
    Search,
    Bell,
    Home,
    LayoutDashboard,
    PlusCircle,
    User,
    Moon,
    Sun,
    LogOut,
    MessageSquare,
    Trophy,

    Users,
    Shield,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import { useAuthStore } from '@/store/authStore'
import { useLeaderboardStore } from '@/store/leaderboardStore'

// Navigation items for the sidebar/bottom nav
const navItems = [
    { icon: Home, label: 'Feed', path: '/feed', roles: ['student', 'coordinator', 'admin'] },
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard', roles: ['student'] },
    { icon: PlusCircle, label: 'Post', path: '/post', roles: ['student'] },
    { icon: Trophy, label: 'Leaderboard', path: '/leaderboard', roles: ['student'] },
    { icon: User, label: 'Profile', path: '/profile', roles: ['student', 'coordinator', 'admin'] },
    { icon: Users, label: 'My Students', path: '/coordinator', roles: ['coordinator'] },
    { icon: Shield, label: 'Admin Panel', path: '/admin', roles: ['admin'] },
]


export function TopBar() {
    const { theme, toggleTheme } = useTheme()
    const [searchOpen, setSearchOpen] = useState(false)
    const logout = useAuthStore(state => state.logout)
    const navigate = useNavigate()

    const notificationCount = 3

    // 🧠 ZUSTAND: Select only the slices you need.
    // This component only re-renders when these specific values change.
    const user = useUserStore(state => state.user)

    // Connect SSE for real-time XP updates app-wide
    const { connectSSE, disconnectSSE, fetchLeaderboard } = useLeaderboardStore()
    useEffect(() => {
        fetchLeaderboard()
        connectSSE()
        return () => disconnectSSE()
    }, [])


    return (
        <header className="z-50 w-full border-b border-border bg-card/80 backdrop-blur-xl shrink-0">
            <div className="flex h-14 items-center justify-between px-4 lg:px-6">
                {/* Left — Logo */}
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-2">
                        <img src="/logo.png" alt="EduPyramids" className="h-8 w-8 object-contain" />
                        <span className="text-lg font-bold tracking-tight hidden sm:inline-block text-foreground">
                            Spoken Social
                        </span>
                        <span className="text-lg font-bold tracking-tight sm:hidden text-foreground">
                            SS
                        </span>
                    </div>
                </div>

                {/* Center — Search Bar (Desktop) */}
                <div className="hidden md:flex flex-1 max-w-md mx-8">
                    <div className="relative w-full">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="Search courses, people, posts..."
                            className="w-full h-9 rounded-lg border border-input bg-muted/50 pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50 focus:border-ring transition-all"
                        />
                    </div>
                </div>

                {/* Right — Actions */}
                <div className="flex items-center gap-1 sm:gap-2">
                    {/* Search icon (mobile) */}
                    <Button
                        variant="ghost"
                        size="icon"
                        className="md:hidden text-muted-foreground hover:text-foreground"
                        onClick={() => setSearchOpen(!searchOpen)}
                    >
                        <Search className="h-5 w-5" />
                    </Button>

                    {/* Notifications */}
                    <Button
                        variant="ghost"
                        size="icon"
                        className="relative text-muted-foreground hover:text-foreground"
                    >
                        <Bell className="h-5 w-5" />
                        {notificationCount > 0 && (
                            <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-white">
                                {notificationCount}
                            </span>
                        )}
                    </Button>

                    {/* Messages */}
                    <Button
                        variant="ghost"
                        size="icon"
                        className="hidden sm:flex text-muted-foreground hover:text-foreground"
                    >
                        <MessageSquare className="h-5 w-5" />
                    </Button>

                    {/* Profile Dropdown */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="relative h-9 w-9 rounded-full p-0">
                                <Avatar className="h-8 w-8 border-2 border-primary/50">
                                    <AvatarFallback className="bg-primary text-sm font-semibold text-primary-foreground">
                                        {user?.displayName?.split(' ').map(n => n[0]).join('').toUpperCase() || '??'}
                                    </AvatarFallback>
                                </Avatar>
                                {/* Level badge */}
                                <span className="absolute -bottom-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-xp-gold text-[9px] font-bold text-black px-0.5">
                                    {user?.level || 1}
                                </span>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-56">
                            {/* User info header */}
                            <div className="px-3 py-2.5">
                                <p className="text-sm font-semibold">{user?.displayName || 'Guest'}</p>
                                <p className="text-xs text-muted-foreground">{user?.departmentYear || ''}</p>
                                <div className="flex items-center gap-2 mt-1.5">
                                    <Badge variant="secondary" className="bg-primary/20 text-primary text-[10px] px-1.5 py-0 h-5">
                                        Level {user?.level || 1}
                                    </Badge>

                                </div>
                            </div>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                                className="cursor-pointer gap-2"
                                onClick={toggleTheme}
                            >
                                {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                                {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-destructive focus:text-destructive cursor-pointer gap-2"
                                onClick={() => { logout(); navigate('/') }}>
                                <LogOut className="h-4 w-4" />
                                Log Out
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>

            {/* Mobile Search Overlay */}
            {searchOpen && (
                <div className="md:hidden border-t border-border px-4 py-2 bg-card">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="Search courses, people, posts..."
                            autoFocus
                            className="w-full h-9 rounded-lg border border-input bg-muted/50 pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50 focus:border-ring transition-all"
                            onBlur={() => setSearchOpen(false)}
                        />
                    </div>
                </div>
            )}
        </header>
    )
}

export function DesktopSidebar() {
    const location = useLocation()
    const user = useUserStore(state => state.user)

    return (
        <aside className="hidden lg:flex flex-col w-60 border-r border-border bg-card/50 shrink-0">
            <nav className="flex flex-col gap-1 p-3 flex-1">
                {navItems
                    .filter(item => item.roles.includes(user?.role || 'student')).map((item) => {
                        const isActive = location.pathname === item.path

                        // Post button opens the compose modal
                        if (item.label === 'Post') {
                            return (
                                <TooltipProvider key={item.label}>
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <div className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground opacity-50 cursor-not-allowed">
                                                <item.icon className="h-5 w-5" />
                                                {item.label}
                                            </div>
                                        </TooltipTrigger>
                                        <TooltipContent side="right">
                                            <p>Coming soon!</p>
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                                // <button
                                //     key={item.label}
                                //     onClick={openCompose}
                                //     className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium
                                //            text-muted-foreground hover:bg-accent hover:text-foreground transition-all"
                                // >
                                //     <item.icon className="h-5 w-5" />
                                //     {item.label}
                                // </button>
                            )
                        }
                        if (item.label === 'Feed') {
                            return (
                                <TooltipProvider key={item.label}>
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <div className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground opacity-50 cursor-not-allowed">
                                                <item.icon className="h-5 w-5" />
                                                {item.label}
                                            </div>
                                        </TooltipTrigger>
                                        <TooltipContent side="right">
                                            <p>Coming soon!</p>
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                            )
                        }

                        return (
                            <Link
                                key={item.label}
                                to={item.path}
                                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all
                                ${isActive
                                        ? 'bg-primary/15 text-primary'
                                        : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                                    }`}
                            >
                                <item.icon className={`h-5 w-5 ${isActive ? 'text-primary' : ''}`} />
                                {item.label}
                                {isActive && (
                                    <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
                                )}
                            </Link>
                        )
                    })}
            </nav>


        </aside>
    )
}



export function MobileBottomNav() {
    const location = useLocation()
    const { open: openCompose } = useComposeModal()
    const user = useUserStore(state => state.user)


    return (
        <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-card/95 backdrop-blur-xl">
            <div className="flex items-center justify-around h-16 px-2">
                {navItems
                    .filter(item => item.roles.includes(user?.role || 'student')).map((item) => {
                        const isActive = location.pathname === item.path

                        // Post button opens the compose modal
                        if (item.label === 'Post') {
                            return (
                                <button
                                    key={item.label}
                                    onClick={openCompose}
                                    className="flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg transition-all"
                                >
                                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary shadow-lg shadow-primary/30 -mt-3">
                                        <PlusCircle className="h-5 w-5 text-primary-foreground" />
                                    </div>
                                </button>
                            )
                        }

                        if (item.label === 'Feed') {
                            return (
                                <TooltipProvider key={item.label}>
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <div className="flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg text-muted-foreground opacity-50 cursor-not-allowed">
                                                <item.icon className="h-5 w-5" />
                                                <span className="text-[10px] font-medium">{item.label}</span>
                                            </div>
                                        </TooltipTrigger>
                                        <TooltipContent side="top">
                                            <p>Coming soon!</p>
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                            )
                        }



                        return (
                            <Link
                                key={item.label}
                                to={item.path}
                                className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg transition-all
                                ${isActive
                                        ? 'text-primary'
                                        : 'text-muted-foreground hover:text-foreground'
                                    }`}
                            >
                                <item.icon className="h-5 w-5" />
                                <span className="text-[10px] font-medium">{item.label}</span>
                                {isActive && (
                                    <div className="h-0.5 w-4 rounded-full bg-primary mt-0" />
                                )}
                            </Link>
                        )
                    })}
            </div>
        </nav>
    )
}
