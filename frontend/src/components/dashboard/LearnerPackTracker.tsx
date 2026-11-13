import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Check, CheckCircle2, ChevronDown, Heart } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Skeleton } from '@/components/ui/skeleton'
import api from '@/lib/axios'
import { getNextStep, getWeekTopic, isLinuxCourse, isTutorialCompleted, tutorialPath } from '@/lib/learnerPack'
import { cn } from '@/lib/utils'
import { useLearnerPackStore } from '@/store/learnerPackStore'
import { useUserStore } from '@/store/userStore'
import type { HabitLogCheckinItem, HabitMilestone, LearnerPackOverviewTutorial } from '@/types'
import { CourseMaterialsCard } from './CourseMaterialsCard'
import { ProgressRing } from './ProgressRing'
import { TutorialRow } from './TutorialRow'

type HabitLogs = Record<string, HabitLogCheckinItem[]>

const tutorialRangeLabel = (tutorials: LearnerPackOverviewTutorial[]): string =>
    tutorials.length === 1
        ? `Tutorial ${tutorials[0].number}`
        : `Tutorials ${tutorials[0].number}–${tutorials[tutorials.length - 1].number}`

export const LearnerPackTracker: React.FC = () => {
    const activeCourseId = useUserStore(state => state.activeCourseId)
    const overview = useLearnerPackStore(state => (state.overviewCourseId === activeCourseId ? state.overview : null))
    const isLoadingOverview = useLearnerPackStore(state => state.isLoadingOverview)
    const fetchOverview = useLearnerPackStore(state => state.fetchOverview)

    const [habitLogs, setHabitLogs] = useState<HabitLogs>({})
    const [openWeeks, setOpenWeeks] = useState<Record<number, boolean>>({})
    const [isCheckingIn, setIsCheckingIn] = useState(false)

    const loadHabitLogs = useCallback(async (courseId: string): Promise<HabitLogs> => {
        const res = await api.get<{ logs?: HabitLogs }>(`/api/learner-pack/habit-logs/${courseId}`)
        return res.data.logs || {}
    }, [])

    useEffect(() => {
        if (!activeCourseId) return
        let isCancelled = false
        void fetchOverview(activeCourseId).then((ok) => {
            if (!ok && !isCancelled) toast.error('Could not load course curriculum.')
        })
        loadHabitLogs(activeCourseId)
            .then((logs) => {
                if (!isCancelled) setHabitLogs(logs)
            })
            .catch(() => undefined)
        return () => {
            isCancelled = true
        }
    }, [activeCourseId, fetchOverview, loadHabitLogs])

    const handleHabitCheckin = async (logType: string, dayNumber: number): Promise<void> => {
        if (!activeCourseId) return
        try {
            setIsCheckingIn(true)
            await api.post('/api/learner-pack/habit-logs/checkin', {
                course_id: activeCourseId,
                log_type: logType,
                day_number: dayNumber,
                checkin_date: new Date().toISOString().split('T')[0],
            })
            toast.success(`Day ${dayNumber} check-in recorded!`)
            setHabitLogs(await loadHabitLogs(activeCourseId))
        } catch {
            toast.error('Failed to record habit check-in.')
        } finally {
            setIsCheckingIn(false)
        }
    }

    if (!overview) {
        if (!isLoadingOverview) return null
        return (
            <Card aria-busy="true">
                <CardContent className="p-8 space-y-4">
                    <Skeleton className="h-6 w-1/3" />
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-32 w-full rounded-xl" />
                </CardContent>
            </Card>
        )
    }

    const courseId = overview.courseId
    const totalTuts = overview.tutorials.length
    const completedTuts = overview.tutorials.filter(tutorial => isTutorialCompleted(courseId, tutorial)).length
    const progressPercent = totalTuts > 0 ? Math.round((completedTuts / totalTuts) * 100) : 0

    const milestonesByWeek: Record<number, HabitMilestone> = {}
    overview.habitMilestones.forEach((milestone) => {
        milestonesByWeek[milestone.week] = milestone
    })

    const nextIncompleteTutorial = overview.tutorials.find(tutorial => !isTutorialCompleted(courseId, tutorial))
    const nextStep = nextIncompleteTutorial ? getNextStep(courseId, nextIncompleteTutorial) : null
    const allCompleted = totalTuts > 0 && !nextIncompleteTutorial
    const currentWeek = nextIncompleteTutorial?.week

    return (
        <div className="space-y-6">
            <Card className="border border-border/80 bg-card shadow-xs overflow-hidden py-0 gap-0">
                <div className="h-1 bg-gradient-to-r from-primary via-primary-light to-primary/20" aria-hidden="true" />
                <CardContent className="p-5 sm:p-7 flex items-center gap-4 sm:gap-6">
                    <ProgressRing
                        percent={progressPercent}
                        label={`${completedTuts} of ${totalTuts} tutorials completed`}
                    />
                    <div className="min-w-0 space-y-1">
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                            Your course
                        </p>
                        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground font-sans truncate">
                            {overview.title}
                        </h2>
                        <p className="text-xs sm:text-sm text-muted-foreground">
                            <span className="font-mono font-semibold text-foreground">{completedTuts}</span> of{' '}
                            <span className="font-mono font-semibold text-foreground">{totalTuts}</span> tutorials completed
                            <span className="hidden sm:inline"> · {overview.totalWeeks}-week curriculum</span>
                        </p>
                    </div>
                </CardContent>

                {nextIncompleteTutorial && nextStep && (
                    <div className="border-t border-border/80 bg-primary/[0.04] px-5 sm:px-7 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div className="space-y-1 min-w-0">
                            <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium flex-wrap">
                                <span className="inline-flex items-center gap-1.5 font-semibold text-primary">
                                    <span className="size-1.5 rounded-full bg-primary" aria-hidden="true" />
                                    Up next
                                </span>
                                <span aria-hidden="true">·</span>
                                <span>Week {nextIncompleteTutorial.week}</span>
                                <span aria-hidden="true">·</span>
                                <span className="text-foreground/90">{nextStep.stepLabel}</span>
                            </div>
                            <h3 className="text-base sm:text-lg font-bold text-foreground truncate">
                                <span className="font-mono text-muted-foreground mr-1.5">#{nextIncompleteTutorial.number}</span>
                                {nextIncompleteTutorial.title}
                            </h3>
                        </div>
                        <Button
                            asChild
                            size="lg"
                            className="font-semibold text-sm gap-2 shrink-0 w-full sm:w-auto min-h-11 transition duration-200 ease-in-out"
                        >
                            <Link to={tutorialPath(courseId, nextIncompleteTutorial.number, nextStep.step)}>
                                {nextStep.isStarted ? 'Continue' : 'Start lesson'}
                                <ArrowRight className="size-4" />
                            </Link>
                        </Button>
                    </div>
                )}

                {allCompleted && (
                    <div className="border-t border-success/25 bg-success/[0.05] px-5 sm:px-7 py-4 flex items-center gap-3">
                        <CheckCircle2 className="size-5 text-success shrink-0" />
                        <div>
                            <h3 className="text-sm font-bold text-foreground">All tutorials completed</h3>
                            <p className="text-xs text-muted-foreground">You have finished all {totalTuts} tutorials in this course.</p>
                        </div>
                    </div>
                )}
            </Card>

            <CourseMaterialsCard urls={overview.materials} showUnzipHint={isLinuxCourse(courseId)} />

            <ol className="space-y-3">
                {Array.from({ length: overview.totalWeeks }, (_, index) => index + 1).map((weekNum) => {
                    const tutorials = overview.tutorials.filter(tutorial => tutorial.week === weekNum)
                    const milestone = milestonesByWeek[weekNum]
                    const completedInWeek = tutorials.filter(tutorial => isTutorialCompleted(courseId, tutorial)).length
                    const isWeekCompleted = tutorials.length > 0 && completedInWeek === tutorials.length
                    const isCurrentWeek = nextIncompleteTutorial?.week === weekNum
                    const isWeekOpen = openWeeks[weekNum] ?? true
                    const isUpcoming = currentWeek !== undefined && weekNum > currentWeek && !isWeekCompleted
                    const weekPercent = tutorials.length > 0 ? Math.round((completedInWeek / tutorials.length) * 100) : 0

                    return (
                        <li key={weekNum} className="relative pl-12">
                            {weekNum < overview.totalWeeks && (
                                <span
                                    aria-hidden="true"
                                    className={cn(
                                        'absolute left-[17px] top-[58px] -bottom-[26px] w-0.5 rounded-full transition-colors duration-500 ease-in-out',
                                        isWeekCompleted ? 'bg-success' : 'bg-border'
                                    )}
                                />
                            )}
                            <div className="absolute left-0 top-[18px] rounded-full bg-background">
                                <ProgressRing
                                    percent={weekPercent}
                                    size={36}
                                    strokeWidth={3}
                                    label={`Week ${weekNum}: ${completedInWeek} of ${tutorials.length} tutorials completed`}
                                >
                                    {isWeekCompleted ? (
                                        <Check className="size-4 text-success" strokeWidth={3} />
                                    ) : (
                                        <span className={cn('text-[10px]', isCurrentWeek ? 'text-primary' : isUpcoming ? 'text-muted-foreground' : 'text-foreground')}>
                                            W{weekNum}
                                        </span>
                                    )}
                                </ProgressRing>
                            </div>
                        <Card
                            className={cn(
                                'relative border py-0 gap-0 overflow-hidden transition-all duration-200 ease-in-out',
                                isWeekCompleted
                                    ? 'border-success/30 bg-success/[0.02]'
                                    : isCurrentWeek
                                        ? 'border-primary/40 shadow-sm'
                                        : 'border-border hover:border-primary/25'
                            )}
                        >
                            {isCurrentWeek && <span aria-hidden="true" className="absolute inset-y-0 left-0 w-1 bg-primary" />}
                            <Collapsible
                                open={isWeekOpen}
                                onOpenChange={(open) => setOpenWeeks(prev => ({ ...prev, [weekNum]: open }))}
                            >
                                <CollapsibleTrigger asChild>
                                    <button
                                        type="button"
                                        className={cn(
                                            'w-full flex items-center justify-between gap-3 p-4 text-left cursor-pointer transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring',
                                            isCurrentWeek ? 'bg-primary/[0.05] hover:bg-primary/[0.08]' : 'hover:bg-muted/30'
                                        )}
                                    >
                                        <div className="flex items-center gap-3 min-w-0">
                                            <div className="min-w-0">
                                                <h3 className={cn('text-sm font-semibold', isUpcoming ? 'text-foreground/70' : 'text-foreground')}>
                                                    {getWeekTopic(weekNum, courseId)}
                                                </h3>
                                                <p className="text-xs text-muted-foreground">
                                                    {tutorials.length > 0 ? (
                                                        <>
                                                            {tutorialRangeLabel(tutorials)}
                                                            <span aria-hidden="true"> · </span>
                                                            <span className="font-mono">{completedInWeek}</span> of{' '}
                                                            <span className="font-mono">{tutorials.length}</span> completed
                                                        </>
                                                    ) : (
                                                        'Milestone week'
                                                    )}
                                                    {isCurrentWeek && <span className="sm:hidden text-primary font-semibold"> · Current week</span>}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 shrink-0">
                                            {isCurrentWeek && (
                                                <Badge variant="outline" className="hidden sm:inline-flex text-[11px] font-semibold bg-primary/10 text-primary border-primary/25">
                                                    Current week
                                                </Badge>
                                            )}
                                            {milestone && (
                                                <Badge variant="secondary" className="hidden sm:inline-flex text-[11px] bg-warning/10 text-warning border border-warning/20">
                                                    {milestone.title}
                                                </Badge>
                                            )}
                                            <ChevronDown className={cn('size-4 text-muted-foreground transition-transform duration-200 ease-in-out', isWeekOpen && 'rotate-180')} />
                                        </div>
                                    </button>
                                </CollapsibleTrigger>

                                <CollapsibleContent className="px-4 pb-4 pt-1 space-y-3">
                                    {milestone && (
                                        <div className="p-3.5 rounded-lg bg-warning/5 border border-warning/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                                            <div className="flex items-center gap-2.5">
                                                <div className="p-2 rounded-full bg-warning/10 text-warning">
                                                    <Heart className="size-4" />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-semibold text-foreground">{milestone.title}</p>
                                                    <p className="text-[11px] text-muted-foreground">
                                                        Daily physical notebook log with dated Spoken Social check-in.
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-1.5 flex-wrap">
                                                {Array.from({ length: milestone.days }, (_, index) => index + 1).map((day) => {
                                                    const isChecked = (habitLogs[milestone.logType] || []).some(checkin => checkin.dayNumber === day)
                                                    return (
                                                        <button
                                                            key={day}
                                                            type="button"
                                                            onClick={() => handleHabitCheckin(milestone.logType, day)}
                                                            disabled={isChecked || isCheckingIn}
                                                            title={isChecked ? `Day ${day} checked in` : `Check in for day ${day}`}
                                                            className={cn(
                                                                'inline-flex items-center justify-center gap-1 min-h-11 min-w-11 sm:min-h-8 sm:min-w-0 px-2.5 font-mono text-[11px] font-medium rounded-md transition-all duration-200 ease-in-out',
                                                                isChecked
                                                                    ? 'bg-success/15 text-success cursor-default'
                                                                    : 'bg-muted text-muted-foreground hover:bg-primary/20 hover:text-primary cursor-pointer'
                                                            )}
                                                        >
                                                            {isChecked && <Check className="size-3" />}
                                                            D{day}
                                                        </button>
                                                    )
                                                })}
                                            </div>
                                        </div>
                                    )}

                                    {tutorials.map(tutorial => (
                                        <TutorialRow
                                            key={tutorial.id}
                                            courseId={courseId}
                                            tutorial={tutorial}
                                            isUpNext={tutorial.id === nextIncompleteTutorial?.id}
                                        />
                                    ))}
                                </CollapsibleContent>
                            </Collapsible>
                        </Card>
                        </li>
                    )
                })}
            </ol>
        </div>
    )
}
