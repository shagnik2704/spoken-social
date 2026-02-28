import {
    Trophy, Zap, TrendingUp, TrendingDown, Minus,
    Crown, Medal, Award, ChevronDown, Star,
    Code, Terminal, BarChart3, FileText, BookOpen, GraduationCap
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import type { LeaderboardUser } from '@/types'
import { useState, useEffect } from 'react'
import api from '@/lib/axios'

const courses = [
    { id: 'all', name: 'All Courses', icon: BookOpen },
    { id: 'python', name: 'Python', icon: Code },
    { id: 'linux', name: 'Linux', icon: Terminal },
    { id: 'scilab', name: 'Scilab', icon: BarChart3 },
    { id: 'cpp', name: 'C/C++', icon: GraduationCap },
    { id: 'libreoffice', name: 'LibreOffice', icon: FileText },
]

// ===== HELPER FUNCTIONS =====

function getTrendIcon(trend: 'up' | 'down' | 'same', delta: number) {
    if (trend === 'up') return (
        <span className="flex items-center gap-0.5 text-success text-[11px] font-medium">
            <TrendingUp className="h-3 w-3" />↑{delta}
        </span>
    )
    if (trend === 'down') return (
        <span className="flex items-center gap-0.5 text-danger text-[11px] font-medium">
            <TrendingDown className="h-3 w-3" />↓{delta}
        </span>
    )
    return (
        <span className="flex items-center gap-0.5 text-muted-foreground text-[11px]">
            <Minus className="h-3 w-3" />
        </span>
    )
}

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
function LeaderboardRow({ user, showWeeklyXP }: { user: LeaderboardUser; showWeeklyXP?: boolean }) {
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
                <p className="text-sm font-bold font-mono">
                    {showWeeklyXP ? `+${user.xpLastWeek}` : user.xp.toLocaleString()}
                </p>
                <p className="text-[10px] text-muted-foreground">{showWeeklyXP ? 'this week' : 'XP'}</p>
            </div>

            {/* Trend */}
            <div className="w-10 text-center shrink-0">
                {getTrendIcon(user.trend, user.trendDelta)}
            </div>
        </div>
    )
}

/** Your Position Highlight Card */
function YourPosition({ user, data }: { user: LeaderboardUser; data: LeaderboardUser[] }) {
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
                            {user.xp.toLocaleString()} XP • {user.rank <= 3 ? 'You\'re in the top 3!' : `${user.xp > 0 ? ((data[user.rank - 2]?.xp || 0) - user.xp).toLocaleString() : 0} XP to rank up`}
                        </p>
                    </div>
                </div>
                <div className="text-right">
                    {getTrendIcon(user.trend, user.trendDelta)}
                    <p className="text-[10px] text-muted-foreground mt-0.5">vs last week</p>
                </div>
            </CardContent>
        </Card>
    )
}

// ===== MAIN LEADERBOARD PAGE =====

type TimeFilter = 'overall' | 'weekly'

export default function Leaderboard() {
    const [leaderboardData, setLeaderboardData] = useState<LeaderboardUser[]>([])
    const [timeFilter, setTimeFilter] = useState<TimeFilter>('overall')
    const [selectedCourse, setSelectedCourse] = useState('all')
    const [courseDropdownOpen, setCourseDropdownOpen] = useState(false)


    useEffect(() => {
        const fetchLeaderboardData = async () => {
            try {
                const { data } = await api.get('/api/leaderboard')
                setLeaderboardData(data)
            }
            catch (error) {
                console.log(error)
            }
        }
        fetchLeaderboardData()
    }, [])

    const currentUser = leaderboardData.find(u => u.isCurrentUser)

    // Sort by weekly XP for the weekly tab
    const displayData = timeFilter === 'weekly'
        ? [...leaderboardData].sort((a, b) => b.xpLastWeek - a.xpLastWeek).map((u, i) => ({ ...u, rank: i + 1 }))
        : leaderboardData

    const selectedCourseInfo = courses.find(c => c.id === selectedCourse)
    const CourseIcon = selectedCourseInfo?.icon || BookOpen

    return (
        <div className="max-w-3xl mx-auto space-y-5">
            {/* Page Title */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Trophy className="h-6 w-6 text-xp-gold" />
                    <h1 className="text-xl sm:text-2xl font-bold">Leaderboard</h1>
                </div>
            </div>

            {/* Filters Row */}
            <div className="flex items-center justify-between gap-3 flex-wrap">
                {/* Time Filter Tabs */}
                <div className="flex items-center gap-1 bg-muted/30 rounded-full p-1">
                    {[
                        { id: 'overall' as TimeFilter, label: 'All Time' },
                        { id: 'weekly' as TimeFilter, label: 'This Week' },
                    ].map(filter => (
                        <button
                            key={filter.id}
                            onClick={() => setTimeFilter(filter.id)}
                            className={`px-4 py-1.5 rounded-full text-xs font-medium transition-all duration-200
                                        ${timeFilter === filter.id
                                    ? 'bg-primary text-white shadow-sm'
                                    : 'text-muted-foreground hover:text-foreground'
                                }`}
                        >
                            {filter.label}
                        </button>
                    ))}
                </div>

                {/* Course Filter */}
                <div className="relative">
                    <Button
                        variant="outline"
                        size="sm"
                        className="rounded-full gap-1.5 text-xs"
                        onClick={() => setCourseDropdownOpen(!courseDropdownOpen)}
                    >
                        <CourseIcon className="h-3.5 w-3.5" />
                        {selectedCourseInfo?.name || 'All Courses'}
                        <ChevronDown className={`h-3 w-3 transition-transform ${courseDropdownOpen ? 'rotate-180' : ''}`} />
                    </Button>
                    {courseDropdownOpen && (
                        <div className="absolute right-0 top-full mt-1 w-48 bg-card border border-border rounded-lg shadow-lg z-10 py-1">
                            {courses.map(course => {
                                const Icon = course.icon
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
                                        {course.name}
                                    </button>
                                )
                            })}
                        </div>
                    )}
                </div>
            </div>

            {/* Your Position */}
            {currentUser && <YourPosition user={currentUser} data={displayData} />}

            {/* Podium */}
            <Podium users={displayData} />

            {/* Full Leaderboard Table */}
            <Card className="border-border/40">
                <CardContent className="p-3 sm:p-4">
                    {/* Table Header */}
                    <div className="flex items-center gap-3 px-3 sm:px-4 py-2 text-[10px] uppercase tracking-wider text-muted-foreground font-semibold border-b border-border/30 mb-1">
                        <div className="w-8 text-center">Rank</div>
                        <div className="flex-1">Student</div>

                        <div className="w-[60px] text-right">{timeFilter === 'weekly' ? 'Weekly' : 'Total'}</div>
                        <div className="w-10 text-center">Δ</div>
                    </div>

                    {/* Rows */}
                    <div className="space-y-0.5">
                        {displayData.map(user => (
                            <LeaderboardRow
                                key={user.id}
                                user={user}
                                showWeeklyXP={timeFilter === 'weekly'}
                            />
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
