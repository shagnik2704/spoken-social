import { useState } from 'react'
import { Play, PlayCircle, VideoOff, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog'
import { useWalkthroughSeen } from '@/hooks/useWalkthroughSeen'
import { getCourseWalkthrough, WALKTHROUGH_WATCHED_FRACTION, type CourseWalkthrough as Walkthrough } from '@/lib/walkthroughs'
import { cn } from '@/lib/utils'
import { useUserStore } from '@/store/userStore'

interface WalkthroughPlayerProps {
    walkthrough: Walkthrough
    courseTitle: string
    open: boolean
    onOpenChange: (open: boolean) => void
    onWatched: () => void
}

const WalkthroughPlayer: React.FC<WalkthroughPlayerProps> = ({ walkthrough, courseTitle, open, onOpenChange, onWatched }) => {
    const [failedUrl, setFailedUrl] = useState<string | null>(null)
    const hasFailed = failedUrl === walkthrough.videoUrl

    const handleTimeUpdate = (event: React.SyntheticEvent<HTMLVideoElement>): void => {
        const { currentTime, duration } = event.currentTarget
        if (duration > 0 && currentTime / duration >= WALKTHROUGH_WATCHED_FRACTION) onWatched()
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent showCloseButton={false} className="sm:max-w-4xl p-0 gap-0 overflow-hidden bg-card">
                <div className="flex items-center justify-between gap-3 pl-4 sm:pl-5 pr-1.5 py-1.5 border-b border-border">
                    <div className="min-w-0">
                        <DialogTitle className="text-sm font-semibold text-foreground truncate">{courseTitle} · Course tour</DialogTitle>
                        <DialogDescription className="text-xs text-muted-foreground truncate">{walkthrough.summary}</DialogDescription>
                    </div>
                    <DialogClose asChild>
                        <Button variant="ghost" size="icon" className="size-11 shrink-0 cursor-pointer transition duration-200 ease-in-out" aria-label="Close course tour">
                            <X className="size-4" />
                        </Button>
                    </DialogClose>
                </div>
                {hasFailed ? (
                    <div className="aspect-video flex flex-col items-center justify-center gap-2 bg-terminal text-terminal-fg px-6 text-center">
                        <VideoOff className="size-6 text-terminal-muted" aria-hidden="true" />
                        <p className="text-sm font-semibold">The course tour isn't available yet</p>
                        <p className="text-xs text-terminal-muted">Check back soon. Everything it covers is already on your dashboard.</p>
                    </div>
                ) : (
                    <video
                        key={walkthrough.videoUrl}
                        src={walkthrough.videoUrl}
                        poster={walkthrough.posterUrl}
                        controls
                        autoPlay
                        playsInline
                        preload="metadata"
                        onTimeUpdate={handleTimeUpdate}
                        onEnded={onWatched}
                        onError={() => setFailedUrl(walkthrough.videoUrl)}
                        className="block w-full aspect-video bg-terminal"
                    >
                        {walkthrough.captionsUrl && (
                            <track kind="captions" src={walkthrough.captionsUrl} srcLang="en" label="English" default />
                        )}
                    </video>
                )}
            </DialogContent>
        </Dialog>
    )
}

interface CourseWalkthroughProps {
    courseId?: string | null
    courseTitle?: string
    className?: string
}

export const CourseWalkthrough: React.FC<CourseWalkthroughProps> = ({ courseId, courseTitle, className }) => {
    const userId = useUserStore(state => state.user?.id)
    const walkthrough = getCourseWalkthrough(courseId)
    const [seen, markSeen] = useWalkthroughSeen(userId, courseId)
    const [isOpen, setIsOpen] = useState(false)

    if (!walkthrough) return null

    const openPlayer = (): void => setIsOpen(true)

    return (
        <>
            {seen ? (
                <div className={cn('shrink-0', className)}>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={openPlayer}
                        className="min-h-11 lg:min-h-9 gap-1.5 px-3 text-xs font-semibold cursor-pointer transition duration-200 ease-in-out"
                    >
                        <PlayCircle className="size-4 text-teal" />
                        Course tour
                        <span className="font-mono font-medium text-muted-foreground">{walkthrough.durationLabel}</span>
                    </Button>
                </div>
            ) : (
                <div
                    className={cn(
                        'group flex items-center gap-3 p-2.5 pr-3 rounded-xl border border-primary/25 bg-card shadow-xs hover:border-primary/45 hover:scale-[1.01] transition-all duration-300 ease-in-out lg:w-[22rem] lg:shrink-0',
                        className
                    )}
                >
                    <button
                        type="button"
                        onClick={openPlayer}
                        aria-label={`Play the ${walkthrough.durationLabel} course tour`}
                        className="relative shrink-0 w-24 sm:w-28 aspect-video rounded-lg overflow-hidden bg-terminal cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                        <img src={walkthrough.posterUrl} alt="" className="absolute inset-0 size-full object-cover" />
                        <span className="absolute inset-0 flex items-center justify-center bg-terminal/30 group-hover:bg-terminal/10 transition-colors duration-200 ease-in-out">
                            <span className="size-8 rounded-full bg-white/95 text-terminal flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform duration-200 ease-in-out">
                                <Play className="size-3.5 fill-current translate-x-px" />
                            </span>
                        </span>
                        <span className="absolute right-1 bottom-1 px-1 rounded bg-terminal/80 text-terminal-fg font-mono text-[10px] leading-4">
                            {walkthrough.durationLabel}
                        </span>
                    </button>
                    <div className="min-w-0 flex-1">
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-teal">New here?</p>
                        <p className="text-sm font-semibold text-foreground leading-snug">Take the course tour</p>
                        <p className="text-xs text-muted-foreground truncate">{walkthrough.summary}</p>
                        <div className="mt-1.5 flex items-center gap-1 -ml-1">
                            <Button
                                size="sm"
                                onClick={openPlayer}
                                className="min-h-11 lg:min-h-8 px-3 text-xs font-semibold cursor-pointer transition duration-200 ease-in-out"
                            >
                                <Play className="size-3 fill-current" />
                                Watch
                            </Button>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={markSeen}
                                className="min-h-11 lg:min-h-8 px-2.5 text-xs text-muted-foreground hover:text-foreground cursor-pointer transition duration-200 ease-in-out"
                            >
                                I've got it
                            </Button>
                        </div>
                    </div>
                </div>
            )}
            <WalkthroughPlayer
                walkthrough={walkthrough}
                courseTitle={courseTitle ?? 'Course'}
                open={isOpen}
                onOpenChange={setIsOpen}
                onWatched={markSeen}
            />
        </>
    )
}
