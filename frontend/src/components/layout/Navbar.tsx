import { useState } from 'react'
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
    Calendar,
    BookOpen,
    ChevronLeft,
} from 'lucide-react'
import { cn } from '@/lib/utils'
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
import { CourseBatchSelector } from './CourseBatchSelector'

// Navigation items for the sidebar/bottom nav
const navItems = [
    { icon: Home, label: 'Feed', path: '/feed', roles: ['student', 'coordinator', 'admin'] },
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard', roles: ['student'] },
    { icon: PlusCircle, label: 'Post', path: '/post', roles: ['student'] },
    { icon: Trophy, label: 'Leaderboard', path: '/leaderboard', roles: ['student'] },
    { icon: User, label: 'Profile', path: '/profile', roles: ['student', 'coordinator', 'admin'] },
    { icon: Users, label: 'My Learners', path: '/coordinator', roles: ['coordinator'] },
    { icon: Shield, label: 'Admin Panel', path: '/admin', roles: ['admin'] },
    { icon: Calendar, label: 'Switch Batch', path: '/landing', roles: ['student', 'coordinator', 'admin'] },
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
    const activeProgrammeName = useUserStore(state => state.activeProgrammeName)
    const setActiveProgramme = useUserStore(state => state.setActiveProgramme)


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

                {/* Center-Right — Global Course Selector */}
                <div className="hidden md:flex items-center">
                    <CourseBatchSelector />
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
                        className="hidden relative text-muted-foreground hover:text-foreground"
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
                        className="hidden text-muted-foreground hover:text-foreground"
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
                                <div className="flex flex-col gap-1.5 mt-1.5">
                                    <div className="flex items-center gap-2">
                                        <Badge variant="secondary" className="bg-primary/20 text-primary text-[10px] px-1.5 py-0 h-5">
                                            Level {user?.level || 1}
                                        </Badge>
                                    </div>
                                    {activeProgrammeName && (
                                        <Badge className="w-fit bg-gradient-to-r from-blue-600 to-indigo-600 text-white border-0 text-[10px] px-1.5 py-0 h-5">
                                            {activeProgrammeName}
                                        </Badge>
                                    )}
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
                            <DropdownMenuItem
                                className="cursor-pointer gap-2"
                                onClick={() => {
                                    setActiveProgramme('', '')
                                    navigate('/programmes')
                                }}
                            >
                                <BookOpen className="h-4 w-4" />
                                Switch Programme
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
    const [isCollapsed, setIsCollapsed] = useState(() => {
        return localStorage.getItem('spoken_sidebar_collapsed') === 'true'
    })

    const toggleSidebar = () => {
        setIsCollapsed(prev => {
            const next = !prev
            localStorage.setItem('spoken_sidebar_collapsed', String(next))
            return next
        })
    }

    return (
        <div className="relative hidden lg:flex shrink-0">
            <aside
                className={cn(
                    "flex flex-col border-r border-border bg-card/50 transition-[width] duration-300 ease-in-out h-full select-none overflow-hidden",
                    isCollapsed ? "w-16" : "w-60"
                )}
            >
                <div className={cn(
                    "flex flex-col h-full transition-[width] duration-300 ease-in-out overflow-hidden",
                    isCollapsed ? "w-16" : "w-60"
                )}>
                    <nav className="flex flex-col gap-1.5 px-2 py-3 flex-1">
                        {navItems
                            .filter(item => item.roles.includes(user?.role || 'student')).map((item) => {
                                const isActive = location.pathname === item.path

                                // Post / Feed disabled buttons with Tooltips
                                if (item.label === 'Post' || item.label === 'Feed') {
                                    const disabledItem = (
                                        <div
                                            className="flex items-center h-10 w-full rounded-xl text-sm font-medium text-muted-foreground opacity-50 cursor-not-allowed px-3.5 gap-3 overflow-hidden"
                                        >
                                            <div className="size-5 shrink-0 flex items-center justify-center">
                                                <item.icon className="size-5 shrink-0" />
                                            </div>
                                            <div
                                                className={cn(
                                                    "flex items-center min-w-0 flex-1 overflow-hidden transition-all duration-300 ease-in-out whitespace-nowrap",
                                                    isCollapsed
                                                        ? "max-w-0 opacity-0 -translate-x-3 pointer-events-none"
                                                        : "max-w-[160px] opacity-100 translate-x-0"
                                                )}
                                            >
                                                <span className="truncate text-sm font-medium">{item.label}</span>
                                            </div>
                                        </div>
                                    )

                                    return (
                                        <TooltipProvider key={item.label} delayDuration={150}>
                                            <Tooltip>
                                                <TooltipTrigger asChild>
                                                    {disabledItem}
                                                </TooltipTrigger>
                                                <TooltipContent side="right" sideOffset={8}>
                                                    <p>{item.label}: Coming soon!</p>
                                                </TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    )
                                }

                                const navLink = (
                                    <Link
                                        to={item.path}
                                        className={cn(
                                            "flex items-center h-10 w-full rounded-xl text-sm font-medium transition-colors duration-200 group/item overflow-hidden px-3.5 gap-3",
                                            isActive
                                                ? "bg-primary/15 text-primary font-semibold shadow-2xs"
                                                : "text-muted-foreground hover:bg-accent hover:text-foreground"
                                        )}
                                    >
                                        <div className="size-5 shrink-0 flex items-center justify-center">
                                            <item.icon className={cn("size-5 shrink-0 transition-transform group-hover/item:scale-110", isActive ? "text-primary" : "")} />
                                        </div>
                                        <div
                                            className={cn(
                                                "flex items-center min-w-0 flex-1 overflow-hidden transition-all duration-300 ease-in-out whitespace-nowrap",
                                                isCollapsed
                                                    ? "max-w-0 opacity-0 -translate-x-3 pointer-events-none"
                                                    : "max-w-[160px] opacity-100 translate-x-0"
                                            )}
                                        >
                                            <span className="truncate text-sm font-medium">{item.label}</span>
                                            {isActive && (
                                                <div className="ml-auto size-1.5 rounded-full bg-primary shrink-0 mr-0.5" />
                                            )}
                                        </div>
                                    </Link>
                                )

                                if (isCollapsed) {
                                    return (
                                        <TooltipProvider key={item.label} delayDuration={50}>
                                            <Tooltip>
                                                <TooltipTrigger asChild>
                                                    {navLink}
                                                </TooltipTrigger>
                                                <TooltipContent side="right" sideOffset={8} className="font-medium text-xs shadow-md">
                                                    <p>{item.label}</p>
                                                </TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    )
                                }

                                return <div key={item.label} className="w-full">{navLink}</div>
                            })}
                    </nav>
                </div>
            </aside>

            {/* Middle panel separator collapse/expand toggle button with animated arrow */}
            <TooltipProvider delayDuration={200}>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <button
                            onClick={toggleSidebar}
                            className={cn(
                                "absolute top-1/2 -translate-y-1/2 z-40",
                                "flex h-7 w-7 items-center justify-center rounded-full border border-border bg-card/95 backdrop-blur-xs text-muted-foreground",
                                "shadow-sm hover:shadow-md hover:bg-accent hover:text-foreground hover:border-primary/50",
                                "transition-[left,transform,background-color,border-color,color] duration-300 ease-in-out cursor-pointer group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            )}
                            style={{
                                left: isCollapsed ? '50px' : '226px', // 64px - 14px or 240px - 14px (centered on separator)
                            }}
                            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                        >
                            <ChevronLeft
                                className={cn(
                                    "h-4 w-4 transition-transform duration-300 ease-in-out",
                                    isCollapsed
                                        ? "rotate-180 group-hover:translate-x-0.5 text-primary"
                                        : "rotate-0 group-hover:-translate-x-0.5"
                                )}
                            />
                        </button>
                    </TooltipTrigger>
                    <TooltipContent side="right" sideOffset={8} className="text-xs">
                        {isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </div>
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
