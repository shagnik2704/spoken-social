import { useState} from 'react'
import {
    MessageCircleQuestion, ChevronDown, ChevronUp,
    BookOpen,
    Clock, Filter, X, Users, Hash
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { REASON_LABELS, STEP_TYPE_LABELS } from '@/lib/feedbackReasons'
import { useFeedbackSummary } from '@/hooks/queries/useAdminQueries'

// ===== TYPES =====

interface FeedbackEntry {
    id: number
    studentId: string
    studentName: string
    studentInitials: string
    collegeName: string
    stepType: string
    reasons: string[]
    otherText: string | null
    createdAt: string
}

interface TutorialGroup {
    tutorialId: string
    tutorialNumber: number
    tutorialTitle: string
    studentCount: number
    entries: FeedbackEntry[]
}

interface FilterOptions {
    tutorials: { id: string; number: number; title: string }[]
    stepTypes: string[]
    reasons: string[]
}

interface FeedbackSummary {
    filterOptions: FilterOptions
    totalEntries: number
    uniqueStudents: number
    topReasons: { key: string; count: number; percentage: number }[]
    stepBreakdown: { stepType: string; count: number }[]
    tutorialGroups: TutorialGroup[]
}


// ===== TUTORIAL GROUP CARD =====

function TutorialGroupCard({ group, onStudentClick }: {
    group: TutorialGroup
    onStudentClick?: (student: { id: string; name: string; initials: string }) => void
}) {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <div className="border border-border/30 rounded-lg overflow-hidden">
            {/* Header */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-primary/5 transition-colors"
            >
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                    <BookOpen className="h-3.5 w-3.5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">
                        Tutorial {group.tutorialNumber}: {group.tutorialTitle}
                    </p>
                    <p className="text-[11px] text-muted-foreground">
                        {group.studentCount} {group.studentCount === 1 ? 'student' : 'students'} · {group.entries.length} {group.entries.length === 1 ? 'issue' : 'issues'}
                    </p>
                </div>
                <span className="text-lg font-bold text-amber-500 tabular-nums shrink-0">
                    {group.entries.length}
                </span>
                {isOpen
                    ? <ChevronUp className="h-4 w-4 text-muted-foreground shrink-0" />
                    : <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
                }
            </button>

            {/* Entries */}
            {isOpen && (
                <div className="border-t border-border/20">
                    {group.entries.map(entry => {
                        const stepLabel = STEP_TYPE_LABELS[entry.stepType] || entry.stepType
                        const date = new Date(entry.createdAt)
                        const dateStr = date.toLocaleDateString('en-IN', {
                            day: 'numeric', month: 'short',
                            hour: '2-digit', minute: '2-digit',
                        })

                        return (
                            <div key={entry.id} className="px-4 py-3 border-b border-border/10 last:border-0 hover:bg-muted/10 transition-colors">
                                {/* Student + Step + Date */}
                                <div className="flex items-center gap-2.5 mb-2">
                                    <button
                                        onClick={() => onStudentClick?.({
                                            id: entry.studentId,
                                            name: entry.studentName,
                                            initials: entry.studentInitials,
                                        })}
                                        className="flex items-center gap-2 hover:underline"
                                    >
                                        <Avatar className="h-6 w-6 shrink-0">
                                            <AvatarFallback className="text-[8px] font-semibold bg-primary/10 text-primary">
                                                {entry.studentInitials}
                                            </AvatarFallback>
                                        </Avatar>
                                        <span className="text-xs font-medium">{entry.studentName}</span>
                                    </button>
                                    <span className="text-[10px] text-muted-foreground">
                                        {entry.collegeName}
                                    </span>
                                    <span className="ml-auto flex items-center gap-2 shrink-0">
                                        <Badge className="bg-amber-500/10 text-amber-500 border-0 text-[9px] px-1.5 py-0">
                                            {stepLabel}
                                        </Badge>
                                        <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                                            <Clock className="h-2.5 w-2.5" />
                                            {dateStr}
                                        </span>
                                    </span>
                                </div>

                                {/* Reasons */}
                                <div className="flex flex-wrap gap-1.5 ml-8">
                                    {entry.reasons.map(reason => (
                                        <span
                                            key={reason}
                                            className="text-[11px] bg-amber-500/5 text-foreground/80 border border-amber-500/15 px-2 py-0.5 rounded-md"
                                        >
                                            {REASON_LABELS[reason] || reason}
                                        </span>
                                    ))}
                                </div>

                                {entry.otherText && (
                                    <p className="text-xs text-muted-foreground mt-1.5 ml-8 italic bg-muted/20 rounded px-2 py-1">
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


// ===== FILTER BAR =====

function FilterBar({ options, filters, onFilterChange }: {
    options: FilterOptions
    filters: { tutorialId: string; stepType: string; reason: string }
    onFilterChange: (key: string, value: string) => void
}) {
    const activeCount = [filters.tutorialId, filters.stepType, filters.reason].filter(Boolean).length

    return (
        <Card className="border-border/40">
            <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-3">
                    <Filter className="h-4 w-4 text-muted-foreground" />
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Filters</span>
                    {activeCount > 0 && (
                        <Badge className="bg-primary/10 text-primary border-0 text-[10px] px-1.5 py-0 h-4">
                            {activeCount} active
                        </Badge>
                    )}
                    {activeCount > 0 && (
                        <button
                            onClick={() => {
                                onFilterChange('tutorialId', '')
                                onFilterChange('stepType', '')
                                onFilterChange('reason', '')
                            }}
                            className="ml-auto text-[11px] text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
                        >
                            <X className="h-3 w-3" />
                            Clear all
                        </button>
                    )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                    {/* Tutorial filter */}
                    <div>
                        <label className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1 block">Tutorial</label>
                        <select
                            value={filters.tutorialId}
                            onChange={(e) => onFilterChange('tutorialId', e.target.value)}
                            className="w-full text-xs bg-muted/30 border border-border/40 rounded-lg px-2.5 py-2 focus:outline-none focus:ring-1 focus:ring-primary/30 appearance-none"
                        >
                            <option value="">All tutorials</option>
                            {options.tutorials.map(t => (
                                <option key={t.id} value={t.id}>
                                    {t.number}. {t.title}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Step type filter */}
                    <div>
                        <label className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1 block">Step Type</label>
                        <select
                            value={filters.stepType}
                            onChange={(e) => onFilterChange('stepType', e.target.value)}
                            className="w-full text-xs bg-muted/30 border border-border/40 rounded-lg px-2.5 py-2 focus:outline-none focus:ring-1 focus:ring-primary/30 appearance-none"
                        >
                            <option value="">All steps</option>
                            {options.stepTypes.map(st => (
                                <option key={st} value={st}>
                                    {STEP_TYPE_LABELS[st] || st}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Reason filter */}
                    <div>
                        <label className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1 block">Reason</label>
                        <select
                            value={filters.reason}
                            onChange={(e) => onFilterChange('reason', e.target.value)}
                            className="w-full text-xs bg-muted/30 border border-border/40 rounded-lg px-2.5 py-2 focus:outline-none focus:ring-1 focus:ring-primary/30 appearance-none"
                        >
                            <option value="">All reasons</option>
                            {options.reasons.map(r => (
                                <option key={r} value={r}>
                                    {REASON_LABELS[r] || r}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}


// ===== MAIN COMPONENT =====

interface FeedbackPanelProps {
    onStudentClick?: (student: { id: string; name: string; initials: string }) => void
}

export function FeedbackPanel({ onStudentClick }: FeedbackPanelProps) {

    const [filters, setFilters] = useState({
        tutorialId: '',
        stepType: '',
        reason: '',
    })
    const { data: summary, isLoading } = useFeedbackSummary(filters) as { data: FeedbackSummary | undefined, isLoading: boolean }
    const handleFilterChange = (key: string, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }))
    }


    if (isLoading && !summary) {
        return (
            <Card className="border-border/40">
                <CardContent className="p-6 text-center text-muted-foreground text-sm">
                    Loading feedback data...
                </CardContent>
            </Card>
        )
    }

    if (!summary) return null

    const hasActiveFilters = filters.tutorialId || filters.stepType || filters.reason
    const maxReasonCount = summary.topReasons[0]?.count || 1

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
                    <MessageCircleQuestion className="h-4 w-4 text-primary" />
                </div>
                <div>
                    <h2 className="text-sm font-bold">Student Feedback</h2>
                    <p className="text-[11px] text-muted-foreground">Why students say "No"</p>
                </div>
                {summary.totalEntries > 0 && (
                    <Badge className="bg-amber-500/10 text-amber-500 border-0 text-[10px] px-2 py-0.5 ml-1">
                        {summary.totalEntries} responses
                    </Badge>
                )}
            </div>

            {/* Filters */}
            <FilterBar
                options={summary.filterOptions}
                filters={filters}
                onFilterChange={handleFilterChange}
            />

            {/* Stats row */}
            <Card className="border-primary/10 bg-primary/[0.02]">
                <CardContent className="p-3">
                    <div className="flex items-center gap-5 text-sm">
                        <div className="flex items-center gap-1.5">
                            <Hash className="h-3.5 w-3.5 text-primary/60" />
                            <span className="font-bold text-lg tabular-nums">{summary.totalEntries}</span>
                            <span className="text-xs text-muted-foreground">
                                {summary.totalEntries === 1 ? 'response' : 'responses'}
                            </span>
                        </div>
                        <div className="h-4 w-px bg-border/30" />
                        <div className="flex items-center gap-1.5">
                            <Users className="h-3.5 w-3.5 text-primary/60" />
                            <span className="font-bold tabular-nums">{summary.uniqueStudents}</span>
                            <span className="text-xs text-muted-foreground">
                                {summary.uniqueStudents === 1 ? 'student' : 'students'} affected
                            </span>
                        </div>
                        {hasActiveFilters && (
                            <>
                                <div className="h-4 w-px bg-border/30" />
                                <Badge className="bg-primary/10 text-primary border-0 text-[10px] px-1.5 py-0">filtered</Badge>
                            </>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* Empty state after filtering */}
            {summary.totalEntries === 0 ? (
                <Card className="border-border/40">
                    <CardContent className="p-6 text-center">
                        <MessageCircleQuestion className="h-10 w-10 text-muted-foreground/30 mx-auto mb-2" />
                        <p className="text-sm font-medium">
                            {hasActiveFilters ? 'No feedback matches your filters' : 'No feedback received yet'}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                            {hasActiveFilters
                                ? 'Try adjusting or clearing your filters'
                                : 'When students select "No" on tutorial steps, their reasons will appear here'}
                        </p>
                    </CardContent>
                </Card>
            ) : (
                <>
                    {/* Top reasons bar chart */}
                    {summary.topReasons.length > 0 && (
                        <Card className="border-border/40">
                            <CardContent className="p-4">
                                <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                                    Top Reasons
                                </h3>
                                <div className="space-y-2">
                                    {summary.topReasons.slice(0, 8).map(reason => (
                                        <button
                                            key={reason.key}
                                            onClick={() => handleFilterChange('reason', filters.reason === reason.key ? '' : reason.key)}
                                            className={`w-full text-left group ${filters.reason === reason.key ? 'opacity-100' : 'opacity-80 hover:opacity-100'} transition-opacity`}
                                        >
                                            <div className="flex items-center justify-between mb-0.5">
                                                <span className={`text-[11px] font-medium truncate ${filters.reason === reason.key ? 'text-primary' : ''}`}>
                                                    {REASON_LABELS[reason.key] || reason.key}
                                                </span>
                                                <span className="text-[10px] text-muted-foreground font-mono shrink-0 ml-2">
                                                    {reason.count} · {reason.percentage}%
                                                </span>
                                            </div>
                                            <div className="h-1.5 bg-muted/30 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full transition-all duration-500 ${filters.reason === reason.key ? 'bg-primary/50' : 'bg-amber-500/30'}`}
                                                    style={{ width: `${(reason.count / maxReasonCount) * 100}%` }}
                                                />
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Step breakdown pills */}
                    {summary.stepBreakdown.length > 0 && (
                        <div className="flex items-center gap-2 flex-wrap px-1">
                            <span className="text-[11px] text-muted-foreground">By step:</span>
                            {summary.stepBreakdown.map(step => {
                                const stepLabel = STEP_TYPE_LABELS[step.stepType] || step.stepType
                                const isActive = filters.stepType === step.stepType
                                return (
                                    <button
                                        key={step.stepType}
                                        onClick={() => handleFilterChange('stepType', isActive ? '' : step.stepType)}
                                    >
                                        <Badge className={`border-0 text-[10px] px-2 py-0.5 transition-colors ${isActive ? 'bg-primary/15 text-primary' : 'bg-muted text-muted-foreground hover:text-foreground'}`}>
                                            {stepLabel}: {step.count}
                                        </Badge>
                                    </button>
                                )
                            })}
                        </div>
                    )}

                    {/* Tutorial groups */}
                    <div>
                        <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2 px-1">
                            {hasActiveFilters ? 'Filtered Results' : 'All Tutorials'} — {summary.tutorialGroups.length} {summary.tutorialGroups.length === 1 ? 'tutorial' : 'tutorials'}
                        </h3>
                        <div className="space-y-2">
                            {summary.tutorialGroups.map(group => (
                                <TutorialGroupCard
                                    key={group.tutorialId}
                                    group={group}
                                    onStudentClick={onStudentClick}
                                />
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}
