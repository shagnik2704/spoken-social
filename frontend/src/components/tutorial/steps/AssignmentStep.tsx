import { Check, CheckCircle2, Download, ExternalLink, Loader2, Sparkles } from 'lucide-react'
import { ArrowRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { isDone, withXp } from '@/lib/learnerPack'
import type { TutorialStepProps } from '../types'

const BOILERPLATE_LINE = /^((?:Personality and Human Development|Developing Empathy and Growth Mindset|Being Creative with AI).*Assignment|as an assignment)/i

const cleanAssignmentText = (raw: string): string =>
    raw
        .replace(/\r\n?/g, '\n')
        .split('\n')
        .filter(line => !BOILERPLATE_LINE.test(line.trim()))
        .join('\n')
        .trim()

export const AssignmentStep: React.FC<TutorialStepProps> = ({ detail, workspace, nav }) => {
    const cleanedAssignmentText = cleanAssignmentText(detail.assignmentInstructions || '')
    const isAssignmentDone = isDone(detail.userTutorial.assignmentDone) || Boolean(detail.userReflection)

    return (
        <div>
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Assignment Body Content */}
                <div className="p-6 sm:p-8 rounded-xl bg-card border border-border/80 shadow-xs space-y-6">
                    <div className="flex items-center justify-between gap-4 pb-4 border-b border-border/60">
                        <h3 className="text-xl sm:text-2xl font-bold text-foreground tracking-tight">Assignment</h3>
                        {detail.assignmentUrl && (
                            <a
                                href={detail.assignmentUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-border/80 bg-background hover:bg-muted text-xs sm:text-sm font-semibold text-foreground transition-all shadow-2xs cursor-pointer shrink-0"
                            >
                                <Download className="h-4 w-4 text-primary" />
                                <span>Download Assignment</span>
                                <ExternalLink className="h-3 w-3 text-muted-foreground/60" />
                            </a>
                        )}
                    </div>

                    {cleanedAssignmentText ? (
                        <div className="prose prose-slate dark:prose-invert max-w-none text-foreground/90 font-sans leading-relaxed text-sm sm:text-base space-y-4">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    h3: ({ ...props }) => <h3 className="text-base sm:text-lg font-bold text-foreground mt-4 mb-2 font-sans" {...props} />,
                                    p: ({ ...props }) => <p className="leading-relaxed mb-3 text-foreground/90 text-sm sm:text-base font-sans" {...props} />,
                                    ul: ({ ...props }) => <ul className="list-disc pl-6 mb-4 space-y-2 text-sm sm:text-base text-foreground/90" {...props} />,
                                    ol: ({ ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-sm sm:text-base text-foreground/90" {...props} />,
                                    li: ({ ...props }) => <li className="leading-relaxed" {...props} />,
                                    strong: ({ ...props }) => <strong className="font-bold text-foreground" {...props} />,
                                }}
                            >
                                {cleanedAssignmentText}
                            </ReactMarkdown>
                        </div>
                    ) : (
                        <p className="text-sm text-muted-foreground italic">
                            Assignment instructions will be available shortly.
                        </p>
                    )}

                    {/* Helpful Tip */}
                    <div className="p-4 rounded-xl bg-muted/60 border border-border/70 text-xs text-foreground/90 flex items-start gap-3 shadow-2xs">
                        <Sparkles className="h-4 w-4 text-xp-gold shrink-0 mt-0.5" />
                        <div className="space-y-1">
                            <p className="font-semibold text-foreground">How to Complete</p>
                            <p className="text-muted-foreground leading-relaxed">
                                Complete this practical task in your physical notebook or discuss it with friends or classmates.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Completion and Next Action Footer */}
                <div className="p-6 rounded-xl bg-card border border-border/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="space-y-1 text-center sm:text-left">
                        <h4 className="font-bold text-foreground text-sm sm:text-base">
                            {isAssignmentDone ? 'Assignment Completed' : 'Completed this assignment?'}
                        </h4>
                        <p className="text-xs text-muted-foreground">
                            {isAssignmentDone
                                ? 'Assignment marked as completed. Next step: 5-Question Quiz.'
                                : nav.xpFor('assignmentDone') > 0
                                    ? `Mark as completed to earn +${nav.xpFor('assignmentDone')} XP toward your course progress.`
                                    : 'Mark as completed to track your course progress.'}
                        </p>
                    </div>

                    <div className="flex items-center gap-3 w-full sm:w-auto">
                        {!isAssignmentDone ? (
                            <Button
                                size="lg"
                                variant="outline"
                                onClick={workspace.markAssignmentComplete}
                                disabled={workspace.isMarkingAssignment}
                                className="min-h-11 sm:min-h-9 font-semibold text-xs sm:text-sm gap-1.5 flex-1 sm:flex-none cursor-pointer"
                            >
                                {workspace.isMarkingAssignment ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        <span>Saving...</span>
                                    </>
                                ) : (
                                    <>
                                        <CheckCircle2 className="h-4 w-4 text-success" />
                                        <span>{withXp('Mark Completed', nav.xpFor('assignmentDone'))}</span>
                                    </>
                                )}
                            </Button>
                        ) : (
                            <Badge variant="outline" className="bg-success/10 text-success border-success/30 text-xs px-3 py-1.5 font-semibold gap-1.5">
                                <Check className="h-3.5 w-3.5" />
                                <span>Completed</span>
                            </Badge>
                        )}

                        <Button
                            size="lg"
                            onClick={() => nav.goToStep('quiz')}
                            className="min-h-11 sm:min-h-9 hidden lg:inline-flex font-semibold text-xs sm:text-sm gap-2 flex-1 sm:flex-none cursor-pointer shadow-xs"
                        >
                            <span>Proceed to Quiz</span>
                            <ArrowRight className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    )
}
