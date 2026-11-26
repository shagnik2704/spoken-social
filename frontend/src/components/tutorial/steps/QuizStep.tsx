import { ArrowRight, Check, CheckCircle2, Lightbulb, Sparkles } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { normalizeQuizOptions, QUIZ_PASS_SCORE, withXp } from '@/lib/learnerPack'
import { cn } from '@/lib/utils'
import type { TutorialStepProps } from '../types'

const WithInlineCode: React.FC<{ text: string }> = ({ text }) => (
    <>
        {text.split(/(`[^`]+`)/).map((part, index) =>
            part.length > 2 && part.startsWith('`') && part.endsWith('`') ? (
                <code key={index} className="font-terminal text-[0.92em] px-1.5 py-0.5 rounded-md bg-muted border border-border text-foreground break-words">
                    {part.slice(1, -1)}
                </code>
            ) : (
                part
            )
        )}
    </>
)

export const QuizStep: React.FC<TutorialStepProps> = ({ detail, workspace, nav }) => {
    const nextTutorial = nav.nextTutorial

    return (
        <div>
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Quiz Overview Banner */}
                <div className="p-6 rounded-xl bg-card border shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2">
                            <h3 className="text-lg font-bold text-foreground">Tutorial Knowledge Quiz</h3>
                            <Badge variant="outline" className="text-xs font-mono">{detail.quiz.questions.length} Questions</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Multiple-choice questions. Explanations unlock once you submit.
                        </p>
                    </div>

                    {detail.quiz.hasAttempted ? (
                        <div className={cn(
                            "px-4 py-2 rounded-xl border flex flex-col items-center sm:items-end justify-center min-w-[90px]",
                            ((detail.quiz.score ?? 0) >= QUIZ_PASS_SCORE)
                                ? 'bg-success/10 border-success/25 text-success'
                                : 'bg-warning/10 border-warning/25 text-warning'
                        )}>
                            <div className="text-[11px] uppercase font-bold tracking-wider text-muted-foreground">
                                Score
                            </div>
                            <div className="text-xl font-bold font-mono">
                                {detail.quiz.score} / {detail.quiz.totalQuestions}
                            </div>
                        </div>
                    ) : nav.xpFor('practiced') > 0 ? (
                        <div className="flex items-center gap-2 text-xs font-mono font-semibold text-foreground bg-muted/60 border border-border px-3 py-1.5 rounded-xl">
                            <Sparkles className="h-4 w-4 text-xp-gold" />
                            +{nav.xpFor('practiced')} XP
                        </div>
                    ) : null}
                </div>

                {/* Questions */}
                <div className="space-y-5">
                    {detail.quiz.questions.map((q) => {
                        const selected = workspace.quizAnswers[String(q.questionNumber)] || q.selectedOption
                        const isSubmitted = detail.quiz.hasAttempted

                        return (
                            <div key={q.id} className="p-6 rounded-xl border bg-card shadow-sm space-y-4">
                                <div className="flex items-start gap-3">
                                    <div className="h-7 w-7 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                                        {q.questionNumber}
                                    </div>
                                    <h4 className="text-sm sm:text-base font-semibold text-foreground leading-relaxed flex-1">
                                        <WithInlineCode text={q.questionText} />
                                    </h4>
                                </div>

                                {/* Options */}
                                <RadioGroup
                                    value={selected || ''}
                                    onValueChange={(val) => workspace.answerQuestion(q.questionNumber, val)}
                                    disabled={isSubmitted}
                                    className="space-y-2.5 pt-1 sm:pl-10"
                                >
                                    {normalizeQuizOptions(q.options).map((opt) => {
                                        const isCorrect = isSubmitted && q.correctOption === opt.id
                                        const isChosen = selected === opt.id
                                        const isWrong = isSubmitted && isChosen && !isCorrect

                                        return (
                                            <label
                                                key={opt.id}
                                                className={`flex items-start gap-3 p-3.5 rounded-xl border text-xs sm:text-sm cursor-pointer transition-all ${isCorrect
                                                    ? 'border-success bg-success/10 text-foreground font-medium'
                                                    : isWrong
                                                        ? 'border-destructive bg-destructive/10 text-destructive font-medium'
                                                        : isChosen
                                                            ? 'border-primary bg-primary/5 text-foreground ring-1 ring-primary/20'
                                                            : 'border-border hover:bg-muted/40 text-muted-foreground hover:text-foreground'
                                                    }`}
                                            >
                                                <RadioGroupItem value={opt.id} className="mt-0.5" />
                                                <span className="flex-1 leading-relaxed">
                                                    <strong className="mr-1.5 font-bold uppercase">{opt.id}.</strong>
                                                    <WithInlineCode text={opt.text} />
                                                </span>
                                                {isCorrect && <Check className="h-4 w-4 text-success shrink-0 mt-0.5" />}
                                            </label>
                                        )
                                    })}
                                </RadioGroup>

                                {/* Explanation Box */}
                                {isSubmitted && q.explanation && (
                                    <div className="mt-4 p-4 rounded-xl bg-muted/60 border border-border/80 text-xs sm:text-sm space-y-1.5 sm:ml-10">
                                        <span className="font-bold text-primary flex items-center gap-1.5 text-xs uppercase tracking-wider">
                                            <Lightbulb className="h-3.5 w-3.5" />
                                            {nav.isLinux ? 'Technical Explanation & Solution' : nav.isCreativeAi ? 'Explanation' : 'Psychological Rationale & Explanation'}
                                        </span>
                                        <p className="text-foreground/80 leading-relaxed font-sans">
                                            <WithInlineCode text={q.explanation} />
                                        </p>
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>

                {/* Submit or Completed Actions */}
                {!detail.quiz.hasAttempted ? (
                    <div className="pt-2 pb-6 flex justify-end">
                        <Button
                            size="lg"
                            onClick={workspace.submitQuiz}
                            disabled={workspace.isSubmittingQuiz}
                            className="min-h-11 sm:min-h-9 font-bold text-sm px-6 cursor-pointer shadow-sm"
                        >
                            {workspace.isSubmittingQuiz
                                ? 'Evaluating Answers...'
                                : withXp('Submit Answers', nav.xpFor('practiced'))}
                        </Button>
                    </div>
                ) : (
                    <div className="space-y-4 pt-2 pb-6">
                        {/* Prompt to move directly to next tutorial */}
                        <div className={cn(
                            "p-6 rounded-xl bg-card border shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4 animate-in fade-in duration-300",
                            (detail.quiz.score ?? 0) > 0 ? "border-success/30" : "border-warning/30"
                        )}>
                            <div className="space-y-1.5 text-center sm:text-left">
                                <div className="flex items-center gap-2 justify-center sm:justify-start">
                                    <CheckCircle2 className={cn("h-5 w-5 shrink-0", (detail.quiz.score ?? 0) > 0 ? "text-success" : "text-warning")} />
                                    <h4 className="font-bold text-foreground text-base sm:text-lg">
                                        {(detail.quiz.score ?? 0) > 0
                                            ? `Tutorial ${detail.tutorialNumber} Completed!`
                                            : `Quiz Submitted (${detail.quiz.score ?? 0}/${detail.quiz.totalQuestions})`}
                                    </h4>
                                    {nav.tutorialXp && (
                                        <Badge variant="outline" className={cn(
                                            "text-xs font-mono font-bold",
                                            (detail.quiz.score ?? 0) > 0
                                                ? "bg-success/15 text-success border-success/30"
                                                : "bg-warning/15 text-warning border-warning/30"
                                        )}>
                                            {nav.tutorialXp.earned} / {nav.tutorialXp.total} XP
                                        </Badge>
                                    )}
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    {(detail.quiz.score ?? 0) === 0
                                        ? 'Review the explanations above and retake the quiz to complete this tutorial.'
                                        : nextTutorial
                                            ? `Ready for the next lesson? Continue directly to Tutorial ${nextTutorial.number}: ${nextTutorial.title}`
                                            : `Outstanding! You have completed all ${nav.totalTutorials} tutorials in this curriculum.`}
                                </p>
                            </div>

                            {nextTutorial ? (
                                <Button
                                    size="lg"
                                    onClick={() => nav.goToTutorial(nextTutorial.number)}
                                    className="min-h-11 sm:min-h-9 bg-primary hover:bg-primary/90 text-primary-foreground font-bold text-xs sm:text-sm px-6 py-3 rounded-xl shadow-xs cursor-pointer shrink-0 gap-2 w-full sm:w-auto hover:scale-[1.02] active:scale-[0.98] transition-all"
                                >
                                    <span>Continue to Tutorial {nextTutorial.number}</span>
                                    <ArrowRight className="h-4 w-4" />
                                </Button>
                            ) : (
                                <Button
                                    size="lg"
                                    variant="outline"
                                    onClick={nav.backToCourse}
                                    className="min-h-11 sm:min-h-9 font-bold text-xs sm:text-sm px-6 py-3 rounded-xl border-success/30 text-success cursor-pointer"
                                >
                                    <span>Back to course</span>
                                </Button>
                            )}
                        </div>

                        <div className="flex justify-end">
                            <Button
                                size="sm"
                                variant="ghost"
                                onClick={workspace.retakeQuiz}
                                className="min-h-11 sm:min-h-9 text-xs text-muted-foreground hover:text-foreground cursor-pointer"
                            >
                                Retake Quiz
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
