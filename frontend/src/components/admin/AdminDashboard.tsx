import { useState, useEffect, useRef } from 'react'
import {
    Users, TrendingUp, AlertTriangle,
    CheckCircle2, Eye,
    Search, Filter, Trophy, BarChart3,
    Zap, Activity, ChevronRight, ArrowLeft,
    Shield, Building2, MessageCircleQuestion,
    X, ChevronDown, CalendarDays, Download
} from 'lucide-react'
import api from '@/lib/axios'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
    PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
    LineChart, Line, XAxis, YAxis, CartesianGrid, Legend,
} from 'recharts'

import { FeedbackPanel } from '@/components/admin/FeedbackPanel'
import { StudentFeedbackDrawer } from '@/components/admin/StudentFeedbackDrawer'
import { useCollegeDetails, useColleges, useCollegesDailyXP, usePlatformSummary } from '@/hooks/queries/useAdminQueries'

// ===== TYPES =====

interface CollegeSummary {
    id: string
    name: string
    location: string
    coordinatorName: string
    course: string
    totalStudents: number
    totalCourseStudents: number
    activeStudents: number
    inactiveStudents: number
    atRiskStudents: number
    completedStudents: number
    avgProgress: number
    avgXP: number
    completionRate: number
}

interface Student {
    id: string
    name: string
    initials: string
    rollNo: string
    tutorialsWatched: number
    tutorialsCompleted: number
    totalTutorials: number
    progress: number
    xp: number
    lastActive: string
    status: 'active' | 'completed' | 'inactive' | 'at_risk' | 'not_started'
}


interface PlatformSummary {
    metrics: {
        totalStudents: number
        totalColleges: number
        avgProgress: number
        avgXP: number
        completionRate: number
        totalCompleted: number
        totalActive: number
        totalAtRisk: number
        totalInactive: number
    }
    statusDistribution: { name: string; value: number; color: string }[]
    progressDistribution: { name: string; value: number; color: string }[]
    topPerformers: EnrichedStudent[]
    atRiskStudents: EnrichedStudent[]
    tutorialCompletion: { number: number; name: string; completedCount: number; rate: number }[]
}

interface EnrichedStudent {
    id: string
    name: string
    initials: string
    xp: number
    progress: number
    status: string
    watched: number
    completed: number
    collegeName: string
}

type Tab = 'overview' | 'colleges' | 'analytics' | 'feedback'
type SortBy = 'name' | 'progress' | 'xp'
type StatusFilter = 'all' | 'active' | 'completed' | 'at_risk' | 'inactive'

// ===== STATUS HELPERS =====

function getStatusConfig(status: string) {
    switch (status) {
        case 'completed': return { label: 'Completed', color: 'bg-success/10 text-success', dot: 'bg-success' }
        case 'active': return { label: 'Active', color: 'bg-primary/10 text-primary', dot: 'bg-primary' }
        case 'at_risk': return { label: 'At Risk', color: 'bg-warning/10 text-warning', dot: 'bg-warning' }
        case 'inactive': return { label: 'Inactive', color: 'bg-destructive/10 text-destructive', dot: 'bg-destructive' }
        case 'not_started': return { label: 'Not Started', color: 'bg-muted text-muted-foreground', dot: 'bg-muted-foreground' }
        default: return { label: status, color: 'bg-muted text-muted-foreground', dot: 'bg-muted-foreground' }
    }
}

// ===== METRIC CARD =====

function MetricCard({ icon: Icon, label, value, subtext, color }: {
    icon: React.ElementType
    label: string
    value: string | number
    subtext?: string
    color: string
}) {
    return (
        <Card className="border-border/40">
            <CardContent className="p-4">
                <div className="flex items-center gap-3">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${color}`}>
                        <Icon className="h-5 w-5" />
                    </div>
                    <div>
                        <p className="text-2xl font-bold">{value}</p>
                        <p className="text-xs text-muted-foreground">{label}</p>
                    </div>
                </div>
                {subtext && (
                    <p className="text-[11px] text-muted-foreground mt-2 pl-[52px]">{subtext}</p>
                )}
            </CardContent>
        </Card>
    )
}

// ===== STUDENT TABLE ROW =====

function StudentRow({ student, collegeName, onClick, index }: { student: Student | EnrichedStudent; collegeName?: string; onClick?: () => void; index?: number }) {
    const statusConfig = getStatusConfig(student.status)
    const cName = collegeName || ('collegeName' in student ? student.collegeName : undefined)

    return (
        <button onClick={onClick} className="w-full text-left flex items-center gap-3 px-3 sm:px-4 py-3 rounded-lg hover:bg-muted/30 transition-colors">
            {index !== undefined && (
                <div className="w-6 shrink-0 text-xs font-semibold text-muted-foreground text-center">
                    {index}
                </div>
            )}
            <Avatar className="h-8 w-8 shrink-0">
                <AvatarFallback className="text-[10px] font-semibold bg-primary/10 text-primary">
                    {student.initials}
                </AvatarFallback>
            </Avatar>

            <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{student.name}</p>
                <p className="text-[11px] text-muted-foreground font-mono">
                    {'rollNo' in student && student.rollNo}
                    {cName && <span className="ml-2 text-primary/70">• {cName}</span>}
                </p>
            </div>

            <div className="hidden sm:flex items-center gap-2 w-28">
                <Progress value={student.progress} className="h-1.5 flex-1" />
                <span className="text-[11px] text-muted-foreground font-mono w-8 text-right">{student.progress}%</span>
            </div>

            <div className="hidden md:flex w-32 items-center gap-4 justify-center">
                <span className="flex items-center gap-1 text-muted-foreground" title="Watched">
                    <Eye className="h-3 w-3 shrink-0" />
                    <span className="text-xs font-mono tabular-nums w-5 text-right">
                        {'tutorialsWatched' in student ? student.tutorialsWatched : student.watched}
                    </span>
                </span>
                <span className="flex items-center gap-1" title="Completed">
                    <CheckCircle2 className="h-3 w-3 text-success shrink-0" />
                    <span className="text-xs font-mono font-medium tabular-nums w-5 text-right">
                        {'tutorialsCompleted' in student ? student.tutorialsCompleted : student.completed}
                    </span>
                </span>
            </div>

            <div className="hidden lg:flex items-center gap-1 w-16 justify-end">
                <Zap className="h-3 w-3 text-xp-gold" />
                <span className="text-xs font-mono font-semibold tabular-nums">{student.xp}</span>
            </div>

            <div className="w-24 shrink-0 flex justify-center">
                <Badge className={`${statusConfig.color} border-0 text-[10px] px-2 py-0.5`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${statusConfig.dot} mr-1.5`} />
                    {statusConfig.label}
                </Badge>
            </div>
        </button>
    )
}

// ===== OVERVIEW TAB =====
// Uses pre-computed data from /api/admin/platform-summary — no client-side aggregation

function OverviewTab({ colleges, summary, onStudentClick }: {
    colleges: CollegeSummary[]
    summary: PlatformSummary
    onStudentClick: (student: { id: string, name: string, initials: string }) => void
}) {
    const m = summary.metrics

    return (
        <div className="space-y-5">
            {/* Platform-wide Metric Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <MetricCard
                    icon={Building2}
                    label="Total Colleges"
                    value={m.totalColleges}
                    subtext={`${m.totalStudents} students enrolled`}
                    color="bg-primary/10 text-primary"
                />
                <MetricCard
                    icon={TrendingUp}
                    label="Avg Progress"
                    value={`${m.avgProgress}%`}
                    subtext={`${m.avgXP} avg XP`}
                    color="bg-secondary/10 text-secondary"
                />
                <MetricCard
                    icon={CheckCircle2}
                    label="Completion Rate"
                    value={`${m.completionRate}%`}
                    subtext={`${m.totalCompleted} of ${m.totalStudents} completed`}
                    color="bg-success/10 text-success"
                />
                <MetricCard
                    icon={AlertTriangle}
                    label="Need Attention"
                    value={m.totalAtRisk + m.totalInactive}
                    subtext={`${m.totalAtRisk} at risk · ${m.totalInactive} inactive`}
                    color="bg-warning/10 text-warning"
                />
            </div>

            {/* College Summary Cards */}
            <Card className="border-border/40">
                <CardContent className="p-4">
                    <h2 className="text-sm font-bold flex items-center gap-2 mb-4">
                        <Building2 className="h-4 w-4 text-primary" />
                        College Performance Overview
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {[...colleges].sort((a, b) => b.avgProgress - a.avgProgress).map((college, i) => (
                            <div
                                key={college.id}
                                className="flex items-center gap-3 p-3 rounded-lg border border-border/30 hover:bg-muted/20 transition-colors"
                            >
                                <div className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold shrink-0
                                    ${i === 0 ? 'bg-xp-gold/15 text-xp-gold' :
                                        i === 1 ? 'bg-gray-300/20 text-gray-500' :
                                            i === 2 ? 'bg-orange-200/20 text-orange-600' :
                                                'bg-muted text-muted-foreground'
                                    }`}>
                                    #{i + 1}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-semibold truncate">{college.name} <span className="text-muted-foreground font-normal">({college.totalCourseStudents} enrolled)</span></p>
                                    <p className="text-[11px] text-muted-foreground">
                                        {college.totalStudents} students · {college.coordinatorName}
                                    </p>
                                </div>
                                <div className="flex items-center gap-3 shrink-0">
                                    <div className="text-right">
                                        <p className="text-sm font-bold">{college.avgProgress}%</p>
                                        <p className="text-[10px] text-muted-foreground">progress</p>
                                    </div>
                                    <div className="text-right">
                                        <p className={`text-sm font-bold ${college.completionRate >= 30 ? 'text-success' : college.completionRate >= 15 ? 'text-warning' : 'text-destructive'}`}>
                                            {college.completionRate}%
                                        </p>
                                        <p className="text-[10px] text-muted-foreground">completed</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Top Performers + At-Risk — Platform-wide */}
            <div className="grid lg:grid-cols-2 gap-5">
                {/* Top Performers */}
                <Card className="border-border/40">
                    <CardContent className="p-4">
                        <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
                            <Trophy className="h-4 w-4 text-xp-gold" />
                            Top Performers — All Colleges
                        </h3>
                        <div className="space-y-1">
                            {summary.topPerformers.map((student, i) => (
                                <button key={student.id} onClick={() => onStudentClick({ id: student.id, name: student.name, initials: student.initials })} className="w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-muted/30 transition-colors">
                                    <span className={`text-xs font-bold w-6 text-right ${i === 0 ? 'text-xp-gold' :
                                        i === 1 ? 'text-gray-400' :
                                            i === 2 ? 'text-orange-500' :
                                                'text-muted-foreground'
                                        }`}>#{i + 1}</span>
                                    <Avatar className="h-7 w-7">
                                        <AvatarFallback className="text-[9px] font-semibold bg-primary/10 text-primary">
                                            {student.initials}
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium truncate">{student.name}</p>
                                        <p className="text-[10px] text-muted-foreground">{student.collegeName}</p>
                                    </div>
                                    <div className="flex items-center gap-3 shrink-0">
                                        <div className="flex items-center gap-1 w-14 justify-end">
                                            <Zap className="h-3 w-3 text-xp-gold" />
                                            <span className="text-xs font-bold tabular-nums">{student.xp}</span>
                                        </div>
                                        <Progress value={student.progress} className="h-1.5 w-14" />
                                    </div>
                                </button>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* At-Risk Students — Platform-wide */}
                <Card className="border-border/40">
                    <CardContent className="p-4">
                        <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
                            <AlertTriangle className="h-4 w-4 text-warning" />
                            At-Risk Students — All Colleges
                            {summary.atRiskStudents.length > 0 && (
                                <Badge className="bg-destructive/10 text-destructive border-0 text-[10px] px-1.5 py-0 h-4">
                                    {summary.atRiskStudents.length} need attention
                                </Badge>
                            )}
                        </h3>
                        {summary.atRiskStudents.length === 0 ? (
                            <div className="text-center py-6">
                                <CheckCircle2 className="h-8 w-8 text-success mx-auto mb-2" />
                                <p className="text-sm font-medium">All students on track! 🎉</p>
                            </div>
                        ) : (
                            <div className="space-y-1.5">
                                {summary.atRiskStudents.map(student => {
                                    const sc = getStatusConfig(student.status)
                                    return (
                                        <button key={student.id} onClick={() => onStudentClick({ id: student.id, name: student.name, initials: student.initials })} className="w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-lg bg-destructive/5 border border-destructive/10 hover:bg-destructive/10 transition-colors">
                                            <Avatar className="h-7 w-7">
                                                <AvatarFallback className="text-[9px] font-semibold bg-destructive/10 text-destructive">
                                                    {student.initials}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">{student.name}</p>
                                                <p className="text-[10px] text-muted-foreground">
                                                    {student.collegeName} · {student.progress}%
                                                </p>
                                            </div>
                                            <Badge className={`text-[9px] px-1.5 py-0 h-4 border-0 ${sc.color}`}>
                                                {sc.label}
                                            </Badge>
                                        </button>
                                    )
                                })}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

// ===== COLLEGE DAILY XP CHART =====

interface ChartCollege {
    id: string
    name: string
    color: string
}


function CollegeXPChart({ colleges }: { colleges: CollegeSummary[] }) {
    const now = new Date()
    const [selectedMonth, setSelectedMonth] = useState(
        `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
    )
    const [selectedCollegeIds, setSelectedCollegeIds] = useState<string[]>(
        colleges.map(c => c.id)
    )
    const { data: chartData, isLoading } = useCollegesDailyXP(selectedMonth, selectedCollegeIds)
    const [dropdownOpen, setDropdownOpen] = useState(false)
    const [collegeSearch, setCollegeSearch] = useState('')
    const dropdownRef = useRef<HTMLDivElement>(null)

    // Close dropdown on outside click
    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
                setDropdownOpen(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])




    // Generate month options (last 12 months)
    const monthOptions: { value: string; label: string }[] = []
    for (let i = 0; i < 12; i++) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
        const val = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
        const label = d.toLocaleString('default', { month: 'long', year: 'numeric' })
        monthOptions.push({ value: val, label })
    }

    const toggleCollege = (id: string) => {
        setSelectedCollegeIds(prev =>
            prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
        )
    }

    const filteredColleges = colleges.filter(c =>
        c.name.toLowerCase().includes(collegeSearch.toLowerCase()) ||
        c.id.toLowerCase().includes(collegeSearch.toLowerCase())
    )

    // Build a color map from API response
    const colorMap: Record<string, string> = {}
    chartData?.colleges.forEach((c: ChartCollege) => { colorMap[c.id] = c.color })

    return (
        <Card className="border-border/40">
            <CardContent className="p-4">
                {/* Header with controls */}
                <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
                    <h3 className="text-sm font-bold flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-primary" />
                        Daily Average XP by College
                    </h3>
                    <div className="flex items-center gap-2">
                        {/* Month Dropdown */}
                        <div className="relative">
                            <CalendarDays className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
                            <select
                                value={selectedMonth}
                                onChange={e => setSelectedMonth(e.target.value)}
                                className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-border bg-muted/30 focus:outline-none focus:ring-1 focus:ring-primary/30 appearance-none cursor-pointer"
                            >
                                {monthOptions.map(opt => (
                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                ))}
                            </select>
                        </div>

                        {/* Multi-select College Dropdown */}
                        <div className="relative" ref={dropdownRef}>
                            <button
                                onClick={() => setDropdownOpen(!dropdownOpen)}
                                className="flex items-center gap-1.5 pl-3 pr-2 py-1.5 text-xs rounded-lg border border-border bg-muted/30 hover:bg-muted/50 transition-colors"
                            >
                                <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
                                <span className="max-w-[120px] truncate">
                                    {selectedCollegeIds.length === colleges.length
                                        ? 'All Colleges'
                                        : selectedCollegeIds.length === 0
                                            ? 'Select colleges'
                                            : `${selectedCollegeIds.length} selected`
                                    }
                                </span>
                                <ChevronDown className={`h-3.5 w-3.5 text-muted-foreground transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
                            </button>

                            {dropdownOpen && (
                                <div className="absolute right-0 top-full mt-1 w-64 bg-popover border border-border rounded-lg shadow-lg z-50 overflow-hidden">
                                    {/* Search */}
                                    <div className="p-2 border-b border-border/50">
                                        <div className="relative">
                                            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                                            <input
                                                type="text"
                                                placeholder="Search colleges..."
                                                value={collegeSearch}
                                                onChange={e => setCollegeSearch(e.target.value)}
                                                className="w-full pl-7 pr-3 py-1.5 text-xs rounded border border-border/50 bg-muted/20 focus:outline-none focus:ring-1 focus:ring-primary/30"
                                                autoFocus
                                            />
                                        </div>
                                    </div>

                                    {/* Select All / Clear */}
                                    <div className="flex items-center justify-between px-3 py-1.5 border-b border-border/30">
                                        <button
                                            onClick={() => setSelectedCollegeIds(colleges.map(c => c.id))}
                                            className="text-[10px] text-primary hover:underline"
                                        >
                                            Select All
                                        </button>
                                        <button
                                            onClick={() => setSelectedCollegeIds([])}
                                            className="text-[10px] text-muted-foreground hover:text-destructive hover:underline"
                                        >
                                            Clear All
                                        </button>
                                    </div>

                                    {/* College List */}
                                    <div className="max-h-48 overflow-y-auto">
                                        {filteredColleges.map(c => {
                                            const isChecked = selectedCollegeIds.includes(c.id)
                                            return (
                                                <button
                                                    key={c.id}
                                                    onClick={() => toggleCollege(c.id)}
                                                    className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-muted/30 transition-colors"
                                                >
                                                    <div className={`h-4 w-4 rounded border flex items-center justify-center shrink-0 transition-colors ${isChecked
                                                        ? 'bg-primary border-primary'
                                                        : 'border-border'
                                                        }`}>
                                                        {isChecked && (
                                                            <CheckCircle2 className="h-3 w-3 text-white" />
                                                        )}
                                                    </div>
                                                    <span className="text-xs truncate">{c.name}</span>
                                                    {colorMap[c.id] && (
                                                        <span
                                                            className="ml-auto h-2.5 w-2.5 rounded-full shrink-0"
                                                            style={{ backgroundColor: colorMap[c.id] }}
                                                        />
                                                    )}
                                                </button>
                                            )
                                        })}
                                        {filteredColleges.length === 0 && (
                                            <p className="text-xs text-muted-foreground text-center py-3">No colleges found</p>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Selected college chips */}
                {selectedCollegeIds.length > 0 && selectedCollegeIds.length < colleges.length && (
                    <div className="flex items-center gap-1.5 flex-wrap mb-3">
                        {selectedCollegeIds.map(id => {
                            const col = colleges.find(c => c.id === id)
                            return (
                                <span key={id} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 text-primary">
                                    <span
                                        className="h-2 w-2 rounded-full"
                                        style={{ backgroundColor: colorMap[id] || '#888' }}
                                    />
                                    {col?.name || id}
                                    <button onClick={() => toggleCollege(id)} className="hover:text-destructive">
                                        <X className="h-3 w-3" />
                                    </button>
                                </span>
                            )
                        })}
                    </div>
                )}

                {/* Chart */}
                {isLoading ? (
                    <div className="h-64 flex items-center justify-center text-sm text-muted-foreground">
                        Loading chart data...
                    </div>
                ) : !chartData || selectedCollegeIds.length === 0 ? (
                    <div className="h-64 flex items-center justify-center text-sm text-muted-foreground">
                        Select at least one college to view the chart
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height={280}>
                        <LineChart data={chartData.series} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                            <XAxis
                                dataKey="day"
                                tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                                tickLine={false}
                                axisLine={{ stroke: 'hsl(var(--border))' }}
                                label={{ value: 'Day of Month', position: 'insideBottom', offset: -2, fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                            />
                            <YAxis
                                tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                                tickLine={false}
                                axisLine={{ stroke: 'hsl(var(--border))' }}
                                label={{ value: 'Avg XP', angle: -90, position: 'insideLeft', offset: 10, fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'hsl(var(--popover))',
                                    border: '1px solid hsl(var(--border))',
                                    borderRadius: '8px',
                                    fontSize: '12px',
                                    color: 'hsl(var(--popover-foreground))',
                                }}
                                labelStyle={{ color: 'hsl(var(--foreground))' }}
                                labelFormatter={(label) => `Day ${label}`}
                                formatter={(value: any, name: any) => {
                                    const col = chartData.colleges.find((c: any) => c.id === name)
                                    return [value, col?.name || name]
                                }}
                            />
                            <Legend
                                formatter={(value) => {
                                    const col = chartData.colleges.find((c: ChartCollege) => c.id === value)
                                    return <span className="text-xs">{col?.name || value}</span>
                                }}
                            />
                            {chartData.colleges
                                .filter((c: ChartCollege) => selectedCollegeIds.includes(c.id))
                                .map((college: ChartCollege) => (
                                    <Line
                                        key={college.id}
                                        type="monotone"
                                        dataKey={college.id}
                                        stroke={college.color}
                                        strokeWidth={2}
                                        dot={{ r: 3, fill: college.color }}
                                        activeDot={{ r: 5 }}
                                        name={college.id}
                                    />
                                ))}
                        </LineChart>
                    </ResponsiveContainer>
                )}
            </CardContent>
        </Card>
    )
}

// ===== COLLEGES TAB =====
// College list uses summary data. Drill-down fetches paginated students on demand.

function CollegesTab({ colleges, onStudentClick }: {
    colleges: CollegeSummary[]
    onStudentClick: (student: { id: string, name: string, initials: string }) => void
}) {
    const [selectedCollegeId, setSelectedCollegeId] = useState<string | null>(null)
    const [sortBy, setSortBy] = useState<SortBy>('progress')
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
    const [searchQuery, setSearchQuery] = useState('')
    const [page, setPage] = useState(1)
    const [collegeSearch, setCollegeSearch] = useState('')
    const [collegeSort, setCollegeSort] = useState<'progress' | 'name' | 'students' | 'completion' | 'xp'>('progress')
    const { data: collegeDetails, isLoading: isLoadingDetails } = useCollegeDetails(selectedCollegeId, page, sortBy, statusFilter, searchQuery)





    // If a college is selected, show drill-down view
    if (selectedCollegeId) {
        const college = colleges.find(c => c.id === selectedCollegeId)
        const students = collegeDetails?.students || []
        const pagination = collegeDetails?.pagination

        return (
            <div className="space-y-5">
                {/* Back button */}
                <button
                    onClick={() => {
                        setSelectedCollegeId(null)
                        setSearchQuery('')
                        setStatusFilter('all')
                        setPage(1)
                    }}
                    className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                    <ArrowLeft className="h-4 w-4" />
                    Back to all colleges
                </button>

                {/* College header */}
                {college && (
                    <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-transparent">
                        <CardContent className="p-5">
                            <div className="flex items-center justify-between flex-wrap gap-3">
                                <div>
                                    <h2 className="text-lg font-bold">{college.name} <span className="text-base font-normal text-muted-foreground">({college.totalCourseStudents} enrolled)</span></h2>
                                    <p className="text-sm text-muted-foreground">
                                        {college.location} · {college.coordinatorName} · {college.course}
                                    </p>
                                </div>
                                <div className="flex gap-4">
                                    <div className="text-center">
                                        <p className="text-xl font-bold">{college.totalStudents}</p>
                                        <p className="text-[10px] text-muted-foreground">Students</p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-xl font-bold text-primary">{college.avgProgress}%</p>
                                        <p className="text-[10px] text-muted-foreground">Progress</p>
                                    </div>
                                    <div className="text-center">
                                        <p className={`text-xl font-bold ${college.completionRate >= 30 ? 'text-success' : 'text-warning'}`}>{college.completionRate}%</p>
                                        <p className="text-[10px] text-muted-foreground">Completed</p>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Student Table */}
                <Card className="border-border/40">
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
                            <h2 className="text-sm font-bold flex items-center gap-2">
                                <Users className="h-4 w-4 text-primary" />
                                Students — {college?.name || selectedCollegeId}
                            </h2>
                            <div className="relative">
                                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                                <input
                                    type="text"
                                    placeholder="Search name..."
                                    value={searchQuery}
                                    onChange={(e) => { setSearchQuery(e.target.value); setPage(1) }}
                                    className="pl-8 pr-3 py-1.5 text-xs rounded-full border border-border bg-muted/30 w-48 focus:outline-none focus:ring-1 focus:ring-primary/30"
                                />
                            </div>
                        </div>

                        {/* Status Filter Chips */}
                        <div className="flex items-center gap-1.5 mb-4 overflow-x-auto pb-1">
                            {([
                                { id: 'all', label: 'All' },
                                { id: 'active', label: 'Active' },
                                { id: 'completed', label: 'Completed' },
                                { id: 'at_risk', label: 'At Risk' },
                                { id: 'inactive', label: 'Inactive' },
                            ] as { id: StatusFilter; label: string }[]).map(filter => (
                                <button
                                    key={filter.id}
                                    onClick={() => { setStatusFilter(filter.id); setPage(1) }}
                                    className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all whitespace-nowrap
                                        ${statusFilter === filter.id
                                            ? 'bg-primary text-white'
                                            : 'bg-muted/40 text-muted-foreground hover:text-foreground'
                                        }`}
                                >
                                    {filter.label}
                                </button>
                            ))}
                        </div>

                        {/* Sort Controls */}
                        <div className="flex items-center gap-1.5 mb-3 text-[10px] text-muted-foreground">
                            <Filter className="h-3 w-3" />
                            <span>Sort:</span>
                            {([
                                { id: 'progress', label: 'Progress' },
                                { id: 'name', label: 'Name' },
                                { id: 'xp', label: 'XP' },
                            ] as { id: SortBy; label: string }[]).map(sort => (
                                <button
                                    key={sort.id}
                                    onClick={() => { setSortBy(sort.id); setPage(1) }}
                                    className={`px-2 py-0.5 rounded text-[10px] transition-colors
                                        ${sortBy === sort.id ? 'bg-primary/10 text-primary font-medium' : 'hover:text-foreground'}`}
                                >
                                    {sort.label}
                                </button>
                            ))}
                        </div>

                        {/* Table Header */}
                        <div className="flex items-center gap-3 px-3 sm:px-4 py-2 text-[10px] uppercase tracking-wider text-muted-foreground font-semibold border-b border-border/30 mb-1">
                            <div className="w-6 shrink-0 text-center">#</div>
                            <div className="w-8 shrink-0" />
                            <div className="flex-1">Student</div>
                            <div className="hidden sm:block w-28 text-center">Progress</div>
                            <div className="hidden md:flex w-32 items-center gap-4 justify-center">
                                <span className="flex items-center gap-0.5"><Eye className="h-3 w-3" /> Watched</span>
                                <span className="flex items-center gap-0.5"><CheckCircle2 className="h-3 w-3" /> Done</span>
                            </div>
                            <div className="hidden lg:block w-16 text-right">XP</div>
                            <div className="w-24 shrink-0 text-center">Status</div>
                        </div>

                        {/* Student Rows */}
                        {isLoadingDetails ? (
                            <p className="text-center text-sm text-muted-foreground py-8">Loading students...</p>
                        ) : (
                            <div className="space-y-0.5">
                                {students.map((student: Student, idx: number) => (
                                    <StudentRow 
                                        key={student.id} 
                                        student={student} 
                                        index={(page - 1) * 10 + idx + 1}
                                        onClick={() => onStudentClick({ id: student.id, name: student.name, initials: student.initials })} 
                                    />
                                ))}
                                {students.length === 0 && (
                                    <p className="text-center text-sm text-muted-foreground py-8">
                                        No students match your filters
                                    </p>
                                )}
                            </div>
                        )}

                        {/* Pagination */}
                        {pagination && pagination.totalPages > 1 && (
                            <div className="flex items-center justify-between pt-4 border-t border-border/30">
                                <p className="text-xs text-muted-foreground">
                                    Page {pagination.currentPage} of {pagination.totalPages} · {pagination.totalRecords} students
                                </p>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => setPage(page - 1)}
                                        disabled={page <= 1}
                                        className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border disabled:opacity-30 hover:bg-muted/50 transition-colors"
                                    >
                                        ← Prev
                                    </button>
                                    <button
                                        onClick={() => setPage(page + 1)}
                                        disabled={page >= pagination.totalPages}
                                        className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border disabled:opacity-30 hover:bg-muted/50 transition-colors"
                                    >
                                        Next →
                                    </button>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        )
    }

    // Default: College list view
    const collegesWithRank = [...colleges]
        .sort((a, b) => b.avgProgress - a.avgProgress)
        .map((c, i) => ({ ...c, rank: i + 1 }))

    const filteredColleges = collegesWithRank.filter(c => 
        c.name.toLowerCase().includes(collegeSearch.toLowerCase()) || 
        c.location.toLowerCase().includes(collegeSearch.toLowerCase()) ||
        c.coordinatorName.toLowerCase().includes(collegeSearch.toLowerCase())
    )
    
    const sortedColleges = [...filteredColleges].sort((a, b) => {
        if (collegeSort === 'progress') return b.avgProgress - a.avgProgress
        if (collegeSort === 'completion') return b.completionRate - a.completionRate
        if (collegeSort === 'students') return b.totalStudents - a.totalStudents
        if (collegeSort === 'xp') return b.avgXP - a.avgXP
        return a.name.localeCompare(b.name)
    })

    return (
        <div className="space-y-5">
            <CollegeXPChart colleges={colleges} />
            <Card className="border-border/40">
                <CardContent className="p-4">
                    <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-3 mb-5">
                        <h2 className="text-sm font-bold flex items-center gap-2">
                            <Building2 className="h-4 w-4 text-primary shrink-0" />
                            All Colleges — Click to view students
                        </h2>
                        <div className="flex flex-col sm:flex-row sm:items-center gap-3 w-full xl:w-auto">
                            <div className="relative w-full sm:w-auto">
                                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                                <input
                                    type="text"
                                    placeholder="Search name, location, coordinator..."
                                    value={collegeSearch}
                                    onChange={(e) => setCollegeSearch(e.target.value)}
                                    className="pl-8 pr-3 py-1.5 text-xs rounded-full border border-border bg-muted/30 w-full sm:w-64 focus:outline-none focus:ring-1 focus:ring-primary/30"
                                />
                            </div>
                            <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground bg-muted/20 px-2 py-1.5 rounded-lg border border-border/30 overflow-x-auto w-full sm:w-auto">
                                <Filter className="h-3 w-3 shrink-0" />
                                <span className="shrink-0 font-medium">Sort:</span>
                                {([
                                    { id: 'progress', label: 'Progress' },
                                    { id: 'completion', label: 'Completion' },
                                    { id: 'students', label: 'Students' },
                                    { id: 'xp', label: 'XP' },
                                    { id: 'name', label: 'Name' },
                                ] as const).map(sort => (
                                    <button
                                        key={sort.id}
                                        onClick={() => setCollegeSort(sort.id)}
                                        className={`px-2 py-0.5 rounded text-[10px] transition-colors shrink-0
                                            ${collegeSort === sort.id ? 'bg-primary/10 text-primary font-bold shadow-sm' : 'hover:text-foreground'}`}
                                    >
                                        {sort.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Table Header */}
                    <div className="flex items-center gap-3 px-4 py-2.5 text-[10px] uppercase tracking-wider text-muted-foreground font-semibold border-b border-border/30 mb-1">
                        <div className="w-8 shrink-0 text-center">Rank</div>
                        <div className="flex-1">College</div>
                        <div className="w-16 text-center">Students</div>
                        <div className="w-24 text-center hidden sm:block">Progress</div>
                        <div className="w-20 text-center">Completion</div>
                        <div className="w-16 text-center hidden md:block">Avg XP</div>
                        <div className="w-8 shrink-0" />
                    </div>

                    {/* College Rows */}
                    <div className="space-y-0.5">
                        {sortedColleges.map((college) => {
                            const rank = college.rank
                            return (
                                <button
                                    key={college.id}
                                    onClick={() => setSelectedCollegeId(college.id)}
                                    className="w-full flex items-center gap-3 px-4 py-3.5 rounded-lg transition-colors hover:bg-muted/30 text-left"
                                >
                                    <div className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold shrink-0
                                        ${rank === 1 ? 'bg-xp-gold/15 text-xp-gold' :
                                            rank === 2 ? 'bg-gray-300/20 text-gray-500' :
                                                rank === 3 ? 'bg-orange-200/20 text-orange-600' :
                                                    'bg-muted text-muted-foreground'
                                        }`}>
                                        #{rank}
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-semibold truncate">{college.name} <span className="text-muted-foreground font-normal">({college.totalCourseStudents})</span></p>
                                        <p className="text-[11px] text-muted-foreground">{college.location} · {college.coordinatorName}</p>
                                    </div>

                                    <div className="w-16 text-center">
                                        <span className="text-sm font-mono font-semibold">{college.totalStudents}</span>
                                    </div>

                                    <div className="hidden sm:flex items-center gap-2 w-24">
                                        <Progress value={college.avgProgress} className="h-1.5 flex-1" />
                                        <span className="text-[11px] font-mono font-semibold w-8 text-right">{college.avgProgress}%</span>
                                    </div>

                                    <div className="w-20 text-center">
                                        <span className={`text-sm font-bold ${college.completionRate >= 30 ? 'text-success' : college.completionRate >= 15 ? 'text-warning' : 'text-destructive'}`}>
                                            {college.completionRate}%
                                        </span>
                                    </div>

                                    <div className="hidden md:block w-16 text-center">
                                        <span className="text-sm font-mono">{college.avgXP}</span>
                                    </div>

                                    <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                                </button>
                            )
                        })}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

// ===== ANALYTICS TAB =====
// Uses pre-computed distributions and tutorial stats from /api/admin/platform-summary

function DonutCenterLabel({ value, label }: { value: string; label: string }) {
    return (
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-2xl font-bold">{value}</span>
            <span className="text-[10px] text-muted-foreground">{label}</span>
        </div>
    )
}

function AnalyticsTab({ colleges, summary }: {
    colleges: CollegeSummary[]
    summary: PlatformSummary
}) {
    const m = summary.metrics
    const statusData = summary.statusDistribution.filter(d => d.value > 0)
    const progressData = summary.progressDistribution.filter(d => d.value > 0)

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-popover border border-border rounded-lg px-3 py-2 shadow-md">
                    <p className="text-sm font-medium">{payload[0].name}</p>
                    <p className="text-xs text-muted-foreground">{payload[0].value} students ({m.totalStudents > 0 ? Math.round((payload[0].value / m.totalStudents) * 100) : 0}%)</p>
                </div>
            )
        }
        return null
    }

    return (
        <div className="space-y-5">
            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-3">
                <Card className="border-border/40">
                    <CardContent className="p-4 text-center">
                        <Eye className="h-5 w-5 text-primary mx-auto mb-1" />
                        <p className="text-2xl font-bold">{m.avgProgress}%</p>
                        <p className="text-[11px] text-muted-foreground">Platform Avg Progress</p>
                    </CardContent>
                </Card>
                <Card className="border-border/40">
                    <CardContent className="p-4 text-center">
                        <Zap className="h-5 w-5 text-xp-gold mx-auto mb-1" />
                        <p className="text-2xl font-bold">{m.avgXP}</p>
                        <p className="text-[11px] text-muted-foreground">Avg XP / Student</p>
                    </CardContent>
                </Card>
                <Card className="border-border/40">
                    <CardContent className="p-4 text-center">
                        <Building2 className="h-5 w-5 text-primary mx-auto mb-1" />
                        <p className="text-2xl font-bold">{m.totalColleges}</p>
                        <p className="text-[11px] text-muted-foreground">Colleges</p>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{m.totalStudents} students</p>
                    </CardContent>
                </Card>
            </div>

            {/* Donut Charts */}
            <div className="grid lg:grid-cols-2 gap-5">
                {/* Status Distribution */}
                <Card className="border-border/40">
                    <CardContent className="p-4">
                        <h3 className="text-sm font-bold flex items-center gap-2 mb-2">
                            <Users className="h-4 w-4 text-primary" />
                            Platform Status Distribution
                        </h3>
                        <div className="flex items-center gap-4">
                            <div className="relative w-40 h-40 shrink-0">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie data={statusData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value" strokeWidth={0}>
                                            {statusData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip content={<CustomTooltip />} />
                                    </PieChart>
                                </ResponsiveContainer>
                                <DonutCenterLabel value={String(m.totalStudents)} label="students" />
                            </div>
                            <div className="flex-1 space-y-2">
                                {statusData.map(item => (
                                    <div key={item.name} className="flex items-center gap-2">
                                        <span className="h-3 w-3 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                                        <span className="text-xs flex-1">{item.name}</span>
                                        <span className="text-sm font-bold">{item.value}</span>
                                        <span className="text-[10px] text-muted-foreground">{Math.round((item.value / m.totalStudents) * 100)}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Progress Distribution */}
                <Card className="border-border/40">
                    <CardContent className="p-4">
                        <h3 className="text-sm font-bold flex items-center gap-2 mb-2">
                            <BarChart3 className="h-4 w-4 text-primary" />
                            Platform Progress Distribution
                        </h3>
                        <div className="flex items-center gap-4">
                            <div className="relative w-40 h-40 shrink-0">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie data={progressData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value" strokeWidth={0}>
                                            {progressData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip content={<CustomTooltip />} />
                                    </PieChart>
                                </ResponsiveContainer>
                                <DonutCenterLabel
                                    value={`${m.avgProgress}%`}
                                    label="avg progress"
                                />
                            </div>
                            <div className="flex-1 space-y-2">
                                {progressData.map(item => (
                                    <div key={item.name} className="flex items-center gap-2">
                                        <span className="h-3 w-3 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                                        <span className="text-xs flex-1">{item.name}</span>
                                        <span className="text-sm font-bold">{item.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Tutorial-wise Completion — Platform-wide */}
            <Card className="border-border/40">
                <CardContent className="p-4">
                    <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
                        <CheckCircle2 className="h-4 w-4 text-success" />
                        Tutorial-wise Completion — All Colleges
                        <span className="text-[10px] font-normal text-muted-foreground">— where are students dropping off?</span>
                    </h3>
                    <div className="space-y-1.5">
                        {summary.tutorialCompletion.map(t => (
                            <div key={t.number} className="flex items-center gap-3">
                                <span className="text-[11px] text-muted-foreground w-5 text-right font-mono shrink-0">{t.number}</span>
                                <span className="text-xs w-44 truncate shrink-0">{t.name}</span>
                                <div className="flex-1 h-5 bg-muted/30 rounded overflow-hidden relative">
                                    <div
                                        className={`h-full rounded transition-all duration-500 ${t.rate >= 75 ? 'bg-success/60' :
                                            t.rate >= 50 ? 'bg-primary/50' :
                                                t.rate >= 25 ? 'bg-warning/50' :
                                                    'bg-destructive/40'
                                            }`}
                                        style={{ width: `${t.rate}%` }}
                                    />
                                    <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono font-semibold">
                                        {t.completedCount}/{m.totalStudents}
                                    </span>
                                </div>
                                <span className={`text-xs font-bold w-10 text-right ${t.rate >= 75 ? 'text-success' :
                                    t.rate >= 50 ? 'text-primary' :
                                        t.rate >= 25 ? 'text-warning' :
                                            'text-destructive'
                                    }`}>{t.rate}%</span>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Per-College Comparison Table */}
            <Card className="border-border/40">
                <CardContent className="p-4">
                    <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
                        <BarChart3 className="h-4 w-4 text-primary" />
                        College Performance Comparison
                    </h3>
                    <div className="space-y-2">
                        {[...colleges].sort((a, b) => b.avgProgress - a.avgProgress).map(college => (
                            <div key={college.id} className="flex items-center gap-3">
                                <span className="text-xs w-32 truncate shrink-0 font-medium">{college.name} <span className="text-muted-foreground font-normal">({college.totalCourseStudents})</span></span>
                                <div className="flex-1 h-6 bg-muted/30 rounded overflow-hidden relative">
                                    <div
                                        className="h-full rounded bg-primary/50 transition-all duration-500"
                                        style={{ width: `${college.avgProgress}%` }}
                                    />
                                    <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono font-semibold">
                                        {college.avgProgress}% avg · {college.completionRate}% done · {college.totalStudents} students
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}


// ===== MAIN COMPONENT =====

export default function AdminDashboard() {

    const { data: colleges = [], isLoading: collegesLoading } = useColleges()
    const { data: summary, isLoading: summaryLoading } = usePlatformSummary()
    const isLoading = collegesLoading || summaryLoading

    const [activeTab, setActiveTab] = useState<Tab>('overview')
    const [selectedStudentForFeedback, setSelectedStudentForFeedback] = useState<{ id: string, name: string, initials: string } | null>(null)

    const totalStudents = colleges.reduce((a: number, c: CollegeSummary) => a + c.totalStudents, 0)

    const tabs = [
        { id: 'overview' as const, label: 'Overview', icon: BarChart3 },
        { id: 'colleges' as const, label: 'Colleges', icon: Building2 },
        { id: 'analytics' as const, label: 'Analytics', icon: Activity },
        { id: 'feedback' as const, label: 'Feedback', icon: MessageCircleQuestion },
    ]

    if (isLoading || !summary) {
        return (
            <div className="max-w-6xl mx-auto p-6 text-center text-muted-foreground">
                Loading admin dashboard...
            </div>
        )
    }

    return (
        <div className="max-w-6xl mx-auto space-y-5">
            {/* Header */}
            <div className="flex items-start sm:items-center justify-between flex-wrap gap-4">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <Shield className="h-6 w-6 text-primary" />
                        <h1 className="text-xl sm:text-2xl font-bold">Admin Panel</h1>
                        <Badge className="bg-primary/10 text-primary border-0 text-[10px] px-2 py-0.5">
                            Platform Admin
                        </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Users className="h-4 w-4" />
                        <span>{colleges.length} colleges • {totalStudents} students • Linux Course</span>
                    </div>
                </div>

                <button
                    onClick={async () => {
                        try {
                            const response = await api.get(`/api/admin/colleges/export`, { responseType: 'blob' });
                            const url = window.URL.createObjectURL(new Blob([response.data]));
                            const link = document.createElement('a');
                            link.href = url;
                            link.setAttribute('download', 'Platform_Colleges_Report.xlsx');
                            document.body.appendChild(link);
                            link.click();
                        } catch (e) {
                            console.error('Failed to export', e);
                        }
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors rounded-md shadow-sm"
                >
                    <Download className="h-3.5 w-3.5" />
                    Download Report
                </button>
            </div>

            {/* Tabs */}
            <div className="flex items-center gap-1 border-b border-border/50">
                {tabs.map(tab => {
                    const Icon = tab.icon
                    const isActive = activeTab === tab.id
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium
                                border-b-2 transition-all duration-200 whitespace-nowrap
                                ${isActive
                                    ? 'border-primary text-primary'
                                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                                }`}
                        >
                            <Icon className="h-4 w-4" />
                            {tab.label}
                        </button>
                    )
                })}
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && (
                <OverviewTab colleges={colleges} summary={summary} onStudentClick={setSelectedStudentForFeedback} />
            )}

            {activeTab === 'colleges' && (
                <CollegesTab colleges={colleges} onStudentClick={setSelectedStudentForFeedback} />
            )}

            {activeTab === 'analytics' && (
                <AnalyticsTab colleges={colleges} summary={summary} />
            )}

            {activeTab === 'feedback' && (
                <FeedbackPanel onStudentClick={setSelectedStudentForFeedback} />
            )}

            {selectedStudentForFeedback && (
                <StudentFeedbackDrawer
                    studentId={selectedStudentForFeedback.id}
                    studentName={selectedStudentForFeedback.name}
                    studentInitials={selectedStudentForFeedback.initials}
                    onClose={() => setSelectedStudentForFeedback(null)}
                />
            )}
        </div>
    )
}
