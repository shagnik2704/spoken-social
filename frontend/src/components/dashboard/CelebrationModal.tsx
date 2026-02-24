import { useEffect, useMemo } from 'react'
import {
    Trophy, CheckCircle2, FileCheck, Sparkles,
    Share2, ArrowRight, Zap, X, Star
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

// ===== TYPES =====

export type CelebrationType =
    | 'tutorial_watched'
    | 'quiz_aced'
    | 'assignment_uploaded'
    | 'tutorial_complete'
    | 'course_complete'

export interface CelebrationModalProps {
    type: CelebrationType
    xpEarned: number
    title?: string
    subtitle?: string
    onClose: () => void
    onShare?: () => void
}

// ===== CONFETTI =====

const CONFETTI_COLORS = [
    '#283593', '#5C6BC0', '#7986CB',  // Indigo shades
    '#FBBF24', '#F59E0B',              // Gold
    '#10B981', '#34D399',              // Green
    '#EC4899',                          // Pink
    '#3B82F6',                          // Blue
]

interface ConfettiPiece {
    id: number
    left: number
    delay: number
    duration: number
    color: string
    width: number
    height: number
    rotation: number
    shape: 'rect' | 'circle' | 'strip'
}

function Confetti({ intensity = 'medium' }: { intensity?: 'low' | 'medium' | 'high' }) {
    const pieces = useMemo<ConfettiPiece[]>(() => {
        const count = intensity === 'high' ? 100 : intensity === 'medium' ? 60 : 30
        return Array.from({ length: count }, (_, i) => {
            const shapes: ('rect' | 'circle' | 'strip')[] = ['rect', 'circle', 'strip']
            return {
                id: i,
                left: Math.random() * 100,
                delay: Math.random() * 2.5,
                duration: 2.5 + Math.random() * 3,
                color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
                width: 6 + Math.random() * 10,
                height: 4 + Math.random() * 6,
                rotation: Math.random() * 360,
                shape: shapes[Math.floor(Math.random() * shapes.length)],
            }
        })
    }, [intensity])

    return (
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
            {pieces.map((p) => (
                <div
                    key={p.id}
                    style={{
                        position: 'absolute',
                        left: `${p.left}%`,
                        top: '-12px',
                        width: `${p.shape === 'strip' ? p.width * 0.4 : p.width}px`,
                        height: `${p.shape === 'strip' ? p.height * 2 : p.shape === 'circle' ? p.width : p.height}px`,
                        backgroundColor: p.color,
                        borderRadius: p.shape === 'circle' ? '50%' : '2px',
                        animation: `confetti-fall ${p.duration}s ease-in ${p.delay}s forwards`,
                        transform: `rotate(${p.rotation}deg)`,
                        opacity: 0.85,
                    }}
                />
            ))}
        </div>
    )
}

// ===== CELEBRATION CONFIGS =====

interface CelebrationConfig {
    icon: React.ElementType
    emoji: string
    heading: string
    defaultSubtitle: string
    iconBg: string
    iconColor: string
    confettiIntensity: 'low' | 'medium' | 'high'
    accentGradient: string
}

const celebrationConfigs: Record<CelebrationType, CelebrationConfig> = {
    tutorial_watched: {
        icon: CheckCircle2,
        emoji: '🎯',
        heading: 'Tutorial Complete!',
        defaultSubtitle: "Great work! You've finished watching this tutorial.",
        iconBg: 'bg-success/10',
        iconColor: 'text-success',
        confettiIntensity: 'low',
        accentGradient: 'from-success/10 via-transparent to-primary/10',
    },
    quiz_aced: {
        icon: Star,
        emoji: '🧠',
        heading: 'Quiz Aced!',
        defaultSubtitle: 'Perfect score! You really know your stuff.',
        iconBg: 'bg-xp-gold/10',
        iconColor: 'text-xp-gold',
        confettiIntensity: 'medium',
        accentGradient: 'from-xp-gold/10 via-transparent to-primary/10',
    },
    assignment_uploaded: {
        icon: FileCheck,
        emoji: '📝',
        heading: 'Assignment Submitted!',
        defaultSubtitle: "Your practice work has been uploaded successfully.",
        iconBg: 'bg-primary/10',
        iconColor: 'text-primary',
        confettiIntensity: 'medium',
        accentGradient: 'from-primary/10 via-transparent to-success/10',
    },
    tutorial_complete: {
        icon: Sparkles,
        emoji: '✨',
        heading: 'Tutorial Mastered!',
        defaultSubtitle: "You've completed all steps for this tutorial.",
        iconBg: 'bg-primary/10',
        iconColor: 'text-primary',
        confettiIntensity: 'medium',
        accentGradient: 'from-primary/10 via-xp-gold/5 to-success/10',
    },
    course_complete: {
        icon: Trophy,
        emoji: '🏆',
        heading: 'Course Complete!',
        defaultSubtitle: "Amazing! You've finished the entire course!",
        iconBg: 'bg-xp-gold/15',
        iconColor: 'text-xp-gold',
        confettiIntensity: 'high',
        accentGradient: 'from-xp-gold/15 via-primary/10 to-success/10',
    },
}

// ===== MAIN COMPONENT =====

export function CelebrationModal({
    type,
    xpEarned,
    title,
    subtitle,
    onClose,
    onShare,
}: CelebrationModalProps) {
    const config = celebrationConfigs[type]
    const Icon = config.icon

    // Prevent background scroll
    useEffect(() => {
        document.body.style.overflow = 'hidden'
        return () => {
            document.body.style.overflow = ''
        }
    }, [])

    // ESC to close
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose()
        }
        window.addEventListener('keydown', handleEsc)
        return () => window.removeEventListener('keydown', handleEsc)
    }, [onClose])

    const isBigCelebration = type === 'course_complete' || type === 'tutorial_complete'

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
                onClick={onClose}
            />

            {/* Confetti */}
            <Confetti intensity={config.confettiIntensity} />

            {/* Modal Card */}
            <div
                className={`relative w-full max-w-sm bg-card border border-border rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-300`}
                style={{
                    animation: isBigCelebration
                        ? 'glow-pulse 2s ease-in-out infinite, celebration-icon-pop 0.5s ease-out'
                        : 'celebration-icon-pop 0.5s ease-out',
                }}
            >
                {/* Gradient accent strip */}
                <div className={`h-1.5 w-full bg-gradient-to-r ${config.accentGradient}`} />

                {/* Close button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-muted transition-colors z-10"
                >
                    <X className="h-4 w-4 text-muted-foreground" />
                </button>

                {/* Content */}
                <div className="p-8 text-center">
                    {/* Emoji + Icon */}
                    <div
                        className="flex justify-center mb-5"
                        style={{ animation: 'celebration-icon-pop 0.6s ease-out' }}
                    >
                        <div className={`relative flex h-20 w-20 items-center justify-center rounded-full ${config.iconBg}`}>
                            <Icon className={`h-10 w-10 ${config.iconColor}`} />
                            <span
                                className="absolute -top-1 -right-1 text-2xl"
                                style={{ animation: 'celebration-icon-pop 0.8s ease-out 0.3s both' }}
                            >
                                {config.emoji}
                            </span>
                        </div>
                    </div>

                    {/* Heading */}
                    <h2
                        className="text-xl font-bold mb-1.5"
                        style={{ animation: 'celebration-text-slide 0.5s ease-out 0.2s both' }}
                    >
                        {title || config.heading}
                    </h2>

                    <p
                        className="text-sm text-muted-foreground mb-6 max-w-xs mx-auto"
                        style={{ animation: 'celebration-text-slide 0.5s ease-out 0.35s both' }}
                    >
                        {subtitle || config.defaultSubtitle}
                    </p>

                    {/* XP Badge */}
                    <div
                        className="flex justify-center mb-6"
                        style={{ animation: 'xp-counter 0.6s ease-out 0.5s both' }}
                    >
                        <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-xp-gold/10 border border-xp-gold/20">
                            <Zap className="h-5 w-5 text-xp-gold" />
                            <span className="text-xl font-bold text-xp-gold font-mono">
                                +{xpEarned}
                            </span>
                            <Badge className="bg-xp-gold/20 text-xp-gold text-[10px] border-0">
                                XP
                            </Badge>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div
                        className="space-y-2.5"
                        style={{ animation: 'celebration-text-slide 0.5s ease-out 0.6s both' }}
                    >
                        {/* Share Achievement */}
                        {onShare && (
                            <Button
                                onClick={onShare}
                                variant="outline"
                                className="w-full gap-2 border-primary/20 text-primary hover:bg-primary/5"
                            >
                                <Share2 className="h-4 w-4" />
                                Share Achievement
                            </Button>
                        )}

                        {/* Continue */}
                        <Button
                            onClick={onClose}
                            className="w-full gap-2 bg-primary hover:bg-primary/90 text-primary-foreground"
                        >
                            {type === 'course_complete' ? 'Celebrate! 🎉' : 'Continue'}
                            <ArrowRight className="h-4 w-4" />
                        </Button>
                    </div>
                </div>

                {/* Shimmer effect for big celebrations */}
                {isBigCelebration && (
                    <div
                        className="absolute inset-0 pointer-events-none opacity-20"
                        style={{
                            background: 'linear-gradient(90deg, transparent, rgba(251,191,36,0.3), transparent)',
                            backgroundSize: '200% 100%',
                            animation: 'shimmer 3s linear infinite',
                        }}
                    />
                )}
            </div>
        </div>
    )
}
