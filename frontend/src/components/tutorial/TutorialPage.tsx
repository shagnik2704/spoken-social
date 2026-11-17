import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, ChevronLeft, ChevronRight, Download, ExternalLink, MessageSquarePlus, Zap } from 'lucide-react'
import { CelebrationModal } from '@/components/dashboard/CelebrationModal'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useSyncActiveCourse } from '@/hooks/useSyncActiveCourse'
import {
    coursePath,
    getActivityLabel,
    getForumAskUrl,
    getForumCategoryUrl,
    getNextStep,
    getStepXp,
    getTutorialXp,
    getTutorialXpFlags,
    getWeekTopic,
    isDone,
    isLinuxCourse,
    isSetupTutorial,
    isTutorialStepId,
    QUIZ_PASS_SCORE,
    tutorialPath,
    type TutorialStepId,
    type XpFlag,
    type XpFlags,
} from '@/lib/learnerPack'
import { useLearnerPackStore } from '@/store/learnerPackStore'
import type { LearnerPackOverview, LearnerPackOverviewTutorial } from '@/types'
import { AssignmentStep } from './steps/AssignmentStep'
import { QuizStep } from './steps/QuizStep'
import { ReadingStep } from './steps/ReadingStep'
import { ReflectionActivityStep } from './steps/ReflectionActivityStep'
import { SetupVerificationStep } from './steps/SetupVerificationStep'
import { TerminalLabStep } from './steps/TerminalLabStep'
import { VideoStep } from './steps/VideoStep'
import { TutorialResources } from './TutorialResources'
import { TutorialStepNav, type TutorialStep } from './TutorialStepNav'
import type { TutorialNav, TutorialStepProps } from './types'
import { useTutorialWorkspace } from './useTutorialWorkspace'

const ACTIVITY_SHORT_LABELS: Record<string, string> = {
    'Activity & reflection': 'Activity',
    'Assignment': 'Assignment',
}

const PageMessage: React.FC<{ title: string; body: string; backTo: string }> = ({ title, body, backTo }) => (
    <div className="max-w-lg mx-auto mt-10 p-6 sm:p-8 rounded-xl bg-card border border-border text-center space-y-4">
        <div className="space-y-1.5">
            <h1 className="text-lg font-bold text-foreground">{title}</h1>
            <p className="text-sm text-muted-foreground">{body}</p>
        </div>
        <Button asChild variant="outline" className="min-h-11">
            <Link to={backTo}>
                <ArrowLeft className="size-4" />
                Back to course
            </Link>
        </Button>
    </div>
)

const PageSkeleton: React.FC = () => (
    <div className="max-w-5xl mx-auto space-y-5" aria-busy="true">
        <Skeleton className="h-9 w-40" />
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="aspect-video w-full max-w-4xl mx-auto rounded-xl" />
    </div>
)

const ActivityStep: React.FC<TutorialStepProps> = (props) => {
    if (props.nav.isSetup) return <SetupVerificationStep {...props} />
    if (props.nav.isLinux) return <TerminalLabStep {...props} />
    return <ReflectionActivityStep {...props} />
}

const STEP_COMPONENTS: Record<TutorialStepId, React.FC<TutorialStepProps>> = {
    video: VideoStep,
    reading: ReadingStep,
    activity: ActivityStep,
    assignment: AssignmentStep,
    quiz: QuizStep,
}

interface TutorialWorkspaceViewProps {
    overview: LearnerPackOverview
    tutorial: LearnerPackOverviewTutorial
    step: TutorialStepId
}

const TutorialWorkspaceView: React.FC<TutorialWorkspaceViewProps> = ({ overview, tutorial, step }) => {
    const navigate = useNavigate()
    const topRef = useRef<HTMLDivElement>(null)
    const courseId = overview.courseId
    const workspace = useTutorialWorkspace(tutorial.id, courseId)
    const { detail } = workspace

    useEffect(() => {
        topRef.current?.scrollIntoView({ block: 'start' })
    }, [step])

    const isLinux = isLinuxCourse(courseId)
    const isSetup = isSetupTutorial(courseId, tutorial.number)
    const progress = tutorial.userProgress
    const activityLabel = getActivityLabel(courseId, tutorial.number)
    const hasAssignment = detail ? Boolean(detail.assignmentInstructions || detail.assignmentUrl) : Boolean(tutorial.hasAssignment)
    const hasQuiz = detail ? detail.quiz.questions.length > 0 : !isSetup
    const isLessonDone = detail ? isDone(detail.userTutorial.watched) : progress.watched
    const codeFilesUrl = detail?.codeFilesUrl
    const forumCategory = detail?.forumCategory ?? overview.forumCategory
    const askForumUrl = getForumAskUrl({
        courseId,
        forumCategory,
        courseTitle: overview.title,
        tutorialTitle: tutorial.title,
        videoPositionSeconds: workspace.videoPositionSeconds,
    })
    const browseForumUrl = getForumCategoryUrl(forumCategory, overview.title)

    const steps: TutorialStep[] = [
        { id: 'video', label: 'Watch video', shortLabel: 'Watch', done: isLessonDone },
        { id: 'reading', label: 'Reading notes', shortLabel: 'Read', done: isLessonDone },
        {
            id: 'activity',
            label: activityLabel,
            shortLabel: ACTIVITY_SHORT_LABELS[activityLabel] ?? activityLabel,
            done: detail ? Boolean(detail.userReflection) || isDone(detail.userTutorial.minitaskOpted) : progress.reflectionSubmitted,
        },
    ]
    if (hasAssignment) {
        steps.push({
            id: 'assignment',
            label: 'Assignment',
            shortLabel: 'Assignment',
            done: detail ? isDone(detail.userTutorial.assignmentDone) : Boolean(progress.assignmentDone),
        })
    }
    if (hasQuiz) {
        steps.push({
            id: 'quiz',
            label: 'Quiz',
            shortLabel: 'Quiz',
            done: detail ? detail.quiz.hasAttempted : progress.quizPassed,
            needsAttention: detail ? (detail.quiz.score ?? 0) < QUIZ_PASS_SCORE : false,
        })
    }

    const rewards = overview.xpRewards
    const xpFlags = getTutorialXpFlags(courseId, hasQuiz)
    const earnedFlags: XpFlags = detail
        ? {
            watched: isDone(detail.userTutorial.watched),
            activityDone: isDone(detail.userTutorial.activityDone),
            assignmentDone: isDone(detail.userTutorial.assignmentDone),
            practiced: isDone(detail.userTutorial.practiced),
        }
        : {
            watched: progress.watched,
            activityDone: Boolean(progress.activityDone),
            assignmentDone: Boolean(progress.assignmentDone),
            practiced: Boolean(progress.practiced),
        }
    const serverXp = Math.max(detail?.userTutorial.xpEarned ?? 0, progress.xpEarned)
    const tutorialXp = rewards ? getTutorialXp(rewards, xpFlags, earnedFlags, serverXp) : null
    const stepXp = rewards ? getStepXp(steps.map(item => item.id), xpFlags, earnedFlags, rewards) : {}
    for (const item of steps) item.xp = stepXp[item.id]
    const xpFor = (flag: XpFlag): number =>
        rewards && xpFlags.includes(flag) && !earnedFlags[flag] ? rewards[flag] : 0
    const forumXp = rewards && detail
        ? {
            ask: isDone(detail.userTutorial.forumAsked) ? 0 : rewards.forumAsked,
            answer: isDone(detail.userTutorial.forumAnswered) ? 0 : rewards.forumAnswered,
        }
        : undefined

    const doneCount = steps.filter(item => item.done).length

    const hrefFor = (target: TutorialStepId): string => tutorialPath(courseId, tutorial.number, target)
    const stepIndex = steps.findIndex(item => item.id === step)

    if (stepIndex === -1) {
        return <Navigate to={hrefFor('video')} replace />
    }

    const prevTutorial = overview.tutorials.find(item => item.number === tutorial.number - 1) ?? null
    const nextTutorial = overview.tutorials.find(item => item.number === tutorial.number + 1) ?? null
    const prevStep = steps[stepIndex - 1]
    const nextStep = steps[stepIndex + 1]

    const nav: TutorialNav = {
        isLinux,
        isSetup,
        hasAssignment,
        nextTutorial,
        totalTutorials: overview.tutorials.length,
        tutorialXp,
        xpFor,
        goToStep: (target) => navigate(hrefFor(target), { replace: true }),
        goToTutorial: (tutorialNumber) => navigate(tutorialPath(courseId, tutorialNumber)),
        backToCourse: () => navigate(coursePath(courseId)),
    }

    const StepComponent = STEP_COMPONENTS[step]
    const tutorialNavButton = 'size-11 lg:size-9 cursor-pointer transition duration-200 ease-in-out'

    return (
        <div>
            <div ref={topRef} className="scroll-mt-4 lg:scroll-mt-6" />
            <header className="max-w-5xl mx-auto mb-2 overflow-hidden rounded-xl border border-primary/15 bg-gradient-to-br from-primary/[0.09] via-card to-teal/[0.08] shadow-xs">
                <div className="px-3 sm:px-5 pt-2.5 pb-4 sm:pb-5 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-2">
                    <Button asChild variant="ghost" className="-ml-2 self-start max-w-full min-h-11 lg:min-h-9 min-w-0 gap-1.5 text-muted-foreground hover:text-foreground hover:bg-primary/10">
                        <Link to={coursePath(courseId)}>
                            <ArrowLeft className="size-4 shrink-0" />
                            <span className="truncate">{overview.title}</span>
                        </Link>
                    </Button>
                    <div className="flex items-center gap-1.5 sm:shrink-0">
                        {codeFilesUrl && (
                            <Button
                                asChild
                                size="sm"
                                className="min-h-11 lg:min-h-9 gap-1.5 px-3 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-xs shadow-xs hover:shadow-sm cursor-pointer transition-all duration-200"
                            >
                                <a href={codeFilesUrl} download>
                                    <Download className="size-3.5" />
                                    <span className="hidden sm:inline">Code Files</span>
                                    <span className="sm:hidden">Code</span>
                                </a>
                            </Button>
                        )}
                        <Button
                            asChild
                            variant="outline"
                            size="sm"
                            className="min-h-11 min-w-11 sm:min-w-0 lg:min-h-9 gap-1.5 px-3 border-primary/30 hover:bg-primary/10 text-primary font-semibold text-xs cursor-pointer transition-all duration-200"
                        >
                            <a href={askForumUrl} target="_blank" rel="noopener noreferrer" aria-label="Have doubts? Ask on forum">
                                <MessageSquarePlus className="size-4 sm:size-3.5" />
                                <span className="hidden md:inline">Have doubts? Ask on forum</span>
                                <span className="md:hidden hidden sm:inline">Ask on forum</span>
                                <ExternalLink className="hidden sm:block size-3 opacity-70" />
                            </a>
                        </Button>
                        <TutorialResources courseId={courseId} urls={detail} askForumUrl={askForumUrl} browseForumUrl={browseForumUrl} forumXp={forumXp} />
                        <div className="ml-auto sm:ml-0 flex items-center gap-1.5">
                        {prevTutorial ? (
                            <Button asChild variant="outline" size="icon" className={tutorialNavButton}>
                                <Link to={tutorialPath(courseId, prevTutorial.number)} aria-label={`Previous: Tutorial ${prevTutorial.number}, ${prevTutorial.title}`} title={`Tutorial ${prevTutorial.number}: ${prevTutorial.title}`}>
                                    <ChevronLeft className="size-4" />
                                </Link>
                            </Button>
                        ) : (
                            <Button variant="outline" size="icon" disabled className={tutorialNavButton} aria-label="No previous tutorial">
                                <ChevronLeft className="size-4" />
                            </Button>
                        )}
                        {nextTutorial ? (
                            <Button asChild variant="outline" size="icon" className={tutorialNavButton}>
                                <Link to={tutorialPath(courseId, nextTutorial.number)} aria-label={`Next: Tutorial ${nextTutorial.number}, ${nextTutorial.title}`} title={`Tutorial ${nextTutorial.number}: ${nextTutorial.title}`}>
                                    <ChevronRight className="size-4" />
                                </Link>
                            </Button>
                        ) : (
                            <Button variant="outline" size="icon" disabled className={tutorialNavButton} aria-label="No next tutorial">
                                <ChevronRight className="size-4" />
                            </Button>
                        )}
                        </div>
                    </div>
                </div>
                <div className="px-1 flex flex-col sm:flex-row sm:items-end justify-between gap-3">
                    <div className="space-y-1 min-w-0">
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-primary">
                            Tutorial <span className="font-mono">{tutorial.number}</span> of{' '}
                            <span className="font-mono">{overview.tutorials.length}</span>
                            <span aria-hidden="true"> · </span>
                            Week {tutorial.week}
                            <span className="hidden sm:inline normal-case tracking-normal font-medium text-muted-foreground">
                                <span aria-hidden="true"> · </span>
                                {getWeekTopic(tutorial.week, courseId)}
                            </span>
                        </p>
                        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground font-sans">{tutorial.title}</h1>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                        <p className="inline-flex items-center gap-1.5 h-8 px-3 rounded-full bg-card border border-border text-xs text-muted-foreground">
                            <span className="font-mono font-semibold text-foreground">{doneCount}</span> of{' '}
                            <span className="font-mono font-semibold text-foreground">{steps.length}</span> steps done
                        </p>
                        {tutorialXp ? (
                            <p
                                className="relative overflow-hidden inline-flex items-center gap-1.5 h-8 px-3 rounded-full bg-card border border-xp-gold/40 text-xs text-muted-foreground"
                                aria-label={`${tutorialXp.earned} of ${tutorialXp.total} XP earned${tutorialXp.forumBonus > 0 ? `, plus ${tutorialXp.forumBonus} forum XP` : ''}`}
                            >
                                <span
                                    aria-hidden="true"
                                    className="absolute inset-y-0 left-0 bg-xp-gold/15 transition-[width] duration-500 ease-out"
                                    style={{ width: `${tutorialXp.total > 0 ? (tutorialXp.earned / tutorialXp.total) * 100 : 0}%` }}
                                />
                                <Zap className="relative size-3.5 text-xp-gold fill-xp-gold" />
                                <span className="relative" aria-hidden="true">
                                    <span className="font-mono font-semibold text-foreground">{tutorialXp.earned}</span>
                                    <span className="font-mono"> / {tutorialXp.total}</span> XP
                                    {tutorialXp.forumBonus > 0 && (
                                        <span className="font-mono font-semibold text-foreground"> +{tutorialXp.forumBonus} forum</span>
                                    )}
                                </span>
                            </p>
                        ) : (
                            <p className="inline-flex items-center gap-1.5 h-8 px-3 rounded-full bg-card border border-xp-gold/40 text-xs text-muted-foreground">
                                <Zap className="size-3.5 text-xp-gold fill-xp-gold" />
                                <span className="font-mono font-semibold text-foreground">{serverXp}</span> XP earned
                            </p>
                        )}
                    </div>
                </div>
                </div>
                <div className="h-1 bg-primary/10" aria-hidden="true">
                    <div
                        className="h-full bg-success transition-[width] duration-500 ease-out"
                        style={{ width: `${(doneCount / steps.length) * 100}%` }}
                    />
                </div>
            </header>

            <TutorialStepNav steps={steps} activeStep={step} justCompletedStep={workspace.justCompletedStep} hrefFor={hrefFor} />

            <div className="max-w-5xl mx-auto pt-5 sm:pt-6">
                {detail ? (
                    <StepComponent detail={detail} workspace={workspace} nav={nav} />
                ) : workspace.loadFailed ? (
                    <PageMessage
                        title="Couldn't load this tutorial"
                        body="Check your connection and try again."
                        backTo={coursePath(courseId)}
                    />
                ) : (
                    <div className="space-y-4" aria-busy="true">
                        <Skeleton className="aspect-video w-full max-w-4xl mx-auto rounded-xl" />
                        <Skeleton className="h-14 w-full max-w-4xl mx-auto rounded-xl" />
                    </div>
                )}
            </div>

            {workspace.celebration && (
                <CelebrationModal
                    type="tutorial_complete"
                    xpEarned={workspace.celebration.xpEarned}
                    title={`Tutorial ${tutorial.number} complete`}
                    subtitle={tutorial.title}
                    onClose={workspace.dismissCelebration}
                />
            )}

            <div className="lg:hidden sticky -bottom-4 z-20 -mx-4 -mb-4 mt-6 px-4 py-2.5 flex items-center gap-2 bg-card/95 backdrop-blur border-t border-border">
                <Button
                    variant="ghost"
                    disabled={!prevStep}
                    onClick={() => prevStep && nav.goToStep(prevStep.id)}
                    className="min-h-11 px-3 gap-1 text-muted-foreground cursor-pointer"
                >
                    <ChevronLeft className="size-4" />
                    Back
                </Button>
                <p className="flex-1 text-center text-xs text-muted-foreground">
                    Step <span className="font-mono font-semibold text-foreground">{stepIndex + 1}</span> of{' '}
                    <span className="font-mono font-semibold text-foreground">{steps.length}</span>
                </p>
                {nextStep ? (
                    <Button onClick={() => nav.goToStep(nextStep.id)} className="min-h-11 gap-1.5 font-semibold cursor-pointer">
                        Next: {nextStep.shortLabel}
                        <ArrowRight className="size-4" />
                    </Button>
                ) : nextTutorial ? (
                    <Button onClick={() => nav.goToTutorial(nextTutorial.number)} className="min-h-11 gap-1.5 font-semibold cursor-pointer">
                        Next tutorial
                        <ArrowRight className="size-4" />
                    </Button>
                ) : (
                    <Button onClick={nav.backToCourse} className="min-h-11 font-semibold cursor-pointer">
                        Finish
                    </Button>
                )}
            </div>
        </div>
    )
}

const TutorialPage: React.FC = () => {
    const params = useParams<{ courseId: string; tutorialNumber: string; step?: string }>()
    const matchedCourseId = useSyncActiveCourse(params.courseId)
    const courseId = matchedCourseId ?? params.courseId ?? ''

    const overview = useLearnerPackStore(state => (state.overviewCourseId === courseId ? state.overview : null))
    const fetchOverview = useLearnerPackStore(state => state.fetchOverview)
    const [failedCourseId, setFailedCourseId] = useState<string | null>(null)

    useEffect(() => {
        if (!courseId) return
        let isCancelled = false
        void fetchOverview(courseId).then((ok) => {
            if (!ok && !isCancelled) setFailedCourseId(courseId)
        })
        return () => {
            isCancelled = true
        }
    }, [courseId, fetchOverview])

    if (!overview) {
        return failedCourseId === courseId ? (
            <PageMessage title="Couldn't load this course" body="Check your connection and try again." backTo="/dashboard" />
        ) : (
            <PageSkeleton />
        )
    }

    const tutorial = overview.tutorials.find(item => item.number === Number(params.tutorialNumber))
    if (!tutorial) {
        return (
            <PageMessage
                title="Tutorial not found"
                body={`${overview.title} doesn't have a tutorial at this address.`}
                backTo={coursePath(overview.courseId)}
            />
        )
    }

    if (!isTutorialStepId(params.step)) {
        const defaultStep = getNextStep(overview.courseId, tutorial).step
        return <Navigate to={tutorialPath(overview.courseId, tutorial.number, defaultStep)} replace />
    }

    return <TutorialWorkspaceView key={tutorial.id} overview={overview} tutorial={tutorial} step={params.step} />
}

export default TutorialPage
