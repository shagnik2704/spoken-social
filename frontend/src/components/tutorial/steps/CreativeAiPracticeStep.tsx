import { AlertCircle, ArrowRight, CheckCircle2, ClipboardCheck, Code2, Lightbulb, Lock, Sparkles, Terminal } from 'lucide-react'
import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { isDone, parseTryItInstructions, withXp } from '@/lib/learnerPack'
import type { TutorialStepProps } from '../types'

const INLINE_MARKDOWN: Components = {
    p: ({ ...props }) => <span {...props} />,
    code: ({ ...props }) => <code className="px-1 py-0.5 rounded bg-muted font-mono text-[11px] text-foreground" {...props} />,
}

export const CreativeAiPracticeStep: React.FC<TutorialStepProps> = ({ detail, workspace, nav }) => {
    const tryIt = parseTryItInstructions(detail.content?.tryItInstructions || '')
    const whatToSubmit = tryIt.submit || (detail.content?.reflectionPrompt ?? '').replace(/^\**What to submit[^:]*:\**\s*/i, '')
    const hasSubmission = Boolean(detail.userReflection)
    const markedDoneWithoutWork = !hasSubmission && (isDone(detail.userTutorial.activityDone) || isDone(detail.userTutorial.minitaskOpted))
    const practiceXp = nav.xpFor('activityDone') + nav.xpFor('assignmentDone')
    const hasAssignment = nav.hasAssignment

    return (
        <div>
            <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Column (5 cols on lg): Practice Task Instructions */}
                <div className="lg:col-span-5 space-y-4 flex flex-col justify-between">
                    <div className="space-y-4">
                        <div className="flex items-center gap-2.5">
                            <div className="p-2.5 rounded-xl bg-teal/15 text-teal border border-teal/20">
                                <Terminal className="h-5 w-5" />
                            </div>
                            <div>
                                <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-teal">Part 1 · Try It</span>
                                <h3 className="text-base font-bold text-foreground">Practice Task</h3>
                            </div>
                        </div>

                        {tryIt.intro && (
                            <p className="text-xs text-muted-foreground leading-relaxed bg-card p-3 rounded-xl border border-border/60">
                                {tryIt.intro}
                            </p>
                        )}

                        {detail.codeFilesUrl && (
                            <div className="p-3 rounded-xl bg-card border border-border/80 flex items-center justify-between gap-3 text-xs shadow-2xs">
                                <div className="flex items-center gap-2 text-foreground font-medium">
                                    <Code2 className="h-4 w-4 text-primary" />
                                    <span>Companion Code Files (.zip)</span>
                                </div>
                                <a
                                    href={detail.codeFilesUrl}
                                    download
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="px-3 py-1.5 rounded-lg bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/90 transition-all shadow-2xs cursor-pointer"
                                >
                                    Download .zip
                                </a>
                            </div>
                        )}

                        {/* Numbered Step Cards */}
                        <div className="space-y-2.5">
                            {tryIt.steps.map((step, idx) => (
                                <div
                                    key={idx}
                                    className="p-3.5 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1 hover:border-primary/40 transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <Badge variant="outline" className="text-[11px] font-mono font-bold px-2 py-0.5 bg-muted text-foreground border-border/80">
                                            Step {idx + 1}
                                        </Badge>
                                    </div>
                                    <div className="prose prose-slate dark:prose-invert max-w-none text-xs text-foreground/90 leading-relaxed font-sans pt-1">
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            components={{
                                                p: ({ ...props }) => <p className="leading-relaxed m-0 text-xs text-foreground/90" {...props} />,
                                                strong: ({ ...props }) => <strong className="font-semibold text-foreground" {...props} />,
                                                code: ({ ...props }) => <code className="px-1 py-0.5 rounded bg-muted font-mono text-[11px] text-foreground" {...props} />,
                                            }}
                                        >
                                            {step}
                                        </ReactMarkdown>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="flex gap-2.5 p-3 rounded-xl bg-warning/10 border border-warning/20">
                            <AlertCircle className="size-4 shrink-0 mt-0.5 text-warning" />
                            <p className="text-xs text-muted-foreground leading-relaxed">
                                <strong className="text-foreground">Keep your work safe:</strong> Never paste your Gemini API key, passwords, or private personal details into your submission.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Right Column (7 cols on lg): Paste & Submit Output */}
                <div className="lg:col-span-7 space-y-4">
                    <div className="p-6 rounded-xl bg-card border shadow-sm space-y-4">
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2.5">
                                    <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
                                        <Lightbulb className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <span className="text-[11px] font-bold uppercase tracking-wider text-primary">Part 2</span>
                                        <h3 className="text-base font-bold text-foreground">Paste & Submit Your Work</h3>
                                    </div>
                                </div>
                                {practiceXp > 0 && (
                                    <div className="flex items-center gap-1.5 font-mono text-xs text-foreground font-semibold bg-muted/60 border border-border px-2.5 py-1 rounded-full">
                                        <Sparkles className="h-3.5 w-3.5 text-xp-gold" />
                                        <span>+{practiceXp} XP</span>
                                    </div>
                                )}
                            </div>

                            {whatToSubmit && (
                                <div className="flex gap-2.5 p-4 rounded-xl border border-primary/15 bg-primary/5">
                                    <ClipboardCheck className="size-4 shrink-0 mt-0.5 text-primary" />
                                    <div className="text-xs text-foreground/90 leading-relaxed [&_p]:m-0">
                                        <span className="font-semibold text-foreground">What to submit: </span>
                                        <ReactMarkdown components={INLINE_MARKDOWN}>{whatToSubmit}</ReactMarkdown>
                                    </div>
                                </div>
                            )}
                            {markedDoneWithoutWork && (
                                <p className="flex gap-2 text-[11px] text-muted-foreground leading-relaxed">
                                    <CheckCircle2 className="size-3.5 shrink-0 mt-0.5 text-success" />
                                    You marked this task as done earlier. Paste your work below so the evaluators can see it.
                                </p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-muted-foreground flex items-center justify-between">
                                <span>Your Submission</span>
                                <span className="text-[11px] text-muted-foreground font-mono">
                                    {workspace.reflectionText.trim() ? workspace.reflectionText.trim().split(/\s+/).length : 0} words
                                </span>
                            </label>
                            <Textarea
                                rows={9}
                                value={workspace.reflectionText}
                                onChange={(e) => workspace.setReflectionText(e.target.value)}
                                placeholder="Paste your prompts, code, or output here..."
                                className="text-sm font-sans leading-relaxed resize-y min-h-[200px] p-3.5"
                            />

                            <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
                                <span className="flex items-center gap-1 text-[11px]">
                                    <Lock className="h-3.5 w-3.5 text-success" />
                                    Visible only to you and academic evaluators
                                </span>
                                <span className="text-[11px] text-muted-foreground">
                                    {hasSubmission ? '✓ Previously submitted' : 'Saved on submission'}
                                </span>
                            </div>
                        </div>

                        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t">
                            <span className={`text-xs ${hasSubmission ? 'text-success font-medium' : 'text-muted-foreground'}`}>
                                {hasSubmission ? '✓ Practice task done' : 'Submitting your work marks this task as done'}
                            </span>
                            <div className="flex items-center gap-2 w-full sm:w-auto">
                                <Button
                                    onClick={workspace.submitReflection}
                                    disabled={workspace.isSubmittingReflection || !workspace.reflectionText.trim()}
                                    className="min-h-11 sm:min-h-9 font-semibold text-xs flex-1 sm:flex-none cursor-pointer"
                                >
                                    {workspace.isSubmittingReflection
                                        ? 'Saving...'
                                        : hasSubmission
                                            ? 'Update Submission'
                                            : withXp('Submit Work', practiceXp)}
                                </Button>
                                {hasSubmission && (
                                    <Button
                                        variant="outline"
                                        onClick={() => nav.goToStep(hasAssignment ? 'assignment' : 'quiz')}
                                        className="min-h-11 sm:min-h-9 hidden lg:inline-flex text-xs gap-1 cursor-pointer"
                                    >
                                        <span>{hasAssignment ? 'Next: Lab Assignment' : 'Take Quiz'}</span>
                                        <ArrowRight className="h-3.5 w-3.5" />
                                    </Button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
