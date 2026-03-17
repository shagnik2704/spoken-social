import { useState} from 'react'
import {
    Users, GraduationCap, TrendingUp, AlertTriangle,
    CheckCircle2, Terminal, Eye,
    Search, Filter, Trophy, BarChart3,
    MessageCircleQuestion,
    // Star,
    Clock, Zap, Activity
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts'
import {
    useCoordinatorColleges,
    useCoordinatorCollegeDetails,
    useCoordinatorCollegeAnalytics,
    useCoordinatorFeedbackSummary
} from '@/hooks/queries/useCoordinatorQueries'
import { FeedbackPanel } from '@/components/admin/FeedbackPanel'

import {
    Pagination,
    PaginationContent,
    PaginationItem,
    PaginationLink,
    PaginationNext,
    PaginationPrevious,
    PaginationEllipsis,
} from '@/components/ui/pagination'
import { useUserStore } from '@/store/userStore'

// ===== TYPES =====

interface CollegeSummary {
    id: string
    name: string
    location: string
    coordinatorName: string
    course: string
    totalCourseStudents: number
    totalStudents: number
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

interface CollegeDetails {
    college: {
        id: string
        name: string
        location: string
        coordinatorName: string
        course: string
    }
    metrics: {
        totalStudents: number
        activeStudents: number
        completedStudents: number
        avgProgress: number
        avgXP: number
        completionRate: number
    }
    students: Student[]
    pagination?: {
        currentPage: number
        totalPages: number
        totalRecords: number
        limit: number
    }
}

type Tab = 'students' | 'analytics' | 'feedback' | 'compare'
type SortBy = 'name' | 'progress' | 'xp'
type StatusFilter = 'all' | 'active' | 'completed' | 'at_risk' | 'inactive'



// ===== STATUS HELPERS =====

function getStatusConfig(status: Student['status']) {
    switch (status) {
        case 'completed': return { label: 'Completed', color: 'bg-success/10 text-success', dot: 'bg-success' }
        case 'active': return { label: 'Active', color: 'bg-primary/10 text-primary', dot: 'bg-primary' }
        case 'at_risk': return { label: 'At Risk', color: 'bg-warning/10 text-warning', dot: 'bg-warning' }
        case 'inactive': return { label: 'Inactive', color: 'bg-destructive/10 text-destructive', dot: 'bg-destructive' }
        case 'not_started': return { label: 'Not Started', color: 'bg-muted text-muted-foreground', dot: 'bg-muted-foreground' }
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

function StudentRow({ student }: { student: Student }) {
    const statusConfig = getStatusConfig(student.status)

    return (
        <div className="flex items-center gap-3 px-3 sm:px-4 py-3 rounded-lg hover:bg-muted/30 transition-colors">
            <Avatar className="h-8 w-8 shrink-0">
                <AvatarFallback className="text-[10px] font-semibold bg-primary/10 text-primary">
                    {student.initials}
                </AvatarFallback>
            </Avatar>

            <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{student.name}</p>
                <p className="text-[11px] text-muted-foreground font-mono">{student.rollNo}</p>
            </div>

            <div className="hidden sm:flex items-center gap-2 w-28">
                <Progress value={student.progress} className="h-1.5 flex-1" />
                <span className="text-[11px] text-muted-foreground font-mono w-8 text-right">{student.progress}%</span>
            </div>

            <div className="hidden md:flex w-32 items-center gap-4 justify-center">
                <span className="flex items-center gap-1 text-muted-foreground" title="Watched">
                    <Eye className="h-3 w-3 shrink-0" />
                    <span className="text-xs font-mono tabular-nums w-5 text-right">{student.tutorialsWatched}</span>
                </span>
                <span className="flex items-center gap-1" title="Completed">
                    <CheckCircle2 className="h-3 w-3 text-success shrink-0" />
                    <span className="text-xs font-mono font-medium tabular-nums w-5 text-right">{student.tutorialsCompleted}</span>
                </span>
            </div>

            <div className="hidden sm:flex w-16 items-center gap-1 justify-center" title="XP">
                <Zap className="h-3 w-3 text-xp-gold shrink-0" />
                <span className="text-xs font-mono font-semibold tabular-nums">{student.xp}</span>
            </div>

            <div className="w-24 shrink-0 flex justify-center">
                <Badge className={`${statusConfig.color} border-0 text-[10px] px-2 py-0.5`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${statusConfig.dot} mr-1.5`} />
                    {statusConfig.label}
                </Badge>
            </div>
        </div>
    )
}

// ===== MY STUDENTS TAB =====

function MyStudentsTab({ college, details, sortBy, setSortBy, statusFilter, setStatusFilter, searchQuery, setSearchQuery, page, setPage }: {
    college: CollegeSummary
    details: CollegeDetails | null
    sortBy: SortBy
    setSortBy: (s: SortBy) => void
    statusFilter: StatusFilter
    setStatusFilter: (s: StatusFilter) => void
    searchQuery: string
    setSearchQuery: (s: string) => void
    page: number
    setPage: (p: number) => void
}) {
    const filteredStudents = (details?.students || [])
    return (
        <div className="space-y-5">
            {/* Metric Cards — horizontally scrollable */}
            <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 snap-x">
                <div className="min-w-[200px] flex-shrink-0 snap-start">
                    <MetricCard
                        icon={GraduationCap}
                        label="Registered for Course"
                        value={college.totalCourseStudents}
                        subtext={`${college.activeStudents} active on platform`}
                        color="bg-secondary/10 text-secondary"
                    />
                </div>
                <div className="min-w-[200px] flex-shrink-0 snap-start">
                    <MetricCard
                        icon={Users}
                        label="Registered on Spoken Social"
                        value={college.totalStudents}
                        subtext={`${college.totalCourseStudents > 0 ? Math.round((college.totalStudents / college.totalCourseStudents) * 100) : 0}% of ${college.totalCourseStudents} course registrations`}
                        color="bg-primary/10 text-primary"
                    />
                </div>
                <div className="min-w-[200px] flex-shrink-0 snap-start">
                    <MetricCard
                        icon={TrendingUp}
                        label="Avg Progress"
                        value={`${college.avgProgress}%`}
                        color="bg-primary/10 text-primary"
                    />
                </div>
                <div className="min-w-[200px] flex-shrink-0 snap-start">
                    <MetricCard
                        icon={CheckCircle2}
                        label="Completion Rate"
                        value={`${college.completionRate}%`}
                        subtext={`${college.completedStudents} completed`}
                        color="bg-success/10 text-success"
                    />
                </div>
                <div className="min-w-[200px] flex-shrink-0 snap-start">
                    <MetricCard
                        icon={AlertTriangle}
                        label="At Risk"
                        value={college.atRiskStudents}
                        subtext={`${college.inactiveStudents} inactive`}
                        color="bg-warning/10 text-warning"
                    />
                </div>
            </div>

            {/* Student Table */}
            <Card className="border-border/40">
                <CardContent className="p-4">
                    {/* Header */}
                    <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
                        <h2 className="text-sm font-bold flex items-center gap-2">
                            <Users className="h-4 w-4 text-primary" />
                            Student Tracker — {college.name}
                        </h2>
                        <div className="relative">
                            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                            <input
                                type="text"
                                placeholder="Search name or roll no..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-8 pr-3 py-1.5 text-xs rounded-full border border-border bg-muted/30 w-48 focus:outline-none focus:ring-1 focus:ring-primary/30"
                            />
                        </div>
                    </div>

                    {/* Status Filter Chips */}
                    <div className="flex items-center gap-1.5 mb-4 overflow-x-auto pb-1">
                        {([
                            { id: 'all', label: 'All', count: details?.students.length },
                            { id: 'active', label: 'Active', count: details?.students.filter(s => s.status === 'active').length },
                            { id: 'completed', label: 'Completed', count: details?.students.filter(s => s.status === 'completed').length },
                            { id: 'at_risk', label: 'At Risk', count: details?.students.filter(s => s.status === 'at_risk').length },
                            { id: 'inactive', label: 'Inactive', count: details?.students.filter(s => s.status === 'inactive' || s.status === 'not_started').length },
                        ] as { id: StatusFilter; label: string; count?: number }[]).map(filter => (
                            <button
                                key={filter.id}
                                onClick={() => setStatusFilter(filter.id)}
                                className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all whitespace-nowrap
                                    ${statusFilter === filter.id
                                        ? 'bg-primary text-white'
                                        : 'bg-muted/40 text-muted-foreground hover:text-foreground'
                                    }`}
                            >
                                {filter.label}
                                {filter.count !== undefined && (
                                    <span className="ml-1 opacity-70">({filter.count})</span>
                                )}
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
                                onClick={() => setSortBy(sort.id)}
                                className={`px-2 py-0.5 rounded text-[10px] transition-colors
                                    ${sortBy === sort.id
                                        ? 'bg-primary/10 text-primary font-medium'
                                        : 'hover:text-foreground'
                                    }`}
                            >
                                {sort.label}
                            </button>
                        ))}
                    </div>

                    {/* Table Header */}
                    <div className="flex items-center gap-3 px-3 sm:px-4 py-2 text-[10px] uppercase tracking-wider text-muted-foreground font-semibold border-b border-border/30 mb-1">
                        <div className="w-8 shrink-0" />
                        <div className="flex-1">Student</div>
                        <div className="hidden sm:block w-28 text-center">Progress</div>
                        <div className="hidden md:flex w-32 items-center gap-4 justify-center">
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <span className="flex items-center gap-0.5 cursor-help"><Eye className="h-3 w-3" /> Watched</span>
                                    </TooltipTrigger>
                                    <TooltipContent side="top">Only watched the tutorials</TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <span className="flex items-center gap-0.5 cursor-help"><CheckCircle2 className="h-3 w-3" /> Completed</span>
                                    </TooltipTrigger>
                                    <TooltipContent side="top">Watched & practiced the tutorials</TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                        </div>
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <div className="hidden sm:flex w-16 items-center gap-0.5 justify-center cursor-help"><Zap className="h-3 w-3" /> XP</div>
                                </TooltipTrigger>
                                <TooltipContent side="top">
                                    Experience Points — earned by completing tutorials, practicing, and participating in forums
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                        <div className="w-24 shrink-0 text-center">Status</div>
                    </div>

                    {/* Student Rows */}
                    <div className="space-y-0.5">
                        {filteredStudents.map(student => (
                            <StudentRow key={student.id} student={student} />
                        ))}
                        {filteredStudents.length === 0 && (
                            <p className="text-center text-sm text-muted-foreground py-8">
                                No students match your filters
                            </p>
                        )}
                    </div>

                    {/* Pagination */}
                    {details?.pagination && details.pagination.totalPages > 1 && (
                        <div className="pt-4 border-t border-border/30">
                            <Pagination>
                                <PaginationContent>
                                    {/* Previous */}
                                    <PaginationItem>
                                        <PaginationPrevious
                                            onClick={(e) => { e.preventDefault(); if (page > 1) setPage(page - 1) }}
                                            aria-disabled={page <= 1}
                                            className={page <= 1 ? 'pointer-events-none opacity-30' : 'cursor-pointer'}
                                        />
                                    </PaginationItem>

                                    {/* Page numbers */}
                                    {Array.from({ length: details.pagination.totalPages }, (_, i) => i + 1).map((p) => {
                                        const total = details.pagination!.totalPages
                                        // Show first, last, current ±1, and ellipsis for the rest
                                        const show = p === 1 || p === total || Math.abs(p - page) <= 1
                                        const showEllipsisBefore = p === page - 2 && page - 2 > 1
                                        const showEllipsisAfter = p === page + 2 && page + 2 < total
                                        if (showEllipsisBefore || showEllipsisAfter) {
                                            return (
                                                <PaginationItem key={`ellipsis-${p}`}>
                                                    <PaginationEllipsis />
                                                </PaginationItem>
                                            )
                                        }
                                        if (!show) return null
                                        return (
                                            <PaginationItem key={p}>
                                                <PaginationLink
                                                    isActive={p === page}
                                                    onClick={(e) => { e.preventDefault(); setPage(p) }}
                                                    className="cursor-pointer"
                                                >
                                                    {p}
                                                </PaginationLink>
                                            </PaginationItem>
                                        )
                                    })}

                                    {/* Next */}
                                    <PaginationItem>
                                        <PaginationNext
                                            onClick={(e) => { e.preventDefault(); if (page < details.pagination!.totalPages) setPage(page + 1) }}
                                            aria-disabled={page >= details.pagination.totalPages}
                                            className={page >= details.pagination.totalPages ? 'pointer-events-none opacity-30' : 'cursor-pointer'}
                                        />
                                    </PaginationItem>
                                </PaginationContent>
                            </Pagination>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}

// ===== COMPARE COLLEGES TAB =====

// function CompareCollegesTab({ colleges, myCollegeId }: { colleges: CollegeSummary[]; myCollegeId: string }) {
//     const ranked = [...colleges].sort((a, b) => b.avgProgress - a.avgProgress)
//     const myRank = ranked.findIndex(c => c.id === myCollegeId) + 1

//     return (
//         <div className="space-y-5">
//             {/* My Rank Card */}
//             <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-transparent">
//                 <CardContent className="p-5 flex items-center justify-between">
//                     <div className="flex items-center gap-3">
//                         <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
//                             <Trophy className="h-6 w-6 text-primary" />
//                         </div>
//                         <div>
//                             <p className="text-sm text-muted-foreground">Your College Rank</p>
//                             <p className="text-2xl font-bold">
//                                 #{myRank} <span className="text-sm font-normal text-muted-foreground">of {colleges.length}</span>
//                             </p>
//                         </div>
//                     </div>
//                     <div className="text-right">
//                         <p className="text-sm text-muted-foreground">Avg Progress</p>
//                         <p className="text-xl font-bold text-primary">
//                             {colleges.find(c => c.id === myCollegeId)?.avgProgress}%
//                         </p>
//                     </div>
//                 </CardContent>
//             </Card>

//             {/* Comparison Table */}
//             <Card className="border-border/40">
//                 <CardContent className="p-4">
//                     <h2 className="text-sm font-bold flex items-center gap-2 mb-5">
//                         <BarChart3 className="h-4 w-4 text-primary" />
//                         All Colleges — Linux Course
//                     </h2>

//                     {/* Table Header */}
//                     <div className="flex items-center gap-3 px-4 py-2.5 text-[10px] uppercase tracking-wider text-muted-foreground font-semibold border-b border-border/30 mb-1">
//                         <div className="w-8 shrink-0 text-center">Rank</div>
//                         <div className="flex-1">College</div>
//                         <div className="w-16 text-center">Students</div>
//                         <div className="w-24 text-center hidden sm:block">Progress</div>
//                         <div className="w-20 text-center">Completion</div>
//                         <div className="w-16 text-center hidden md:block">Avg XP</div>
//                     </div>

//                     {/* College Rows */}
//                     <div className="space-y-0.5">
//                         {ranked.map((college, i) => {
//                             const isMe = college.id === myCollegeId
//                             const rank = i + 1

//                             return (
//                                 <div
//                                     key={college.id}
//                                     className={`flex items-center gap-3 px-4 py-3.5 rounded-lg transition-colors
//                                         ${isMe
//                                             ? 'bg-primary/5 border border-primary/20'
//                                             : 'hover:bg-muted/30'
//                                         }`}
//                                 >
//                                     {/* Rank */}
//                                     <div className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold shrink-0
//                                         ${rank === 1
//                                             ? 'bg-xp-gold/15 text-xp-gold'
//                                             : rank === 2
//                                                 ? 'bg-gray-300/20 text-gray-500'
//                                                 : rank === 3
//                                                     ? 'bg-orange-200/20 text-orange-600'
//                                                     : 'bg-muted text-muted-foreground'
//                                         }`}
//                                     >
//                                         #{rank}
//                                     </div>

//                                     {/* College Name */}
//                                     <div className="flex-1 min-w-0">
//                                         <div className="flex items-center gap-2">
//                                             <p className="text-sm font-semibold truncate">{college.name}</p>
//                                             {isMe && (
//                                                 <Badge className="bg-primary/10 text-primary border-0 text-[9px] px-1.5 py-0 h-4 gap-0.5">
//                                                     <Star className="h-2.5 w-2.5" />
//                                                     You
//                                                 </Badge>
//                                             )}
//                                         </div>
//                                         <p className="text-[11px] text-muted-foreground">{college.location}</p>
//                                     </div>

//                                     {/* Students */}
//                                     <div className="w-16 text-center">
//                                         <span className="text-sm font-mono font-semibold">{college.totalStudents}</span>
//                                     </div>

//                                     {/* Progress */}
//                                     <div className="hidden sm:flex items-center gap-2 w-24">
//                                         <Progress value={college.avgProgress} className="h-1.5 flex-1" />
//                                         <span className="text-[11px] font-mono font-semibold w-8 text-right">{college.avgProgress}%</span>
//                                     </div>

//                                     {/* Completion */}
//                                     <div className="w-20 text-center">
//                                         <span className={`text-sm font-bold ${college.completionRate >= 30 ? 'text-success' : college.completionRate >= 15 ? 'text-warning' : 'text-destructive'}`}>
//                                             {college.completionRate}%
//                                         </span>
//                                     </div>

//                                     {/* Avg XP */}
//                                     <div className="hidden md:block w-16 text-center">
//                                         <span className="text-sm font-mono">{college.avgXP}</span>
//                                     </div>
//                                 </div>
//                             )
//                         })}
//                     </div>

//                     {/* Note */}
//                     <p className="text-[10px] text-muted-foreground mt-4 text-center">
//                         Only aggregate metrics are shown. Individual student data is visible only to their college coordinator.
//                     </p>
//                 </CardContent>
//             </Card>
//         </div>
//     )
// }

// ===== ANALYTICS TAB =====

const TUTORIAL_NAMES = [
    'Installation of VirtualBox on Windows',
    'Installing Ubuntu OS in Oracle VirtualBox',
    'Ubuntu Desktop',
    'Synaptic Package Manager',
    'Basic Commands in Linux',
    'Date and Time Commands',
    'Structure of Linux Commands',
    'General Purpose Utilities',
    'File System in Linux',
    'Working with Regular Files in Linux',
    'Redirecting Streams and Pipes',
    'Working with Linux Processes',
    'The Linux Environment',
    'Basics of System Administration in Linux',
    'Linux File Ownership and Permissions',
    'Simple Filters in Linux',
    'Introduction to grep Command',
    'Mastering grep',
    'Introduction to the Stream Editor sed',
    'Text Editing using sed',
]

// Donut chart center label component
function DonutCenterLabel({ value, label }: { value: string; label: string }) {
    return (
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-2xl font-bold">{value}</span>
            <span className="text-[10px] text-muted-foreground">{label}</span>
        </div>
    )
}

function AnalyticsTab({ collegeId }: { collegeId: string }) {
    const {data,isLoading:loading}=useCoordinatorCollegeAnalytics(collegeId)

    if (loading) return <div className="p-10 text-center text-muted-foreground animate-pulse">Computing college-wide analytics...</div>
    if (!data) return <div className="p-10 text-center text-red-500">Failed to load analytics.</div>

    const {
        totalStudents: total,
        avgProgress,
        avgWatched,
        totalTutorials,
        avgXP,
        totalXP,
        statusData,
        progressData,
        tutorialCompletion,
        topPerformers,
        atRisk
    } = data

    // Attach tutorial names from frontend constants
    const tutorialCompletionWithNames = tutorialCompletion.map((t: any) => ({
        ...t,
        name: TUTORIAL_NAMES[t.number - 1] || `Tutorial ${t.number}`
    }))

    const watchRate = totalTutorials > 0 ? Math.round((avgWatched / totalTutorials) * 100) : 0

    // Custom tooltip for donut charts
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-popover border border-border rounded-lg px-3 py-2 shadow-md">
                    <p className="text-sm font-medium">{payload[0].name}</p>
                    <p className="text-xs text-muted-foreground">{payload[0].value} students ({total > 0 ? Math.round((payload[0].value / total) * 100) : 0}%)</p>
                </div>
            )
        }
        return null
    }

    return (
        <div className="space-y-5">
            {/* Row 1: Quick Stats */}
            <div className="grid grid-cols-3 gap-3">
                <Card className="border-border/40">
                    <CardContent className="p-4 text-center">
                        <Eye className="h-5 w-5 text-primary mx-auto mb-1" />
                        <p className="text-2xl font-bold">{watchRate}%</p>
                        <p className="text-[11px] text-muted-foreground">Watch Rate</p>
                        <p className="text-[10px] text-muted-foreground mt-0.5">avg {avgWatched.toFixed(1)} / {totalTutorials} per student</p>
                    </CardContent>
                </Card>
                <Card className="border-border/40">
                    <CardContent className="p-4 text-center">
                        <Zap className="h-5 w-5 text-xp-gold mx-auto mb-1" />
                        <p className="text-2xl font-bold">{avgXP}</p>
                        <p className="text-[11px] text-muted-foreground">Avg XP / Student</p>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{totalXP} total</p>
                    </CardContent>
                </Card>

            </div>

            {/* Row 2: Donut Charts */}
            <div className="grid lg:grid-cols-2 gap-5">
                {/* Status Distribution Donut */}
                <Card className="border-border/40">
                    <CardContent className="p-4">
                        <h3 className="text-sm font-bold flex items-center gap-2 mb-2">
                            <Users className="h-4 w-4 text-primary" />
                            Status Distribution
                        </h3>
                        <div className="flex items-center gap-4">
                            <div className="relative w-40 h-40 shrink-0">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={statusData.filter((d: any) => d.value > 0)}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={45}
                                            outerRadius={70}
                                            paddingAngle={3}
                                            dataKey="value"
                                            strokeWidth={0}
                                        >
                                            {statusData.filter((d: any) => d.value > 0).map((entry: any, index: number) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <RechartsTooltip content={<CustomTooltip />} />
                                    </PieChart>
                                </ResponsiveContainer>
                                <DonutCenterLabel value={String(total)} label="students" />
                            </div>
                            <div className="flex-1 space-y-2">
                                {statusData.filter((d: any) => d.value > 0).map((item: any) => (
                                    <div key={item.name} className="flex items-center gap-2">
                                        <span className="h-3 w-3 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                                        <span className="text-xs flex-1">{item.name}</span>
                                        <span className="text-sm font-bold">{item.value}</span>
                                        <span className="text-[10px] text-muted-foreground">{Math.round((item.value / total) * 100)}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Progress Distribution Donut */}
                <Card className="border-border/40">
                    <CardContent className="p-4">
                        <h3 className="text-sm font-bold flex items-center gap-2 mb-2">
                            <BarChart3 className="h-4 w-4 text-primary" />
                            Progress Distribution
                        </h3>
                        <div className="flex items-center gap-4">
                            <div className="relative w-40 h-40 shrink-0">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={progressData.filter((d: any) => d.value > 0)}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={45}
                                            outerRadius={70}
                                            paddingAngle={3}
                                            dataKey="value"
                                            strokeWidth={0}
                                        >
                                            {progressData.filter((d: any) => d.value > 0).map((entry: any, index: number) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <RechartsTooltip content={<CustomTooltip />} />
                                    </PieChart>
                                </ResponsiveContainer>
                                <DonutCenterLabel
                                    value={`${avgProgress}%`}
                                    label="avg progress"
                                />
                            </div>
                            <div className="flex-1 space-y-2">
                                {progressData.filter((d: any) => d.value > 0).map((item: any) => (
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

            {/* Row 3: Tutorial-wise Completion */}
            <Card className="border-border/40">
                <CardContent className="p-4">
                    <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
                        <CheckCircle2 className="h-4 w-4 text-success" />
                        Tutorial-wise Completion
                        <span className="text-[10px] font-normal text-muted-foreground">— where are students dropping off?</span>
                    </h3>
                    <div className="space-y-1.5">
                        {tutorialCompletionWithNames.map((t: any) => (
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
                                        {t.completedCount}/{total}
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


            {/* Row 5: Top Performers + At-Risk */}
            <div className="grid lg:grid-cols-2 gap-5">
                {/* Top Performers */}
                <Card className="border-border/40">
                    <CardContent className="p-4">
                        <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
                            <Trophy className="h-4 w-4 text-xp-gold" />
                            Top Performers
                        </h3>
                        <div className="space-y-1">
                            {topPerformers.map((student: any, i: number) => (
                                <div key={student.id} className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-muted/30 transition-colors">
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
                                    </div>
                                    <div className="flex items-center gap-3 shrink-0">
                                        <div className="flex items-center gap-1 w-14 justify-end">
                                            <Zap className="h-3 w-3 text-xp-gold" />
                                            <span className="text-xs font-bold tabular-nums">{student.xp}</span>
                                        </div>
                                        <Progress value={student.progress} className="h-1.5 w-14" />
                                        <span className="text-[11px] font-mono text-muted-foreground w-9 text-right tabular-nums">{student.progress}%</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* At-Risk Alerts */}
                <Card className="border-border/40">
                    <CardContent className="p-4">
                        <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
                            <AlertTriangle className="h-4 w-4 text-warning" />
                            At-Risk Students
                            {atRisk.length > 0 && (
                                <Badge className="bg-destructive/10 text-destructive border-0 text-[10px] px-1.5 py-0 h-4">
                                    {atRisk.length} need attention
                                </Badge>
                            )}
                        </h3>
                        {atRisk.length === 0 ? (
                            <div className="text-center py-6">
                                <CheckCircle2 className="h-8 w-8 text-success mx-auto mb-2" />
                                <p className="text-sm font-medium">All students on track! 🎉</p>
                                <p className="text-xs text-muted-foreground">No at-risk students right now</p>
                            </div>
                        ) : (
                            <div className="space-y-1.5">
                                {atRisk.map((student: any) => (
                                    <div key={student.id} className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-destructive/5 border border-destructive/10">
                                        <Avatar className="h-7 w-7">
                                            <AvatarFallback className="text-[9px] font-semibold bg-destructive/10 text-destructive">
                                                {student.initials}
                                            </AvatarFallback>
                                        </Avatar>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate">{student.name}</p>
                                            <p className="text-[10px] text-muted-foreground">
                                                Watched {student.tutorialsWatched} · Done {student.tutorialsCompleted}/{student.totalTutorials} • {student.progress}%
                                            </p>
                                        </div>
                                        <div className="shrink-0 text-right">
                                            <div className="flex items-center gap-1 text-destructive">
                                                <Clock className="h-3 w-3" />
                                                <span className="text-[10px] font-medium">{student.lastActive}</span>
                                            </div>
                                            <Badge className={`text-[9px] px-1.5 py-0 h-4 border-0 mt-0.5 ${student.status === 'at_risk' ? 'bg-warning/10 text-warning' :
                                                student.status === 'not_started' ? 'bg-muted text-muted-foreground' :
                                                    'bg-destructive/10 text-destructive'
                                                }`}>
                                                {student.status === 'at_risk' ? 'At Risk' :
                                                    student.status === 'not_started' ? 'Not Started' : 'Inactive'}
                                            </Badge>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}


// ===== COORDINATOR FEEDBACK TAB =====

function CoordinatorFeedbackTab({ collegeId }: { collegeId: string }) {
    const feedbackHook = (filters: { tutorialId: string; stepType: string; reason: string }) =>
        useCoordinatorFeedbackSummary(collegeId, filters)

    return <FeedbackPanel useFeedbackData={feedbackHook} />
}


// ===== MAIN COMPONENT =====

export default function CoordinatorDashboard() {
    const [activeTab, setActiveTab] = useState<Tab>('students')
    const [sortBy, setSortBy] = useState<SortBy>('progress')
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
    const [searchQuery, setSearchQuery] = useState('')
    const [page, setPage] = useState(1)
    const user = useUserStore(state => state.user)
    const MY_COLLEGE_ID = user?.collegeId || 'iitb'

    const {data:colleges=[],isLoading:isLoadingColleges}=useCoordinatorColleges()

    const {data:myCollegeDetails,isLoading:isLoadingDetails}=useCoordinatorCollegeDetails(
        MY_COLLEGE_ID,
        page,
        sortBy,
        statusFilter,
        searchQuery
    )

    const isLoading = isLoadingColleges||isLoadingDetails

    const myCollege = colleges.find((c: CollegeSummary) => c.id === MY_COLLEGE_ID)

    const tabs = [
        { id: 'students' as const, label: 'My Students', icon: Users },
        { id: 'analytics' as const, label: 'Analytics', icon: Activity },
        { id: 'feedback' as const, label: 'Feedback', icon: MessageCircleQuestion },
        // { id: 'compare' as const, label: 'Compare Colleges', icon: BarChart3 },
    ]

    if (isLoading) {
        return (
            <div className="max-w-5xl mx-auto p-6 text-center text-muted-foreground">
                Loading coordinator dashboard...
            </div>
        )
    }

    return (
        <div className="max-w-5xl mx-auto space-y-5">
            {/* Header */}
            <div>
                <div className="flex items-center gap-2 mb-1">
                    <GraduationCap className="h-6 w-6 text-primary" />
                    <h1 className="text-xl sm:text-2xl font-bold">Coordinator Dashboard</h1>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Terminal className="h-4 w-4" />
                    <span>{myCollege?.name} • Linux Course • No. of students registered: {myCollege?.totalCourseStudents}</span>
                </div>
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
            {activeTab === 'students' && myCollege && (
                <MyStudentsTab
                    college={myCollege}
                    details={myCollegeDetails}
                    sortBy={sortBy}
                    setSortBy={(s) => { setSortBy(s); setPage(1) }}
                    statusFilter={statusFilter}
                    setStatusFilter={(s) => { setStatusFilter(s); setPage(1) }}
                    searchQuery={searchQuery}
                    setSearchQuery={(s) => { setSearchQuery(s); setPage(1) }}
                    page={page}
                    setPage={setPage}
                />
            )}

            {activeTab === 'analytics' && myCollege && (
                <AnalyticsTab collegeId={myCollege.id} />
            )}

            {activeTab === 'feedback' && myCollege && (
                <CoordinatorFeedbackTab collegeId={myCollege.id} />
            )}

            {/* {activeTab === 'compare' && (
                <CompareCollegesTab
                    colleges={colleges}
                    myCollegeId={MY_COLLEGE_ID}
                />
            )} */}
        </div>
    )
}
