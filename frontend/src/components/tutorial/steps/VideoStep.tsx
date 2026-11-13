import { ArrowRight, CheckCircle2, ExternalLink, Loader2, PlayCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { isDone } from '@/lib/learnerPack'
import type { TutorialStepProps } from '../types'

const SPOKEN_TUTORIAL_URL = 'https://spoken-tutorial.org'
const SAMPLE_SUFFIX = '-English.webm'

export const VideoStep: React.FC<TutorialStepProps> = ({ detail, workspace, nav }) => {
    const isWatched = isDone(detail.userTutorial.watched)
    const videoUrl = detail.videoUrl

    if (!videoUrl) {
        return (
            <div className="max-w-lg mx-auto text-center space-y-5 p-6 sm:p-8 rounded-xl bg-card border border-border shadow-xs">
                <div className="size-14 rounded-xl bg-primary/10 text-primary flex items-center justify-center mx-auto">
                    <PlayCircle className="size-8" />
                </div>
                <div className="space-y-2">
                    <h2 className="text-lg font-bold text-foreground">Watch on Spoken Tutorial</h2>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                        This lesson's video plays on the Spoken Tutorial site, in English or dubbed into Indian regional languages.
                    </p>
                </div>
                <div className="flex flex-col sm:flex-row justify-center gap-3">
                    <Button asChild className="min-h-11 font-semibold">
                        <a href={SPOKEN_TUTORIAL_URL} target="_blank" rel="noopener noreferrer">
                            Open Spoken Tutorial player
                            <ExternalLink className="size-4" />
                        </a>
                    </Button>
                    <Button
                        variant="outline"
                        onClick={workspace.markVideoWatched}
                        disabled={isWatched}
                        className="min-h-11 cursor-pointer"
                    >
                        {isWatched ? 'Watched' : 'Mark as watched (+10 XP)'}
                    </Button>
                </div>
            </div>
        )
    }

    return (
        <div className="max-w-4xl mx-auto space-y-4">
            <div className="relative aspect-video w-full rounded-xl bg-black border border-border overflow-hidden shadow-sm">
                <video
                    key={videoUrl}
                    controls
                    playsInline
                    preload="auto"
                    poster={detail.videoPosterUrl || undefined}
                    className="w-full h-full object-contain"
                    onWaiting={() => workspace.setIsVideoBuffering(true)}
                    onPlaying={() => workspace.setIsVideoBuffering(false)}
                    onCanPlay={() => workspace.setIsVideoBuffering(false)}
                    onTimeUpdate={(e) => {
                        const video = e.currentTarget
                        if (video.duration > 0) {
                            workspace.reportVideoProgress(Math.round((video.currentTime / video.duration) * 100))
                        }
                    }}
                    onEnded={workspace.markVideoWatched}
                >
                    <source src={videoUrl} type="video/webm" />
                    {videoUrl.endsWith(SAMPLE_SUFFIX) && (
                        <source src={videoUrl.replace(SAMPLE_SUFFIX, '-English-sample.webm')} type="video/webm" />
                    )}
                    Your browser does not support WebM video streaming.
                </video>
            </div>

            <div className="flex items-center justify-between gap-3 p-3 sm:p-4 rounded-xl bg-card border border-border shadow-xs">
                {isWatched ? (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-success/10 border border-success/25 text-success text-xs font-semibold">
                        <CheckCircle2 className="size-4" />
                        <span>Watched</span>
                    </div>
                ) : workspace.isVideoBuffering ? (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted/60 border border-border text-xs font-medium text-muted-foreground">
                        <Loader2 className="size-3.5 animate-spin" />
                        <span>Buffering…</span>
                    </div>
                ) : (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted/60 border border-border text-xs font-medium text-muted-foreground">
                        <span>
                            Watched <span className="font-mono font-semibold text-foreground">{workspace.videoWatchPercent}%</span>
                        </span>
                    </div>
                )}
                {!isWatched && <p className="text-xs text-muted-foreground lg:hidden">Watch 80% to complete</p>}
                <Button
                    onClick={() => nav.goToStep('reading')}
                    className="min-h-11 sm:min-h-9 hidden lg:inline-flex text-xs font-semibold gap-1.5 cursor-pointer transition duration-200 ease-in-out"
                >
                    <span>Next: Reading notes</span>
                    <ArrowRight className="size-4" />
                </Button>
            </div>
        </div>
    )
}
