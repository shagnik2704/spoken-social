import { useEffect } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
    buildCourseDocuments,
    coursePath,
    getActivityLabel,
    getGuideVideos,
    getWeekTopic,
    hasCourseContentPage,
    isSetupTutorial,
    spokenTutorialWatchUrl,
    tutorialPath,
    type TutorialStepId,
} from '@/lib/learnerPack'
import { useLearnerPackStore } from '@/store/learnerPackStore'
import type { LearnerPackOverviewTutorial } from '@/types'
import { GuideVideoLink, MaterialLink } from './CourseMaterialsCard'

const CHIP_CLASS =
    'inline-flex items-center gap-1 min-h-11 sm:min-h-8 px-3 rounded-md border border-border/70 bg-card text-xs font-medium text-foreground hover:border-primary/40 hover:bg-primary/[0.04] hover:text-primary transition duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'

interface SectionProps {
    title: string
    hint?: string
    children: React.ReactNode
}

const Section: React.FC<SectionProps> = ({ title, hint, children }) => (
    <Card className="border border-border/80 bg-card shadow-xs py-0 gap-0">
        <div className="px-4 sm:px-5 pt-4 flex items-baseline justify-between gap-3">
            <h2 className="text-sm font-semibold text-foreground">{title}</h2>
            {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
        </div>
        <div className="p-3 sm:p-4">{children}</div>
    </Card>
)

interface TutorialLinksRowProps {
    courseId: string
    tutorial: LearnerPackOverviewTutorial
}

const TutorialLinksRow: React.FC<TutorialLinksRowProps> = ({ courseId, tutorial }) => {
    const watchUrl = spokenTutorialWatchUrl(tutorial.videoUrl)
    const steps: { step: TutorialStepId; label: string }[] = [
        { step: 'video', label: 'Video' },
        { step: 'reading', label: 'Reading' },
        { step: 'activity', label: getActivityLabel(courseId, tutorial.number) },
    ]
    if (!isSetupTutorial(courseId, tutorial.number)) steps.push({ step: 'quiz', label: 'Quiz' })

    return (
        <li className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 py-3 first:pt-0 last:pb-0">
            <div className="flex items-baseline gap-3 min-w-0 flex-1">
                <span className="w-6 shrink-0 text-right font-mono text-sm font-semibold text-muted-foreground">{tutorial.number}</span>
                <span className="text-sm font-medium text-foreground">{tutorial.title}</span>
            </div>
            <div className="flex flex-wrap gap-1.5 pl-9 sm:pl-0">
                {watchUrl && (
                    <a href={watchUrl} target="_blank" rel="noopener noreferrer" className={CHIP_CLASS} title="Watch on spoken-tutorial.org">
                        Spoken Tutorial
                        <ExternalLink className="size-3 text-muted-foreground" />
                    </a>
                )}
                {steps.map(({ step, label }) => (
                    <Link key={step} to={tutorialPath(courseId, tutorial.number, step)} className={CHIP_CLASS}>
                        {label}
                    </Link>
                ))}
            </div>
        </li>
    )
}

const CourseContentPage: React.FC = () => {
    const { courseId = '' } = useParams<{ courseId: string }>()
    const overview = useLearnerPackStore(state => (state.overviewCourseId === courseId ? state.overview : null))
    const fetchOverview = useLearnerPackStore(state => state.fetchOverview)

    useEffect(() => {
        if (hasCourseContentPage(courseId)) void fetchOverview(courseId)
    }, [courseId, fetchOverview])

    if (!hasCourseContentPage(courseId)) return <Navigate to={coursePath(courseId)} replace />

    const documents = buildCourseDocuments(courseId, overview?.materials)
    const guideVideos = getGuideVideos(courseId)
    const weeks = new Map<number, LearnerPackOverviewTutorial[]>()
    overview?.tutorials.forEach((tutorial) => {
        weeks.set(tutorial.week, [...(weeks.get(tutorial.week) ?? []), tutorial])
    })

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            <div className="space-y-2">
                <Link
                    to={coursePath(courseId)}
                    className="inline-flex items-center gap-1.5 min-h-11 text-xs font-semibold text-muted-foreground hover:text-primary transition duration-200 ease-in-out"
                >
                    <ArrowLeft className="size-3.5" />
                    Back to the course
                </Link>
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                    {overview?.title ?? 'Course'}: all course content
                </h1>
                <p className="text-sm text-muted-foreground">
                    Every document, video and tutorial in this course, on one page.
                    {overview && (
                        <>
                            {' '}
                            <span className="font-mono font-semibold text-foreground">{overview.tutorials.length}</span> tutorials over{' '}
                            <span className="font-mono font-semibold text-foreground">{overview.totalWeeks}</span> weeks.
                        </>
                    )}
                </p>
            </div>

            <Section title="Documents" hint="Opens in a new tab">
                <div className="grid gap-2 sm:grid-cols-2">
                    {documents.map((material) => <MaterialLink key={material.key} material={material} />)}
                </div>
            </Section>

            {guideVideos.length > 0 && (
                <Section title="How to learn on this course" hint="Spoken Tutorial videos">
                    <div className="grid gap-2 sm:grid-cols-2">
                        {guideVideos.map((video) => <GuideVideoLink key={video.key} video={video} />)}
                    </div>
                </Section>
            )}

            <Section title="All tutorials" hint="By week">
                {overview ? (
                    <div className="space-y-5">
                        {[...weeks.entries()].map(([week, tutorials]) => (
                            <section key={week} aria-labelledby={`week-${week}`} className="space-y-3">
                                <h3 id={`week-${week}`} className="flex items-baseline gap-2 border-b border-border/70 pb-2 text-xs">
                                    <span className="font-mono font-semibold uppercase tracking-wider text-primary">Week {week}</span>
                                    <span className="text-muted-foreground">{getWeekTopic(week, courseId)}</span>
                                </h3>
                                <ul className="divide-y divide-border/50">
                                    {tutorials.map((tutorial) => (
                                        <TutorialLinksRow key={tutorial.id} courseId={courseId} tutorial={tutorial} />
                                    ))}
                                </ul>
                            </section>
                        ))}
                    </div>
                ) : (
                    <div className="space-y-3" aria-busy="true">
                        <Skeleton className="h-4 w-1/3" />
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-10 w-full" />
                    </div>
                )}
            </Section>
        </div>
    )
}

export default CourseContentPage
