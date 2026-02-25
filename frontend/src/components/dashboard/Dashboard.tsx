import {
    Flame, Zap, Calendar, ChevronRight, Trophy, Lock,
    BookOpen, Hand, Code, Terminal, BarChart3, FileText, Settings,
    ClipboardCheck, GraduationCap, CalendarClock, MessageCircle,
    CheckCircle2
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { ActiveCourseTracker } from './ActiveCourseTracker'


import { useUserStore } from '@/store/userStore'
import { MOCK_UPCOMING } from '@/data/mockData'


const courseIconMap: Record<string, React.ReactNode> = {
    'Python': <Code className="h-6 w-6 text-primary" />,
    'Linux': <Terminal className="h-6 w-6 text-green-500" />,
    'Scilab': <BarChart3 className="h-6 w-6 text-blue-500" />,
    'C/C++': <Settings className="h-6 w-6 text-orange-500" />,
    'LibreOffice': <FileText className="h-6 w-6 text-emerald-500" />,
}


const badgeIconMap: Record<string, React.ReactNode> = {
    '7-Day Streak': <Flame className="h-5 w-5 text-warning" />,
    '5 Courses': <BookOpen className="h-5 w-5 text-primary" />,
    'First Post': <MessageCircle className="h-5 w-5 text-secondary" />,
}



function getGreeting(): string {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
}


function GreetingBanner() {

    const userName = useUserStore(state => state.user?.name)
    const streak = useUserStore(state => state.streak)


    return (
        <Card className="border-warning/20 bg-gradient-to-r from-warning/5 via-orange-500/5 to-danger/5">
            <CardContent className="p-5 sm:p-6">
                <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <Hand className="h-5 w-5 text-xp-gold shrink-0" />
                            <h1 className="text-lg sm:text-2xl font-bold truncate">
                                {getGreeting()},    {userName || 'there'}!
                            </h1>
                        </div>
                        <p className="text-muted-foreground text-sm mt-1">
                            Ready to learn something new today?
                        </p>
                    </div>
                    <div className="flex flex-col items-center shrink-0">
                        <Flame className="h-9 w-9 sm:h-10 sm:w-10 text-warning animate-pulse" />
                        <span className="text-xl sm:text-2xl font-bold text-warning font-mono">{streak.current}</span>
                        <span className="text-[10px] text-muted-foreground -mt-0.5">day streak</span>
                    </div>
                </div>
                {streak.isActiveToday && (
                    <p className="text-xs text-muted-foreground mt-3">
                        Your longest: <span className="text-foreground font-medium">{streak.longest} days</span> — keep it going!
                    </p>
                )}
            </CardContent>
        </Card>
    )
}


function XPLevelCard() {
    const user = useUserStore(state => state.user)
    if (!user) return null

    const xpPercent = Math.round((user.xpTotal / user.xpForNextLevel) * 100)

    return (
        <Card>
            <CardContent className="p-5 sm:p-6">
                <div className="flex items-center justify-between gap-2 mb-4">
                    <div className="flex items-center gap-2 min-w-0">
                        <Zap className="h-5 w-5 text-xp-gold shrink-0" />
                        <div className="min-w-0">
                            <span className="text-sm font-semibold">Level {user.level}</span>
                            <span className="text-xs text-muted-foreground ml-1.5">— {user.levelTitle}</span>
                        </div>
                    </div>
                    <Badge variant="secondary" className="bg-xp-gold/15 text-xp-gold text-xs font-mono shrink-0">
                        {user.xpTotal.toLocaleString()} XP
                    </Badge>
                </div>
                <div className="space-y-2">
                    <Progress value={xpPercent} className="h-2.5 bg-muted" />
                    <div className="flex justify-between text-[11px] text-muted-foreground">
                        <span>{user.xpTotal.toLocaleString()} / {user.xpForNextLevel.toLocaleString()} XP</span>
                        <span>{xpPercent}%</span>
                    </div>
                </div>
                <div className="flex items-center gap-4 mt-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1.5">
                        <span className="inline-block h-2 w-2 rounded-full bg-success" />
                        +{user.xpToday} XP today
                    </span>
                    <span className="flex items-center gap-1.5">
                        <span className="inline-block h-2 w-2 rounded-full bg-primary" />
                        +{user.xpThisWeek} XP this week
                    </span>
                </div>
            </CardContent>
        </Card>
    )
}


function WeeklyGoalTracker() {
    const weeklyGoal = useUserStore(state => state.weeklyGoal)

    const isToday = (index: number) => {
        const today = new Date().getDay()
        const todayIndex = today === 0 ? 6 : today - 1
        return index === todayIndex
    }

    return (
        <Card>
            <CardContent className="p-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-primary" />
                        <span className="text-sm font-semibold">Weekly Goal</span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                        {weeklyGoal.completed}/{weeklyGoal.target} tutorials
                    </span>
                </div>
                <div className="flex items-center justify-between gap-2 sm:gap-3">
                    {weeklyGoal.days.map((done, i) => (
                        <div key={i} className="flex flex-col items-center gap-1.5">
                            <div
                                className={`flex h-10 w-10 sm:h-11 sm:w-11 items-center justify-center rounded-full text-xs font-semibold transition-all
                  ${done
                                        ? 'bg-primary text-primary-foreground'
                                        : isToday(i)
                                            ? 'border-2 border-dashed border-primary/50 text-primary animate-pulse'
                                            : 'bg-muted text-muted-foreground'
                                    }`}
                            >
                                {done ? <CheckCircle2 className="h-4 w-4" /> : weeklyGoal.dayLabels[i]}
                            </div>
                            <span className={`text-[10px] ${isToday(i) ? 'text-primary font-semibold' : 'text-muted-foreground'}`}>
                                {weeklyGoal.dayLabels[i]}
                            </span>
                        </div>
                    ))}
                </div>
                <p className="text-xs text-muted-foreground mt-4 text-center">
                    {weeklyGoal.completed >= weeklyGoal.target
                        ? 'Weekly goal smashed!'
                        : `${weeklyGoal.target - weeklyGoal.completed} more to hit your goal!`
                    }
                </p>
            </CardContent>
        </Card>
    )
}


function MyCourses() {
    const courses = useUserStore(state => state.courses)

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold flex items-center gap-2">
                    <BookOpen className="h-4 w-4 text-primary" />
                    My Courses
                </h2>
                <button className="text-xs text-primary hover:text-primary/80 flex items-center gap-0.5 transition-colors">
                    See All <ChevronRight className="h-3 w-3" />
                </button>
            </div>
            <div className="flex gap-4 overflow-x-auto pb-2 -mx-1 px-1 snap-x snap-mandatory scrollbar-hide">
                {courses.map((course) => (
                    <Card key={course.id} className="min-w-[150px] sm:min-w-[170px] snap-start shrink-0 hover:border-primary/30 transition-colors cursor-pointer">
                        <CardContent className="p-4 sm:p-5">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted/50 mb-3">
                                {courseIconMap[course.title] || <Code className="h-5 w-5 text-muted-foreground" />}
                            </div>
                            <h3 className="text-sm font-semibold truncate">{course.title}</h3>
                            <p className="text-[11px] text-muted-foreground mt-1">
                                {course.completed}/{course.total} tutorials
                            </p>
                            <div className="flex items-center gap-2 mt-3">
                                <Progress
                                    value={course.progress}
                                    className={`h-1.5 flex-1 ${course.status === 'completed' ? '[&>div]:bg-success' : ''}`}
                                />
                                <span className="text-[11px] font-mono text-muted-foreground">
                                    {course.progress}%
                                </span>
                            </div>
                            {course.status === 'completed' && (
                                <Badge variant="secondary" className="bg-success/15 text-success text-[10px] mt-3 px-1.5 py-0 h-5 gap-1">
                                    <CheckCircle2 className="h-3 w-3" />
                                    Completed
                                </Badge>
                            )}
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    )
}


function AchievementsPreview() {
    const badges = useUserStore(state => state.badges)
    const earnedBadges = badges.filter(b => b.earned)
    const upcomingBadges = badges.filter(b => !b.earned && b.progress)

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
                <p className="text-[11px] text-muted-foreground uppercase tracking-wider mb-3">Recently Earned</p>
                <div className="flex gap-3 mb-5">
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
                                    <span className="ml-auto text-[11px] font-mono text-muted-foreground">{badge.progress}</span>
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
                <div className="space-y-3">
                    {MOCK_UPCOMING.map((event) => (
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
            </CardContent>
        </Card>
    )
}

// ===== MAIN DASHBOARD PAGE =====

export function Dashboard() {
    return (
        <div className="max-w-3xl mx-auto space-y-6">
            {/* Section 1 & 2: Greeting + XP side by side on desktop */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <GreetingBanner />
                <XPLevelCard />
            </div>

            {/* Section 3: Active Course Tracker */}
            <ActiveCourseTracker />

            {/* Section 4: Weekly Goal */}
            <WeeklyGoalTracker />

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
