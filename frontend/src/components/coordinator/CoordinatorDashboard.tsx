import { useState, useEffect } from 'react'
import {
    Users, GraduationCap, TrendingUp, AlertTriangle,
    CheckCircle2, Terminal, Eye,
    Search, Filter, Trophy, BarChart3, 
    // Star,
    Clock, Zap, Activity
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import api from '@/lib/axios'
import { useUserStore } from '@/store/userStore'

// ===== TYPES =====

interface CollegeSummary {
    id: string
    name: string
    location: string
    coordinatorName: string
    course: string
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

type Tab = 'students' | 'analytics' | 'compare'
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
            {/* Metric Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <MetricCard
                    icon={Users}
                    label="Total Students"
                    value={college.totalStudents}
                    subtext={`${college.activeStudents} active`}
                    color="bg-primary/10 text-primary"
                />
                <MetricCard
                    icon={TrendingUp}
                    label="Avg Progress"
                    value={`${college.avgProgress}%`}
                    color="bg-secondary/10 text-secondary"
                />
                <MetricCard
                    icon={CheckCircle2}
                    label="Completion Rate"
                    value={`${college.completionRate}%`}
                    subtext={`${college.completedStudents} completed`}
                    color="bg-success/10 text-success"
                />
                <MetricCard
                    icon={AlertTriangle}
                    label="At Risk"
                    value={college.atRiskStudents}
                    subtext={`${college.inactiveStudents} inactive`}
                    color="bg-warning/10 text-warning"
                />
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
                            <span className="flex items-center gap-0.5"><Eye className="h-3 w-3" /> Watched</span>
                            <span className="flex items-center gap-0.5"><CheckCircle2 className="h-3 w-3" /> Completed</span>
                        </div>

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
                        <div className="flex items-center justify-between pt-4 border-t border-border/30">
                            <p className="text-xs text-muted-foreground">
                                Page {details.pagination.currentPage} of {details.pagination.totalPages} · {details.pagination.totalRecords} students
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
                                    disabled={page >= details.pagination.totalPages}
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

function AnalyticsTab({ details }: { details: CollegeDetails | null }) {
    const students = details?.students || []
    const total = students.length

    // ── Status Distribution (Donut) ──
    const statusData = [
        { name: 'Completed', value: students.filter(s => s.status === 'completed').length, color: 'hsl(142, 76%, 36%)' },
        { name: 'Active', value: students.filter(s => s.status === 'active').length, color: 'hsl(221, 83%, 53%)' },
        { name: 'At Risk', value: students.filter(s => s.status === 'at_risk').length, color: 'hsl(38, 92%, 50%)' },
        { name: 'Inactive', value: students.filter(s => s.status === 'inactive' || s.status === 'not_started').length, color: 'hsl(0, 72%, 51%)' },
    ].filter(d => d.value > 0)

    // ── Progress Distribution (Donut) ──
    const progressData = [
        { name: '0%', value: students.filter(s => s.progress === 0).length, color: 'hsl(0, 72%, 70%)' },
        { name: '1–25%', value: students.filter(s => s.progress >= 1 && s.progress <= 25).length, color: 'hsl(25, 95%, 60%)' },
        { name: '26–50%', value: students.filter(s => s.progress >= 26 && s.progress <= 50).length, color: 'hsl(38, 92%, 55%)' },
        { name: '51–75%', value: students.filter(s => s.progress >= 51 && s.progress <= 75).length, color: 'hsl(221, 83%, 60%)' },
        { name: '76–99%', value: students.filter(s => s.progress >= 76 && s.progress <= 99).length, color: 'hsl(142, 60%, 50%)' },
        { name: '100%', value: students.filter(s => s.progress === 100).length, color: 'hsl(142, 76%, 36%)' },
    ].filter(d => d.value > 0)

    // ── Tutorial-wise Completion ──
    const tutorialCompletion = TUTORIAL_NAMES.map((name, i) => {
        const completedCount = students.filter(s => s.tutorialsCompleted > i).length
        const rate = total > 0 ? Math.round((completedCount / total) * 100) : 0
        return { name, number: i + 1, completedCount, rate }
    })

    // ── Top Performers ──
    const topPerformers = [...students].sort((a, b) => b.xp - a.xp).slice(0, 5)

    // ── At-Risk Students ──
    const atRisk = students.filter(s => s.status === 'at_risk' || s.status === 'inactive' || s.status === 'not_started')
        .sort((a, b) => a.progress - b.progress)

    // ── Watch Rate ──
    const avgWatched = total > 0 ? students.reduce((sum, s) => sum + (s.tutorialsWatched || 0), 0) / total : 0
    const totalTutorials = students.length > 0 ? students[0].totalTutorials : 20
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
                        <p className="text-2xl font-bold">{total > 0 ? Math.round(students.reduce((a, s) => a + s.xp, 0) / total) : 0}</p>
                        <p className="text-[11px] text-muted-foreground">Avg XP / Student</p>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{students.reduce((a, s) => a + s.xp, 0)} total</p>
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
                                            data={statusData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={45}
                                            outerRadius={70}
                                            paddingAngle={3}
                                            dataKey="value"
                                            strokeWidth={0}
                                        >
                                            {statusData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip content={<CustomTooltip />} />
                                    </PieChart>
                                </ResponsiveContainer>
                                <DonutCenterLabel value={String(total)} label="students" />
                            </div>
                            <div className="flex-1 space-y-2">
                                {statusData.map(item => (
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
                                            data={progressData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={45}
                                            outerRadius={70}
                                            paddingAngle={3}
                                            dataKey="value"
                                            strokeWidth={0}
                                        >
                                            {progressData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip content={<CustomTooltip />} />
                                    </PieChart>
                                </ResponsiveContainer>
                                <DonutCenterLabel
                                    value={`${total > 0 ? Math.round(students.reduce((a, s) => a + s.progress, 0) / total) : 0}%`}
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

            {/* Row 3: Tutorial-wise Completion */}
            <Card className="border-border/40">
                <CardContent className="p-4">
                    <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
                        <CheckCircle2 className="h-4 w-4 text-success" />
                        Tutorial-wise Completion
                        <span className="text-[10px] font-normal text-muted-foreground">— where are students dropping off?</span>
                    </h3>
                    <div className="space-y-1.5">
                        {tutorialCompletion.map(t => (
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
                            {topPerformers.map((student, i) => (
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
                                {atRisk.map(student => (
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


// ===== MAIN COMPONENT =====

export default function CoordinatorDashboard() {
    const [activeTab, setActiveTab] = useState<Tab>('students')
    const [colleges, setColleges] = useState<CollegeSummary[]>([])
    const [myCollegeDetails, setMyCollegeDetails] = useState<CollegeDetails | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [sortBy, setSortBy] = useState<SortBy>('progress')
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
    const [searchQuery, setSearchQuery] = useState('')
    const [page, setPage] = useState(1)
    const user = useUserStore(state => state.user) 
    const MY_COLLEGE_ID = user?.collegeId || 'iitb'



    // Fetch all colleges + my college's student details
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [collegesRes, detailsRes] = await Promise.all([
                    api.get('/api/coordinator/colleges'),
                    api.get(`/api/coordinator/colleges/${MY_COLLEGE_ID}?page=${page}&limit=10&sort=${sortBy}&status=${statusFilter}&search=${searchQuery}`),
                ])
                setColleges(collegesRes.data)
                setMyCollegeDetails(detailsRes.data)
                setIsLoading(false)
            } catch (error) {
                console.error('Failed to fetch coordinator data:', error)
                setIsLoading(false)
            }
        }
        fetchData()
    }, [page, sortBy, statusFilter, searchQuery])

    const myCollege = colleges.find(c => c.id === MY_COLLEGE_ID)

    const tabs = [
        { id: 'students' as const, label: 'My Students', icon: Users },
        { id: 'analytics' as const, label: 'Analytics', icon: Activity },
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
                    <span>{myCollege?.name} • Linux Course • {myCollege?.totalStudents} students</span>
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

            {activeTab === 'analytics' && (
                <AnalyticsTab details={myCollegeDetails} />
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
