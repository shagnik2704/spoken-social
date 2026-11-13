import { ArrowRight, BookOpen } from 'lucide-react'
import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Button } from '@/components/ui/button'
import { isDone } from '@/lib/learnerPack'
import type { TutorialStepProps } from '../types'

const READING_COMPONENTS: Components = {
    h1: ({ ...props }) => <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground mb-6 font-sans" {...props} />,
    h2: ({ ...props }) => <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground mt-10 mb-3 pl-3 border-l-4 border-teal font-sans" {...props} />,
    h3: ({ ...props }) => <h3 className="text-lg sm:text-xl font-bold text-foreground mt-9 mb-3 pl-3 border-l-4 border-teal font-sans" {...props} />,
    h4: ({ ...props }) => <h4 className="text-base sm:text-lg font-semibold text-foreground mt-6 mb-2 font-sans" {...props} />,
    p: ({ ...props }) => <p className="mb-4 text-sm sm:text-base leading-7 text-foreground/85 font-sans" {...props} />,
    ul: ({ ...props }) => <ul className="list-disc pl-6 mb-4 space-y-2 text-sm sm:text-base text-foreground/85 marker:text-teal" {...props} />,
    ol: ({ ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-sm sm:text-base text-foreground/85 marker:text-teal marker:font-semibold" {...props} />,
    li: ({ ...props }) => <li className="leading-7" {...props} />,
    a: ({ ...props }) => <a className="font-medium text-teal underline underline-offset-2 hover:no-underline transition duration-200 ease-in-out" target="_blank" rel="noopener noreferrer" {...props} />,
    code: ({ ...props }) => <code className="font-terminal text-[0.9em] px-1.5 py-0.5 rounded-md bg-teal/10 text-teal border border-teal/20" {...props} />,
    pre: ({ ...props }) => <pre className="my-5 p-4 rounded-xl bg-terminal border border-terminal-border font-terminal text-[13px] leading-6 text-terminal-fg overflow-x-auto [&_code]:bg-transparent [&_code]:border-0 [&_code]:p-0 [&_code]:text-inherit" {...props} />,
    blockquote: ({ ...props }) => <blockquote className="my-5 pl-4 pr-3 py-3 border-l-4 border-teal bg-teal/[0.06] rounded-r-lg text-foreground/90 [&>p:last-child]:mb-0" {...props} />,
    table: ({ ...props }) => <div className="my-6 overflow-x-auto rounded-xl border border-border"><table className="w-full border-collapse text-left" {...props} /></div>,
    thead: ({ ...props }) => <thead className="bg-primary/[0.06] text-foreground text-xs sm:text-sm font-semibold border-b border-border" {...props} />,
    th: ({ ...props }) => <th className="px-4 py-3 text-left font-bold border-r border-border/40 last:border-r-0" {...props} />,
    td: ({ ...props }) => <td className="px-4 py-3 text-xs sm:text-sm text-foreground/85 border-t border-border/40 border-r border-border/30 last:border-r-0" {...props} />,
    hr: ({ ...props }) => <hr className="my-8 border-border" {...props} />,
    strong: ({ ...props }) => <strong className="font-semibold text-foreground" {...props} />,
}

export const ReadingStep: React.FC<TutorialStepProps> = ({ detail, workspace, nav }) => {
    const isRead = isDone(detail.userTutorial.watched)
    const readingMinutes = detail.content?.readingTimeMinutes ?? 0

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
                </article>

                {/* Completion Banner at bottom of reading */}
                <div className="p-5 sm:p-6 rounded-xl bg-card border border-border/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="space-y-1 text-center sm:text-left">
                        <h4 className="font-bold text-foreground text-sm sm:text-base">
                            {isRead ? 'Lesson Reading Complete' : 'Finished this reading?'}
                        </h4>
                        <p className="text-xs text-muted-foreground">
                            {isRead
                                ? (nav.isLinux
                                    ? (nav.isSetup ? 'Core lesson completed. Move to verify your local lab environment.' : 'Core lesson completed. Move directly to hands-on terminal practice.')
                                    : 'Core lesson completed. Move directly to the notebook activity & reflection.')
                                : (nav.isLinux
                                    ? (nav.isSetup ? 'Mark as read to claim +10 XP and set up your lab environment.' : 'Mark as read to claim +10 XP and practice Linux commands.')
                                    : 'Mark as read to claim +10 XP and move directly to the personal notebook exercise & reflection.')}
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
                        {isRead
                            ? (nav.isLinux
                                ? (nav.isSetup ? 'Proceed to Setup Verification' : 'Proceed to Terminal Lab')
                                : 'Proceed to Activity & Reflection')
                            : 'Mark Complete (+10 XP) & Continue'}
                        <ArrowRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    )
}
