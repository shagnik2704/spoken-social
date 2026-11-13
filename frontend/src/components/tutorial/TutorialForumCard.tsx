import React from 'react'
import { ExternalLink, MessageSquarePlus, Sparkles } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getForumAskUrl, getForumCategoryUrl } from '@/lib/learnerPack'

interface TutorialForumCardProps {
    courseId?: string | null
    forumCategory?: string | null
    courseTitle?: string | null
    tutorialTitle: string
}

export const TutorialForumCard: React.FC<TutorialForumCardProps> = ({
    courseId,
    forumCategory,
    courseTitle,
    tutorialTitle,
}) => {
    const askUrl = getForumAskUrl({
        courseId,
        forumCategory,
        courseTitle,
        tutorialTitle,
    })
    const browseUrl = getForumCategoryUrl(forumCategory, courseTitle)

    return (
        <section
            aria-label="Discussion forum help"
            className="mt-8 rounded-2xl border border-primary/20 bg-gradient-to-r from-primary/[0.04] via-card to-primary/[0.07] p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs"
        >
            <div className="flex items-start gap-3.5 min-w-0">
                <div className="size-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 mt-0.5">
                    <MessageSquarePlus className="size-5" />
                </div>
                <div className="space-y-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-sm font-bold text-foreground">
                            Have doubts or questions on this tutorial?
                        </h3>
                        <Badge
                            variant="outline"
                            className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/25 gap-1 shrink-0"
                        >
                            <Sparkles className="size-3 text-emerald-500" />
                            +5 XP for questions
                        </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                        Ask on the official Spoken Tutorial Forum right away. Your question is pre-tagged with this tutorial so instructors &amp; peers can answer quickly.
                    </p>
                </div>
            </div>

            <div className="flex flex-col sm:items-end gap-1.5 w-full sm:w-auto shrink-0">
                <Button
                    asChild
                    size="sm"
                    className="w-full sm:w-auto min-h-10 sm:min-h-9 gap-1.5 px-3.5 font-semibold text-xs bg-primary hover:bg-primary/90 text-primary-foreground shadow-xs cursor-pointer transition-all duration-200"
                >
                    <a href={askUrl} target="_blank" rel="noopener noreferrer">
                        <MessageSquarePlus className="size-3.5" />
                        <span>Ask on Forum</span>
                        <ExternalLink className="size-3.5 opacity-80" />
                    </a>
                </Button>
                <a
                    href={browseUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] font-medium text-muted-foreground hover:text-primary transition-colors inline-flex items-center gap-1 self-center sm:self-end"
                >
                    <span>Browse discussions</span>
                    <ExternalLink className="size-3" />
                </a>
            </div>
        </section>
    )
}
