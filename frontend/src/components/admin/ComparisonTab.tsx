import { useState, useMemo, useEffect } from 'react'
import {
    BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer
} from 'recharts'
import {
    Building2, Users, CheckCircle2, Zap,
    MapPin, Filter, Layers, Check, Sparkles, TrendingUp
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { useComparisonMetrics } from '@/hooks/queries/useAdminQueries'

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

interface MetricValues {
    colleges: number
    students: number
    progress: number
    avgXP: number
}

interface BatchData {
    batchId: string
    batchName: string
    metrics: MetricValues
}

interface CourseData {
    courseId: string
    courseName: string
    batches: BatchData[]
}

interface ProgrammeData {
    id: string
    name: string
    color: string
    metrics: MetricValues
    courses: CourseData[]
}

interface ComparisonMetricsResponse {
    programmes: ProgrammeData[]
}

// Color schemes matching the database setup
const PROGRAMME_COLORS: Record<string, string> = {
    fdp: 'hsl(262, 83%, 58%)',        // Violet
    swayam_plus: 'hsl(221, 83%, 53%)', // Blue
    ilw: 'hsl(142, 76%, 36%)'          // Emerald
}

const COURSE_COLORS: Record<string, string[]> = {
    fdp: [
        'hsl(262, 83%, 65%)', // Light Violet
        'hsl(282, 83%, 50%)', // Magenta-Violet
        'hsl(242, 83%, 45%)'  // Dark Violet/Blue
    ],
    swayam_plus: [
        'hsl(221, 83%, 60%)', // Light Blue
        'hsl(201, 83%, 50%)', // Cyan-Blue
        'hsl(231, 83%, 40%)'  // Indigo
    ],
    ilw: [
        'hsl(142, 76%, 45%)', // Light Emerald
        'hsl(162, 76%, 35%)', // Teal-Green
        'hsl(122, 76%, 25%)'  // Dark Forest Green
    ]
}

type CompareMode = 'programmes' | 'courses_same' | 'courses_diff'
type ParameterType = 'colleges' | 'students' | 'progress' | 'avgXP'

export function ComparisonTab({ colleges }: { colleges: CollegeSummary[] }) {
    // 1. Core filters state
    const [compareMode, setCompareMode] = useState<CompareMode>('programmes')
    const [selectedState, setSelectedState] = useState<string>('all')
    const [selectedParameter, setSelectedParameter] = useState<ParameterType>('students')
    const [forceMock, setForceMock] = useState<boolean>(false)

    // 2. Fetch data from backend API route
    const { data, isLoading } = useComparisonMetrics(selectedState, forceMock)
    const metricsData = data as ComparisonMetricsResponse | undefined

    // 3. Selection list states
    const [selectedProgrammes, setSelectedProgrammes] = useState<string[]>([])
    const [selectedSameProg, setSelectedSameProg] = useState<string>('')
    const [selectedSameCourses, setSelectedSameCourses] = useState<string[]>([]) // CourseId + "_" + BatchId
    const [selectedDiffCourses, setSelectedDiffCourses] = useState<string[]>([]) // ProgId + "_" + CourseId + "_" + BatchId

    // Extract unique states dynamically from current college locations
    const states = useMemo(() => {
        const set = new Set<string>()
        colleges.forEach(c => {
            if (c.location) {
                const parts = c.location.split(',')
                let stateName = parts[parts.length - 1].trim()
                if (stateName === 'India' && parts.length > 1) {
                    stateName = parts[parts.length - 2].trim()
                }
                if (stateName && stateName !== 'India') set.add(stateName)
            }
        })
        return Array.from(set).sort()
    }, [colleges])

    // Reset and initialize selections when metricsData is loaded or compareMode changes
    useEffect(() => {
        if (!metricsData?.programmes) return

        const progs = metricsData.programmes.map(p => p.id)
        setSelectedProgrammes(progs)

        if (progs.length > 0) {
            // Pick first program as default for "Same Program" compare
            const defaultProg = progs.find(p => p === 'swayam_plus') || progs[0]
            setSelectedSameProg(defaultProg)

            const targetProg = metricsData.programmes.find(p => p.id === defaultProg)
            if (targetProg) {
                const sameKeys: string[] = []
                targetProg.courses.forEach(c => {
                    c.batches.forEach(b => {
                        sameKeys.push(`${c.courseId}_${b.batchId}`)
                    })
                })
                setSelectedSameCourses(sameKeys)
            }
        }

        // Initialize different courses selection (All available course batches)
        const diffKeys: string[] = []
        metricsData.programmes.forEach(p => {
            p.courses.forEach(c => {
                c.batches.forEach(b => {
                    diffKeys.push(`${p.id}_${c.courseId}_${b.batchId}`)
                })
            })
        })
        setSelectedDiffCourses(diffKeys)
    }, [metricsData, compareMode])

    // Update Same-Program courses when selected program changes
    useEffect(() => {
        if (!metricsData?.programmes || !selectedSameProg) return
        const targetProg = metricsData.programmes.find(p => p.id === selectedSameProg)
        if (targetProg) {
            const sameKeys: string[] = []
            targetProg.courses.forEach(c => {
                c.batches.forEach(b => {
                    sameKeys.push(`${c.courseId}_${b.batchId}`)
                })
            })
            setSelectedSameCourses(sameKeys)
        }
    }, [selectedSameProg, metricsData])

    // 4. Map HSL Colors dynamically to specific bars
    const getColorForCourse = (progId: string, courseIdx: number) => {
        const pColors = COURSE_COLORS[progId] || COURSE_COLORS['fdp']
        return pColors[courseIdx % pColors.length]
    }

    // 5. Build chart series based on selected mode
    const chartData = useMemo(() => {
        if (!metricsData?.programmes) return []

        if (compareMode === 'programmes') {
            return metricsData.programmes
                .filter(p => selectedProgrammes.includes(p.id))
                .map(p => ({
                    name: p.name,
                    value: p.metrics[selectedParameter],
                    color: PROGRAMME_COLORS[p.id] || p.color || 'hsl(200, 80%, 50%)',
                    // Additional info for Custom Tooltip
                    colleges: p.metrics.colleges,
                    students: p.metrics.students,
                    progress: p.metrics.progress,
                    avgXP: p.metrics.avgXP,
                    type: 'programme',
                    programmeName: p.name
                }))
        }

        if (compareMode === 'courses_same') {
            const targetProg = metricsData.programmes.find(p => p.id === selectedSameProg)
            if (!targetProg) return []

            const series: any[] = []
            let colorIdx = 0
            targetProg.courses.forEach(c => {
                c.batches.forEach(b => {
                    const key = `${c.courseId}_${b.batchId}`
                    if (selectedSameCourses.includes(key)) {
                        series.push({
                            name: `${c.courseName} (${b.batchName})`,
                            value: b.metrics[selectedParameter],
                            color: getColorForCourse(targetProg.id, colorIdx),
                            colleges: b.metrics.colleges,
                            students: b.metrics.students,
                            progress: b.metrics.progress,
                            avgXP: b.metrics.avgXP,
                            type: 'course',
                            programmeName: targetProg.name
                        })
                    }
                    colorIdx++
                })
            })
            return series
        }

        if (compareMode === 'courses_diff') {
            const series: any[] = []
            metricsData.programmes.forEach(p => {
                let colorIdx = 0
                p.courses.forEach(c => {
                    c.batches.forEach(b => {
                        const key = `${p.id}_${c.courseId}_${b.batchId}`
                        if (selectedDiffCourses.includes(key)) {
                            series.push({
                                name: `[${p.name}] ${c.courseName} (${b.batchName})`,
                                value: b.metrics[selectedParameter],
                                color: getColorForCourse(p.id, colorIdx),
                                colleges: b.metrics.colleges,
                                students: b.metrics.students,
                                progress: b.metrics.progress,
                                avgXP: b.metrics.avgXP,
                                type: 'course_diff',
                                programmeName: p.name
                            })
                        }
                        colorIdx++
                    })
                })
            })
            return series
        }

        return []
    }, [metricsData, compareMode, selectedProgrammes, selectedSameProg, selectedSameCourses, selectedDiffCourses, selectedParameter])

    // Labels for the parameters
    const getParamLabel = (param: ParameterType) => {
        switch (param) {
            case 'colleges': return 'Colleges Enrolled'
            case 'students': return 'Total Students'
            case 'progress': return 'Average Progress (%)'
            case 'avgXP': return 'Average XP Gained'
        }
    }


    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload
            return (
                <div className="bg-popover border border-border/80 rounded-xl p-4 shadow-xl backdrop-blur-md min-w-[200px] text-xs">
                    <p className="font-bold text-sm mb-1 text-foreground border-b border-border/50 pb-1">{data.name}</p>
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-3">{data.programmeName} Programme</p>
                    <div className="space-y-2">
                        <div className="flex items-center justify-between gap-4">
                            <span className="text-muted-foreground flex items-center gap-1.5"><Building2 className="h-3.5 w-3.5 text-primary/70" /> Colleges</span>
                            <span className="font-bold font-mono text-right">{data.colleges}</span>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                            <span className="text-muted-foreground flex items-center gap-1.5"><Users className="h-3.5 w-3.5 text-primary/70" /> Students</span>
                            <span className="font-bold font-mono text-right">{data.students}</span>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                            <span className="text-muted-foreground flex items-center gap-1.5"><CheckCircle2 className="h-3.5 w-3.5 text-success/75" /> Progress</span>
                            <span className="font-bold font-mono text-success text-right">{data.progress}%</span>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                            <span className="text-muted-foreground flex items-center gap-1.5"><Zap className="h-3.5 w-3.5 text-xp-gold" /> Avg XP</span>
                            <span className="font-bold font-mono text-xp-gold text-right">{data.avgXP}</span>
                        </div>
                    </div>
                </div>
            )
        }
        return null
    }

    if (isLoading) {
        return (
            <div className="max-w-6xl mx-auto p-12 text-center text-muted-foreground bg-background/50 rounded-2xl border border-border/30">
                <TrendingUp className="h-8 w-8 text-primary animate-pulse mx-auto mb-2" />
                Loading comparison dashboard...
            </div>
        )
    }

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            {/* Header Control Panel */}
            <div className="flex flex-col lg:flex-row justify-between items-stretch gap-4 bg-muted/10 p-4 rounded-2xl border border-border/30">
                <div className="space-y-1">
                    <h2 className="text-sm font-bold flex items-center gap-2 text-foreground">
                        <Layers className="h-4 w-4 text-primary" />
                        Course & Programme Comparison
                    </h2>
                    <p className="text-[11px] text-muted-foreground">Compare enrollment count, learning progress, and XP metrics across courses, batches, and programs</p>
                </div>

                <div className="flex items-center gap-2.5 flex-wrap">
                    {/* State Filter Dropdown */}
                    <div className="relative">
                        <MapPin className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
                        <select
                            value={selectedState}
                            onChange={e => setSelectedState(e.target.value)}
                            className="pl-8 pr-8 py-1.5 text-xs rounded-full border border-border bg-muted/30 focus:outline-none focus:ring-1 focus:ring-primary/30 appearance-none cursor-pointer w-40 text-foreground font-semibold"
                        >
                            <option value="all">All States</option>
                            {states.map(state => (
                                <option key={state} value={state}>{state}</option>
                            ))}
                        </select>
                    </div>

                    {/* Parameter Selector Dropdown */}
                    <div className="relative">
                        <Filter className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
                        <select
                            value={selectedParameter}
                            onChange={e => setSelectedParameter(e.target.value as ParameterType)}
                            className="pl-8 pr-8 py-1.5 text-xs rounded-full border border-border bg-muted/30 focus:outline-none focus:ring-1 focus:ring-primary/30 appearance-none cursor-pointer w-52 text-foreground font-semibold"
                        >
                            <option value="colleges">Colleges Count</option>
                            <option value="students">Learners Enrolled</option>
                            <option value="progress">Average Progress (%)</option>
                            <option value="avgXP">Average XP Gained</option>
                        </select>
                    </div>

                    {/* Toggle between Live and Mock Mode */}
                    <button
                        onClick={() => setForceMock(!forceMock)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-full font-semibold border transition-all ${
                            forceMock 
                                ? 'bg-primary/10 border-primary text-primary' 
                                : 'bg-muted/30 border-border text-muted-foreground hover:text-foreground'
                        }`}
                    >
                        <Sparkles className="h-3.5 w-3.5" />
                        Demo Mode {forceMock && '(Active)'}
                    </button>
                </div>
            </div>

            {/* Mode selection buttons */}
            <div className="grid grid-cols-3 gap-2 bg-muted/20 p-1 rounded-xl border border-border/30">
                {(['programmes', 'courses_same', 'courses_diff'] as const).map(mode => {
                    const isActive = compareMode === mode
                    let label = ''
                    if (mode === 'programmes') label = 'Between Programmes'
                    if (mode === 'courses_same') label = 'Courses of Same Programme'
                    if (mode === 'courses_diff') label = 'Courses of Different Programmes'

                    return (
                        <button
                            key={mode}
                            onClick={() => setCompareMode(mode)}
                            className={`py-2 text-xs font-semibold rounded-lg transition-all text-center ${
                                isActive 
                                    ? 'bg-card text-foreground shadow-sm' 
                                    : 'text-muted-foreground hover:text-foreground'
                            }`}
                        >
                            {label}
                        </button>
                    )
                })}
            </div>

            {/* Main Content Grid: Graph + Item Toggles */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Left Graph Panel */}
                <Card className="lg:col-span-3 border-border/40 bg-card/40 backdrop-blur-md">
                    <CardContent className="p-5 space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-sm font-bold flex items-center gap-2 text-foreground">
                                <TrendingUp className="h-4 w-4 text-primary" />
                                {getParamLabel(selectedParameter)} Comparison Chart
                            </h3>
                            <span className="text-[10px] text-muted-foreground uppercase font-mono tracking-wider font-semibold">
                                {chartData.length} items rendered
                            </span>
                        </div>

                        {chartData.length === 0 ? (
                            <div className="h-[340px] flex items-center justify-center text-sm text-muted-foreground border border-dashed border-border/60 rounded-xl">
                                Select at least one item from the side panel to view the graph comparison
                            </div>
                        ) : (
                            <div className="h-[340px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={chartData} margin={{ top: 15, right: 10, left: -20, bottom: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.25} />
                                        <XAxis 
                                            dataKey="name" 
                                            tick={{ fontSize: 9, fill: 'hsl(var(--muted-foreground))' }}
                                            tickLine={false}
                                            axisLine={{ stroke: 'hsl(var(--border))' }}
                                            interval={0}
                                            tickFormatter={(val) => val.length > 25 ? `${val.slice(0, 22)}...` : val}
                                        />
                                        <YAxis 
                                            tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                                            tickLine={false}
                                            axisLine={{ stroke: 'hsl(var(--border))' }}
                                            allowDecimals={false}
                                        />
                                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))', opacity: 0.15 }} />
                                        <Bar 
                                            dataKey="value" 
                                            radius={[6, 6, 0, 0]} 
                                            animationDuration={600} 
                                            animationEasing="ease-out"
                                        >
                                            {chartData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Right Item Selection Toggles */}
                <Card className="border-border/40 bg-card/20">
                    <CardContent className="p-4 space-y-4">
                        <div className="border-b border-border/50 pb-2">
                            <h4 className="text-xs font-bold text-foreground">Select to Include</h4>
                            <p className="text-[10px] text-muted-foreground">Select options to dynamically update graph bars</p>
                        </div>

                        {/* RENDER DYNAMIC FILTER OPTIONS BASED ON COMPARISON MODE */}
                        {compareMode === 'programmes' && metricsData?.programmes && (
                            <div className="space-y-2">
                                <div className="flex items-center justify-between text-[10px] text-muted-foreground font-semibold px-1">
                                    <button 
                                        onClick={() => setSelectedProgrammes(metricsData.programmes.map(p => p.id))}
                                        className="hover:text-primary transition-colors hover:underline"
                                    >
                                        Select All
                                    </button>
                                    <button 
                                        onClick={() => setSelectedProgrammes([])}
                                        className="hover:text-destructive transition-colors hover:underline"
                                    >
                                        Clear All
                                    </button>
                                </div>
                                <div className="space-y-1 max-h-[260px] overflow-y-auto pr-1">
                                    {metricsData.programmes.map(p => {
                                        const isChecked = selectedProgrammes.includes(p.id)
                                        return (
                                            <button
                                                key={p.id}
                                                onClick={() => {
                                                    setSelectedProgrammes(prev => 
                                                        prev.includes(p.id) ? prev.filter(x => x !== p.id) : [...prev, p.id]
                                                    )
                                                }}
                                                className="w-full flex items-center gap-2.5 px-2.5 py-2 hover:bg-muted/30 rounded-lg text-left text-xs transition-colors"
                                            >
                                                <div className={`h-4.5 w-4.5 border rounded flex items-center justify-center shrink-0 transition-all ${
                                                    isChecked ? 'bg-primary border-primary' : 'border-border'
                                                }`}>
                                                    {isChecked && <Check className="h-3 w-3 text-white stroke-[3px]" />}
                                                </div>
                                                <span className="truncate flex-1 font-medium">{p.name}</span>
                                                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: PROGRAMME_COLORS[p.id] || p.color }} />
                                            </button>
                                        )
                                    })}
                                </div>
                            </div>
                        )}

                        {compareMode === 'courses_same' && metricsData?.programmes && (
                            <div className="space-y-4">
                                <div className="space-y-1">
                                    <label className="text-[10px] text-muted-foreground uppercase font-bold px-1">Choose Programme</label>
                                    <select
                                        value={selectedSameProg}
                                        onChange={e => setSelectedSameProg(e.target.value)}
                                        className="w-full px-2.5 py-2 text-xs rounded-lg border border-border bg-muted/40 focus:outline-none focus:ring-1 focus:ring-primary/30"
                                    >
                                        {metricsData.programmes.map(p => (
                                            <option key={p.id} value={p.id}>{p.name}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="space-y-2">
                                    <div className="flex items-center justify-between text-[10px] text-muted-foreground font-semibold px-1 border-t border-border/40 pt-3">
                                        <span className="font-semibold">Courses & Batches</span>
                                        <div className="flex gap-2">
                                            <button 
                                                onClick={() => {
                                                    const target = metricsData.programmes.find(p => p.id === selectedSameProg)
                                                    if (target) {
                                                        const keys: string[] = []
                                                        target.courses.forEach(c => c.batches.forEach(b => keys.push(`${c.courseId}_${b.batchId}`)))
                                                        setSelectedSameCourses(keys)
                                                    }
                                                }}
                                                className="hover:text-primary transition-colors hover:underline"
                                            >
                                                All
                                            </button>
                                            <button 
                                                onClick={() => setSelectedSameCourses([])}
                                                className="hover:text-destructive transition-colors hover:underline"
                                            >
                                                Clear
                                            </button>
                                        </div>
                                    </div>

                                    <div className="space-y-1 max-h-[190px] overflow-y-auto pr-1">
                                        {(() => { let runningIdx = 0; return metricsData.programmes.find(p => p.id === selectedSameProg)?.courses.flatMap((c) =>
                                            c.batches.map(b => {
                                                const colorIdx = runningIdx++  // matches the bars' per-batch color index
                                                const key = `${c.courseId}_${b.batchId}`
                                                const isChecked = selectedSameCourses.includes(key)
                                                return (
                                                    <button
                                                        key={key}
                                                        onClick={() => {
                                                            setSelectedSameCourses(prev => 
                                                                prev.includes(key) ? prev.filter(x => x !== key) : [...prev, key]
                                                            )
                                                        }}
                                                        className="w-full flex items-center gap-2.5 px-2 py-1.5 hover:bg-muted/30 rounded-lg text-left text-xs transition-colors"
                                                    >
                                                        <div className={`h-4 w-4 border rounded flex items-center justify-center shrink-0 transition-all ${
                                                            isChecked ? 'bg-primary border-primary' : 'border-border'
                                                        }`}>
                                                            {isChecked && <Check className="h-2.5 w-2.5 text-white stroke-[3px]" />}
                                                        </div>
                                                        <div className="truncate flex-1 min-w-0">
                                                            <p className="truncate font-semibold text-[11px]">{c.courseName}</p>
                                                            <p className="text-[9px] text-muted-foreground font-mono">{b.batchName}</p>
                                                        </div>
                                                        <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: getColorForCourse(selectedSameProg, colorIdx) }} />
                                                    </button>
                                                )
                                            })
                                        )})()}
                                        {metricsData.programmes.find(p => p.id === selectedSameProg)?.courses.length === 0 && (
                                            <p className="text-[11px] text-muted-foreground text-center py-4">No courses available for this program</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        {compareMode === 'courses_diff' && metricsData?.programmes && (
                            <div className="space-y-2">
                                <div className="flex items-center justify-between text-[10px] text-muted-foreground font-semibold px-1">
                                    <button 
                                        onClick={() => {
                                            const keys: string[] = []
                                            metricsData.programmes.forEach(p => p.courses.forEach(c => c.batches.forEach(b => keys.push(`${p.id}_${c.courseId}_${b.batchId}`))))
                                            setSelectedDiffCourses(keys)
                                        }}
                                        className="hover:text-primary transition-colors hover:underline"
                                    >
                                        Select All
                                    </button>
                                    <button 
                                        onClick={() => setSelectedDiffCourses([])}
                                        className="hover:text-destructive transition-colors hover:underline"
                                    >
                                        Clear All
                                    </button>
                                </div>

                                <div className="space-y-1 max-h-[260px] overflow-y-auto pr-1">
                                    {metricsData.programmes.flatMap(p => { let runningIdx = 0; return p.courses.flatMap((c) =>
                                            c.batches.map(b => {
                                                const colorIdx = runningIdx++  // matches the bars' per-batch color index (reset per programme)
                                                const key = `${p.id}_${c.courseId}_${b.batchId}`
                                                const isChecked = selectedDiffCourses.includes(key)
                                                return (
                                                    <button
                                                        key={key}
                                                        onClick={() => {
                                                            setSelectedDiffCourses(prev => 
                                                                prev.includes(key) ? prev.filter(x => x !== key) : [...prev, key]
                                                            )
                                                        }}
                                                        className="w-full flex items-center gap-2.5 px-2 py-1.5 hover:bg-muted/30 rounded-lg text-left text-xs transition-colors"
                                                    >
                                                        <div className={`h-4 w-4 border rounded flex items-center justify-center shrink-0 transition-all ${
                                                            isChecked ? 'bg-primary border-primary' : 'border-border'
                                                        }`}>
                                                            {isChecked && <Check className="h-2.5 w-2.5 text-white stroke-[3px]" />}
                                                        </div>
                                                        <div className="truncate flex-1 min-w-0">
                                                            <p className="truncate font-semibold text-[11px]">{c.courseName}</p>
                                                            <p className="text-[9px] text-muted-foreground font-mono flex items-center gap-1">
                                                                <span>[{p.name}]</span>
                                                                <span>•</span>
                                                                <span>{b.batchName}</span>
                                                            </p>
                                                        </div>
                                                        <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: getColorForCourse(p.id, colorIdx) }} />
                                                    </button>
                                                )
                                            })
                                        )
                                    })}
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
