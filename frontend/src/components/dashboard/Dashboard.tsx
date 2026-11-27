import { useEffect } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import {
    Zap, ChevronRight, Trophy, Lock,
    BookOpen,
    ClipboardCheck, GraduationCap, CalendarClock, MessageCircle,
    CheckCircle2,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { ActiveCourseTracker } from './ActiveCourseTracker'
import { LearnerPackTracker } from './LearnerPackTracker'
import { CourseWalkthrough } from './CourseWalkthrough'
import { CourseUnderDevelopment, KNOWN_SWAYAM_COURSES } from './CourseUnderDevelopment'
import { useSyncActiveCourse } from '@/hooks/useSyncActiveCourse'
import api from '@/lib/axios'
import { useUserStore } from '@/store/userStore'
import { CourseIcon } from '@/components/CourseIcon'
import type { UpcomingEvent } from '@/types'

// Will be replaced with API call later
const UPCOMING: UpcomingEvent[] = []






const badgeIconMap: Record<string, React.ReactNode> = {
    'Quick Learner': <Zap className="h-5 w-5 text-warning" />,
    '5 Courses': <BookOpen className="h-5 w-5 text-primary" />,
    'First Post': <MessageCircle className="h-5 w-5 text-secondary" />,
}



function getGreeting(): string {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
}


function GreetingHeader() {
    const userName = useUserStore(state => state.user?.displayName)
    const firstName = userName?.split(' ')[0]
    const today = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })

    return (
        <header className="space-y-1 pt-1">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{today}</p>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                {getGreeting()}, {firstName || 'there'}
            </h1>
            <p className="text-sm text-muted-foreground">Pick up where you left off.</p>
        </header>
    )
}


interface StatCellProps {
    label: string
    value: string
    hint: string
    icon?: React.ReactNode
}

const StatCell: React.FC<StatCellProps> = ({ label, value, hint, icon }) => (
    <div className="px-4 sm:px-5 py-4 space-y-1 min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
            {icon}
            {label}
        </p>
        <p className="font-mono text-2xl font-bold text-foreground leading-tight">{value}</p>
        <p className="text-xs text-muted-foreground truncate">{hint}</p>
    </div>
)


function XPLevelCard() {
    const user = useUserStore(state => state.user)
    if (!user) return null

    const xpPercent = Math.min(100, Math.round((user.xpTotal / user.xpForNextLevel) * 100))
    const xpRemaining = Math.max(0, user.xpForNextLevel - user.xpTotal)

    return (
        <Card className="border-border/80 bg-card shadow-xs py-0 gap-0 overflow-hidden transition-all duration-300 hover:border-primary/30">
            <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-y sm:divide-y-0 divide-border/70 [&>*:nth-child(-n+2)]:border-t-0 [&>*:nth-child(odd)]:border-l-0 sm:[&>*:nth-child(odd)]:border-l sm:[&>*:first-child]:border-l-0">
                <StatCell label="Level" value={String(user.level)} hint={user.levelTitle} />
                <StatCell
                    label="Total XP"
                    value={user.xpTotal.toLocaleString()}
                    hint="All courses"
                    icon={<Zap className="h-3 w-3 text-xp-gold" />}
                />
                <StatCell label="This week" value={`+${user.xpThisWeek.toLocaleString()}`} hint="XP earned" />
                <StatCell label="Today" value={`+${user.xpToday.toLocaleString()}`} hint="XP earned" />
            </div>
            <div className="border-t border-border/70 px-4 sm:px-5 py-3 space-y-1.5 bg-muted/30">
                <div className="flex justify-between text-xs text-muted-foreground">
                    <span>
                        <span className="font-mono font-semibold text-foreground">{xpRemaining.toLocaleString()} XP</span> to Level {user.level + 1}
                    </span>
                    <span className="font-mono font-semibold text-foreground">{xpPercent}%</span>
                </div>
                <Progress value={xpPercent} className="h-1.5 bg-muted rounded-full" />
            </div>
        </Card>
    )
}


// WeeklyGoalTracker removed — weekly_goal field no longer in schema


function MyCourses() {
    const courses = useUserStore(state => state.courses)
    const activeCourseId = useUserStore(state => state.activeCourseId)
    const setActiveCourse = useUserStore(state => state.setActiveCourse)

    const handleCourseClick = (courseId: string) => {
        // Just set the active course; ActiveCourseTracker's effect owns fetching tutorials
        // + forum activity for it (removing this avoids a duplicate fetch per course switch).
        setActiveCourse(courseId)
    }

    if (courses.length === 0) {
        return (
            <div>
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-semibold flex items-center gap-2">
                        <BookOpen className="h-4 w-4 text-primary" />
                        My Courses
                    </h2>
                </div>
                <Card>
                    <CardContent className="p-6 text-center">
                        <BookOpen className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                        <p className="text-sm text-muted-foreground">No courses enrolled yet.</p>
                        <p className="text-xs text-muted-foreground mt-1">Courses will appear here after enrollment.</p>
                    </CardContent>
                </Card>
            </div>
        )
    }

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold flex items-center gap-2">
                    <BookOpen className="h-4 w-4 text-primary" />
                    My Courses
                </h2>
            </div>
            <div className="flex gap-4 overflow-x-auto pb-2 -mx-1 px-1 snap-x snap-mandatory scrollbar-hide">
                {courses.map((course) => {
                    const isActive = course.id === activeCourseId
                    return (
                        <Card 
                            key={course.id} 
                            className={`min-w-[150px] sm:min-w-[170px] snap-start shrink-0 transition-all cursor-pointer
                                ${isActive 
                                    ? 'border-primary/50 bg-primary/5 ring-1 ring-primary/20' 
                                    : 'hover:border-primary/30'
                                }`}
                            onClick={() => handleCourseClick(course.id)}
                        >
                            <CardContent className="p-4 sm:p-5">
                                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted/50 mb-3">
                                    <CourseIcon title={course.title} className="h-6 w-6" />
                                </div>
                                <h3 className="text-sm font-semibold truncate">{course.title}</h3>
                                {course.batchName && (
                                    <p className="text-[10px] text-muted-foreground mt-0.5">{course.batchName}</p>
                                )}
                                <div className="flex items-center gap-2 mt-3">
                                    <Progress
                                        value={course.progressPercent}
                                        className={`h-1.5 flex-1 ${course.status === 'completed' ? '[&>div]:bg-success' : ''}`}
                                    />
                                    <span className="text-[11px] font-mono text-muted-foreground">
                                        {Math.round(course.progressPercent)}%
                                    </span>
                                </div>
                                {course.status === 'completed' && (
                                    <Badge variant="secondary" className="bg-success/15 text-success text-[10px] mt-3 px-1.5 py-0 h-5 gap-1">
                                        <CheckCircle2 className="h-3 w-3" />
                                        Completed
                                    </Badge>
                                )}
                                {isActive && (
                                    <Badge variant="secondary" className="bg-primary/15 text-primary text-[10px] mt-2 px-1.5 py-0 h-5">
                                        Active
                                    </Badge>
                                )}
                            </CardContent>
                        </Card>
                    )
                })}
            </div>
        </div>
    )
}


function AchievementsPreview() {
    const badges = useUserStore(state => state.badges)
    const earnedBadges = badges.filter(b => b.earnedAt)
    const upcomingBadges: typeof badges = []  // no progress tracking in new schema

    return (
        <Card>
            <CardContent className="p-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-semibold flex items-center gap-2">
                        <Trophy className="h-4 w-4 text-xp-gold" />
                        Achievements
                    </h2>
                    <button className="text-xs text-primary hover:text-primary/80 flex items-center gap-0.5 transition-colors">
                        See All <ChevronRight className="h-3 w-3" />
                    </button>
                </div>

                {/* Earned badges */}
                {earnedBadges.length > 0 && (
                    <p className="text-[11px] text-muted-foreground uppercase tracking-wider mb-3">Recently Earned</p>
                )}
                {earnedBadges.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-4 text-center text-muted-foreground/60">
                        <Trophy className="h-8 w-8 text-muted-foreground/40 mb-2" />
                        <p className="text-sm">No badges yet. Complete tutorials to earn your first.</p>
                    </div>
                )}
                <div className={earnedBadges.length > 0 ? "flex gap-3 mb-5" : "hidden"}>
                    {earnedBadges.slice(0, 3).map((badge) => (
                        <div
                            key={badge.id}
                            className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-xp-gold/5 border border-xp-gold/10 min-w-[75px]"
                        >
                            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-xp-gold/10">
                                {badgeIconMap[badge.name] || <Trophy className="h-5 w-5 text-xp-gold" />}
                            </div>
                            <span className="text-[10px] font-medium text-center leading-tight">{badge.name}</span>
                        </div>
                    ))}
                </div>

                {/* Upcoming badges */}
                {upcomingBadges.length > 0 && (
                    <>
                        <p className="text-[11px] text-muted-foreground uppercase tracking-wider mb-3">Next Up</p>
                        <div className="space-y-2.5">
                            {upcomingBadges.map((badge) => (
                                <div key={badge.id} className="flex items-center gap-2.5 text-xs">
                                    <Lock className="h-3.5 w-3.5 text-muted-foreground" />
                                    <span className="text-muted-foreground">{badge.name}</span>
                                    <span className="ml-auto text-[11px] font-mono text-muted-foreground">{badge.name}</span>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </CardContent>
        </Card>
    )
}


function UpcomingDeadlines() {
    const getUrgencyColor = (daysAway: number) => {
        if (daysAway <= 3) return 'border-l-destructive'
        if (daysAway <= 7) return 'border-l-warning'
        return 'border-l-border'
    }

    const getTypeIcon = (type: 'test' | 'workshop') => {
        return type === 'test'
            ? <ClipboardCheck className="h-5 w-5 text-primary mt-0.5" />
            : <GraduationCap className="h-5 w-5 text-success mt-0.5" />
    }

    return (
        <Card>
            <CardContent className="p-5 sm:p-6">
                <h2 className="text-sm font-semibold flex items-center gap-2 mb-4">
                    <CalendarClock className="h-4 w-4 text-primary" />
                    Upcoming
                </h2>
                {UPCOMING.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground/60">
                        <CalendarClock className="h-8 w-8 text-muted-foreground/40 mb-2" />
                        <p className="text-sm">No upcoming events. You're all clear.</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {UPCOMING.map((event) => (
                            <div
                                key={event.id}
                                className={`flex items-start gap-3 p-3 rounded-lg bg-muted/30 border-l-[3px] ${getUrgencyColor(event.daysAway)}`}
                            >
                                {getTypeIcon(event.type)}
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium truncate">{event.title}</p>
                                    <p className="text-[11px] text-muted-foreground mt-0.5">{event.location}</p>
                                </div>
                                <div className="text-right shrink-0">
                                    <p className="text-xs font-semibold">{event.date}</p>
                                    <p className={`text-[11px] mt-0.5 ${event.daysAway <= 3 ? 'text-destructive font-semibold' : 'text-muted-foreground'}`}>
                                        {event.daysAway === 1 ? 'Tomorrow!' : `${event.daysAway} days`}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}


// ===== MAIN DASHBOARD PAGE =====

export default function Dashboard() {
    const params = useParams<{ courseId?: string }>()
    const [searchParams] = useSearchParams()
    const targetCourseId = params.courseId || searchParams.get('course')
    const swayamEnrollmentId = searchParams.get('swayamEnrollmentId') || searchParams.get('enrollmentId')

    const { user, isLoading, courses, activeCourseId } = useUserStore()
    const activeBatchIsActive = useUserStore(state => state.activeBatchIsActive)

    useEffect(() => {
        if (swayamEnrollmentId) {
            localStorage.setItem('swayamEnrollmentId', swayamEnrollmentId)
            const cid = targetCourseId || activeCourseId
            if (cid && user?.role === 'student') {
                void api.post('/api/auth/swayam/link-enrollment', {
                    course_id: cid,
                    enrollment_id: swayamEnrollmentId,
                }).catch(() => {
                    // Best-effort enrollment linking for already-signed-in fallback launches
                })
            }
        }
    }, [swayamEnrollmentId, targetCourseId, activeCourseId, user?.role])

    useSyncActiveCourse(targetCourseId)

    const activeCourse = courses.find(c => c.id === activeCourseId)
    const isLearnerPack = activeCourse?.uiLayout === 'learner_pack'

    const targetSlug = (targetCourseId || activeCourseId || '').toLowerCase().replace(/_/g, '-')
    const isUnderDevelopment =
        activeCourse?.uiLayout === 'under_development' ||
        (targetSlug in KNOWN_SWAYAM_COURSES && (!activeCourse || activeCourse.uiLayout === 'under_development'))

    if (isLoading) {
        return (
            <div className="max-w-3xl mx-auto space-y-6">
                <div className="h-24 bg-muted/40 animate-pulse rounded-2xl" />
                <div className="h-64 bg-muted/20 animate-pulse rounded-2xl" />
            </div>
        )
    }

    if (!user || user.role !== 'student') return null

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            {!activeBatchIsActive && (
                <div className="rounded-xl border border-border/80 bg-muted/40 px-3.5 py-2.5 flex items-center justify-between gap-3 text-xs text-muted-foreground shadow-2xs">
                    <div className="flex items-center gap-2 min-w-0">
                        <Lock className="h-3.5 w-3.5 text-muted-foreground/80 shrink-0" />
                        <span className="truncate">Viewing historical batch archive (Read-Only).</span>
                    </div>
                    <Link to="/landing" className="text-xs font-semibold text-primary hover:underline shrink-0">
                        Switch Batch →
                    </Link>
                </div>
            )}
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 lg:gap-6">
                <GreetingHeader />
                {!isUnderDevelopment && (
                    <CourseWalkthrough courseId={activeCourseId} courseTitle={activeCourse?.title} />
                )}
            </div>
            <XPLevelCard />

            {/* Section 3: Active Course Tracker, SWAYAM Plus Learner Pack, or Under Development Placeholder */}
            {isUnderDevelopment ? (
                <CourseUnderDevelopment
                    courseId={targetCourseId || activeCourseId}
                    courseTitle={activeCourse?.title}
                />
            ) : isLearnerPack ? (
                <LearnerPackTracker />
            ) : (
                <ActiveCourseTracker />
            )}

            {/* Weekly Goal removed from schema */}

            {/* Section 5: My Courses */}
            <MyCourses />
            {/* Section 6 & 7: Achievements + Upcoming side by side on desktop */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <AchievementsPreview />
                <UpcomingDeadlines />
            </div>
        </div>
    )
}
