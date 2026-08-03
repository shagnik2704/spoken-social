import {
    Trophy, Zap,
    Crown, Medal, Award, ChevronDown, Star,
    Code, Terminal, BarChart3, FileText, BookOpen, GraduationCap
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import type { LeaderboardUser } from '@/types'
import { useState } from 'react'
import { useLeaderboard, useMyCourses } from '@/hooks/queries/useLeaderboardQueries'
import { useAuthStore } from '@/store/authStore'
import { useUserStore } from '@/store/userStore'
import XPGrowthGraph from './XPGrowthGraph'

const COURSE_ICONS: Record<string, typeof BookOpen> = {
    python: Code,
    linux: Terminal,
    scilab: BarChart3,
    latex: FileText,
    cpp: GraduationCap,
}

// ===== HELPER FUNCTIONS =====

function getRankDisplay(rank: number) {
    if (rank === 1) return { color: 'text-yellow-500', bg: 'bg-yellow-500/10', icon: Crown, label: '1st' }
    if (rank === 2) return { color: 'text-gray-400', bg: 'bg-gray-400/10', icon: Medal, label: '2nd' }
    if (rank === 3) return { color: 'text-amber-600', bg: 'bg-amber-600/10', icon: Award, label: '3rd' }
    return { color: 'text-muted-foreground', bg: 'bg-muted/50', icon: null, label: `${rank}` }
}

// ===== COMPONENTS =====

/** Top 3 Podium Display */
function Podium({ users }: { users: LeaderboardUser[] }) {
    const top3 = users.slice(0, 3)
    if (top3.length < 3) return null

    // Reorder for podium display: [2nd, 1st, 3rd]
    const podiumOrder = [top3[1], top3[0], top3[2]]
    const podiumConfig = [
        { height: 'h-20', rank: 2, medal: 'text-gray-400', bg: 'from-gray-400/10 to-gray-400/5', border: 'border-gray-400/30', size: 'h-14 w-14' },
        { height: 'h-28', rank: 1, medal: 'text-yellow-500', bg: 'from-yellow-500/10 to-yellow-500/5', border: 'border-yellow-500/30', size: 'h-16 w-16' },
        { height: 'h-16', rank: 3, medal: 'text-amber-600', bg: 'from-amber-600/10 to-amber-600/5', border: 'border-amber-600/30', size: 'h-12 w-12' },
    ]

    return (
        <Card className="border-border/40 overflow-hidden">
            <CardContent className="p-5 sm:p-6">
                <div className="flex items-center gap-2 mb-5">
                    <Trophy className="h-5 w-5 text-xp-gold" />
                    <h2 className="font-semibold">Top 3</h2>
                </div>
                <div className="flex items-end justify-center gap-3 sm:gap-6">
                    {podiumOrder.map((user, index) => {
                        const config = podiumConfig[index]
                        return (
                            <div key={user.id} className="flex flex-col items-center">
                                {/* Avatar */}
                                <div className="relative mb-2">
                                    <Avatar className={`${config.size} border-2 ${config.border}`}>
                                        <AvatarFallback className={`bg-gradient-to-b ${config.bg} text-foreground text-sm font-bold`}>
                                            {user.name?.split(' ').map((n: string) => n[0]).join('').toUpperCase() || '??'}
                                        </AvatarFallback>
                                    </Avatar>
                                    {config.rank === 1 && (
                                        <Crown className="h-5 w-5 text-yellow-500 absolute -top-3 left-1/2 -translate-x-1/2" />
                                    )}
                                </div>
                                {/* Info */}
                                <p className="text-xs sm:text-sm font-semibold text-center truncate max-w-[80px] sm:max-w-[100px]">
                                    {user.name.split(' ')[0]}
                                </p>
                                <p className="text-[10px] text-muted-foreground">Lv.{user.level}</p>
                                <Badge className={`mt-1 text-[10px] px-1.5 py-0 border-0 ${config.rank === 1 ? 'bg-yellow-500/10 text-yellow-600' :
                                    config.rank === 2 ? 'bg-gray-400/10 text-gray-500' :
                                        'bg-amber-600/10 text-amber-600'
                                    }`}>
                                    <Zap className="h-2.5 w-2.5 mr-0.5" />
                                    {user.xp.toLocaleString()}
                                </Badge>
                                {/* Podium bar */}
                                <div className={`${config.height} w-16 sm:w-20 mt-2 rounded-t-lg bg-gradient-to-b ${config.bg} 
                                                 border ${config.border} border-b-0 flex items-start justify-center pt-2`}>
                                    <span className={`text-lg sm:text-xl font-bold font-mono ${config.medal}`}>
                                        {config.rank}
                                    </span>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </CardContent>
        </Card>
    )
}

/** Leaderboard Table Row */
function LeaderboardRow({ user }: { user: LeaderboardUser }) {
    const rankInfo = getRankDisplay(user.rank)

    return (
        <div className={`flex items-center gap-3 px-3 sm:px-4 py-3 rounded-lg transition-all duration-200
                         ${user.isCurrentUser
                ? 'bg-primary/5 border border-primary/20 shadow-sm'
                : 'hover:bg-muted/30'
            }`}
        >
            {/* Rank */}
            <div className="w-8 text-center shrink-0">
                {rankInfo.icon ? (
                    <rankInfo.icon className={`h-5 w-5 mx-auto ${rankInfo.color}`} />
                ) : (
                    <span className="text-sm font-mono font-bold text-muted-foreground">{rankInfo.label}</span>
                )}
            </div>

            {/* Avatar + Name */}
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
                <Avatar className="h-9 w-9 shrink-0">
                    <AvatarFallback className={`text-[11px] font-semibold ${user.isCurrentUser ? 'bg-primary/10 text-primary' : 'bg-muted text-foreground'}`}>
                        {user.name?.split(' ').map((n: string) => n[0]).join('').toUpperCase() || '??'}
                    </AvatarFallback>
                </Avatar>
                <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                        <span className={`text-sm font-medium truncate ${user.isCurrentUser ? 'text-primary' : ''}`}>
                            {user.name}
                            {user.isCurrentUser && <span className="text-xs text-muted-foreground ml-1">(You)</span>}
                        </span>
                    </div>
                    <p className="text-[10px] text-muted-foreground truncate">
                        Lv.{user.level} • {user.levelTitle}
                    </p>
                </div>
            </div>



            {/* XP */}
            <div className="text-right shrink-0 min-w-[60px]">
                <p className="text-sm font-bold font-mono">{user.xp.toLocaleString()}</p>
                <p className="text-[10px] text-muted-foreground">XP</p>
            </div>
        </div>
    )
}

/**
 * Your Position Highlight Card.
 *
 * Driven by the envelope's `yourEntry`, not by finding yourself in the page —
 * the page is only the top 100, so the old lookup rendered nothing at all for
 * the overwhelming majority of students.
 *
 * `nextUp` is the entry one rank above, and only exists when you're on the page;
 * off-page we show total board size instead of an unknowable XP gap.
 */
function YourPosition({ user, total, nextUp }: { user: LeaderboardUser; total: number; nextUp?: LeaderboardUser }) {
    const subtitle = user.rank <= 3
        ? "You're in the top 3!"
        : nextUp
            ? `${(nextUp.xp - user.xp).toLocaleString()} XP to rank up`
            : `of ${total.toLocaleString()} ranked learners`

    return (
        <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-transparent">
            <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <Star className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                        <p className="text-sm font-semibold">Your Position: <span className="text-primary">#{user.rank}</span></p>
                        <p className="text-xs text-muted-foreground">
                            {user.xp.toLocaleString()} XP • {subtitle}
                        </p>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

/** Shown to students who haven't earned XP yet — they have no rank to display. */
function NotRankedYet() {
    return (
        <Card className="border-border/60 bg-muted/30">
            <CardContent className="p-4 flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                    <Star className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                    <p className="text-sm font-semibold">You're not ranked yet</p>
                    <p className="text-xs text-muted-foreground">
                        Complete a tutorial to earn your first XP and join the leaderboard.
                    </p>
                </div>
            </CardContent>
        </Card>
    )
}

// ===== MAIN LEADERBOARD PAGE =====

export default function Leaderboard() {
    const [selectedCourse, setSelectedCourse] = useState('all')
    const [courseDropdownOpen, setCourseDropdownOpen] = useState(false)
    const [audience, setAudience] = useState<'global' | 'college'>('global')

    const isAuthenticated = useAuthStore(state => state.isAuthenticated)
    const collegeId = useUserStore(state => state.user?.collegeId)
    const { data: myCourses = [] } = useMyCourses()

    // A course board ranks by XP earned in that course, so it replaces the
    // audience filter rather than combining with it.
    const scope = selectedCourse === 'all' ? audience : 'course'
    const scopeId = selectedCourse === 'all' ? collegeId : selectedCourse

    const { data } = useLeaderboard({ scope, scopeId })

    const displayData = data?.entries ?? []
    // yourEntry is authoritative and present even when you're off the page.
    // It's null both for signed-out visitors and for students with no XP yet,
    // so isAuthenticated is what separates "nothing to show" from "not ranked".
    const yourEntry = data?.yourEntry ?? null
    const nextUp = yourEntry ? displayData.find(u => u.rank === yourEntry.rank - 1) : undefined
    const showNotRanked = isAuthenticated && data !== undefined && yourEntry === null

    const courseOptions = [{ id: 'all', title: 'All Courses' }, ...myCourses]
    const selectedCourseInfo = courseOptions.find(c => c.id === selectedCourse)
    const CourseIcon = COURSE_ICONS[selectedCourse] ?? BookOpen

    return (
        <div className="max-w-3xl mx-auto space-y-5">
            {/* Page Title */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Trophy className="h-6 w-6 text-xp-gold" />
                    <div>
                        <h1 className="text-xl sm:text-2xl font-bold">Leaderboard</h1>
                        {data && (
                            <p className="text-xs text-muted-foreground">
                                {data.scope.name ?? 'All learners'} • {data.total.toLocaleString()} ranked
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* Filters Row */}
            <div className="flex items-center justify-end gap-3 flex-wrap">
                {collegeId && selectedCourse === 'all' && (
                    <div className="flex items-center rounded-full border border-border p-0.5">
                        {(['global', 'college'] as const).map(option => (
                            <button
                                key={option}
                                onClick={() => setAudience(option)}
                                className={`rounded-full px-3 py-1 text-xs font-medium transition duration-200 ease-in-out
                                            ${audience === option
                                        ? 'bg-primary text-primary-foreground'
                                        : 'text-muted-foreground hover:text-foreground'
                                    }`}
                            >
                                {option === 'global' ? 'Everyone' : 'My College'}
                            </button>
                        ))}
                    </div>
                )}

                {/* Course Filter */}
                <div className="relative">
                    <Button
                        variant="outline"
                        size="sm"
                        className="rounded-full gap-1.5 text-xs"
                        onClick={() => setCourseDropdownOpen(!courseDropdownOpen)}
                    >
                        <CourseIcon className="h-3.5 w-3.5" />
                        {selectedCourseInfo?.title || 'All Courses'}
                        <ChevronDown className={`h-3 w-3 transition-transform ${courseDropdownOpen ? 'rotate-180' : ''}`} />
                    </Button>
                    {courseDropdownOpen && (
                        <div className="absolute right-0 top-full mt-1 w-48 bg-card border border-border rounded-lg shadow-lg z-10 py-1">
                            {courseOptions.map(course => {
                                const Icon = COURSE_ICONS[course.id] ?? BookOpen
                                return (
                                    <button
                                        key={course.id}
                                        onClick={() => {
                                            setSelectedCourse(course.id)
                                            setCourseDropdownOpen(false)
                                        }}
                                        className={`w-full flex items-center gap-2 px-3 py-2 text-sm transition-colors
                                                    ${selectedCourse === course.id
                                                ? 'bg-primary/10 text-primary'
                                                : 'hover:bg-muted/50 text-foreground'
                                            }`}
                                    >
                                        <Icon className="h-4 w-4" />
                                        {course.title}
                                    </button>
                                )
                            })}
                        </div>
                    )}
                </div>
            </div>

            {/* Podium */}
            <Podium users={displayData} />

            {/* XP Growth Graph */}
            <XPGrowthGraph />

            {/* Your Position */}
            {yourEntry && (
                <YourPosition user={yourEntry} total={data?.total ?? 0} nextUp={nextUp} />
            )}
            {showNotRanked && <NotRankedYet />}

            {/* Full Leaderboard Table */}
            <Card className="border-border/40">
                <CardContent className="p-3 sm:p-4">
                    {/* Table Header */}
                    <div className="flex items-center gap-3 px-3 sm:px-4 py-2 text-[10px] uppercase tracking-wider text-muted-foreground font-semibold border-b border-border/30 mb-1">
                        <div className="w-8 text-center">Rank</div>
                        <div className="flex-1">Learner</div>
                        <div className="w-[60px] text-right">Total</div>
                    </div>

                    {/* Rows */}
                    <div className="space-y-0.5">
                        {displayData.map(user => (
                            <LeaderboardRow key={user.id} user={user} />
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
