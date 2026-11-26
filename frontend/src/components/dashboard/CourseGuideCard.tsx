import { useState } from 'react'
import { BookMarked, ChevronDown, GraduationCap, Layers, Percent, ShieldCheck, Video } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'
import type { CourseGuide } from '@/types'

const tutorialRange = (tutorials: number[]): string =>
    tutorials.length === 1 ? `Tutorial ${tutorials[0]}` : `Tutorials ${tutorials[0]}–${tutorials[tutorials.length - 1]}`

const weekRange = (weeks: number[]): string =>
    weeks.length === 1 ? `Week ${weeks[0]}` : `Weeks ${weeks[0]}–${weeks[weeks.length - 1]}`

interface GuideSectionProps {
    icon: React.ElementType
    title: string
    children: React.ReactNode
}

const GuideSection: React.FC<GuideSectionProps> = ({ icon: Icon, title, children }) => (
    <section className="space-y-3">
        <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <Icon className="size-3.5 text-teal" aria-hidden="true" />
            {title}
        </h3>
        {children}
    </section>
)

interface CourseGuideCardProps {
    guide: CourseGuide
}

export const CourseGuideCard: React.FC<CourseGuideCardProps> = ({ guide }) => {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <Card className="border border-border/80 bg-card shadow-xs py-0 gap-0 overflow-hidden transition-all duration-200 ease-in-out hover:border-primary/25">
            <Collapsible open={isOpen} onOpenChange={setIsOpen}>
                <CollapsibleTrigger asChild>
                    <button
                        type="button"
                        className="w-full flex items-center justify-between gap-3 p-4 sm:px-6 text-left cursor-pointer transition-colors duration-200 ease-in-out hover:bg-muted/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                    >
                        <span className="flex items-center gap-3 min-w-0">
                            <span className="size-9 shrink-0 rounded-lg bg-teal/10 text-teal border border-teal/20 flex items-center justify-center">
                                <BookMarked className="size-4" aria-hidden="true" />
                            </span>
                            <span className="min-w-0">
                                <span className="block text-sm font-semibold text-foreground">How this course works</span>
                                <span className="block text-xs text-muted-foreground">Modules, marks, live sessions and keeping your work safe</span>
                            </span>
                        </span>
                        <ChevronDown className={cn('size-4 shrink-0 text-muted-foreground transition-transform duration-200 ease-in-out', isOpen && 'rotate-180')} />
                    </button>
                </CollapsibleTrigger>

                <CollapsibleContent className="border-t border-border/70 px-4 sm:px-6 py-5 space-y-7">
                    {guide.intro && <p className="text-sm leading-6 text-foreground/85">{guide.intro}</p>}

                    {guide.modules.length > 0 && (
                        <GuideSection icon={Layers} title="Modules">
                            <ol className="space-y-2">
                                {guide.modules.map(module => (
                                    <li key={module.number} className="p-3.5 rounded-lg border border-border/70 bg-background/40">
                                        <p className="text-[11px] font-medium text-muted-foreground">
                                            <span className="font-mono font-semibold text-teal">Module {module.number}</span>
                                            <span aria-hidden="true"> · </span>
                                            {weekRange(module.weeks)}
                                            <span aria-hidden="true"> · </span>
                                            {tutorialRange(module.tutorials)}
                                        </p>
                                        <p className="mt-0.5 text-sm font-semibold text-foreground">{module.title}</p>
                                        {module.summary.map((paragraph, index) => (
                                            <p key={index} className="mt-1.5 text-xs leading-5 text-muted-foreground">{paragraph}</p>
                                        ))}
                                    </li>
                                ))}
                            </ol>
                        </GuideSection>
                    )}

                    {guide.marks.length > 0 && (
                        <GuideSection icon={Percent} title="What counts towards your marks">
                            <ul className="divide-y divide-border/60 rounded-lg border border-border/70">
                                {guide.marks.map(row => (
                                    <li key={row.what} className="flex items-start justify-between gap-4 p-3">
                                        <span className="min-w-0">
                                            <span className="block text-sm font-medium text-foreground">{row.what}</span>
                                            <span className="block text-xs text-muted-foreground">{row.how}</span>
                                        </span>
                                        <span className="shrink-0 font-mono text-sm font-semibold text-foreground">{row.marks}</span>
                                    </li>
                                ))}
                            </ul>
                            {guide.passRule && <p className="text-xs leading-5 text-muted-foreground">{guide.passRule}</p>}
                        </GuideSection>
                    )}

                    {guide.safetyRules.length > 0 && (
                        <GuideSection icon={ShieldCheck} title="Keeping your work safe">
                            <ul className="grid gap-2 sm:grid-cols-2">
                                {guide.safetyRules.map(rule => (
                                    <li key={rule.title} className="p-3 rounded-lg border border-warning/25 bg-warning/[0.06] text-xs leading-5 text-foreground/85">
                                        <span className="font-semibold text-foreground">{rule.title}</span> {rule.text}
                                    </li>
                                ))}
                            </ul>
                        </GuideSection>
                    )}

                    {guide.liveSessions.length > 0 && (
                        <GuideSection icon={Video} title="Live sessions">
                            {guide.liveSessionNote && <p className="text-xs leading-5 text-muted-foreground">{guide.liveSessionNote}</p>}
                            <ul className="space-y-2">
                                {guide.liveSessions.map(session => (
                                    <li key={session.number} className="text-xs leading-5 text-foreground/85">
                                        <span className="font-semibold text-foreground">
                                            Live session {session.number}
                                            {session.week !== undefined && <> · week <span className="font-mono">{session.week}</span></>}:
                                        </span>{' '}
                                        {session.text}
                                    </li>
                                ))}
                            </ul>
                        </GuideSection>
                    )}

                    {(guide.revision || guide.finalExam) && (
                        <GuideSection icon={GraduationCap} title="Final exam">
                            {guide.finalExam && <p className="text-xs leading-5 text-foreground/85">{guide.finalExam}</p>}
                            {guide.revision && (
                                <div className="space-y-1.5">
                                    <p className="text-xs font-medium text-foreground">{guide.revision.intro}</p>
                                    <ul className="list-disc pl-5 space-y-1 text-xs leading-5 text-muted-foreground marker:text-teal">
                                        {guide.revision.items.map(item => <li key={item}>{item}</li>)}
                                    </ul>
                                </div>
                            )}
                        </GuideSection>
                    )}
                </CollapsibleContent>
            </Collapsible>
        </Card>
    )
}
