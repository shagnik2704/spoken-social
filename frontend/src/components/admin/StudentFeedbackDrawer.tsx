import { useState, useEffect } from 'react'
import {
    X, AlertTriangle,
    CheckCircle2, BookOpen,
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


// ===== ENTRY CARD (Simplified) =====

function FeedbackEntryCard({ entry, showTutorial = true }: { entry: FeedbackEntry; showTutorial?: boolean }) {
    const stepLabel = STEP_TYPE_LABELS[entry.stepType] || entry.stepType

    const date = new Date(entry.createdAt)
    const dateStr = date.toLocaleDateString('en-IN', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    })

    return (
        <div className="py-3 border-b border-border/20 last:border-0">
            {/* Tutorial name */}
            {showTutorial && (
                <p className="text-xs font-medium mb-1.5">
                    Tutorial {entry.tutorialNumber}: {entry.tutorialTitle}
                </p>
            )}

            {/* Step type + date */}
            <div className="flex items-center justify-between mb-2">
                <Badge className="bg-muted text-muted-foreground border-0 text-[10px] px-2 py-0.5">
                    {stepLabel}
                </Badge>
                <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                    <Clock className="h-2.5 w-2.5" />
                    {dateStr}
                </span>
            </div>

            {/* Reasons — simple muted pills */}
            <div className="flex flex-wrap gap-1.5">
                {entry.reasons.map(reason => (
                    <span
                        key={reason}
                        className="text-[11px] bg-muted/50 text-foreground/70 border border-border/40 px-2 py-0.5 rounded-md"
                    >
                        {REASON_LABELS[reason] || reason}
                    </span>
                ))}
            </div>

            {/* "Other" text */}
            {entry.otherText && (
                <p className="text-xs text-muted-foreground mt-2 italic bg-muted/20 rounded px-2 py-1">
                    "{entry.otherText}"
                </p>
            )}
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
                <span className="text-[11px] text-muted-foreground font-mono shrink-0">
                    {group.issueCount} {group.issueCount === 1 ? 'issue' : 'issues'}
                </span>
            </button>

            {isOpen && (
                <div className="border-t border-border/20 px-3">
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
                                {data?.student.collegeName || 'Loading...'} {data?.student.rollNo ? `· @${data.student.rollNo}` : ''}
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
                            {/* Quick stats — simple text row */}
                            <div className="flex items-center gap-4 text-sm">
                                <div>
                                    <span className="font-bold text-lg">{data.totalEntries}</span>
                                    <span className="text-muted-foreground text-xs ml-1">issues</span>
                                </div>
                                <div className="h-4 w-px bg-border/50" />
                                <div className="text-xs text-muted-foreground">
                                    Top issue: <span className="text-foreground font-medium">
                                        {data.summary.mostCommonReason
                                            ? (REASON_LABELS[data.summary.mostCommonReason] || data.summary.mostCommonReason)
                                            : '—'}
                                    </span>
                                </div>
                            </div>

                            {/* Reason breakdown — uniform muted bars */}
                            {data.reasonBreakdown.length > 0 && (
                                <Card className="border-border/40">
                                    <CardContent className="p-4">
                                        <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                                            Reason Breakdown
                                        </h3>
                                        <div className="space-y-2.5">
                                            {data.reasonBreakdown.map(reason => (
                                                <div key={reason.key}>
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="text-[11px] font-medium truncate">
                                                            {REASON_LABELS[reason.key] || reason.key}
                                                        </span>
                                                        <span className="text-[10px] text-muted-foreground font-mono shrink-0 ml-2">
                                                            {reason.count}×
                                                        </span>
                                                    </div>
                                                    <div className="h-1.5 bg-muted/30 rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full rounded-full bg-foreground/20 transition-all duration-700"
                                                            style={{ width: `${(reason.count / maxReasonCount) * 100}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            )}

                            {/* Step type — simple text pills */}
                            {data.stepBreakdown.length > 0 && (
                                <div className="flex items-center gap-2 flex-wrap">
                                    <span className="text-[11px] text-muted-foreground">By step:</span>
                                    {data.stepBreakdown.map(step => {
                                        const stepLabel = STEP_TYPE_LABELS[step.stepType] || step.stepType
                                        return (
                                            <Badge key={step.stepType} className="bg-muted text-muted-foreground border-0 text-[10px] px-2 py-0.5">
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
                                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">
                                        Feedback Timeline
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
                                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">
                                        Issues by Tutorial
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
