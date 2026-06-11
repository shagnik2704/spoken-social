import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUserStore } from '@/store/userStore'
import api from '@/lib/axios'
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Loader2, BookOpen, Calendar, ArrowRight, CheckCircle2, Lock } from 'lucide-react'

interface Batch {
    id: string
    name: string
    status: string
    is_active: boolean
    startDate: string
    endDate: string
}

interface Course {
    id: string
    title: string
    batches: Batch[]
}

export function LandingPage() {
    const [courses, setCourses] = useState<Course[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
    const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null)
    
    const user = useUserStore(state => state.user)
    const setActiveCourse = useUserStore(state => state.setActiveCourse)
    const setActiveBatch = useUserStore(state => state.setActiveBatch)
    const activeProgrammeId = useUserStore(state => state.activeProgrammeId)
    const activeProgrammeName = useUserStore(state => state.activeProgrammeName)
    const setActiveProgramme = useUserStore(state => state.setActiveProgramme)
    const navigate = useNavigate()

    useEffect(() => {
        const endpoint = activeProgrammeId ? `/api/courses/me?programme_id=${activeProgrammeId}` : '/api/courses/me';
        console.log('DEBUG LANDING: user role =', user?.role, 'fetching endpoint =', endpoint);
        api.get(endpoint)
            .then(res => {
                console.log('DEBUG LANDING: fetched courses length =', res.data?.length, 'data =', res.data);
                setCourses(res.data)
                
                // Default to Linux if present, otherwise select the first available course
                const defaultCourse = res.data.find((c: any) => c.id === 'linux' || c.id === 'swayam_plus-linux') || res.data[0]
                if (defaultCourse) {
                    console.log('DEBUG LANDING: setting defaultCourse =', defaultCourse.id);
                    setSelectedCourse(defaultCourse)
                }
                setIsLoading(false)
            })
            .catch(err => {
                console.error('Failed to fetch courses', err)
                setIsLoading(false)
            })
    }, [user, activeProgrammeId])

    useEffect(() => {
        // Auto-select batch if there is exactly 1 batch available
        if (selectedCourse && selectedCourse.batches?.length === 1) {
            setSelectedBatchId(selectedCourse.batches[0].id)
        } else {
            setSelectedBatchId(null)
        }
    }, [selectedCourse])

    const handleProceed = () => {
        if (selectedCourse && selectedBatchId) {
            const batch = selectedCourse.batches.find(b => b.id === selectedBatchId)
            setActiveCourse(selectedCourse.id)
            setActiveBatch(selectedBatchId, batch?.is_active)
            
            // Redirect based on role
            if (user?.role === 'admin') navigate('/admin')
            else if (user?.role === 'coordinator') navigate('/coordinator')
            else navigate('/dashboard')
        }
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/10 via-background to-background flex flex-col items-center justify-center p-4 lg:p-8">
            <div className="w-full max-w-5xl space-y-8 animate-in fade-in zoom-in duration-500">
                
                {/* Header Section */}
                <div className="text-center space-y-2">
                    <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20 px-3 py-1 text-xs font-semibold uppercase tracking-wider">
                        Welcome back, {user?.displayName || 'Learner'}
                    </Badge>
                    <div className="flex items-center justify-center gap-2">
                        <Badge className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white border-0 font-bold px-3 py-1 text-xs">
                            {activeProgrammeName}
                        </Badge>
                        <Button 
                            variant="link" 
                            size="sm" 
                            className="h-auto p-0 text-xs font-bold text-muted-foreground hover:text-foreground transition-all"
                            onClick={() => {
                                setActiveProgramme('', '')
                                navigate('/programmes')
                            }}
                        >
                            (Change Programme)
                        </Button>
                    </div>
                    <h1 className="text-4xl lg:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
                        Choose Your Course & Batch
                    </h1>
                </div>

                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Course Selection Panel */}
                    <div className="lg:col-span-1 space-y-4">
                        <div className="flex items-center gap-2 mb-2 px-1">
                            <BookOpen className="w-4 h-4 text-primary" />
                            <h2 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Available Courses</h2>
                        </div>
                        <div className="space-y-3">
                            {courses.map(course => (
                                <button
                                    key={course.id}
                                    onClick={() => {
                                        setSelectedCourse(course)
                                    }}
                                    className={`w-full text-left p-4 rounded-xl border transition-all duration-300 group
                                        ${selectedCourse?.id === course.id 
                                            ? 'bg-primary/5 border-primary shadow-[0_0_20px_rgba(var(--primary),0.1)] ring-1 ring-primary' 
                                            : 'bg-card border-border hover:border-primary/50 hover:bg-muted/50'
                                        }`}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="space-y-1">
                                            <p className={`font-bold transition-colors ${selectedCourse?.id === course.id ? 'text-primary' : 'text-foreground'}`}>
                                                {course.title}
                                            </p>
                                            <div className="flex items-center gap-1.5">
                                                {(() => {
                                                    const isCourseActive = course.batches && course.batches.some(b => b.is_active);
                                                    return (
                                                        <>
                                                            <span className={`h-2 w-2 rounded-full ${isCourseActive ? 'bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-red-500'}`} />
                                                            <span className="text-[10px] uppercase font-bold tracking-tighter text-muted-foreground">
                                                                {isCourseActive ? 'Active' : 'Inactive'}
                                                            </span>
                                                        </>
                                                    );
                                                })()}
                                            </div>
                                        </div>
                                        <ArrowRight className={`w-4 h-4 transition-all duration-300 ${selectedCourse?.id === course.id ? 'translate-x-1 text-primary' : 'opacity-0 -translate-x-2'}`} />
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Batch Selection Panel */}
                    <div className="lg:col-span-2 space-y-4">
                        <div className="flex items-center gap-2 mb-2 px-1">
                            <Calendar className="w-4 h-4 text-primary" />
                            <h2 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Select Batch</h2>
                        </div>
                        
                        {selectedCourse ? (
                            <div className="grid sm:grid-cols-2 gap-4">
                                {selectedCourse.batches.length > 0 ? (
                                    selectedCourse.batches.map(batch => (
                                        <button
                                            key={batch.id}
                                            onClick={() => setSelectedBatchId(batch.id)}
                                            className={`p-5 rounded-2xl border text-left transition-all duration-300 flex flex-col h-full relative overflow-hidden group
                                                ${selectedBatchId === batch.id 
                                                    ? 'bg-card border-primary ring-1 ring-primary shadow-xl scale-[1.02]' 
                                                    : 'bg-card/50 border-border/50 hover:border-primary/30 hover:bg-card hover:scale-[1.01]'
                                                }`}
                                        >
                                            {selectedBatchId === batch.id && (
                                                <div className="absolute top-0 right-0 p-3">
                                                    <CheckCircle2 className="w-5 h-5 text-primary" />
                                                </div>
                                            )}

                                            <div className="space-y-4 flex-1">
                                                <div className="space-y-1">
                                                    <p className="text-lg font-bold tracking-tight">{batch.name}</p>
                                                    <Badge variant={batch.is_active ? "secondary" : "outline"} className={`text-[10px] px-1.5 h-5 ${batch.is_active ? 'bg-primary/10 text-primary border-0' : 'text-muted-foreground'}`}>
                                                        {batch.is_active ? 'Active Offering' : 'Archived'}
                                                    </Badge>
                                                </div>

                                                <div className="space-y-2 mt-auto">
                                                    <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 p-2 rounded-lg">
                                                        <Calendar className="w-3.5 h-3.5" />
                                                        <span>{new Date(batch.startDate).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })} – {new Date(batch.endDate).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </button>
                                    ))
                                ) : (
                                    <div className="col-span-full py-12 flex flex-col items-center justify-center text-center space-y-3 bg-muted/20 border border-dashed border-border rounded-2xl">
                                        <Lock className="w-8 h-8 text-muted-foreground/30" />
                                        <p className="text-sm text-muted-foreground font-medium">No batches available for this course yet.</p>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-[300px] border border-dashed border-border rounded-2xl bg-muted/10">
                                <p className="text-muted-foreground text-sm font-medium">Please select a course path on the left</p>
                            </div>
                        )}

                        {/* Action Area */}
                        <div className="mt-8 pt-6 border-t border-border flex justify-end">
                            <Button 
                                size="lg" 
                                disabled={!selectedBatchId}
                                onClick={handleProceed}
                                className="group px-8 rounded-full shadow-lg shadow-primary/20 transition-all hover:shadow-primary/30"
                            >
                                Enter Dashboard
                                <ArrowRight className="ml-2 w-4 h-4 transition-transform group-hover:translate-x-1" />
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Footer Credits */}
                <div className="pt-12 text-center">
                    <p className="text-xs text-muted-foreground font-medium uppercase tracking-[0.2em]">
                        Spoken Social • Empowering Open Source Education
                    </p>
                </div>
            </div>
        </div>
    )
}
