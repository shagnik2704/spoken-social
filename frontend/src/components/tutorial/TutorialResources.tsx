import { ChevronDown, Download, ExternalLink, FolderOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { buildMaterials } from '@/lib/learnerPack'
import type { CourseMaterialUrls } from '@/types'

interface TutorialResourcesProps {
    urls?: CourseMaterialUrls | null
}

export const TutorialResources: React.FC<TutorialResourcesProps> = ({ urls }) => {
    const materials = buildMaterials(urls)
    if (materials.length === 0) return null

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
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
