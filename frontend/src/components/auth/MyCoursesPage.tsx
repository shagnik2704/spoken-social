import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueries } from '@tanstack/react-query'
import { ArrowRight, BookOpen, CheckCircle2, Repeat } from 'lucide-react'
import api from '@/lib/axios'
import { getNextStep, isTutorialCompleted } from '@/lib/learnerPack'
import { cn } from '@/lib/utils'
import { CourseIcon } from '@/components/CourseIcon'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useUserStore } from '@/store/userStore'
import type { LearnerPackOverview } from '@/types'

interface Batch {
    id: string
    name: string
    status: string
    is_active: boolean
    startDate: string | null
    endDate: string | null
}

interface Course {
    id: string
    title: string
    batches: Batch[]
}

interface CourseProgress {
    completed: number
    total: number
    upNext: { number: number; title: string; stepLabel: string; isStarted: boolean } | null
}

const mergeEnrollments = (rows: Course[]): Course[] => {
    const byId = new Map<string, Course>()
    for (const row of rows) {
        const existing = byId.get(row.id)
        const batches = row.batches ?? []
        if (existing) {
            existing.batches.push(...batches.filter(batch => !existing.batches.some(b => b.id === batch.id)))
        } else {
            byId.set(row.id, { id: row.id, title: row.title, batches: [...batches] })
        }
    }
    return [...byId.values()]
}

const defaultBatch = (course: Course): Batch | null =>
    course.batches.find(batch => batch.is_active) ?? course.batches[0] ?? null

const formatMonth = (iso: string): string =>
    new Date(iso).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })

const statusLabel = (batch: Batch | null): string | null => {
    if (!batch) return 'No batch yet'
    if (batch.startDate && new Date(batch.startDate) > new Date()) return `Starts ${formatMonth(batch.startDate)}`
    if (!batch.is_active) return 'Ended'
    return null
}

const summarise = (overview: LearnerPackOverview): CourseProgress => {
    const courseId = overview.courseId
    const completed = overview.tutorials.filter(tutorial => isTutorialCompleted(courseId, tutorial)).length
    const next = overview.tutorials.find(tutorial => !isTutorialCompleted(courseId, tutorial))
    const step = next ? getNextStep(courseId, next) : null
    return {
        completed,
        total: overview.tutorials.length,
        upNext: next && step ? { number: next.number, title: next.title, stepLabel: step.stepLabel, isStarted: step.isStarted } : null,
    }
}

const ProgressRing: React.FC<{ percent: number }> = ({ percent }) => {
    const radius = 20
    const circumference = 2 * Math.PI * radius
    return (
        <div className="relative size-14 shrink-0" role="img" aria-label={`${percent}% complete`}>
            <svg viewBox="0 0 48 48" className="size-14 -rotate-90">
                <circle cx="24" cy="24" r={radius} fill="none" strokeWidth="4" className="stroke-primary/10" />
                <circle
                    cx="24"
                    cy="24"
                    r={radius}
                    fill="none"
                    strokeWidth="4"
                    strokeLinecap="round"
                    className={cn('transition-[stroke-dashoffset] duration-700 ease-out', percent >= 100 ? 'stroke-success' : 'stroke-primary')}
                    strokeDasharray={circumference}
                    strokeDashoffset={circumference * (1 - percent / 100)}
                />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center font-mono text-xs font-bold text-foreground">{percent}%</span>
        </div>
    )
}

interface CourseCardProps {
    course: Course
    progress: CourseProgress | null
    isLoadingProgress: boolean
    isLastOpened: boolean
    onOpen: (course: Course, batch: Batch | null) => void
}

const CourseCard: React.FC<CourseCardProps> = ({ course, progress, isLoadingProgress, isLastOpened, onOpen }) => {
    const [batchId, setBatchId] = useState<string | null>(defaultBatch(course)?.id ?? null)
    const batch = course.batches.find(item => item.id === batchId) ?? null
    const status = statusLabel(batch)
    const hasTutorials = Boolean(progress && progress.total > 0)
    const percent = progress && progress.total > 0 ? Math.round((progress.completed / progress.total) * 100) : 0
    const isComplete = hasTutorials && !progress?.upNext
    const actionLabel = !hasTutorials ? 'Open course' : isComplete ? 'Review course' : progress?.upNext?.isStarted || percent > 0 ? 'Continue' : 'Start course'

    return (
        <article
            className={cn(
                'group relative flex flex-col gap-4 p-5 rounded-2xl border bg-card transition-all duration-300 ease-in-out hover:scale-[1.01] hover:shadow-md focus-within:ring-2 focus-within:ring-ring',
                isLastOpened ? 'border-primary/50 shadow-sm ring-1 ring-primary/20' : 'border-border hover:border-primary/40'
            )}
        >
            <div className="flex items-start gap-3.5">
                <span className="size-11 shrink-0 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                    <CourseIcon title={course.title} className="size-5" />
                </span>
                <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-1.5">
                        {isLastOpened && (
                            <span className="inline-flex items-center h-5 px-2 rounded-full bg-primary/10 text-[10px] font-semibold uppercase tracking-wider text-primary">
                                Last opened
                            </span>
                        )}
                        {status && (
                            <span className="inline-flex items-center h-5 px-2 rounded-full bg-muted text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                                {status}
                            </span>
                        )}
                    </div>
                    <h2 className="text-base sm:text-lg font-bold leading-snug tracking-tight text-foreground">{course.title}</h2>
                </div>
                {hasTutorials && progress && <ProgressRing percent={percent} />}
            </div>

            <div className="min-h-11">
                {isLoadingProgress ? (
                    <div className="space-y-2" aria-hidden="true">
                        <Skeleton className="h-3 w-24" />
                        <Skeleton className="h-4 w-3/4" />
                    </div>
                ) : hasTutorials && progress ? (
                    isComplete ? (
                        <p className="flex items-center gap-1.5 text-sm font-medium text-success">
                            <CheckCircle2 className="size-4" />
                            All <span className="font-mono">{progress.total}</span> tutorials complete
                        </p>
                    ) : progress.upNext ? (
                        <div className="space-y-0.5 min-w-0">
                            <p className="text-[11px] font-semibold uppercase tracking-wider text-teal">
                                Up next · {progress.upNext.stepLabel}
                            </p>
                            <p className="text-sm font-medium text-foreground truncate">
                                <span className="font-mono text-muted-foreground">T{progress.upNext.number}</span> {progress.upNext.title}
                            </p>
                            <p className="text-xs text-muted-foreground">
                                <span className="font-mono font-semibold text-foreground">{progress.completed}</span> of{' '}
                                <span className="font-mono">{progress.total}</span> tutorials done
                            </p>
                        </div>
                    ) : null
                ) : (
                    <p className="text-sm text-muted-foreground">Open the course dashboard to get started.</p>
                )}
            </div>

            <div className="mt-auto flex flex-col gap-2">
                {course.batches.length > 1 && (
                    <label className="relative z-10 w-full">
                        <span className="sr-only">Batch for {course.title}</span>
                        <select
                            value={batchId ?? ''}
                            onChange={(event) => setBatchId(event.target.value)}
                            className="w-full min-h-11 rounded-lg border border-border bg-background px-3 text-sm text-foreground cursor-pointer transition duration-200 ease-in-out hover:border-primary/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        >
                            {course.batches.map(item => (
                                <option key={item.id} value={item.id}>
                                    {item.name}{item.is_active ? '' : ' (ended)'}
                                </option>
                            ))}
                        </select>
                    </label>
                )}
                <Button
                    onClick={() => onOpen(course, batch)}
                    variant={isLastOpened ? 'default' : 'outline'}
                    className={cn(
                        'min-h-11 gap-1.5 font-semibold cursor-pointer transition duration-200 ease-in-out after:absolute after:inset-0 after:rounded-2xl focus-visible:ring-0',
                        'self-end'
                    )}
                    aria-label={`${actionLabel}: ${course.title}`}
                >
                    {actionLabel}
                    <ArrowRight className="size-4 transition-transform duration-200 group-hover:translate-x-0.5" />
                </Button>
            </div>
        </article>
    )
}

export function MyCoursesPage() {
    const [courses, setCourses] = useState<Course[] | null>(null)
    const [loadFailed, setLoadFailed] = useState(false)

    const user = useUserStore(state => state.user)
    const programmes = useUserStore(state => state.programmes)
    const activeCourseId = useUserStore(state => state.activeCourseId)
    const setActiveCourse = useUserStore(state => state.setActiveCourse)
    const setActiveBatch = useUserStore(state => state.setActiveBatch)
    const activeProgrammeId = useUserStore(state => state.activeProgrammeId)
    const activeProgrammeName = useUserStore(state => state.activeProgrammeName)
    const setActiveProgramme = useUserStore(state => state.setActiveProgramme)
    const navigate = useNavigate()
    const isStudent = (user?.role ?? 'student') === 'student'

    const enterDashboard = useCallback((course: Course, batch: Batch | null, replace = false) => {
        setActiveCourse(course.id)
        setActiveBatch(batch?.id ?? null, batch?.is_active ?? true)

        if (user?.role === 'admin') navigate('/admin', { replace })
        else if (user?.role === 'coordinator') navigate('/coordinator', { replace })
        else navigate('/dashboard', { replace })
    }, [navigate, setActiveBatch, setActiveCourse, user?.role])

    useEffect(() => {
        let isCancelled = false
        const endpoint = activeProgrammeId ? `/api/courses/me?programme_id=${activeProgrammeId}` : '/api/courses/me'
        api.get<Course[]>(endpoint)
            .then(res => {
                if (isCancelled) return
                const fetched = mergeEnrollments(res.data || [])
                if (fetched.length === 1 && fetched[0].batches.length <= 1) {
                    enterDashboard(fetched[0], fetched[0].batches[0] ?? null, true)
                    return
                }
                setCourses(fetched)
            })
            .catch(() => {
                if (!isCancelled) setLoadFailed(true)
            })
        return () => {
            isCancelled = true
        }
    }, [user, activeProgrammeId, enterDashboard])

    const progressQueries = useQueries({
        queries: (isStudent ? courses ?? [] : []).map(course => ({
            queryKey: ['learner-pack-overview', course.id],
            queryFn: async () => (await api.get<LearnerPackOverview>(`/api/learner-pack/course/${course.id}/overview`)).data,
            staleTime: 0,
            select: summarise,
        })),
    })

    const sortedCourses = [...(courses ?? [])].sort((a, b) => Number(b.id === activeCourseId) - Number(a.id === activeCourseId))

    return (
        <div className="max-w-5xl mx-auto py-2 sm:py-6 space-y-6">
            <header className="flex items-start sm:items-end justify-between gap-3">
                <div className="space-y-1 min-w-0">
                    <p className="text-xs font-semibold uppercase tracking-wider text-primary">
                        {activeProgrammeName || 'Your programme'}
                    </p>
                    <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-sans">My courses</h1>
                    {user?.displayName && (
                        <p className="text-sm text-muted-foreground">Welcome back, {user.displayName}. Pick up where you left off.</p>
                    )}
                </div>
                {programmes.length > 1 && (
                    <Button
                        variant="outline"
                        aria-label="Switch programme"
                        className="shrink-0 min-h-11 gap-1.5 px-3 cursor-pointer transition duration-200 ease-in-out"
                        onClick={() => {
                            setActiveProgramme('', '')
                            navigate('/programmes')
                        }}
                    >
                        <Repeat className="size-4" />
                        <span className="sm:hidden">Switch</span>
                        <span className="hidden sm:inline">Switch programme</span>
                    </Button>
                )}
            </header>

            {loadFailed ? (
                <div className="p-8 rounded-2xl border border-border bg-card text-center space-y-2">
                    <p className="font-semibold text-foreground">Couldn't load your courses</p>
                    <p className="text-sm text-muted-foreground">Check your connection and refresh the page.</p>
                </div>
            ) : courses === null ? (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true">
                    {[0, 1, 2].map(index => <Skeleton key={index} className="h-56 rounded-2xl" />)}
                </div>
            ) : courses.length === 0 ? (
                <div className="py-14 px-6 rounded-2xl border border-dashed border-border bg-card/50 flex flex-col items-center text-center gap-3">
                    <BookOpen className="size-8 text-muted-foreground/50" />
                    <p className="font-semibold text-foreground">No courses in {activeProgrammeName || 'this programme'} yet</p>
                    <p className="text-sm text-muted-foreground max-w-sm">Once you're enrolled in a course it will appear here.</p>
                </div>
            ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {sortedCourses.map(course => {
                        const query = isStudent ? progressQueries[courses.indexOf(course)] : undefined
                        return (
                            <CourseCard
                                key={course.id}
                                course={course}
                                progress={query?.data ?? null}
                                isLoadingProgress={Boolean(query?.isPending)}
                                isLastOpened={course.id === activeCourseId}
                                onOpen={enterDashboard}
                            />
                        )
                    })}
                </div>
            )}
        </div>
    )
}
