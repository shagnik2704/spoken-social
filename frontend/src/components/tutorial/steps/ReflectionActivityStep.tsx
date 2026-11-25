import { ArrowRight, CheckCircle2, Code2, Lightbulb, Lock, PenTool, Sparkles } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { isDone, parseTryItInstructions, withXp } from '@/lib/learnerPack'
import type { TutorialStepProps } from '../types'

export const ReflectionActivityStep: React.FC<TutorialStepProps> = ({ detail, workspace, nav }) => {
    const tryIt = parseTryItInstructions(detail.content?.tryItInstructions || '')
    const rawPrompt = detail.content?.reflectionPrompt || ''
    const promptParts = rawPrompt.split(/(?:\n\*\s*|\n?•\s*)/).map(part => part.trim()).filter(Boolean)
    const promptIntro = promptParts.length > 1 ? promptParts[0] : rawPrompt
    const promptQuestions = promptParts.length > 1 ? promptParts.slice(1) : []
    const isActivityDone = isDone(detail.userTutorial.activityDone) || isDone(detail.userTutorial.minitaskOpted)
    const hasAssignment = nav.hasAssignment

    return (
        <div>
            <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Column (5 cols on lg, full width on mobile): Personal Notebook Exercise */}
                <div className="lg:col-span-5 space-y-4 flex flex-col justify-between">
                    <div className="space-y-4">
                        <div className="flex items-center gap-2.5">
                            <div className="p-2.5 rounded-xl bg-muted text-foreground border border-border/70">
                                <PenTool className="h-5 w-5" />
                            </div>
                            <div>
                                <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-muted-foreground">Part 1</span>
                                <h3 className="text-base font-bold text-foreground">
                                    {detail.codeFilesUrl || detail.assignmentUrl ? 'Hands-On Practice / Assignment' : 'Personal Notebook Exercise'}
                                </h3>
                            </div>
                        </div>

                        {/* Explicit callout: Personal notebook & No upload needed */}
                        <div className="p-3.5 rounded-xl bg-muted/60 border border-border/80 text-xs text-foreground/90 space-y-1.5 shadow-2xs">
                            <div className="flex items-center gap-2 font-bold text-foreground">
                                <Lock className="h-3.5 w-3.5 text-primary" />
                                <span>Personal Notebook • No Upload Needed</span>
                            </div>
                            <p className="text-[11px] text-muted-foreground leading-relaxed">
                                This exercise is for your own personal reflection and self-growth. You <strong>do not need to upload or submit any files</strong> here. Complete the exercise in your physical notebook, diary, or notes app, then check off the exercise below.
                            </p>
                        </div>

                        {/* Optional Code Files Download Tile */}
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

                        {/* Intro description */}
                        {tryIt.intro && (
                            <p className="text-xs text-muted-foreground leading-relaxed bg-card p-3 rounded-xl border border-border/60">
                                {tryIt.intro}
                            </p>
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
                                    <p className="text-xs text-foreground/90 leading-relaxed font-sans pt-1">
                                        {step}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Interactive Completion Trigger for Private Exercise */}
                    <div className="space-y-3 pt-2">
                        <div className={`p-4 rounded-xl border transition-all ${isActivityDone
                            ? 'bg-success/10 border-success/30 shadow-2xs'
                            : 'bg-card border-border hover:border-primary/40'
                            }`}>
                            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                                <div className="space-y-0.5">
                                    <div className="flex items-center gap-2">
                                        <CheckCircle2 className={`h-4 w-4 ${isActivityDone ? 'text-success' : 'text-muted-foreground'}`} />
                                        <span className="text-xs font-bold text-foreground">
                                            {isActivityDone ? 'Completed in Notebook' : 'Mark Exercise as Done'}
                                        </span>
                                    </div>
                                    <p className="text-[11px] text-muted-foreground">
                                        {isActivityDone
                                            ? 'Personal notebook exercise verified.'
                                            : 'Click when finished writing in your personal notebook. No upload needed.'}
                                    </p>
                                </div>
                                <Button
                                    size="sm"
                                    onClick={workspace.markActivityComplete}
                                    disabled={isActivityDone || workspace.isMarkingActivity}
                                    className={`min-h-11 sm:min-h-9 text-xs font-semibold shrink-0 w-full sm:w-auto cursor-pointer ${isActivityDone
                                        ? 'bg-success/15 text-success border border-success/30 shadow-none'
                                        : ''
                                        }`}
                                >
                                    {isActivityDone
                                        ? '✓ Completed'
                                        : workspace.isMarkingActivity
                                            ? 'Saving...'
                                            : withXp('Mark Done', nav.xpFor('activityDone'))}
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column (7 cols on lg, full width on mobile): Written Reflection */}
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
                                        <h3 className="text-base font-bold text-foreground">Written Reflection</h3>
                                    </div>
                                </div>
                                {nav.xpFor('assignmentDone') > 0 && (
                                    <div className="flex items-center gap-1.5 font-mono text-xs text-foreground font-semibold bg-muted/60 border border-border px-2.5 py-1 rounded-full">
                                        <Sparkles className="h-3.5 w-3.5 text-xp-gold" />
                                        <span>+{nav.xpFor('assignmentDone')} XP</span>
                                    </div>
                                )}
                            </div>

                            {/* Formatted Reflection Prompt */}
                            <div className="space-y-2 bg-primary/5 p-4 rounded-xl border border-primary/15">
                                <p className="text-xs font-semibold text-primary">
                                    {promptIntro}
                                </p>
                                {promptQuestions.length > 0 && (
                                    <div className="space-y-1.5 pt-1">
                                        {promptQuestions.map((q, idx) => (
                                            <div key={idx} className="flex items-start gap-2 text-xs text-foreground/90">
                                                <span className="h-4 w-4 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-[11px] shrink-0 mt-0.5">
                                                    {idx + 1}
                                                </span>
                                                <span className="leading-snug">{q}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Textarea */}
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-muted-foreground flex items-center justify-between">
                                <span>Your Reflection</span>
                                <span className="text-[11px] text-muted-foreground font-mono">
                                    {workspace.reflectionText.trim() ? workspace.reflectionText.trim().split(/\s+/).length : 0} words
                                </span>
                            </label>
                            <Textarea
                                rows={7}
                                value={workspace.reflectionText}
                                onChange={(e) => workspace.setReflectionText(e.target.value)}
                                placeholder="Write your reflection here. Address the questions above..."
                                className="text-sm font-sans leading-relaxed resize-none p-3.5"
                            />

                            <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
                                <span className="flex items-center gap-1 text-[11px]">
                                    <Lock className="h-3.5 w-3.5 text-success" />
                                    Visible only to you and academic evaluators
                                </span>
                                <span className="text-[11px] text-muted-foreground">
                                    {detail.userReflection ? '✓ Previously submitted' : 'Personal reflection'}
                                </span>
                            </div>
                        </div>

                        {/* Submit Button */}
                        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t">
                            <span className="text-xs text-muted-foreground">
                                {detail.userReflection ? 'Reflection recorded in portfolio' : 'Saved to your portfolio on submission'}
                            </span>
                            <div className="flex items-center gap-2 w-full sm:w-auto">
                                <Button
                                    onClick={workspace.submitReflection}
                                    disabled={workspace.isSubmittingReflection || !workspace.reflectionText.trim()}
                                    className="min-h-11 sm:min-h-9 font-semibold text-xs flex-1 sm:flex-none cursor-pointer"
                                >
                                    {workspace.isSubmittingReflection ? 'Saving...' : detail.userReflection ? 'Update Reflection' : withXp('Submit Reflection', nav.xpFor('assignmentDone'))}
                                </Button>
                                {detail.userReflection && (
                                    <Button
                                        variant="outline"
                                        onClick={() => nav.goToStep(hasAssignment ? 'assignment' : 'quiz')}
                                        className="min-h-11 sm:min-h-9 hidden lg:inline-flex text-xs gap-1 cursor-pointer"
                                    >
                                        <span>{hasAssignment ? 'Next: Assignment' : 'Take Quiz'}</span>
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
