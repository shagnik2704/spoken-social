import { Download, ExternalLink } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { buildMaterials } from '@/lib/learnerPack'
import { cn } from '@/lib/utils'
import type { CourseMaterialUrls } from '@/types'

const GRID_COLUMNS: Record<number, string> = {
    1: 'sm:grid-cols-1',
    2: 'sm:grid-cols-2',
    3: 'sm:grid-cols-3',
}

interface CourseMaterialsCardProps {
    urls?: CourseMaterialUrls | null
}

export const CourseMaterialsCard: React.FC<CourseMaterialsCardProps> = ({ urls }) => {
    const materials = buildMaterials(urls)
    if (materials.length === 0) return null

    return (
        <Card className="border border-border/80 bg-card shadow-xs py-0 gap-0">
            <div className="px-4 sm:px-5 pt-4 flex items-baseline justify-between gap-3">
                <h3 className="text-sm font-semibold text-foreground">Course materials</h3>
                <p className="text-xs text-muted-foreground">Used across all tutorials</p>
            </div>
            <div className={cn('p-3 sm:p-4 grid gap-2', GRID_COLUMNS[materials.length] ?? 'sm:grid-cols-3')}>
                {materials.map((material) => {
                    const ActionIcon = material.isDownload ? Download : ExternalLink
                    return (
                        <a
                            key={material.key}
                            href={material.url}
                            title={material.description}
                            {...(material.isDownload ? { download: true } : { target: '_blank', rel: 'noopener noreferrer' })}
                            className="group flex items-center gap-3 min-h-14 p-3 rounded-lg border border-border/70 bg-card hover:border-primary/40 hover:bg-primary/[0.03] transition-all duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        >
                            <span className="size-9 shrink-0 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                                <material.icon className="size-4" />
                            </span>
                            <span className="min-w-0 flex-1">
                                <span className="block text-sm font-medium text-foreground truncate">{material.title}</span>
                                <span className="block text-[11px] text-muted-foreground">
                                    <span className="font-mono">{material.format}</span>
                                    {material.isDownload ? ' · Download' : ' · Opens in a new tab'}
                                </span>
                            </span>
                            <ActionIcon className="size-4 shrink-0 text-muted-foreground group-hover:text-primary transition-colors duration-200 ease-in-out" />
                        </a>
                    )
                })}
            </div>
        </Card>
    )
}
