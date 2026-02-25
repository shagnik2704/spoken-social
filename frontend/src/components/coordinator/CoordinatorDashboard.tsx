import { useState, useEffect } from 'react'
import {
    Users, GraduationCap, TrendingUp, AlertTriangle,
    CheckCircle2, Flame, Terminal,
    Search, Filter, Trophy, BarChart3, Star
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import api from '@/lib/axios'

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
    tutorialsCompleted: number
    totalTutorials: number
    progress: number
    xp: number
    streak: number
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
}

type Tab = 'students' | 'compare'
type SortBy = 'name' | 'progress' | 'xp' | 'streak'
type StatusFilter = 'all' | 'active' | 'completed' | 'at_risk' | 'inactive'

// The coordinator's own college — later this comes from auth
const MY_COLLEGE_ID = 'vjti'

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

            <div className="hidden md:block w-16 text-center">
                <span className="text-sm font-mono">{student.tutorialsCompleted}/{student.totalTutorials}</span>
            </div>

            <div className="hidden md:flex items-center gap-1 w-12 justify-center">
                {student.streak > 0 ? (
                    <>
                        <Flame className="h-3 w-3 text-warning" />
                        <span className="text-xs font-mono">{student.streak}</span>
                    </>
                ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                )}
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

function MyStudentsTab({ college, details, sortBy, setSortBy, statusFilter, setStatusFilter, searchQuery, setSearchQuery }: {
    college: CollegeSummary
    details: CollegeDetails | null
    sortBy: SortBy
    setSortBy: (s: SortBy) => void
    statusFilter: StatusFilter
    setStatusFilter: (s: StatusFilter) => void
    searchQuery: string
    setSearchQuery: (s: string) => void
}) {
    const filteredStudents = (details?.students || [])
        .filter(s => statusFilter === 'all' || s.status === statusFilter)
        .filter(s =>
            searchQuery === '' ||
            s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            s.rollNo.toLowerCase().includes(searchQuery.toLowerCase())
        )
        .sort((a, b) => {
            switch (sortBy) {
                case 'name': return a.name.localeCompare(b.name)
                case 'progress': return b.progress - a.progress
                case 'xp': return b.xp - a.xp
                case 'streak': return b.streak - a.streak
                default: return 0
            }
        })

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
                            { id: 'streak', label: 'Streak' },
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
                        <div className="hidden md:block w-16 text-center">Done</div>
                        <div className="hidden md:block w-12 text-center">Streak</div>
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
                </CardContent>
            </Card>
        </div>
    )
}

// ===== COMPARE COLLEGES TAB =====

function CompareCollegesTab({ colleges, myCollegeId }: { colleges: CollegeSummary[]; myCollegeId: string }) {
    const ranked = [...colleges].sort((a, b) => b.avgProgress - a.avgProgress)
    const myRank = ranked.findIndex(c => c.id === myCollegeId) + 1

    return (
        <div className="space-y-5">
            {/* My Rank Card */}
            <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-transparent">
                <CardContent className="p-5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                            <Trophy className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Your College Rank</p>
                            <p className="text-2xl font-bold">
                                #{myRank} <span className="text-sm font-normal text-muted-foreground">of {colleges.length}</span>
                            </p>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-sm text-muted-foreground">Avg Progress</p>
                        <p className="text-xl font-bold text-primary">
                            {colleges.find(c => c.id === myCollegeId)?.avgProgress}%
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Comparison Table */}
            <Card className="border-border/40">
                <CardContent className="p-4">
                    <h2 className="text-sm font-bold flex items-center gap-2 mb-5">
                        <BarChart3 className="h-4 w-4 text-primary" />
                        All Colleges — Linux Course
                    </h2>

                    {/* Table Header */}
                    <div className="flex items-center gap-3 px-4 py-2.5 text-[10px] uppercase tracking-wider text-muted-foreground font-semibold border-b border-border/30 mb-1">
                        <div className="w-8 shrink-0 text-center">Rank</div>
                        <div className="flex-1">College</div>
                        <div className="w-16 text-center">Students</div>
                        <div className="w-24 text-center hidden sm:block">Progress</div>
                        <div className="w-20 text-center">Completion</div>
                        <div className="w-16 text-center hidden md:block">Avg XP</div>
                    </div>

                    {/* College Rows */}
                    <div className="space-y-0.5">
                        {ranked.map((college, i) => {
                            const isMe = college.id === myCollegeId
                            const rank = i + 1

                            return (
                                <div
                                    key={college.id}
                                    className={`flex items-center gap-3 px-4 py-3.5 rounded-lg transition-colors
                                        ${isMe
                                            ? 'bg-primary/5 border border-primary/20'
                                            : 'hover:bg-muted/30'
                                        }`}
                                >
                                    {/* Rank */}
                                    <div className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold shrink-0
                                        ${rank === 1
                                            ? 'bg-xp-gold/15 text-xp-gold'
                                            : rank === 2
                                                ? 'bg-gray-300/20 text-gray-500'
                                                : rank === 3
                                                    ? 'bg-orange-200/20 text-orange-600'
                                                    : 'bg-muted text-muted-foreground'
                                        }`}
                                    >
                                        #{rank}
                                    </div>

                                    {/* College Name */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <p className="text-sm font-semibold truncate">{college.name}</p>
                                            {isMe && (
                                                <Badge className="bg-primary/10 text-primary border-0 text-[9px] px-1.5 py-0 h-4 gap-0.5">
                                                    <Star className="h-2.5 w-2.5" />
                                                    You
                                                </Badge>
                                            )}
                                        </div>
                                        <p className="text-[11px] text-muted-foreground">{college.location}</p>
                                    </div>

                                    {/* Students */}
                                    <div className="w-16 text-center">
                                        <span className="text-sm font-mono font-semibold">{college.totalStudents}</span>
                                    </div>

                                    {/* Progress */}
                                    <div className="hidden sm:flex items-center gap-2 w-24">
                                        <Progress value={college.avgProgress} className="h-1.5 flex-1" />
                                        <span className="text-[11px] font-mono font-semibold w-8 text-right">{college.avgProgress}%</span>
                                    </div>

                                    {/* Completion */}
                                    <div className="w-20 text-center">
                                        <span className={`text-sm font-bold ${college.completionRate >= 30 ? 'text-success' : college.completionRate >= 15 ? 'text-warning' : 'text-destructive'}`}>
                                            {college.completionRate}%
                                        </span>
                                    </div>

                                    {/* Avg XP */}
                                    <div className="hidden md:block w-16 text-center">
                                        <span className="text-sm font-mono">{college.avgXP}</span>
                                    </div>
                                </div>
                            )
                        })}
                    </div>

                    {/* Note */}
                    <p className="text-[10px] text-muted-foreground mt-4 text-center">
                        Only aggregate metrics are shown. Individual student data is visible only to their college coordinator.
                    </p>
                </CardContent>
            </Card>
        </div>
    )
}

// ===== MAIN COMPONENT =====

export function CoordinatorDashboard() {
    const [activeTab, setActiveTab] = useState<Tab>('students')
    const [colleges, setColleges] = useState<CollegeSummary[]>([])
    const [myCollegeDetails, setMyCollegeDetails] = useState<CollegeDetails | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [sortBy, setSortBy] = useState<SortBy>('progress')
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
    const [searchQuery, setSearchQuery] = useState('')

    // Fetch all colleges + my college's student details
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [collegesRes, detailsRes] = await Promise.all([
                    api.get('/api/coordinator/colleges'),
                    api.get(`/api/coordinator/colleges/${MY_COLLEGE_ID}`),
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
    }, [])

    const myCollege = colleges.find(c => c.id === MY_COLLEGE_ID)

    const tabs = [
        { id: 'students' as const, label: 'My Students', icon: Users },
        { id: 'compare' as const, label: 'Compare Colleges', icon: BarChart3 },
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
                    setSortBy={setSortBy}
                    statusFilter={statusFilter}
                    setStatusFilter={setStatusFilter}
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                />
            )}

            {activeTab === 'compare' && (
                <CompareCollegesTab
                    colleges={colleges}
                    myCollegeId={MY_COLLEGE_ID}
                />
            )}
        </div>
    )
}
