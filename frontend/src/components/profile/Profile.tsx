import { useState } from 'react'
import {
    Flame, Zap, BookOpen, Trophy, Calendar, MapPin, LinkIcon,
    Settings, Edit3, Share2, Code, Terminal, BarChart3, FileText,
    CheckCircle2, Lock, MessageCircle, Heart, Star, Clock,
    GraduationCap, TrendingUp, Award, Users
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Skeleton } from '@/components/ui/skeleton'
import { useUserStore } from '@/store/userStore'
import type { ActivityType } from '@/types'

// Will be replaced with API call later
const ACTIVITY = [
    { id: '1', type: 'achievement' as ActivityType, text: 'Completed C/C++ course with 85% test score', time: '3 days ago' },
    { id: '2', type: 'post' as ActivityType, text: 'Shared a tip about Python dictionaries', time: '5 days ago' },
    { id: '3', type: 'badge' as ActivityType, text: 'Earned the "Quick Learner" badge', time: '1 week ago' },
    { id: '5', type: 'course' as ActivityType, text: 'Started learning Scilab', time: '2 weeks ago' },
    { id: '6', type: 'answer' as ActivityType, text: 'Answered a question about Linux file permissions', time: '2 weeks ago' },
]

// ===== ICON MAPS =====

const courseIconMap: Record<string, { icon: React.ElementType; color: string }> = {
    'Python': { icon: Code, color: 'text-primary' },
    'Linux': { icon: Terminal, color: 'text-green-500' },
    'Scilab': { icon: BarChart3, color: 'text-blue-500' },
    'C/C++': { icon: GraduationCap, color: 'text-orange-500' },
    'LibreOffice': { icon: FileText, color: 'text-emerald-500' },
}

const badgeIconMap: Record<string, { icon: React.ElementType; color: string; bgColor: string }> = {
    'flame': { icon: Flame, color: 'text-warning', bgColor: 'bg-warning/10' },
    'book-open': { icon: BookOpen, color: 'text-primary', bgColor: 'bg-primary/10' },
    'message-circle': { icon: MessageCircle, color: 'text-secondary', bgColor: 'bg-secondary/10' },
    'check-circle': { icon: CheckCircle2, color: 'text-success', bgColor: 'bg-success/10' },
    'heart': { icon: Heart, color: 'text-danger', bgColor: 'bg-danger/10' },
    'code': { icon: Code, color: 'text-primary', bgColor: 'bg-primary/10' },
    'users': { icon: Users, color: 'text-secondary', bgColor: 'bg-secondary/10' },
    'trophy': { icon: Trophy, color: 'text-xp-gold', bgColor: 'bg-xp-gold/10' },
}

// ===== COMPONENTS =====

/** Profile Header with Avatar, Name, Bio, and Edit — reads from userStore */
function ProfileHeader() {
    const user = useUserStore(state => state.user)
    if (!user) return null

    return (
        <Card className="border-border/40 overflow-hidden">
            {/* Gradient Banner */}
            <div className="h-28 sm:h-36 bg-gradient-to-r from-primary via-primary-light to-secondary relative">
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMSIgZmlsbD0icmdiYSgyNTUsMjU1LDI1NSwwLjEpIi8+PC9zdmc+')] opacity-50" />
                <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-3 right-3 h-8 w-8 bg-white/10 hover:bg-white/20 text-white backdrop-blur-sm"
                >
                    <Edit3 className="h-4 w-4" />
                </Button>
            </div>

            <CardContent className="p-5 sm:p-6 relative">
                {/* Avatar */}
                <Avatar className="h-20 w-20 sm:h-24 sm:w-24 border-4 border-background absolute -top-10 sm:-top-12 shadow-lg">
                    <AvatarFallback className="bg-primary text-primary-foreground text-xl sm:text-2xl font-bold">
                        {user.displayName?.split(' ').map(n => n[0]).join('').toUpperCase() || '??'}
                    </AvatarFallback>
                </Avatar>

                {/* Action Buttons aligned right */}
                <div className="flex justify-end gap-2 mb-4 sm:mb-0">
                    <Button variant="outline" size="sm" className="rounded-full gap-1.5 text-xs">
                        <Share2 className="h-3.5 w-3.5" />
                        Share
                    </Button>
                    <Button size="sm" className="rounded-full gap-1.5 text-xs bg-primary hover:bg-primary-hover text-white">
                        <Settings className="h-3.5 w-3.5" />
                        Edit Profile
                    </Button>
                </div>

                {/* User Info */}
                <div className="mt-4 sm:mt-2">
                    <div className="flex items-center gap-2 flex-wrap">
                        <h1 className="text-xl sm:text-2xl font-bold">{user.displayName}</h1>
                        <Badge variant="secondary" className="text-[10px] px-2 py-0.5 gap-1">
                            <Zap className="h-3 w-3 text-xp-gold" />
                            Level {user.level} — {user.levelTitle}
                        </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-0.5">{user.username}</p>
                    <p className="text-sm mt-3 leading-relaxed">{user.bio}</p>

                    {/* Meta Info */}
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 mt-3 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                            <MapPin className="h-3.5 w-3.5" />
                            {user.location}
                        </span>
                        <span className="flex items-center gap-1">
                            <LinkIcon className="h-3.5 w-3.5" />
                            <a href="#" className="text-primary hover:underline">{user.website}</a>
                        </span>

                    </div>

                    {/* Follower Counts */}
                    <div className="flex items-center gap-4 mt-3 text-sm">
                        <button className="hover:underline">
                            <span className="font-semibold">{user.following}</span>
                            <span className="text-muted-foreground ml-1">Following</span>
                        </button>
                        <button className="hover:underline">
                            <span className="font-semibold">{user.followers}</span>
                            <span className="text-muted-foreground ml-1">Followers</span>
                        </button>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

/** Stats Overview Row — reads from userStore */
function StatsRow() {
    const user = useUserStore(state => state.user)
    const courses = useUserStore(state => state.courses)


    if (!user) return null

    const stats = [
        { label: 'Total XP', value: user.xpTotal.toLocaleString(), icon: Zap, color: 'text-xp-gold' },
        { label: 'Courses', value: String(courses.length), icon: BookOpen, color: 'text-primary' },
        { label: 'Followers', value: String(user.followers), icon: Users, color: 'text-warning' },
        { label: 'Posts', value: String(user.postsCount), icon: MessageCircle, color: 'text-secondary' },
    ]

    return (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {stats.map(stat => {
                const Icon = stat.icon
                return (
                    <Card key={stat.label} className="border-border/40">
                        <CardContent className="p-4 text-center">
                            <Icon className={`h-5 w-5 mx-auto mb-1.5 ${stat.color}`} />
                            <p className="text-lg sm:text-xl font-bold font-mono">{stat.value}</p>
                            <p className="text-[11px] text-muted-foreground mt-0.5">{stat.label}</p>
                        </CardContent>
                    </Card>
                )
            })}
        </div>
    )
}

/** Badge / Achievement Wall — reads from userStore */
function BadgeWall() {
    const badges = useUserStore(state => state.badges)
    const earnedBadges = badges.filter(b => b.earnedAt)
    const lockedBadges = badges.filter(b => !b.earnedAt)

    return (
        <div className="space-y-4">
            {/* Earned */}
            <div>
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    Earned — {earnedBadges.length} badges
                </h3>
                <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
                    {earnedBadges.map(badge => {
                        const iconConfig = badgeIconMap[badge.icon] || { icon: Trophy, color: 'text-xp-gold', bgColor: 'bg-xp-gold/10' }
                        const Icon = iconConfig.icon
                        return (
                            <div
                                key={badge.id}
                                className="flex flex-col items-center p-3 rounded-xl bg-card border border-border/40
                                           hover:border-border hover:shadow-sm transition-all duration-200 cursor-pointer group"
                            >
                                <div className={`h-12 w-12 rounded-full ${iconConfig.bgColor} flex items-center justify-center
                                                mb-2 group-hover:scale-110 transition-transform duration-200`}>
                                    <Icon className={`h-6 w-6 ${iconConfig.color}`} />
                                </div>
                                <p className="text-[11px] font-medium text-center leading-tight">{badge.name}</p>
                                <p className="text-[9px] text-muted-foreground mt-0.5">{badge.earnedAt ? new Date(badge.earnedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : ''}</p>
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* Locked */}
            <div>
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    Locked — {lockedBadges.length} remaining
                </h3>
                <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
                    {lockedBadges.map(badge => {
                        const iconConfig = badgeIconMap[badge.icon] || { icon: Trophy, color: 'text-muted-foreground/50', bgColor: 'bg-muted/50' }
                        const Icon = iconConfig.icon
                        return (
                            <div
                                key={badge.id}
                                className="flex flex-col items-center p-3 rounded-xl bg-muted/30 border border-border/20
                                           opacity-50 cursor-default group"
                            >
                                <div className="h-12 w-12 rounded-full bg-muted/50 flex items-center justify-center mb-2 relative">
                                    <Icon className="h-6 w-6 text-muted-foreground/50" />
                                    <Lock className="h-3 w-3 text-muted-foreground absolute -bottom-0.5 -right-0.5" />
                                </div>
                                <p className="text-[11px] font-medium text-center text-muted-foreground leading-tight">{badge.name}</p>
                            </div>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}

/** Completed Courses — reads from userStore */
function CompletedCoursesSection() {
    const courses = useUserStore(state => state.courses)
    const completed = courses.filter(c => c.status === 'completed')

    return (
        <div className="space-y-3">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Completed — {completed.length} course{completed.length !== 1 ? 's' : ''}
            </h3>
            {completed.map(course => {
                const courseInfo = courseIconMap[course.title] || { icon: BookOpen, color: 'text-muted-foreground' }
                const Icon = courseInfo.icon
                return (
                    <Card key={course.id} className="border-success/20 bg-success/5">
                        <CardContent className="p-4 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="h-10 w-10 rounded-lg bg-success/10 flex items-center justify-center">
                                    <Icon className={`h-5 w-5 ${courseInfo.color}`} />
                                </div>
                                <div>
                                    <p className="font-semibold text-sm">{course.title}</p>
                                    <p className="text-xs text-muted-foreground">
                                        Completed {course.completedAt ? new Date(course.completedAt).toLocaleDateString() : ''}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                                <Badge className="bg-success/10 text-success border-0 text-[10px] gap-1">
                                    <CheckCircle2 className="h-3 w-3" />
                                    Completed
                                </Badge>
                            </div>
                        </CardContent>
                    </Card>
                )
            })}
        </div>
    )
}

/** In-Progress Courses — reads from userStore */
function InProgressCoursesSection() {
    const courses = useUserStore(state => state.courses)
    const inProgress = courses.filter(c => c.status === 'in_progress')

    return (
        <div className="space-y-3">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                In Progress — {inProgress.length} courses
            </h3>
            {inProgress.map(course => {
                const courseInfo = courseIconMap[course.title] || { icon: BookOpen, color: 'text-muted-foreground' }
                const Icon = courseInfo.icon
                return (
                    <Card key={course.id} className="border-border/40">
                        <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-3">
                                    <div className="h-10 w-10 rounded-lg bg-muted/50 flex items-center justify-center">
                                        <Icon className={`h-5 w-5 ${courseInfo.color}`} />
                                    </div>
                                    <div>
                                        <p className="font-semibold text-sm">{course.title}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {Math.round(course.progressPercent)}% complete
                                        </p>
                                    </div>
                                </div>
                                <span className="text-xs font-mono font-semibold">{Math.round(course.progressPercent)}%</span>
                            </div>
                            <Progress value={course.progressPercent} className="h-1.5" />
                        </CardContent>
                    </Card>
                )
            })}
        </div>
    )
}

/** Recent Activity Timeline */
function ActivityTimeline() {
    const getActivityIcon = (type: ActivityType) => {
        switch (type) {
            case 'achievement': return { icon: Trophy, color: 'text-xp-gold', bg: 'bg-xp-gold/10' }
            case 'post': return { icon: MessageCircle, color: 'text-primary', bg: 'bg-primary/10' }

            case 'badge': return { icon: Award, color: 'text-secondary', bg: 'bg-secondary/10' }
            case 'course': return { icon: BookOpen, color: 'text-success', bg: 'bg-success/10' }
            case 'answer': return { icon: Star, color: 'text-primary-light', bg: 'bg-primary-light/10' }
            default: return { icon: Clock, color: 'text-muted-foreground', bg: 'bg-muted/50' }
        }
    }

    return (
        <div className="space-y-1">
            {ACTIVITY.map((activity, index) => {
                const config = getActivityIcon(activity.type)
                const Icon = config.icon
                return (
                    <div key={activity.id} className="flex gap-3 group">
                        {/* Timeline line + dot */}
                        <div className="flex flex-col items-center">
                            <div className={`h-8 w-8 rounded-full ${config.bg} flex items-center justify-center shrink-0
                                            group-hover:scale-110 transition-transform duration-200`}>
                                <Icon className={`h-4 w-4 ${config.color}`} />
                            </div>
                            {index < ACTIVITY.length - 1 && (
                                <div className="w-px h-full bg-border/50 min-h-[16px]" />
                            )}
                        </div>

                        {/* Content */}
                        <div className="pb-4 min-w-0">
                            <p className="text-sm leading-relaxed">{activity.text}</p>
                            <p className="text-[11px] text-muted-foreground mt-0.5">{activity.time}</p>
                        </div>
                    </div>
                )
            })}
        </div>
    )
}

// ===== MAIN PROFILE PAGE =====

type ProfileTab = 'activity' | 'courses' | 'badges'

export default function Profile() {
    const [activeTab, setActiveTab] = useState<ProfileTab>('activity')
    const courses = useUserStore(state => state.courses)
    const badges = useUserStore(state => state.badges)
    const isLoading = useUserStore(state => state.isLoading)
    if (isLoading) {
        return (
            <div className="max-w-3xl mx-auto space-y-5">
                {/* Skeleton Header */}
                <Card className="border-border/40 overflow-hidden">
                    <div className="h-28 sm:h-36 bg-muted animate-pulse" />
                    <CardContent className="p-5 sm:p-6 relative">
                        <Skeleton className="h-20 w-20 sm:h-24 sm:w-24 rounded-full border-4 border-background absolute -top-10 sm:-top-12 z-10" />
                        <div className="flex justify-end gap-2 mb-4 sm:mb-0">
                            <Skeleton className="h-8 w-16 rounded-full" />
                            <Skeleton className="h-8 w-24 rounded-full" />
                        </div>
                        <div className="mt-4 sm:mt-2 space-y-3">
                            <Skeleton className="h-7 w-48" />
                            <Skeleton className="h-4 w-32" />
                            <Skeleton className="h-4 w-3/4 mt-4" />
                            <Skeleton className="h-4 w-1/2" />
                        </div>
                    </CardContent>
                </Card>

                {/* Skeleton Stats */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[1, 2, 3, 4].map(i => (
                        <Card key={i} className="border-border/40">
                            <CardContent className="p-4 flex flex-col items-center justify-center gap-2">
                                <Skeleton className="h-5 w-5 rounded-full" />
                                <Skeleton className="h-6 w-16" />
                                <Skeleton className="h-3 w-12" />
                            </CardContent>
                        </Card>
                    ))}
                </div>

                {/* Skeleton Tabs Content Space */}
                <Card className="border-border/40 mt-5">
                    <CardContent className="p-5 space-y-4">
                        <Skeleton className="h-5 w-40 mb-4" />
                        {[1, 2, 3].map(i => (
                            <div key={i} className="flex gap-3">
                                <Skeleton className="h-8 w-8 rounded-full shrink-0" />
                                <div className="space-y-2 flex-1">
                                    <Skeleton className="h-4 w-full" />
                                    <Skeleton className="h-3 w-20" />
                                </div>
                            </div>
                        ))}
                    </CardContent>
                </Card>
            </div>
        )
    }
    const tabs: { id: ProfileTab; label: string; icon: React.ElementType; count?: number }[] = [
        { id: 'activity', label: 'Activity', icon: Clock },
        { id: 'courses', label: 'Courses', icon: BookOpen, count: courses.length },
        { id: 'badges', label: 'Badges', icon: Trophy, count: badges.filter(b => b.earnedAt).length },
    ]


    return (
        <div className="max-w-3xl mx-auto space-y-5">
            {/* Profile Header */}
            <ProfileHeader />

            {/* Stats Row */}
            <StatsRow />

            {/* Tabs */}
            <div className="flex items-center gap-1 border-b border-border/50 overflow-x-auto">
                {tabs.map(tab => {
                    const Icon = tab.icon
                    const isActive = activeTab === tab.id
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium
                                        border-b-2 transition-all duration-200 whitespace-nowrap
                                        ${isActive
                                    ? 'border-primary text-primary'
                                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                                }`}
                        >
                            <Icon className="h-4 w-4" />
                            {tab.label}
                            {tab.count !== undefined && (
                                <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono
                                    ${isActive ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>
                                    {tab.count}
                                </span>
                            )}
                        </button>
                    )
                })}
            </div>

            {/* Tab Content */}
            <div>
                {activeTab === 'activity' && (
                    <Card className="border-border/40">
                        <CardContent className="p-5">
                            <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                                <TrendingUp className="h-4 w-4 text-primary" />
                                Recent Activity
                            </h3>
                            <ActivityTimeline />
                        </CardContent>
                    </Card>
                )}

                {activeTab === 'courses' && (
                    <div className="space-y-5">
                        <CompletedCoursesSection />
                        <InProgressCoursesSection />
                    </div>
                )}

                {activeTab === 'badges' && (
                    <Card className="border-border/40">
                        <CardContent className="p-5">
                            <BadgeWall />
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    )
}
