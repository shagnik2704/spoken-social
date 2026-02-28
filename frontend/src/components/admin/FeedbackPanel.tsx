import { useState, useEffect } from 'react'
import {
    MessageCircleQuestion, ChevronDown, ChevronUp,
    AlertTriangle, Eye, CheckCircle2, BookOpen,
    MessageSquare, PenTool, Filter,
    Wifi, LifeBuoy, GraduationCap, Lightbulb, HelpCircle
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { REASON_LABELS, STEP_TYPE_LABELS, REASON_CATEGORIES } from '@/lib/feedbackReasons'
import api from '@/lib/axios'

// ===== TYPES =====

interface FeedbackEntry {
    id: number
    tutorialNumber: number
    tutorialTitle: string
    stepType: string
    reasons: string[]
    otherText: string | null
    createdAt: string
}

interface StudentFeedback {
    id: string
    name: string
    initials: string
    collegeName: string
    feedbackCount: number
    entries: FeedbackEntry[]
}

interface FeedbackSummary {
    totalEntries: number
    topReasons: { key: string; count: number; percentage: number }[]
    stepBreakdown: { stepType: string; count: number }[]
    students: StudentFeedback[]
}

// Step type icons
const STEP_ICONS: Record<string, React.ReactNode> = {
    watched: <Eye className="h-3 w-3" />,
    practiced: <PenTool className="h-3 w-3" />,
    assignmentDone: <CheckCircle2 className="h-3 w-3" />,
    forumAsked: <MessageSquare className="h-3 w-3" />,
    forumAnswered: <MessageSquare className="h-3 w-3" />,
}

// Step type colors
const STEP_COLORS: Record<string, string> = {
    watched: 'bg-blue-500/10 text-blue-500',
    practiced: 'bg-orange-500/10 text-orange-500',
    assignmentDone: 'bg-purple-500/10 text-purple-500',
    forumAsked: 'bg-teal-500/10 text-teal-500',
    forumAnswered: 'bg-teal-500/10 text-teal-500',
}

// ===== EXPANDABLE STUDENT CARD =====

function StudentFeedbackCard({ student }: { student: StudentFeedback }) {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <div className="rounded-lg border border-border/40 overflow-hidden">
            {/* Header — clickable */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-muted/20 transition-colors"
            >
                <Avatar className="h-8 w-8 shrink-0">
                    <AvatarFallback className="text-[10px] font-semibold bg-destructive/10 text-destructive">
                        {student.initials}
                    </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{student.name}</p>
                    <p className="text-[11px] text-muted-foreground">{student.collegeName}</p>
                </div>
                <Badge className="bg-warning/10 text-warning border-0 text-[10px] px-2 py-0.5 shrink-0">
                    {student.feedbackCount} {student.feedbackCount === 1 ? 'issue' : 'issues'}
                </Badge>
                {isOpen
                    ? <ChevronUp className="h-4 w-4 text-muted-foreground shrink-0" />
                    : <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
                }
            </button>

            {/* Expanded: feedback entries */}
            {isOpen && (
                <div className="border-t border-border/30 divide-y divide-border/20">
                    {student.entries.map(entry => {
                        const stepColor = STEP_COLORS[entry.stepType] || 'bg-muted text-muted-foreground'
                        const stepIcon = STEP_ICONS[entry.stepType] || <AlertTriangle className="h-3 w-3" />
                        const stepLabel = STEP_TYPE_LABELS[entry.stepType] || entry.stepType
                        const date = new Date(entry.createdAt)
                        const dateStr = date.toLocaleDateString('en-IN', {
                            day: 'numeric', month: 'short', year: 'numeric',
                            hour: '2-digit', minute: '2-digit',
                        })

                        return (
                            <div key={entry.id} className="px-4 py-3 bg-muted/10">
                                {/* Tutorial + step info */}
                                <div className="flex items-center gap-2 mb-2 flex-wrap">
                                    <BookOpen className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                                    <span className="text-xs font-medium">
                                        Tutorial {entry.tutorialNumber}: {entry.tutorialTitle}
                                    </span>
                                    <Badge className={`${stepColor} border-0 text-[9px] px-1.5 py-0 h-4 gap-0.5`}>
                                        {stepIcon}
                                        {stepLabel}
                                    </Badge>
                                    <span className="text-[10px] text-muted-foreground ml-auto shrink-0">
                                        {dateStr}
                                    </span>
                                </div>

                                {/* Reasons */}
                                <div className="flex flex-wrap gap-1.5 ml-5">
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
                                    <p className="text-xs text-muted-foreground ml-5 mt-1.5 italic bg-muted/30 rounded px-2 py-1">
                                        "{entry.otherText}"
                                    </p>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}


// ===== MAIN COMPONENT =====

export function FeedbackPanel() {
    const [summary, setSummary] = useState<FeedbackSummary | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [collegeFilter, setCollegeFilter] = useState<string>('')

    useEffect(() => {
        const fetchFeedback = async () => {
            try {
                const url = collegeFilter
                    ? `/api/admin/feedback-summary?college_id=${collegeFilter}`
                    : '/api/admin/feedback-summary'
                const res = await api.get(url)
                setSummary(res.data)
            } catch (error) {
                console.error('Failed to fetch feedback:', error)
            } finally {
                setIsLoading(false)
            }
        }
        fetchFeedback()
    }, [collegeFilter])

    if (isLoading || !summary) {
        return (
            <Card className="border-border/40">
                <CardContent className="p-6 text-center text-muted-foreground text-sm">
                    Loading feedback data...
                </CardContent>
            </Card>
        )
    }

    if (summary.totalEntries === 0) {
        return (
            <Card className="border-border/40">
                <CardContent className="p-6 text-center">
                    <MessageCircleQuestion className="h-10 w-10 text-muted-foreground/30 mx-auto mb-2" />
                    <p className="text-sm font-medium">No feedback received yet</p>
                    <p className="text-xs text-muted-foreground mt-1">
                        When students select "No" on tutorial steps, their reasons will appear here
                    </p>
                </CardContent>
            </Card>
        )
    }

    // Map icon name from category config to actual component
    const CATEGORY_ICONS: Record<string, React.ReactNode> = {
        Wifi: <Wifi className="h-4 w-4" />,
        LifeBuoy: <LifeBuoy className="h-4 w-4" />,
        GraduationCap: <GraduationCap className="h-4 w-4" />,
        Lightbulb: <Lightbulb className="h-4 w-4" />,
        HelpCircle: <HelpCircle className="h-4 w-4" />,
    }

    // Build a quick-lookup: reason key → count
    const reasonCountMap: Record<string, number> = {}
    for (const r of summary.topReasons) {
        reasonCountMap[r.key] = r.count
    }

    // Compute totals per category (only keep categories with > 0 reports)
    const categoryStats = REASON_CATEGORIES.map(cat => {
        const matchedReasons = cat.reasons
            .filter(r => (reasonCountMap[r] || 0) > 0)
            .map(r => ({ key: r, count: reasonCountMap[r] || 0 }))
            .sort((a, b) => b.count - a.count)

        const total = matchedReasons.reduce((sum, r) => sum + r.count, 0)
        return { ...cat, total, matchedReasons }
    }).filter(cat => cat.total > 0)
        .sort((a, b) => b.total - a.total)

    const maxCategoryTotal = categoryStats[0]?.total || 1
    const grandTotal = categoryStats.reduce((sum, c) => sum + c.total, 0)

    return (
        <div className="space-y-5">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold flex items-center gap-2">
                    <MessageCircleQuestion className="h-4 w-4 text-warning" />
                    Student Feedback — Why students say "No"
                    <Badge className="bg-warning/10 text-warning border-0 text-[10px] px-2 py-0.5">
                        {summary.totalEntries} responses
                    </Badge>
                </h2>
            </div>

            {/* Category Insight Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {categoryStats.map(cat => {
                    const pct = grandTotal > 0 ? Math.round((cat.total / grandTotal) * 100) : 0
                    return (
                        <Card key={cat.id} className={`${cat.borderColor} border ${cat.bgColor} overflow-hidden`}>
                            <CardContent className="p-4">
                                {/* Category header */}
                                <div className="flex items-center gap-3 mb-3">
                                    <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${cat.bgColor} ${cat.color}`}>
                                        {CATEGORY_ICONS[cat.icon]}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className={`text-sm font-bold ${cat.color}`}>{cat.label}</p>
                                        <p className="text-[10px] text-muted-foreground">
                                            {cat.total} {cat.total === 1 ? 'report' : 'reports'} · {pct}% of all issues
                                        </p>
                                    </div>
                                    <div className="text-right shrink-0">
                                        <p className={`text-xl font-bold ${cat.color}`}>{cat.total}</p>
                                    </div>
                                </div>

                                {/* Share bar */}
                                <div className="h-1.5 bg-muted/40 rounded-full overflow-hidden mb-3">
                                    <div
                                        className={`h-full rounded-full transition-all duration-700 ${cat.color.replace('text-', 'bg-')}/40`}
                                        style={{ width: `${(cat.total / maxCategoryTotal) * 100}%` }}
                                    />
                                </div>

                                {/* Individual reason pills */}
                                <div className="flex flex-wrap gap-1.5">
                                    {cat.matchedReasons.map(r => (
                                        <span
                                            key={r.key}
                                            className={`inline-flex items-center gap-1 text-[10px] ${cat.bgColor} ${cat.color} border ${cat.borderColor} px-2 py-0.5 rounded-full font-medium`}
                                        >
                                            {REASON_LABELS[r.key] || r.key}
                                            <span className="opacity-60 font-mono">×{r.count}</span>
                                        </span>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )
                })}
            </div>

            {/* Step-type breakdown pills */}
            <div className="flex items-center gap-2 flex-wrap">
                <Filter className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-[11px] text-muted-foreground">By step:</span>
                {summary.stepBreakdown.map(step => {
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

            {/* Per-student feedback */}
            <Card className="border-border/40">
                <CardContent className="p-4">
                    <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                        Student Issues — Click to expand
                    </h3>
                    <div className="space-y-2">
                        {summary.students.map(student => (
                            <StudentFeedbackCard key={student.id} student={student} />
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
