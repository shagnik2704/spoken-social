import { ChevronDown, Download, ExternalLink, FolderOpen, MessageSquare, MessageSquarePlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { buildMaterials } from '@/lib/learnerPack'
import type { CourseMaterialUrls } from '@/types'

interface TutorialResourcesProps {
    urls?: CourseMaterialUrls | null
    askForumUrl?: string | null
    browseForumUrl?: string | null
}

export const TutorialResources: React.FC<TutorialResourcesProps> = ({ urls, askForumUrl, browseForumUrl }) => {
    const materials = buildMaterials(urls)
    const hasForum = Boolean(askForumUrl || browseForumUrl)
    if (materials.length === 0 && !hasForum) return null

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" className="min-h-11 lg:min-h-9 gap-1.5 text-xs font-semibold cursor-pointer transition duration-200 ease-in-out">
                    <FolderOpen className="size-4" />
                    <span>Resources</span>
                    <ChevronDown className="size-3.5 text-muted-foreground" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-72">
                {materials.length > 0 && (
                    <>
                        <DropdownMenuLabel className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                            Course materials
                        </DropdownMenuLabel>
                        {materials.map((material) => {
                            const ActionIcon = material.isDownload ? Download : ExternalLink
                            return (
                                <DropdownMenuItem key={material.key} asChild className="min-h-11 cursor-pointer">
                                    <a
                                        href={material.url}
                                        {...(material.isDownload ? { download: true } : { target: '_blank', rel: 'noopener noreferrer' })}
                                    >
                                        <material.icon className="size-4 text-primary" />
                                        <span className="flex-1 min-w-0">
                                            <span className="block text-sm font-medium text-foreground">{material.title}</span>
                                            <span className="block text-[11px] text-muted-foreground truncate">{material.description}</span>
                                        </span>
                                        <ActionIcon className="size-3.5 text-muted-foreground" />
                                    </a>
                                </DropdownMenuItem>
                            )
                        })}
                    </>
                )}

                {hasForum && (
                    <>
                        {materials.length > 0 && <DropdownMenuSeparator />}
                        <DropdownMenuLabel className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                            Discussion Forum
                        </DropdownMenuLabel>
                        {askForumUrl && (
                            <DropdownMenuItem asChild className="min-h-11 cursor-pointer">
                                <a href={askForumUrl} target="_blank" rel="noopener noreferrer">
                                    <MessageSquarePlus className="size-4 text-primary" />
                                    <span className="flex-1 min-w-0">
                                        <span className="block text-sm font-medium text-foreground">Have doubts? Ask on forum</span>
                                        <span className="block text-[11px] text-muted-foreground truncate">Pre-filled for this tutorial</span>
                                    </span>
                                    <ExternalLink className="size-3.5 text-muted-foreground" />
                                </a>
                            </DropdownMenuItem>
                        )}
                        {browseForumUrl && (
                            <DropdownMenuItem asChild className="min-h-11 cursor-pointer">
                                <a href={browseForumUrl} target="_blank" rel="noopener noreferrer">
                                    <MessageSquare className="size-4 text-primary" />
                                    <span className="flex-1 min-w-0">
                                        <span className="block text-sm font-medium text-foreground">Browse Forum</span>
                                        <span className="block text-[11px] text-muted-foreground truncate">Explore questions by peers</span>
                                    </span>
                                    <ExternalLink className="size-3.5 text-muted-foreground" />
                                </a>
                            </DropdownMenuItem>
                        )}
                    </>
                )}
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
