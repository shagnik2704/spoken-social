import { ArrowRight, BookOpen } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Button } from '@/components/ui/button'
import { isDone, withXp } from '@/lib/learnerPack'
import type { TutorialStepProps } from '../types'
import { READING_COMPONENTS } from '../readingMarkdown'
import { ReadingExtras } from '../ReadingExtras'

export const ReadingStep: React.FC<TutorialStepProps> = ({ detail, workspace, nav }) => {
    const isRead = isDone(detail.userTutorial.readingDone)
    const readingXp = !detail.videoUrl ? nav.xpFor('watched') : 0
    const markAsRead = readingXp > 0 ? `Mark as read to claim +${readingXp} XP` : 'Mark as read'
    const readingMinutes = detail.content?.readingTimeMinutes ?? 0
    const hasPracticeTask = nav.isCreativeAi || nav.isInteractiveAi
    const nextStep = nav.isLinux
        ? nav.isSetup
            ? { done: 'Core lesson completed. Move to the setup assignment.', todo: 'and complete the setup assignment', button: 'Proceed to Assignment' }
            : { done: 'Core lesson completed. Move directly to the hands-on terminal assignment.', todo: 'and complete the terminal assignment', button: 'Proceed to Assignment' }
        : hasPracticeTask
            ? { done: 'Reading done. Next, try it yourself in the practice task.', todo: 'and go on to the practice task', button: 'Go to Practice Task' }
            : { done: 'Core lesson completed. Move directly to the notebook activity & reflection.', todo: 'and move directly to the personal notebook exercise & reflection', button: 'Proceed to Activity & Reflection' }

    return (
        <div>
            <div className="max-w-3xl mx-auto space-y-6">
                <article className="rounded-xl bg-card border border-border shadow-xs px-5 py-6 sm:px-10 sm:py-9">
                    <p className="inline-flex items-center gap-1.5 mb-4 text-[11px] font-semibold uppercase tracking-wider text-teal">
                        <BookOpen className="size-3.5" />
                        Reading notes
                        {readingMinutes > 0 && (
                            <span className="normal-case tracking-normal font-medium text-muted-foreground">
                                · <span className="font-mono">{readingMinutes}</span> min read
                            </span>
                        )}
                    </p>
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={READING_COMPONENTS}>
                        {detail.content?.readingMarkdown || ''}
                    </ReactMarkdown>
                    <ReadingExtras
                        keyTerms={detail.content?.keyTerms}
                        readMore={detail.content?.readMore}
                        keyTermsTitle={hasPracticeTask ?'Key terms for this module' : 'Key terms'}
                    />
                </article>

                {/* Completion Banner at bottom of reading */}
                <div className="p-5 sm:p-6 rounded-xl bg-card border border-border/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="space-y-1 text-center sm:text-left">
                        <h4 className="font-bold text-foreground text-sm sm:text-base">
                            {isRead ? 'Lesson Reading Complete' : 'Finished this reading?'}
                        </h4>
                        <p className="text-xs text-muted-foreground">
                            {isRead ? nextStep.done : `${markAsRead} ${nextStep.todo}.`}
                        </p>
                    </div>
                    <Button
                        size="lg"
                        onClick={async () => {
                            if (!isRead) {
                                await workspace.markReadingComplete()
                            }
                            nav.goToStep('activity')
                        }}
                        className="min-h-11 sm:min-h-9 font-semibold text-xs sm:text-sm shrink-0 gap-1.5 w-full sm:w-auto cursor-pointer"
                    >
                        {isRead ? nextStep.button : `${withXp('Mark Complete', readingXp)} & Continue`}
                        <ArrowRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    )
}
