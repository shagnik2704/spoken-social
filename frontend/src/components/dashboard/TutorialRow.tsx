import { Link } from 'react-router-dom'
import { ArrowRight, Check, CheckCircle2, FileText, HelpCircle, MonitorCheck, PenLine, PlayCircle, Terminal, type LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { getNextStep, getOverviewSteps, isTutorialCompleted, tutorialPath, type OverviewStepKind } from '@/lib/learnerPack'
import { cn } from '@/lib/utils'
import type { LearnerPackOverviewTutorial } from '@/types'

const STEP_ICONS: Record<OverviewStepKind, LucideIcon> = {
    lesson: PlayCircle,
    setup: MonitorCheck,
    lab: Terminal,
    activity: PenLine,
    assignment: FileText,
    quiz: HelpCircle,
}

interface TutorialRowProps {
    courseId: string
    tutorial: LearnerPackOverviewTutorial
    isUpNext: boolean
}

export const TutorialRow: React.FC<TutorialRowProps> = ({ courseId, tutorial, isUpNext }) => {
    const steps = getOverviewSteps(courseId, tutorial)
    const doneCount = steps.filter(step => step.done).length
    const isCompleted = isTutorialCompleted(courseId, tutorial)
    const isInProgress = !isCompleted && doneCount > 0
    const isHighlighted = isUpNext || isInProgress
    const quizScore = tutorial.userProgress.quizScore
    const actionLabel = isCompleted ? 'Review' : isInProgress ? 'Continue' : isUpNext ? 'Start' : 'Open'
    const stepSummary = `${doneCount} of ${steps.length} steps done`

    return (
        <div
            className={cn(
                'group flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 p-3.5 sm:p-4 rounded-xl border transition-all duration-200 ease-in-out',
                isCompleted
                    ? 'bg-card/60 border-success/25 hover:border-success/40'
                    : isHighlighted
                        ? 'bg-primary/[0.03] border-primary/40 hover:border-primary/60'
                        : 'bg-card border-border/70 hover:border-primary/30'
            )}
        >
            <div className="flex items-center gap-3 min-w-0 flex-1">
                <div
                    className={cn(
                        'size-8 shrink-0 rounded-lg border font-mono text-xs font-bold flex items-center justify-center transition-colors duration-200 ease-in-out',
                        isCompleted
                            ? 'bg-success/10 text-success border-success/25'
                            : isHighlighted
                                ? 'bg-primary/10 text-primary border-primary/25'
                                : 'bg-muted text-muted-foreground border-border/60'
                    )}
                >
                    {isCompleted ? <Check className="size-4" aria-label="Completed" /> : tutorial.number}
                </div>
                <h4 className="min-w-0 text-sm font-semibold text-foreground line-clamp-2 sm:line-clamp-1">{tutorial.title}</h4>
                {isUpNext && (
                    <span className="shrink-0 text-[11px] font-semibold text-primary bg-primary/10 border border-primary/25 rounded-full px-2 py-0.5">
                        Up next
                    </span>
                )}
            </div>

            <div className="flex items-center justify-between sm:justify-end gap-2 sm:gap-4 min-w-0 sm:shrink-0 pl-11 sm:pl-0">
                {isCompleted ? (
                    <p className="inline-flex flex-wrap items-center gap-x-1.5 min-w-0 text-xs font-medium text-success">
                        <CheckCircle2 className="size-3.5" />
                        Completed
                        {quizScore !== null && (
                            <span className="font-mono text-muted-foreground">· Quiz {quizScore}/5</span>
                        )}
                    </p>
                ) : (
                    <ul className="flex items-center gap-1" aria-label={stepSummary}>
                        {steps.map((step) => {
                            const StepIcon = STEP_ICONS[step.kind]
                            return (
                                <li
                                    key={step.kind}
                                    title={`${step.label}: ${step.done ? 'done' : 'to do'}`}
                                    className={cn(
                                        'size-7 rounded-full border flex items-center justify-center transition-colors duration-200 ease-in-out',
                                        step.done
                                            ? 'bg-success/15 text-success border-success/30'
                                            : 'bg-muted text-foreground/70 border-foreground/20'
                                    )}
                                >
                                    <StepIcon className="size-3.5" />
                                </li>
                            )
                        })}
                    </ul>
                )}

                <Button
                    asChild
                    size="sm"
                    variant={isHighlighted ? 'default' : 'outline'}
                    className="min-h-11 sm:min-h-9 shrink-0 px-3.5 text-xs font-semibold transition-all duration-200 ease-in-out"
                >
                    <Link to={tutorialPath(courseId, tutorial.number, getNextStep(courseId, tutorial).step)}>
                        {actionLabel}
                        <ArrowRight className="size-3.5 group-hover:translate-x-0.5 transition-transform duration-200 ease-in-out" />
                    </Link>
                </Button>
            </div>
        </div>
    )
}
