import { Link } from 'react-router-dom'
import { ArrowRight, CheckCircle2, ClipboardCheck, FlaskConical, GraduationCap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { assessmentLabel, assessmentPath } from '@/lib/learnerPack'
import { cn } from '@/lib/utils'
import type { AssessmentSummary } from '@/types'

interface AssessmentRowProps {
    courseId: string
    assessment: AssessmentSummary
    isDueThisWeek: boolean
}

export const AssessmentRow: React.FC<AssessmentRowProps> = ({ courseId, assessment, isDueThisWeek }) => {
    const submission = assessment.submission
    const isReviewed = Boolean(submission?.reviewedAt)
    const isSubmitted = Boolean(submission)
    const Icon = assessment.kind === 'capstone' ? GraduationCap : FlaskConical
    const actionLabel = isSubmitted ? 'View' : 'Open'

    return (
        <div
            className={cn(
                'group flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 p-3.5 sm:p-4 rounded-xl border transition-all duration-200 ease-in-out',
                isSubmitted
                    ? 'bg-card/60 border-success/25 hover:border-success/40'
                    : isDueThisWeek
                        ? 'bg-teal/[0.04] border-teal/40 hover:border-teal/60'
                        : 'bg-card border-dashed border-teal/35 hover:border-teal/60'
            )}
        >
            <div className="flex items-center gap-3 min-w-0 flex-1">
                <div
                    className={cn(
                        'size-8 shrink-0 rounded-lg border flex items-center justify-center transition-colors duration-200 ease-in-out',
                        isSubmitted ? 'bg-success/10 text-success border-success/25' : 'bg-teal/10 text-teal border-teal/25'
                    )}
                >
                    <Icon className="size-4" aria-hidden="true" />
                </div>
                <div className="min-w-0">
                    <h4 className="text-sm font-semibold text-foreground line-clamp-2 sm:line-clamp-1">
                        {assessmentLabel(assessment)}: {assessment.title}
                    </h4>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">
                        {assessment.covers && <>Covers {assessment.covers.toLowerCase()}<span aria-hidden="true"> · </span></>}
                        Graded by evaluators
                    </p>
                </div>
            </div>

            <div className="flex items-center justify-between sm:justify-end gap-2 sm:gap-4 min-w-0 sm:shrink-0 pl-11 sm:pl-0">
                {isSubmitted ? (
                    <p className="inline-flex items-center gap-1.5 text-xs font-medium text-success">
                        {isReviewed ? <ClipboardCheck className="size-3.5" /> : <CheckCircle2 className="size-3.5" />}
                        {isReviewed ? 'Reviewed' : 'Submitted'}
                    </p>
                ) : (
                    <p className="text-xs font-semibold text-teal">
                        Due week <span className="font-mono">{assessment.weekDue}</span>
                    </p>
                )}
                <Button
                    asChild
                    size="sm"
                    variant={isSubmitted ? 'outline' : 'default'}
                    className="min-h-11 sm:min-h-9 shrink-0 px-3.5 text-xs font-semibold transition-all duration-200 ease-in-out"
                >
                    <Link to={assessmentPath(courseId, assessment.key)}>
                        {actionLabel}
                        <ArrowRight className="size-3.5 group-hover:translate-x-0.5 transition-transform duration-200 ease-in-out" />
                    </Link>
                </Button>
            </div>
        </div>
    )
}
