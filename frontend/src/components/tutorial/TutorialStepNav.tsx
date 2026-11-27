import { Link } from 'react-router-dom'
import { Check, Zap } from 'lucide-react'
import type { TutorialStepId } from '@/lib/learnerPack'
import { cn } from '@/lib/utils'

export interface TutorialStep {
    id: TutorialStepId
    label: string
    shortLabel: string
    done: boolean
    needsAttention?: boolean
    xp?: number
}

interface TutorialStepNavProps {
    steps: TutorialStep[]
    activeStep: TutorialStepId
    justCompletedStep: TutorialStepId | null
    hrefFor: (step: TutorialStepId) => string
    compactTitle?: string | null
}

const markerClasses = (step: TutorialStep, isActive: boolean): string => {
    if (step.done) {
        return step.needsAttention
            ? cn('bg-warning border-warning text-background', isActive && 'ring-4 ring-warning/20')
            : cn('bg-success border-success text-background', isActive && 'ring-4 ring-success/20')
    }
    return isActive
        ? 'bg-primary border-primary text-primary-foreground ring-4 ring-primary/15'
        : 'bg-card border-border text-muted-foreground group-hover:border-primary/50 group-hover:text-foreground'
}

const CompactStepNav: React.FC<Omit<TutorialStepNavProps, 'compactTitle'> & { title: string }> = ({ steps, activeStep, justCompletedStep, hrefFor, title }) => (
    <div className="sm:hidden flex items-center gap-2 h-12 animate-in fade-in slide-in-from-top-1 duration-200">
        <p className="flex-1 min-w-0 truncate text-sm font-semibold text-foreground">{title}</p>
        <ol className="flex items-center shrink-0 -mr-2">
            {steps.map((step, index) => {
                const isActive = step.id === activeStep
                return (
                    <li key={step.id}>
                        <Link
                            to={hrefFor(step.id)}
                            replace
                            aria-current={isActive ? 'step' : undefined}
                            aria-label={`Step ${index + 1}: ${step.label}${step.done ? ', done' : ''}`}
                            className="size-11 flex items-center justify-center rounded-lg transition duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                        >
                            <span
                                className={cn(
                                    'size-6 rounded-full border-2 flex items-center justify-center font-mono text-[11px] font-bold transition duration-200 ease-in-out',
                                    markerClasses(step, isActive),
                                    step.done && justCompletedStep === step.id && 'animate-step-pop'
                                )}
                            >
                                {step.done ? <Check className="size-3.5" strokeWidth={3} aria-hidden="true" /> : index + 1}
                            </span>
                        </Link>
                    </li>
                )
            })}
        </ol>
    </div>
)

export const TutorialStepNav: React.FC<TutorialStepNavProps> = ({ steps, activeStep, justCompletedStep, hrefFor, compactTitle }) => (
    <nav
        aria-label="Tutorial steps"
        className="sticky -top-4 lg:-top-6 z-20 -mx-4 lg:-mx-6 px-4 lg:px-6 bg-background/95 backdrop-blur border-b border-border"
    >
        {compactTitle && (
            <CompactStepNav steps={steps} activeStep={activeStep} justCompletedStep={justCompletedStep} hrefFor={hrefFor} title={compactTitle} />
        )}
        <ol className={cn('max-w-3xl mx-auto flex', compactTitle && 'max-sm:hidden')}>
            {steps.map((step, index) => {
                const isActive = step.id === activeStep
                const previous = steps[index - 1]
                return (
                    <li key={step.id} className="relative flex-1 min-w-0">
                        {previous && (
                            <span
                                aria-hidden="true"
                                className={cn(
                                    'absolute top-[23px] -left-1/2 right-1/2 mx-[22px] h-0.5 rounded-full transition-colors duration-500 ease-in-out',
                                    previous.done ? 'bg-success' : 'bg-border'
                                )}
                            />
                        )}
                        <Link
                            to={hrefFor(step.id)}
                            replace
                            aria-current={isActive ? 'step' : undefined}
                            className="group relative flex flex-col items-center gap-1 min-h-16 pt-2.5 pb-2 px-1 rounded-lg transition duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                        >
                            <span
                                key={`${step.id}-${step.done}`}
                                className={cn(
                                    'size-7 shrink-0 rounded-full border-2 flex items-center justify-center font-mono text-xs font-bold transition duration-200 ease-in-out',
                                    markerClasses(step, isActive),
                                    step.done && justCompletedStep === step.id && 'animate-step-pop'
                                )}
                            >
                                {step.done ? <Check className="size-4" strokeWidth={3} aria-label="Done" /> : index + 1}
                            </span>
                            <span
                                className={cn(
                                    'max-w-full truncate text-[11px] sm:text-xs transition-colors duration-200 ease-in-out',
                                    isActive
                                        ? 'text-foreground font-semibold'
                                        : step.done
                                            ? 'text-foreground/80 font-medium'
                                            : 'text-muted-foreground font-medium group-hover:text-foreground'
                                )}
                            >
                                <span className="sm:hidden">{step.shortLabel}</span>
                                <span className="hidden sm:inline">{step.label}</span>
                            </span>
                            {!step.done && step.xp ? (
                                <span className="inline-flex items-center gap-0.5 font-mono text-[10px] leading-none font-semibold text-foreground/75">
                                    <Zap className="size-2.5 text-xp-gold fill-xp-gold" aria-hidden="true" />
                                    +{step.xp} XP
                                </span>
                            ) : null}
                        </Link>
                    </li>
                )
            })}
        </ol>
    </nav>
)
