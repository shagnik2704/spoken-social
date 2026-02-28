import { useState, useEffect } from 'react'
import {
    X, AlertTriangle, Eye,
    CheckCircle2, MessageSquare, PenTool, BookOpen,
    Clock, Layers, List, Loader2
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { REASON_LABELS, STEP_TYPE_LABELS } from '@/lib/feedbackReasons'
import api from '@/lib/axios'


// ===== TYPES =====

interface FeedbackEntry {
    id: number
    tutorialId: string
    tutorialNumber: number
    tutorialTitle: string
    stepType: string
    reasons: string[]
    otherText: string | null
    createdAt: string
}

interface TutorialGroup {
    tutorialId: string
    tutorialNumber: number
    tutorialTitle: string
    issueCount: number
    entries: FeedbackEntry[]
}

interface StudentFeedbackData {
    student: {
        id: string
        name: string
        initials: string
        rollNo: string
        collegeName: string
    }
    totalEntries: number
    summary: {
        mostCommonReason: string | null
        mostProblematicStep: string | null
    }
    reasonBreakdown: { key: string; count: number; percentage: number }[]
    stepBreakdown: { stepType: string; count: number }[]
    entries: FeedbackEntry[]
    tutorialGroups: TutorialGroup[]
}


// Step type icons & colors (reused from FeedbackPanel)
const STEP_ICONS: Record<string, React.ReactNode> = {
    watched: <Eye className="h-3 w-3" />,
    practiced: <PenTool className="h-3 w-3" />,
    assignmentDone: <CheckCircle2 className="h-3 w-3" />,
    forumAsked: <MessageSquare className="h-3 w-3" />,
    forumAnswered: <MessageSquare className="h-3 w-3" />,
}

const STEP_COLORS: Record<string, string> = {
    watched: 'bg-blue-500/10 text-blue-500',
    practiced: 'bg-orange-500/10 text-orange-500',
    assignmentDone: 'bg-purple-500/10 text-purple-500',
    forumAsked: 'bg-teal-500/10 text-teal-500',
    forumAnswered: 'bg-teal-500/10 text-teal-500',
}


// ===== ENTRY CARD =====

function FeedbackEntryCard({ entry, showTutorial = true }: { entry: FeedbackEntry; showTutorial?: boolean }) {
    const stepColor = STEP_COLORS[entry.stepType] || 'bg-muted text-muted-foreground'
    const stepIcon = STEP_ICONS[entry.stepType] || <AlertTriangle className="h-3 w-3" />
    const stepLabel = STEP_TYPE_LABELS[entry.stepType] || entry.stepType

    const date = new Date(entry.createdAt)
    const dateStr = date.toLocaleDateString('en-IN', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    })

    return (
        <div className="relative pl-6 pb-5 last:pb-0">
            {/* Timeline dot and line */}
            <div className="absolute left-0 top-1.5 w-3 h-3 rounded-full bg-destructive/20 border-2 border-destructive/40" />
            <div className="absolute left-[5px] top-4 bottom-0 w-0.5 bg-border/40 last:hidden" />

            <div className="bg-muted/10 border border-border/30 rounded-lg p-3">
                {/* Tutorial + step info */}
                {showTutorial && (
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <BookOpen className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                        <span className="text-xs font-medium">
                            Tutorial {entry.tutorialNumber}: {entry.tutorialTitle}
                        </span>
                    </div>
                )}

                <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <Badge className={`${stepColor} border-0 text-[9px] px-1.5 py-0 h-4 gap-0.5`}>
                        {stepIcon}
                        {stepLabel}
                    </Badge>
                    <span className="text-[10px] text-muted-foreground ml-auto shrink-0 flex items-center gap-1">
                        <Clock className="h-2.5 w-2.5" />
                        {dateStr}
                    </span>
                </div>

                {/* Reasons */}
                <div className="flex flex-wrap gap-1.5">
                    {entry.reasons.map(reason => (
                        <span
                            key={reason}
                            className="text-[11px] bg-destructive/8 text-destructive/90 border border-destructive/15 px-2 py-0.5 rounded-md"
                        >
                            {REASON_LABELS[reason] || reason}
                        </span>
                    ))}
                </div>

                {/* "Other" text */}
                {entry.otherText && (
                    <p className="text-xs text-muted-foreground mt-2 italic bg-muted/30 rounded px-2 py-1">
                        "{entry.otherText}"
                    </p>
                )}
            </div>
        </div>
    )
}


// ===== TUTORIAL GROUP =====

function TutorialGroupCard({ group }: { group: TutorialGroup }) {
    const [isOpen, setIsOpen] = useState(true)

    return (
        <div className="border border-border/30 rounded-lg overflow-hidden">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left hover:bg-muted/20 transition-colors"
            >
                <BookOpen className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                    <span className="text-xs font-medium">
                        Tutorial {group.tutorialNumber}: {group.tutorialTitle}
                    </span>
                </div>
                <Badge className="bg-destructive/10 text-destructive border-0 text-[10px] px-2 py-0.5 shrink-0">
                    {group.issueCount} {group.issueCount === 1 ? 'issue' : 'issues'}
                </Badge>
            </button>

            {isOpen && (
                <div className="border-t border-border/20 px-3 py-3">
                    {group.entries.map(entry => (
                        <FeedbackEntryCard key={entry.id} entry={entry} showTutorial={false} />
                    ))}
                </div>
            )}
        </div>
    )
}


// ===== MAIN DRAWER =====

type ViewMode = 'timeline' | 'grouped'

interface StudentFeedbackDrawerProps {
    studentId: string
    studentName: string
    studentInitials: string
    onClose: () => void
}

export function StudentFeedbackDrawer({ studentId, studentName, studentInitials, onClose }: StudentFeedbackDrawerProps) {
    const [data, setData] = useState<StudentFeedbackData | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [viewMode, setViewMode] = useState<ViewMode>('timeline')

    useEffect(() => {
        const fetchData = async () => {
            try {
                setIsLoading(true)
                setError(null)
                const res = await api.get(`/api/admin/students/${studentId}/feedback`)
                setData(res.data)
            } catch (err) {
                console.error('Failed to fetch student feedback:', err)
                setError('Failed to load feedback data')
            } finally {
                setIsLoading(false)
            }
        }
        fetchData()
    }, [studentId])

    const maxReasonCount = data?.reasonBreakdown[0]?.count || 1

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 z-40 bg-background/60 backdrop-blur-sm animate-in fade-in duration-200"
                onClick={onClose}
            />

            {/* Drawer panel */}
            <div className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-lg bg-card border-l border-border shadow-2xl overflow-y-auto animate-in slide-in-from-right duration-300">

                {/* Sticky header */}
                <div className="sticky top-0 z-10 bg-card/95 backdrop-blur-md border-b border-border/40">
                    <div className="flex items-center gap-3 px-5 py-4">
                        <Avatar className="h-10 w-10 shrink-0">
                            <AvatarFallback className="text-xs font-semibold bg-primary/10 text-primary">
                                {studentInitials}
                            </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                            <h2 className="text-sm font-bold truncate">{studentName}</h2>
                            <p className="text-[11px] text-muted-foreground">
                                {data?.student.collegeName || 'Loading...'} {data?.student.rollNo ? `· ${data.student.rollNo}` : ''}
                            </p>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-lg hover:bg-muted/50 transition-colors shrink-0"
                        >
                            <X className="h-4 w-4 text-muted-foreground" />
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="p-5 space-y-5">

                    {/* Loading state */}
                    {isLoading && (
                        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                            <Loader2 className="h-8 w-8 animate-spin mb-3" />
                            <p className="text-sm">Loading feedback...</p>
                        </div>
                    )}

                    {/* Error state */}
                    {error && (
                        <div className="text-center py-12">
                            <AlertTriangle className="h-8 w-8 text-destructive mx-auto mb-2" />
                            <p className="text-sm text-destructive">{error}</p>
                        </div>
                    )}

                    {/* Empty state */}
                    {!isLoading && !error && data?.totalEntries === 0 && (
                        <div className="text-center py-16">
                            <CheckCircle2 className="h-12 w-12 text-success/30 mx-auto mb-3" />
                            <p className="text-sm font-medium">No feedback issues!</p>
                            <p className="text-xs text-muted-foreground mt-1">
                                {studentName} hasn't reported any problems with tutorials
                            </p>
                        </div>
                    )}

                    {/* Data loaded */}
                    {!isLoading && !error && data && data.totalEntries > 0 && (
                        <>
                            {/* Quick stats */}
                            <div className="grid grid-cols-3 gap-2.5">
                                <Card className="border-border/40">
                                    <CardContent className="p-3 text-center">
                                        <p className="text-xl font-bold text-destructive">{data.totalEntries}</p>
                                        <p className="text-[10px] text-muted-foreground">Total Issues</p>
                                    </CardContent>
                                </Card>
                                <Card className="border-border/40">
                                    <CardContent className="p-3 text-center">
                                        <p className="text-[11px] font-bold truncate">
                                            {data.summary.mostCommonReason
                                                ? (REASON_LABELS[data.summary.mostCommonReason] || data.summary.mostCommonReason)
                                                : '—'}
                                        </p>
                                        <p className="text-[10px] text-muted-foreground mt-0.5">Top Reason</p>
                                    </CardContent>
                                </Card>
                                <Card className="border-border/40">
                                    <CardContent className="p-3 text-center">
                                        <p className="text-[11px] font-bold truncate">
                                            {data.summary.mostProblematicStep
                                                ? (STEP_TYPE_LABELS[data.summary.mostProblematicStep] || data.summary.mostProblematicStep)
                                                : '—'}
                                        </p>
                                        <p className="text-[10px] text-muted-foreground mt-0.5">Top Step Issue</p>
                                    </CardContent>
                                </Card>
                            </div>

                            {/* Reason breakdown bar chart */}
                            {data.reasonBreakdown.length > 0 && (
                                <Card className="border-border/40">
                                    <CardContent className="p-4">
                                        <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                                            Reason Breakdown
                                        </h3>
                                        <div className="space-y-2">
                                            {data.reasonBreakdown.map((reason, i) => (
                                                <div key={reason.key} className="flex items-center gap-2.5">
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-center justify-between mb-0.5">
                                                            <span className="text-[11px] font-medium truncate">
                                                                {REASON_LABELS[reason.key] || reason.key}
                                                            </span>
                                                            <span className="text-[10px] text-muted-foreground font-mono shrink-0 ml-2">
                                                                {reason.count}×
                                                            </span>
                                                        </div>
                                                        <div className="h-3 bg-muted/30 rounded overflow-hidden">
                                                            <div
                                                                className={`h-full rounded transition-all duration-700 ${i === 0 ? 'bg-destructive/60' :
                                                                    i === 1 ? 'bg-warning/60' :
                                                                        i === 2 ? 'bg-orange-400/50' :
                                                                            'bg-muted-foreground/30'
                                                                    }`}
                                                                style={{ width: `${(reason.count / maxReasonCount) * 100}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            )}

                            {/* Step type pills */}
                            {data.stepBreakdown.length > 0 && (
                                <div className="flex items-center gap-2 flex-wrap">
                                    <span className="text-[11px] text-muted-foreground">By step:</span>
                                    {data.stepBreakdown.map(step => {
                                        const stepColor = STEP_COLORS[step.stepType] || 'bg-muted text-muted-foreground'
                                        const stepLabel = STEP_TYPE_LABELS[step.stepType] || step.stepType
                                        return (
                                            <Badge key={step.stepType} className={`${stepColor} border-0 text-[10px] px-2 py-0.5 gap-1`}>
                                                {STEP_ICONS[step.stepType]}
                                                {stepLabel}: {step.count}
                                            </Badge>
                                        )
                                    })}
                                </div>
                            )}

                            {/* View mode toggle */}
                            <div className="flex items-center gap-1 bg-muted/30 rounded-lg p-0.5">
                                <button
                                    onClick={() => setViewMode('timeline')}
                                    className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-medium transition-all
                                        ${viewMode === 'timeline'
                                            ? 'bg-card text-foreground shadow-sm'
                                            : 'text-muted-foreground hover:text-foreground'
                                        }`}
                                >
                                    <List className="h-3 w-3" />
                                    Timeline
                                </button>
                                <button
                                    onClick={() => setViewMode('grouped')}
                                    className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-medium transition-all
                                        ${viewMode === 'grouped'
                                            ? 'bg-card text-foreground shadow-sm'
                                            : 'text-muted-foreground hover:text-foreground'
                                        }`}
                                >
                                    <Layers className="h-3 w-3" />
                                    By Tutorial
                                </button>
                            </div>

                            {/* Timeline view */}
                            {viewMode === 'timeline' && (
                                <div>
                                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                                        Feedback Timeline — Most Recent First
                                    </h3>
                                    <div>
                                        {data.entries.map(entry => (
                                            <FeedbackEntryCard key={entry.id} entry={entry} />
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Grouped by tutorial view */}
                            {viewMode === 'grouped' && (
                                <div>
                                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                                        Issues by Tutorial — Most Problematic First
                                    </h3>
                                    <div className="space-y-2">
                                        {data.tutorialGroups.map(group => (
                                            <TutorialGroupCard key={group.tutorialId} group={group} />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </>
    )
}
