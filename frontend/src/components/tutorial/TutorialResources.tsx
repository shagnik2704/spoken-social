import { ChevronDown, ChevronRight, Download, ExternalLink, FolderOpen, MessageSquare, MessageSquarePlus, MoreHorizontal, PlayCircle, X } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { buildMaterials, getGuideVideos } from '@/lib/learnerPack'
import type { CourseMaterialUrls } from '@/types'

interface TutorialResourcesProps {
    courseId?: string | null
    urls?: CourseMaterialUrls | null
    askForumUrl?: string | null
    browseForumUrl?: string | null
    forumXp?: { ask: number; answer: number }
}

interface ResourceLink {
    key: string
    icon: LucideIcon
    title: string
    description: string
    url: string
    isDownload: boolean
    xp?: number
}

interface ResourceSection {
    title: string
    links: ResourceLink[]
}

const buildSections = ({ courseId, urls, askForumUrl, browseForumUrl, forumXp }: TutorialResourcesProps): ResourceSection[] => {
    const materials: ResourceLink[] = [
        ...getGuideVideos(courseId).map((video) => ({
            key: video.key,
            icon: PlayCircle,
            title: video.title,
            description: `${video.description} · ${video.durationLabel}`,
            url: video.url,
            isDownload: false,
        })),
        ...buildMaterials(urls).map((material) => ({
            key: material.key,
            icon: material.icon,
            title: material.title,
            description: material.description,
            url: material.url,
            isDownload: material.isDownload,
        })),
    ]
    const forum: ResourceLink[] = []
    if (askForumUrl) {
        forum.push({
            key: 'ask',
            icon: MessageSquarePlus,
            title: 'Have doubts? Ask on forum',
            description: 'Pre-filled for this tutorial',
            url: askForumUrl,
            isDownload: false,
            xp: forumXp?.ask,
        })
    }
    if (browseForumUrl) {
        forum.push({
            key: 'browse',
            icon: MessageSquare,
            title: 'Browse Forum',
            description: "Answer a peer's question",
            url: browseForumUrl,
            isDownload: false,
            xp: forumXp?.answer,
        })
    }
    return [
        { title: 'Course materials', links: materials },
        { title: 'Discussion Forum', links: forum },
    ].filter(section => section.links.length > 0)
}

const linkProps = (link: ResourceLink): React.AnchorHTMLAttributes<HTMLAnchorElement> =>
    link.isDownload ? { href: link.url, download: true } : { href: link.url, target: '_blank', rel: 'noopener noreferrer' }

const LinkText: React.FC<{ link: ResourceLink }> = ({ link }) => (
    <span className="flex-1 min-w-0">
        <span className="block text-sm font-medium text-foreground">{link.title}</span>
        <span className="block text-[11px] text-muted-foreground truncate">
            {link.description}
            {link.xp ? <span className="font-mono font-semibold text-foreground"> · +{link.xp} XP</span> : null}
        </span>
    </span>
)

export const TutorialResources: React.FC<TutorialResourcesProps> = (props) => {
    const sections = buildSections(props)
    if (sections.length === 0) return null

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" className="min-h-9 gap-1.5 text-xs font-semibold cursor-pointer transition duration-200 ease-in-out">
                    <FolderOpen className="size-4" />
                    Resources
                    <ChevronDown className="size-3.5 text-muted-foreground" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-72">
                {sections.map((section, index) => (
                    <div key={section.title}>
                        {index > 0 && <DropdownMenuSeparator />}
                        <DropdownMenuLabel className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                            {section.title}
                        </DropdownMenuLabel>
                        {section.links.map((link) => {
                            const ActionIcon = link.isDownload ? Download : ExternalLink
                            return (
                                <DropdownMenuItem key={link.key} asChild className="min-h-11 cursor-pointer">
                                    <a {...linkProps(link)}>
                                        <link.icon className="size-4 text-primary" />
                                        <LinkText link={link} />
                                        <ActionIcon className="size-3.5 text-muted-foreground" />
                                    </a>
                                </DropdownMenuItem>
                            )
                        })}
                    </div>
                ))}
            </DropdownMenuContent>
        </DropdownMenu>
    )
}

export const TutorialActionsSheet: React.FC<TutorialResourcesProps & { tutorialTitle: string }> = ({ tutorialTitle, ...props }) => {
    const sections = buildSections(props)
    if (sections.length === 0) return null

    return (
        <Sheet>
            <SheetTrigger asChild>
                <Button variant="outline" className="min-h-11 gap-1.5 px-3 text-xs font-semibold cursor-pointer transition duration-200 ease-in-out">
                    <MoreHorizontal className="size-4" />
                    More
                </Button>
            </SheetTrigger>
            <SheetContent side="bottom" showCloseButton={false} className="rounded-t-2xl max-h-[85dvh] overflow-y-auto pb-[max(1rem,env(safe-area-inset-bottom))]">
                <div aria-hidden="true" className="mx-auto mt-2.5 h-1.5 w-10 rounded-full bg-border" />
                <div className="flex items-start gap-2 pr-2">
                    <SheetHeader className="flex-1 min-w-0 pt-1 pb-0">
                        <SheetTitle className="text-base">Files &amp; help</SheetTitle>
                        <SheetDescription className="truncate">{tutorialTitle}</SheetDescription>
                    </SheetHeader>
                    <SheetClose asChild>
                        <Button variant="ghost" size="icon" aria-label="Close" className="size-11 shrink-0 cursor-pointer">
                            <X className="size-5" />
                        </Button>
                    </SheetClose>
                </div>
                <div className="px-4 space-y-5">
                    {sections.map((section) => (
                        <section key={section.title} aria-label={section.title} className="space-y-1.5">
                            <h3 className="px-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{section.title}</h3>
                            <ul className="rounded-xl border border-border bg-card divide-y divide-border overflow-hidden">
                                {section.links.map((link) => {
                                    const ActionIcon = link.isDownload ? Download : ChevronRight
                                    return (
                                        <li key={link.key}>
                                            <a
                                                {...linkProps(link)}
                                                className="flex items-center gap-3 min-h-14 px-3.5 py-2.5 hover:bg-primary/5 active:bg-primary/10 transition duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                                            >
                                                <span className="size-9 shrink-0 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                                                    <link.icon className="size-4" />
                                                </span>
                                                <LinkText link={link} />
                                                <ActionIcon className="size-4 shrink-0 text-muted-foreground" />
                                            </a>
                                        </li>
                                    )
                                })}
                            </ul>
                        </section>
                    ))}
                </div>
            </SheetContent>
        </Sheet>
    )
}
