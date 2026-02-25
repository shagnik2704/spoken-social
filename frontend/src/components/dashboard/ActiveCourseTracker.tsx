import { useState, useCallback } from 'react'
import {
    CheckCircle2, ChevronDown, ChevronUp,
    Zap, Code, Terminal, BarChart3, Settings, FileText,
    CircleDot, BookOpenCheck, Award, FileCheck, PlayCircle
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { CelebrationModal, type CelebrationType } from './CelebrationModal'

// ===== TYPES =====

interface Tutorial {
    id: string
    number: number
    title: string
    completed: boolean
    // Questionnaire checkboxes
    watched: boolean
    assignmentDone: boolean
    xpEarned: number
}

// ===== COURSE ICON MAP =====
const courseIconMap: Record<string, React.ReactNode> = {
    'Python': <Code className="h-5 w-5" />,
    'Linux': <Terminal className="h-5 w-5" />,
    'Scilab': <BarChart3 className="h-5 w-5" />,
    'C/C++': <Settings className="h-5 w-5" />,
    'LibreOffice': <FileText className="h-5 w-5" />,
}

// ===== MOCK DATA =====

const ACTIVE_COURSE = {
    title: 'Python',
    totalTutorials: 10,
}

const XP_PER_TUTORIAL = 30

const initialTutorials: Tutorial[] = [
    { id: '1', number: 1, title: 'Getting Started with IPython', completed: true, watched: true, assignmentDone: true, xpEarned: 30 },
    { id: '2', number: 2, title: 'Basic Data Types in Python', completed: true, watched: true, assignmentDone: true, xpEarned: 30 },
    { id: '3', number: 3, title: 'Input & Output', completed: true, watched: true, assignmentDone: true, xpEarned: 30 },
    { id: '4', number: 4, title: 'Lists and List Operations', completed: true, watched: true, assignmentDone: true, xpEarned: 30 },
    { id: '5', number: 5, title: 'Conditionals', completed: true, watched: true, assignmentDone: true, xpEarned: 30 },
    { id: '6', number: 6, title: 'Loops and Iterations', completed: true, watched: true, assignmentDone: true, xpEarned: 30 },
    { id: '7', number: 7, title: 'Working with Dictionaries', completed: false, watched: false, assignmentDone: false, xpEarned: 0 },
    { id: '8', number: 8, title: 'Sets and Tuples', completed: false, watched: false, assignmentDone: false, xpEarned: 0 },
    { id: '9', number: 9, title: 'Functions', completed: false, watched: false, assignmentDone: false, xpEarned: 0 },
    { id: '10', number: 10, title: 'File Handling', completed: false, watched: false, assignmentDone: false, xpEarned: 0 },
]

// ===== QUESTIONNAIRE COMPONENT =====

interface QuestionnaireProps {
    tutorial: Tutorial
    onCheckChange: (tutorialId: string, field: 'watched' | 'assignmentDone', value: boolean) => void
    onComplete: (tutorialId: string) => void
}

function Questionnaire({ tutorial, onCheckChange, onComplete }: QuestionnaireProps) {
    const allChecked = tutorial.watched && tutorial.assignmentDone

    const checks = [
        {
            key: 'watched' as const,
            label: 'Have you watched the tutorial?',
            icon: PlayCircle,
            checked: tutorial.watched,
        },
        {
            key: 'assignmentDone' as const,
            label: 'Have you finished the assignment?',
            icon: FileCheck,
            checked: tutorial.assignmentDone,
        },
    ]

    return (
        <div className="space-y-3">
            <div className="space-y-2">
                {checks.map((check) => {
                    const Icon = check.icon
                    return (
                        <label
                            key={check.key}
                            className={`flex items-center gap-3 p-3.5 rounded-xl border cursor-pointer transition-all duration-200
                                ${check.checked
                                    ? 'border-success/30 bg-success/5'
                                    : 'border-border bg-muted/20 hover:border-primary/30 hover:bg-muted/40'
                                }`}
                        >
                            <input
                                type="checkbox"
                                checked={check.checked}
                                onChange={(e) => onCheckChange(tutorial.id, check.key, e.target.checked)}
                                className="sr-only"
                            />
                            <div className={`flex h-7 w-7 items-center justify-center rounded-full shrink-0 transition-all duration-200
                                ${check.checked
                                    ? 'bg-success text-success-foreground'
                                    : 'bg-muted text-muted-foreground'
                                }`}
                            >
                                {check.checked ? (
                                    <CheckCircle2 className="h-4 w-4" />
                                ) : (
                                    <Icon className="h-3.5 w-3.5" />
                                )}
                            </div>
                            <span className={`text-sm transition-colors ${check.checked ? 'text-success font-medium' : 'text-foreground'}`}>
                                {check.label}
                            </span>
                        </label>
                    )
                })}
            </div>

            {allChecked && (
                <Button
                    onClick={() => onComplete(tutorial.id)}
                    className="w-full gap-2 bg-success hover:bg-success/90 text-white"
                >
                    <Award className="h-4 w-4" />
                    Complete Tutorial · Earn +{XP_PER_TUTORIAL} XP
                </Button>
            )}
        </div>
    )
}

// ===== PROGRESS DOTS =====

function ProgressDots({ tutorial }: { tutorial: Tutorial }) {
    const checks = [tutorial.watched, tutorial.assignmentDone]
    const doneCount = checks.filter(Boolean).length

    return (
        <div className="flex items-center gap-1">
            {checks.map((done, i) => (
                <div
                    key={i}
                    className={`h-1.5 w-1.5 rounded-full transition-colors ${done ? 'bg-success' : 'bg-muted-foreground/30'}`}
                />
            ))}
            {doneCount > 0 && doneCount < 2 && (
                <span className="text-[10px] text-muted-foreground ml-1">{doneCount}/2</span>
            )}
        </div>
    )
}

// ===== TUTORIAL TIMELINE ITEM =====

interface TimelineItemProps {
    tutorial: Tutorial
    isLast: boolean
    isActive: boolean
    onSelect: (tutorialId: string) => void
}

function TimelineItem({ tutorial, isLast, isActive, onSelect }: TimelineItemProps) {
    return (
        <div className="flex gap-3">
            {/* Timeline connector */}
            <div className="flex flex-col items-center">
                <button
                    onClick={() => !tutorial.completed && onSelect(tutorial.id)}
                    className={`flex h-8 w-8 items-center justify-center rounded-full shrink-0 transition-all
                        ${tutorial.completed
                            ? 'bg-success text-success-foreground'
                            : isActive
                                ? 'bg-primary text-primary-foreground ring-4 ring-primary/20'
                                : 'bg-muted text-muted-foreground hover:bg-primary/20 hover:text-primary cursor-pointer'
                        }`}
                >
                    {tutorial.completed ? (
                        <CheckCircle2 className="h-4 w-4" />
                    ) : (
                        <CircleDot className="h-4 w-4" />
                    )}
                </button>
                {!isLast && (
                    <div className={`w-0.5 flex-1 min-h-[20px] transition-colors
                        ${tutorial.completed ? 'bg-success/40' : 'bg-muted'}`}
                    />
                )}
            </div>

            {/* Content */}
            <div className="flex-1 pb-4 min-w-0">
                <button
                    onClick={() => !tutorial.completed && onSelect(tutorial.id)}
                    className={`flex items-center gap-2 flex-wrap text-left ${!tutorial.completed ? 'cursor-pointer' : ''}`}
                >
                    <span className={`text-sm font-medium truncate ${isActive ? 'text-primary' : ''}`}>
                        {tutorial.number}. {tutorial.title}
                    </span>
                    {!tutorial.completed && <ProgressDots tutorial={tutorial} />}
                </button>
                {tutorial.completed && (
                    <p className="text-[11px] text-muted-foreground mt-0.5 flex items-center gap-1">
                        <Zap className="h-3 w-3 text-xp-gold" />
                        {tutorial.xpEarned} XP earned
                    </p>
                )}
                {isActive && !tutorial.completed && (
                    <p className="text-[11px] text-primary mt-0.5 font-medium">
                        Currently selected
                    </p>
                )}
            </div>
        </div>
    )
}

// ===== MAIN COMPONENT =====

export function ActiveCourseTracker() {
    const [tutorials, setTutorials] = useState<Tutorial[]>(initialTutorials)
    const [activeTutorialId, setActiveTutorialId] = useState<string | null>(() => {
        // Default to first incomplete tutorial
        const first = initialTutorials.find(t => !t.completed)
        return first?.id || null
    })
    const [showTimeline, setShowTimeline] = useState(false)

    // Celebration state
    const [celebration, setCelebration] = useState<{
        type: CelebrationType
        xpEarned: number
        title?: string
        subtitle?: string
    } | null>(null)

    const activeTutorial = tutorials.find(t => t.id === activeTutorialId)
    const completedCount = tutorials.filter(t => t.completed).length
    const overallProgress = Math.round((completedCount / tutorials.length) * 100)

    const handleSelectTutorial = useCallback((tutorialId: string) => {
        setActiveTutorialId(tutorialId)
    }, [])

    const handleCheckChange = useCallback((tutorialId: string, field: 'watched' | 'assignmentDone', value: boolean) => {
        setTutorials(prev => prev.map(t =>
            t.id === tutorialId ? { ...t, [field]: value } : t
        ))
    }, [])

    const handleTutorialComplete = useCallback((tutorialId: string) => {
        const tutorial = tutorials.find(t => t.id === tutorialId)
        if (!tutorial) return

        const isLastTutorial = completedCount + 1 === tutorials.length

        setTutorials(prev => prev.map(t =>
            t.id === tutorialId
                ? { ...t, completed: true, xpEarned: XP_PER_TUTORIAL }
                : t
        ))

        // Move to next incomplete tutorial
        const nextIncomplete = tutorials.find(t => !t.completed && t.id !== tutorialId)
        setActiveTutorialId(nextIncomplete?.id || null)

        // Show celebration
        if (isLastTutorial) {
            setCelebration({
                type: 'course_complete',
                xpEarned: XP_PER_TUTORIAL,
                title: `${ACTIVE_COURSE.title} Complete! 🏆`,
                subtitle: `You've mastered all ${tutorials.length} tutorials. Share your achievement!`,
            })
        } else {
            setCelebration({
                type: 'tutorial_complete',
                xpEarned: XP_PER_TUTORIAL,
                title: 'Tutorial Complete! ✨',
                subtitle: `You earned ${XP_PER_TUTORIAL} XP! Pick any tutorial to continue.`,
            })
        }
    }, [tutorials, completedCount])

    const handleShare = useCallback(() => {
        setCelebration(null)
        console.log('Share achievement — will open compose modal')
    }, [])

    const handleCloseCelebration = useCallback(() => {
        setCelebration(null)
    }, [])

    const allDone = completedCount === tutorials.length

    return (
        <>
            <Card className="border-primary/20 bg-gradient-to-br from-primary/[0.03] via-transparent to-transparent overflow-hidden">
                <CardContent className="p-5 sm:p-6">
                    {/* Header */}
                    <div className="flex items-center justify-between gap-3 mb-5">
                        <div className="flex items-center gap-3 min-w-0">
                            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 shrink-0">
                                {courseIconMap[ACTIVE_COURSE.title] || <Code className="h-5 w-5 text-primary" />}
                            </div>
                            <div className="min-w-0">
                                <div className="flex items-center gap-2">
                                    <h2 className="text-sm font-bold">{ACTIVE_COURSE.title}</h2>
                                    <Badge variant="secondary" className="text-[10px] px-1.5 h-5">
                                        {completedCount}/{tutorials.length}
                                    </Badge>
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                    <Progress value={overallProgress} className="h-1.5 flex-1 max-w-[120px]" />
                                    <span className="text-[11px] text-muted-foreground font-mono">{overallProgress}%</span>
                                </div>
                            </div>
                        </div>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowTimeline(!showTimeline)}
                            className="shrink-0 text-xs text-muted-foreground hover:text-foreground gap-1"
                        >
                            {showTimeline ? 'Hide' : 'All Tutorials'}
                            {showTimeline ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                        </Button>
                    </div>

                    {/* Current Tutorial Questionnaire */}
                    {activeTutorial && !activeTutorial.completed && !allDone && (
                        <div className="mb-4">
                            <div className="bg-muted/30 rounded-xl p-4 border border-border/50">
                                <div className="flex items-center gap-2 mb-1">
                                    <BookOpenCheck className="h-4 w-4 text-primary" />
                                    <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
                                        Tutorial {activeTutorial.number}
                                    </span>
                                </div>
                                <h3 className="text-base font-semibold mb-4">{activeTutorial.title}</h3>

                                <Questionnaire
                                    tutorial={activeTutorial}
                                    onCheckChange={handleCheckChange}
                                    onComplete={handleTutorialComplete}
                                />
                            </div>
                        </div>
                    )}

                    {/* All complete indicator */}
                    {allDone && (
                        <div className="mb-4 p-5 rounded-xl bg-gradient-to-r from-success/10 to-primary/10 border border-success/20 text-center">
                            <Award className="h-10 w-10 text-success mx-auto mb-2" />
                            <h3 className="font-bold text-lg">Course Complete! 🏆</h3>
                            <p className="text-sm text-muted-foreground mt-1">
                                You've finished all {tutorials.length} tutorials in {ACTIVE_COURSE.title}!
                            </p>
                        </div>
                    )}

                    {/* Expandable Timeline */}
                    {showTimeline && (
                        <div className="mt-4 pt-4 border-t border-border">
                            <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-4">
                                All Tutorials — click any to start
                            </p>
                            <div>
                                {tutorials.map((tutorial, i) => (
                                    <TimelineItem
                                        key={tutorial.id}
                                        tutorial={tutorial}
                                        isLast={i === tutorials.length - 1}
                                        isActive={tutorial.id === activeTutorialId}
                                        onSelect={handleSelectTutorial}
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Celebration Modal */}
            {celebration && (
                <CelebrationModal
                    type={celebration.type}
                    xpEarned={celebration.xpEarned}
                    title={celebration.title}
                    subtitle={celebration.subtitle}
                    onClose={handleCloseCelebration}
                    onShare={handleShare}
                />
            )}
        </>
    )
}
