// ============================================================
// LearnerPackTracker.tsx — 12-Week Workspace for SWAYAM Plus
// ============================================================
// Interactive curriculum and assessment system for
// "Personality and Human Development" course featuring:
// 1. 12-Week collapsible roadmap & habit milestones
// 2. 4-step tutorial modal:
//    - Video (Spoken Tutorial player link)
//    - 3-5 page Reading with ReactMarkdown & Key Terms glossary
//    - Notebook Try-It activity + 3-5 sentence private Reflection
//    - 5-question automated MCQ Quiz with instant explanations
// 3. Multi-day Habit Logs (Emotion, Belief, Empathy, Breathing, Portfolio)
// ============================================================

import { useState, useEffect } from 'react'
import {
    CheckCircle2, ChevronDown, Lock, BookOpen,
    PlayCircle, HelpCircle, PenTool, Sparkles,
    Heart, Lightbulb, Compass,
    Check, ArrowRight, ExternalLink, FileText, Code2, Loader2,
    Download, ChevronLeft, ChevronRight, FolderArchive, Terminal, Wrench,
    UploadCloud, AlertCircle
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { toast } from 'sonner'
import api from '@/lib/axios'
import { useUserStore } from '@/store/userStore'
import type {
    LearnerPackOverview,
    LearnerPackOverviewTutorial,
    LearnerPackTutorialDetail,
    HabitMilestone,
    HabitLogCheckinItem
} from '@/types'

// Week titles mapping per course
const PERSONALITY_DEV_WEEKS: Record<number, string> = {
    1: 'Week 1: Introduction to Emotions & Understanding Fear',
    2: 'Week 2: Understanding Anger & Sadness',
    3: 'Week 3: Happiness, Guilt & 7-Day Emotion Log',
    4: 'Week 4: Jealousy, Admiration & Emotion Log Wrap-up',
    5: 'Week 5: Reality, Interpretations & Understanding Beliefs',
    6: 'Week 6: How to Change Beliefs & 7-Day Belief Log',
    7: 'Week 7: Judgment, Feedback & 7-Day Empathy Log',
    8: 'Week 8: Catch-up, Live Session 1 & Midterm Revision',
    9: 'Week 9: Neuroplasticity & The Magic of Failures',
    10: 'Week 10: The Word "Yet" & Mindful Breathing Log',
    11: 'Week 11: Practising Growth Mindset & Growth Plan',
    12: 'Week 12: Personal Growth Portfolio & Final Exam Prep'
}

const LINUX_WEEKS: Record<number, string> = {
    1: 'Week 1: VirtualBox & Ubuntu Linux Installation (Tutorials 1–2)',
    2: 'Week 2: Ubuntu Desktop, Synaptic & Lab 1 (Tutorials 3–4)',
    3: 'Week 3: Basic Commands, Date & Time (Tutorials 5–6)',
    4: 'Week 4: Command Structure, Utilities & Lab 2 (Tutorials 7–8)',
    5: 'Week 5: File System & Regular Files (Tutorials 9–10)',
    6: 'Week 6: Streams, Pipes, Processes & Lab 3 (Tutorials 11–12)',
    7: 'Week 7: Linux Environment & System Administration (Tutorials 13–14)',
    8: 'Week 8: Permissions, Ownership & Lab 4 (Tutorial 15)',
    9: 'Week 9: Simple Filters & Introduction to grep (Tutorials 16–17)',
    10: 'Week 10: Mastering grep & Introduction to sed (Tutorials 18–19)',
    11: 'Week 11: sed Text Editing, Lab 5 & Capstone Start (Tutorial 20)',
    12: 'Week 12: Capstone Project Submission & Final Exam Revision'
}

const getWeekTitle = (weekNum: number, courseId?: string) => {
    if (courseId === 'linux') {
        return LINUX_WEEKS[weekNum] || `Week ${weekNum}`
    }
    return PERSONALITY_DEV_WEEKS[weekNum] || `Week ${weekNum}`
}

export const resolveMediaUrl = (url?: string | null) => {
    if (!url) return ''
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('blob:')) return url
    const apiUrl = import.meta.env.VITE_API_URL || ''
    if (apiUrl && !apiUrl.startsWith('/')) {
        return `${apiUrl.replace(/\/$/, '')}${url}`
    }
    return url
}

export function LearnerPackTracker() {
    const { activeCourseId, addXP } = useUserStore()
    const [overview, setOverview] = useState<LearnerPackOverview | null>(null)
    const [habitLogs, setHabitLogs] = useState<Record<string, HabitLogCheckinItem[]>>({})
    const [isLoading, setIsLoading] = useState(true)
    const [openWeeks, setOpenWeeks] = useState<Record<number, boolean>>({ 1: true, 2: true })

    // Active tutorial modal state
    const [activeTutorialId, setActiveTutorialId] = useState<string | null>(null)
    const [tutorialDetail, setTutorialDetail] = useState<LearnerPackTutorialDetail | null>(null)
    const [isLoadingDetail, setIsLoadingDetail] = useState(false)
    const [activeTab, setActiveTab] = useState<'video' | 'reading' | 'activity' | 'assignment' | 'quiz'>('video')
    const [videoSubTab, setVideoSubTab] = useState<'stream' | 'code' | 'instruction' | 'installation'>('stream')

    // Assignment state
    const [isMarkingAssignment, setIsMarkingAssignment] = useState(false)

    // Reflection submission state
    const [reflectionText, setReflectionText] = useState('')
    const [isSubmittingReflection, setIsSubmittingReflection] = useState(false)

    // Technical lab submission state (Linux)
    const [terminalOutput, setTerminalOutput] = useState('')
    const [screenshotFile, setScreenshotFile] = useState<File | null>(null)
    const [screenshotPreview, setScreenshotPreview] = useState<string | null>(null)
    const [screenshotNotes, setScreenshotNotes] = useState('')
    const [isSubmittingLab, setIsSubmittingLab] = useState(false)

    // Quiz submission state
    const [quizAnswers, setQuizAnswers] = useState<Record<string, string>>({})
    const [isSubmittingQuiz, setIsSubmittingQuiz] = useState(false)

    // Activity completion state
    const [isMarkingActivity, setIsMarkingActivity] = useState(false)

    // Habit check-in state
    const [habitNote, setHabitNote] = useState('')
    const [isCheckingIn, setIsCheckingIn] = useState(false)

    // Current tutorial navigation targets
    const prevTutorial = tutorialDetail && overview?.tutorials
        ? overview.tutorials.find(t => t.number === tutorialDetail.tutorialNumber - 1)
        : null
    const nextTutorial = tutorialDetail && overview?.tutorials
        ? overview.tutorials.find(t => t.number === tutorialDetail.tutorialNumber + 1)
        : null

    const isLinux = overview?.courseId === 'linux'
    const isSetupTutorial = isLinux && (tutorialDetail?.tutorialNumber === 1 || tutorialDetail?.tutorialNumber === 2)

    const fetchOverview = async (isBackground = false) => {
        if (!activeCourseId) return
        try {
            if (!isBackground && !overview) {
                setIsLoading(true)
            }
            const [ovRes, logsRes] = await Promise.all([
                api.get(`/api/learner-pack/course/${activeCourseId}/overview`),
                api.get(`/api/learner-pack/habit-logs/${activeCourseId}`)
            ])
            setOverview(ovRes.data)
            setHabitLogs(logsRes.data.logs || {})
            const tuts = ovRes.data?.tutorials || []
            const activeTut = tuts.find(
                (t: any) => !t.userProgress?.quizPassed && t.userProgress?.status !== 'completed'
            )
            if (activeTut?.week) {
                setOpenWeeks(prev => ({ ...prev, [activeTut.week]: true }))
            }
        } catch (err: any) {
            console.error('Failed to load learner pack overview', err)
            toast.error('Could not load course curriculum.')
        } finally {
            if (!isBackground) {
                setIsLoading(false)
            }
        }
    }

    useEffect(() => {
        fetchOverview()
    }, [activeCourseId])

    const [videoWatchPercent, setVideoWatchPercent] = useState<number>(0)
    const [isVideoBuffering, setIsVideoBuffering] = useState(false)

    const switchTab = (tab: 'video' | 'reading' | 'activity' | 'assignment' | 'quiz') => {
        setActiveTab(tab)
        requestAnimationFrame(() => {
            const btn = document.getElementById(`tab-btn-${tab}`)
            if (btn) {
                btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
            }
            const modalBody = document.getElementById('tutorial-modal-body')
            if (modalBody) {
                modalBody.scrollTo({ top: 0, behavior: 'smooth' })
            }
        })
    }

    const openTutorialModal = async (
        tutId: string,
        initialTab: 'video' | 'reading' | 'activity' | 'assignment' | 'quiz' = 'video'
    ) => {
        setActiveTutorialId(tutId)
        setIsLoadingDetail(true)
        setActiveTab(initialTab)
        setVideoSubTab('stream')
        setVideoWatchPercent(0)
        setIsVideoBuffering(false)
        setQuizAnswers({})
        requestAnimationFrame(() => {
            const btn = document.getElementById(`tab-btn-${initialTab}`)
            if (btn) btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
        })
        try {
            const res = await api.get(`/api/learner-pack/tutorials/${tutId}`)
            const data: LearnerPackTutorialDetail = res.data
            setTutorialDetail(data)
            if (data.userReflection) {
                setReflectionText(data.userReflection.reflectionText || '')
                setTerminalOutput(data.userReflection.reflectionText || '')
                setScreenshotPreview(data.userReflection.imageUrl || null)
                setScreenshotNotes(data.userReflection.reflectionText || '')
            } else {
                setReflectionText('')
                setTerminalOutput('')
                setScreenshotPreview(null)
                setScreenshotFile(null)
                setScreenshotNotes('')
            }
        } catch (err) {
            toast.error('Failed to load tutorial content.')
            setActiveTutorialId(null)
        } finally {
            setIsLoadingDetail(false)
        }
    }

    const handleMarkVideoWatched = async () => {
        if (!activeTutorialId) return
        if (tutorialDetail?.userTutorial.watched === 'yes') return
        try {
            await api.post(`/api/learner-pack/tutorials/${activeTutorialId}/video-watched`)
            toast.success('Video watched! +10 XP awarded 🎬')
            addXP(10)
            if (tutorialDetail) {
                setTutorialDetail({
                    ...tutorialDetail,
                    userTutorial: {
                        ...tutorialDetail.userTutorial,
                        watched: 'yes'
                    }
                })
            }
            fetchOverview(true)
        } catch (err) {
            toast.error('Failed to update video progress.')
        }
    }

    const handleVideoEnded = () => {
        if (tutorialDetail && tutorialDetail.userTutorial.watched !== 'yes') {
            handleMarkVideoWatched()
        }
    }

    const handleMarkReadingComplete = async () => {
        if (!activeTutorialId) return
        if (tutorialDetail?.userTutorial.watched === 'yes') return
        try {
            await api.post(`/api/learner-pack/tutorials/${activeTutorialId}/reading-complete`)
            toast.success('Reading completed! +10 XP awarded 📚')
            addXP(10)
            if (tutorialDetail) {
                setTutorialDetail({
                    ...tutorialDetail,
                    userTutorial: {
                        ...tutorialDetail.userTutorial,
                        watched: 'yes'
                    }
                })
            }
            fetchOverview(true)
        } catch (err) {
            toast.error('Failed to update reading status.')
        }
    }

    const handleMarkActivityComplete = async () => {
        if (!activeTutorialId) return
        try {
            setIsMarkingActivity(true)
            await api.post(`/api/learner-pack/tutorials/${activeTutorialId}/activity-complete`)
            toast.success('Private notebook exercise completed! +5 XP awarded 📓')
            addXP(5)
            if (tutorialDetail) {
                setTutorialDetail({
                    ...tutorialDetail,
                    userTutorial: {
                        ...tutorialDetail.userTutorial,
                        minitaskOpted: 'yes'
                    }
                })
            }
            fetchOverview(true)
        } catch (err) {
            toast.error('Failed to mark exercise status.')
        } finally {
            setIsMarkingActivity(false)
        }
    }

    const handleMarkAssignmentComplete = async () => {
        if (!activeTutorialId) return
        try {
            setIsMarkingAssignment(true)
            await api.post(`/api/learner-pack/tutorials/${activeTutorialId}/assignment-complete`)
            toast.success('Official assignment marked completed! +5 XP awarded 📝')
            addXP(5)
            if (tutorialDetail) {
                setTutorialDetail({
                    ...tutorialDetail,
                    userTutorial: {
                        ...tutorialDetail.userTutorial,
                        assignmentDone: 'yes'
                    }
                })
            }
            fetchOverview(true)
        } catch (err) {
            toast.error('Failed to update assignment status.')
        } finally {
            setIsMarkingAssignment(false)
        }
    }

    const handleSubmitReflection = async () => {
        if (!activeTutorialId) return
        if (!reflectionText.trim()) {
            toast.error('Please enter your reflection before submitting.')
            return
        }

        try {
            setIsSubmittingReflection(true)
            const res = await api.post(`/api/learner-pack/tutorials/${activeTutorialId}/reflection`, {
                reflection_text: reflectionText
            })
            toast.success('Reflection submitted! +5 XP awarded ✨')
            addXP(5)
            if (tutorialDetail) {
                setTutorialDetail({
                    ...tutorialDetail,
                    userReflection: res.data.reflection,
                    userTutorial: {
                        ...tutorialDetail.userTutorial,
                        assignmentDone: 'yes'
                    }
                })
            }
            fetchOverview(true)
        } catch (err) {
            toast.error('Failed to submit reflection.')
        } finally {
            setIsSubmittingReflection(false)
        }
    }

    const handleTerminalSubmit = async () => {
        if (!activeTutorialId) return
        const text = terminalOutput.trim()
        if (!text) {
            toast.error('Please paste your terminal commands and output before submitting.')
            return
        }
        if (text.length > 20000) {
            toast.error('Submission exceeds 20,000 characters limit. Please paste only relevant command output.')
            return
        }
        try {
            setIsSubmittingLab(true)
            const res = await api.post(`/api/learner-pack/tutorials/${activeTutorialId}/terminal-submission`, {
                commands_output: text
            })
            toast.success('Terminal lab submission verified! +10 XP awarded 💻')
            addXP(res.data.xpGained || 10)
            setTutorialDetail(prev => prev ? {
                ...prev,
                userReflection: res.data.submission,
                userTutorial: res.data.userTutorial
            } : null)
            fetchOverview(true)
        } catch (err: any) {
            const msg = err.response?.data?.detail
            toast.error(typeof msg === 'string' ? msg : 'Failed to submit terminal output.')
        } finally {
            setIsSubmittingLab(false)
        }
    }

    const handleScreenshotUpload = async () => {
        if (!activeTutorialId) return
        if (!screenshotFile) {
            toast.error('Please select an image file first.')
            return
        }
        if (screenshotFile.size > 5 * 1024 * 1024) {
            toast.error('Image file exceeds the 5 MB limit. Please resize or take a standard screenshot.')
            return
        }
        try {
            setIsSubmittingLab(true)
            const formData = new FormData()
            formData.append('file', screenshotFile)
            if (screenshotNotes.trim()) {
                formData.append('notes', screenshotNotes.trim())
            }
            const res = await api.post(`/api/learner-pack/tutorials/${activeTutorialId}/screenshot-submission`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            toast.success('Installation screenshot verified! +15 XP awarded 🚀')
            addXP(res.data.xpGained || 15)
            setScreenshotPreview(res.data.submission?.imageUrl || null)
            setScreenshotFile(null)
            setTutorialDetail(prev => prev ? {
                ...prev,
                userReflection: res.data.submission,
                userTutorial: res.data.userTutorial
            } : null)
            fetchOverview(true)
        } catch (err: any) {
            const msg = err.response?.data?.detail
            toast.error(typeof msg === 'string' ? msg : 'Failed to upload screenshot.')
        } finally {
            setIsSubmittingLab(false)
        }
    }

    const handleSubmitQuiz = async () => {
        if (!activeTutorialId || !tutorialDetail) return
        const questions = tutorialDetail.quiz.questions
        const answeredCount = Object.keys(quizAnswers).length
        if (answeredCount < questions.length) {
            toast.error(`Please answer all ${questions.length} questions before submitting.`)
            return
        }

        try {
            setIsSubmittingQuiz(true)
            const res = await api.post(`/api/learner-pack/tutorials/${activeTutorialId}/quiz`, {
                answers: quizAnswers
            })
            const { score, totalQuestions, passed, results, xpGained } = res.data

            toast.success(`Quiz completed! Scored ${score}/${totalQuestions}${xpGained > 0 ? ` (+${xpGained} XP)` : ''} 🎉`)
            if (xpGained > 0) addXP(xpGained)

            setTutorialDetail({
                ...tutorialDetail,
                quiz: {
                    hasAttempted: true,
                    score,
                    totalQuestions,
                    passed,
                    submittedAt: new Date().toISOString(),
                    questions: results
                },
                userTutorial: {
                    ...tutorialDetail.userTutorial,
                    practiced: 'yes',
                    completed: true
                }
            })
            fetchOverview(true)
        } catch (err) {
            toast.error('Failed to submit quiz.')
        } finally {
            setIsSubmittingQuiz(false)
        }
    }

    const handleHabitCheckin = async (logType: string, dayNumber: number) => {
        if (!activeCourseId) return
        try {
            setIsCheckingIn(true)
            const todayStr = new Date().toISOString().split('T')[0]
            await api.post('/api/learner-pack/habit-logs/checkin', {
                course_id: activeCourseId,
                log_type: logType,
                day_number: dayNumber,
                checkin_date: todayStr,
                summary_reflection: habitNote.trim() || undefined
            })
            toast.success(`Day ${dayNumber} check-in recorded! 🌱`)
            setHabitNote('')
            fetchOverview(true)
        } catch (err) {
            toast.error('Failed to record habit check-in.')
        } finally {
            setIsCheckingIn(false)
        }
    }

    if (isLoading && !overview) {
        return (
            <Card className="animate-pulse">
                <CardContent className="p-8 space-y-4">
                    <div className="h-6 w-1/3 bg-muted rounded" />
                    <div className="h-4 w-1/2 bg-muted/60 rounded" />
                    <div className="h-32 bg-muted/30 rounded-xl" />
                </CardContent>
            </Card>
        )
    }

    if (!overview) return null

    // Compute progress
    const totalTuts = overview.tutorials.length
    const completedTuts = overview.tutorials.filter(t => t.userProgress.status === 'completed' || t.userProgress.quizPassed).length
    const progressPercent = totalTuts > 0 ? Math.round((completedTuts / totalTuts) * 100) : 0

    // Group tutorials by week
    const tutorialsByWeek: Record<number, LearnerPackOverviewTutorial[]> = {}
    for (let w = 1; w <= 12; w++) {
        tutorialsByWeek[w] = overview.tutorials.filter(t => t.week === w)
    }

    // Milestones by week
    const milestonesByWeek: Record<number, HabitMilestone> = {}
    overview.habitMilestones.forEach(m => {
        milestonesByWeek[m.week] = m
    })

    // Next incomplete tutorial to guide the student directly
    const nextIncompleteTutorial = overview.tutorials.find(
        t => !t.userProgress.quizPassed &&
             t.userProgress.status !== 'completed' &&
             !(overview.courseId === 'linux' && t.number <= 2 && t.userProgress.reflectionSubmitted)
    )
    const allCompleted = overview.tutorials.length > 0 && !nextIncompleteTutorial

    const getNextStepInfo = (tut: LearnerPackOverviewTutorial) => {
        const p = tut.userProgress
        if (!p.watched) {
            return { stepLabel: 'Watch Video', tab: 'video' as const, isStarted: false }
        }
        if (!p.readingCompleted) {
            return { stepLabel: 'Reading Notes', tab: 'reading' as const, isStarted: true }
        }
        if (!p.reflectionSubmitted) {
            return {
                stepLabel: tut.hasAssignment ? 'Assignment' : 'Activity & Reflection',
                tab: tut.hasAssignment ? ('assignment' as const) : ('activity' as const),
                isStarted: true
            }
        }
        if (overview.courseId === 'linux' && tut.number <= 2) {
            return { stepLabel: 'Setup Complete', tab: 'activity' as const, isStarted: true }
        }
        return { stepLabel: 'Quiz', tab: 'quiz' as const, isStarted: true }
    }

    const nextStep = nextIncompleteTutorial ? getNextStepInfo(nextIncompleteTutorial) : null

    return (
        <div className="space-y-6">
            {/* Header Card */}
            <Card className="border border-border/80 bg-card shadow-xs overflow-hidden">
                <CardContent className="p-6 sm:p-7">
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                        <div className="space-y-1.5">
                            <div className="flex items-center gap-3">
                                <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20 shadow-2xs">
                                    <Compass className="h-6 w-6 text-primary" />
                                </div>
                                <div>
                                    <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground font-sans">
                                        {overview.title}
                                    </h2>
                                    <p className="text-xs sm:text-sm text-muted-foreground">
                                        12-Week Interactive Curriculum & Learning Workspace
                                    </p>
                                </div>
                            </div>
                        </div>
                        <Badge variant="outline" className="px-3.5 py-1.5 font-mono text-xs font-semibold border-border bg-muted/60 text-foreground shadow-2xs">
                            {completedTuts} / {totalTuts} Completed ({progressPercent}%)
                        </Badge>
                    </div>

                    <div className="mt-5 space-y-2">
                        <div className="flex justify-between text-xs font-medium text-muted-foreground">
                            <span>Curriculum Progress</span>
                            <span className="font-mono text-foreground font-semibold">{progressPercent}%</span>
                        </div>
                        <Progress value={progressPercent} className="h-2.5 bg-muted/80 rounded-full" />
                    </div>
                </CardContent>
            </Card>

            {/* Minimal Next-Action Card */}
            {nextIncompleteTutorial && nextStep && (
                <Card className="border border-primary/25 bg-primary/[0.03] shadow-2xs hover:shadow-xs transition-all">
                    <CardContent className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div className="space-y-1 min-w-0">
                            <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium flex-wrap">
                                <span className="font-semibold text-primary">Up Next</span>
                                <span>•</span>
                                <span>Week {nextIncompleteTutorial.week}</span>
                                <span>•</span>
                                <span className="text-foreground/90 font-medium">{nextStep.stepLabel}</span>
                            </div>
                            <h3 className="text-base sm:text-lg font-bold text-foreground truncate">
                                #{nextIncompleteTutorial.number}. {nextIncompleteTutorial.title}
                            </h3>
                        </div>
                        <Button
                            onClick={() => openTutorialModal(nextIncompleteTutorial.id, nextStep.tab)}
                            className="font-semibold text-xs sm:text-sm gap-2 shrink-0 w-full sm:w-auto shadow-2xs hover:shadow-xs cursor-pointer"
                        >
                            <span>{nextStep.isStarted ? 'Continue' : 'Start Lesson'}</span>
                            <ArrowRight className="h-4 w-4" />
                        </Button>
                    </CardContent>
                </Card>
            )}

            {allCompleted && (
                <Card className="border border-emerald-500/25 bg-emerald-500/[0.03] shadow-2xs">
                    <CardContent className="p-4 sm:p-5 flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <div className="h-8 w-8 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-sm shrink-0">
                                ✓
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-foreground">All Tutorials Completed!</h3>
                                <p className="text-xs text-muted-foreground">You have finished the entire 17-tutorial curriculum.</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* 12-Week Collapsible Accordion */}
            <div className="space-y-3">
                {Array.from({ length: 12 }, (_, idx) => idx + 1).map((weekNum) => {
                    const tuts = tutorialsByWeek[weekNum] || []
                    const milestone = milestonesByWeek[weekNum]
                    const isWeekOpen = openWeeks[weekNum] ?? false
                    const weekCompleted = tuts.length > 0 && tuts.every(t => t.userProgress.quizPassed)

                    return (
                        <Card key={weekNum} className={`border transition-colors ${weekCompleted ? 'border-emerald-500/30 bg-emerald-500/[0.02]' : 'border-border'}`}>
                            <Collapsible
                                open={isWeekOpen}
                                onOpenChange={(open) => setOpenWeeks({ ...openWeeks, [weekNum]: open })}
                            >
                                <CollapsibleTrigger asChild>
                                    <div className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/30 transition-colors">
                                        <div className="flex items-center gap-3">
                                            {weekCompleted ? (
                                                <div className="h-7 w-7 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0">
                                                    <CheckCircle2 className="h-4 w-4" />
                                                </div>
                                            ) : (
                                                <div className="h-7 w-7 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center shrink-0">
                                                    W{weekNum}
                                                </div>
                                            )}
                                            <div>
                                                <h3 className="text-sm font-semibold text-foreground">
                                                    {getWeekTitle(weekNum, overview.courseId)}
                                                </h3>
                                                <p className="text-xs text-muted-foreground">
                                                    {tuts.length > 0 ? `${tuts.length} Tutorials` : 'Special Milestone Week'}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {milestone && (
                                                <Badge variant="secondary" className="text-[11px] bg-amber-500/10 text-amber-600 border border-amber-500/20">
                                                    {milestone.title}
                                                </Badge>
                                            )}
                                            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${isWeekOpen ? 'rotate-180' : ''}`} />
                                        </div>
                                    </div>
                                </CollapsibleTrigger>

                                <CollapsibleContent className="px-4 pb-4 pt-1 space-y-3">
                                    {/* Milestone Card if present */}
                                    {milestone && (
                                        <div className="p-3.5 rounded-lg bg-amber-500/5 border border-amber-500/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                                            <div className="flex items-center gap-2.5">
                                                <div className="p-2 rounded-full bg-amber-500/10 text-amber-600">
                                                    <Heart className="h-4 w-4" />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-semibold text-foreground">{milestone.title}</p>
                                                    <p className="text-[11px] text-muted-foreground">
                                                        Daily physical notebook log with dated Spoken Social check-in.
                                                    </p>
                                                </div>
                                            </div>
                                            {/* Days indicator */}
                                            <div className="flex items-center gap-1.5 flex-wrap">
                                                {Array.from({ length: milestone.days }, (_, dIdx) => dIdx + 1).map((d) => {
                                                    const checkins = habitLogs[milestone.logType] || []
                                                    const isChecked = checkins.some(c => c.dayNumber === d)
                                                    return (
                                                        <button
                                                            key={d}
                                                            onClick={() => !isChecked && handleHabitCheckin(milestone.logType, d)}
                                                            disabled={isChecked || isCheckingIn}
                                                            className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-all ${isChecked
                                                                ? 'bg-emerald-500 text-white cursor-default'
                                                                : 'bg-muted hover:bg-primary/20 hover:text-primary text-muted-foreground cursor-pointer'
                                                                }`}
                                                            title={isChecked ? `Day ${d} checked in` : `Click to check-in for Day ${d}`}
                                                        >
                                                            {isChecked ? `✓ D${d}` : `D${d}`}
                                                        </button>
                                                    )
                                                })}
                                            </div>
                                        </div>
                                    )}

                                    {/* Tutorials in this week */}
                                    {tuts.map((tut) => {
                                        const p = tut.userProgress
                                        const isCompleted = p.status === 'completed' || p.quizPassed || (overview.courseId === 'linux' && tut.number <= 2 && Boolean(p.reflectionSubmitted))

                                        return (
                                            <div
                                                key={tut.id}
                                                className={cn(
                                                    "group flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-xl border transition-all gap-4",
                                                    isCompleted 
                                                        ? "bg-card/60 border-emerald-500/25 hover:border-emerald-500/40 hover:shadow-xs" 
                                                        : (p.watched || p.reflectionSubmitted)
                                                            ? "bg-card border-primary/30 hover:border-primary/50 shadow-2xs"
                                                            : "bg-card border-border/70 hover:border-primary/30 hover:shadow-2xs"
                                                )}
                                            >
                                                <div className="flex items-start sm:items-center gap-3 min-w-0">
                                                    <div className={cn(
                                                        "h-8 w-8 rounded-lg font-mono text-xs font-bold flex items-center justify-center shrink-0 border transition-colors",
                                                        isCompleted
                                                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/25"
                                                            : (p.watched || p.reflectionSubmitted)
                                                                ? "bg-primary/10 text-primary border-primary/25"
                                                                : "bg-muted text-muted-foreground border-border/60"
                                                    )}>
                                                        {isCompleted ? "✓" : `#${tut.number}`}
                                                    </div>
                                                    <div className="space-y-1 min-w-0">
                                                        <h4 className="text-sm font-semibold truncate text-foreground group-hover:text-primary transition-colors">
                                                            {tut.title}
                                                        </h4>
                                                        {(tut.hasCodeFiles || tut.hasInstructionSheet) && (
                                                            <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
                                                                {tut.hasCodeFiles && (
                                                                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-muted-foreground bg-muted/60 px-2 py-0.5 rounded border border-border/70">
                                                                        <Code2 className="h-3 w-3" />
                                                                        Code Files
                                                                    </span>
                                                                )}
                                                                {tut.hasInstructionSheet && (
                                                                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-muted-foreground bg-muted/60 px-2 py-0.5 rounded border border-border/70">
                                                                        <FileText className="h-3 w-3" />
                                                                        PDF Sheet
                                                                    </span>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-2.5 shrink-0 w-full sm:w-auto justify-between sm:justify-end">
                                                    {/* Step Badges */}
                                                    <div className="flex items-center gap-1.5 flex-wrap sm:flex-nowrap">
                                                        <Badge
                                                            variant="outline"
                                                            className={cn(
                                                                "text-[10px] px-2 py-0.5 font-medium transition-colors",
                                                                p.watched 
                                                                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30" 
                                                                    : "text-muted-foreground/60 border-dashed border-border/80 bg-muted/20"
                                                            )}
                                                            title="Video Watched"
                                                        >
                                                            {p.watched ? "✓ Video" : "Video"}
                                                        </Badge>
                                                        <Badge
                                                            variant="outline"
                                                            className={cn(
                                                                "text-[10px] px-2 py-0.5 font-medium transition-colors",
                                                                p.reflectionSubmitted 
                                                                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30" 
                                                                    : "text-muted-foreground/60 border-dashed border-border/80 bg-muted/20"
                                                            )}
                                                            title="Written Reflection"
                                                        >
                                                            {p.reflectionSubmitted ? "✓ Reflection" : "Reflection"}
                                                        </Badge>
                                                        {tut.hasAssignment && (
                                                            <Badge
                                                                variant="outline"
                                                                className={cn(
                                                                    "text-[10px] px-2 py-0.5 font-medium transition-colors",
                                                                    p.assignmentDone 
                                                                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30" 
                                                                        : "text-muted-foreground/60 border-dashed border-border/80 bg-muted/20"
                                                                )}
                                                                title="Official Assignment (+5 XP)"
                                                            >
                                                                {p.assignmentDone ? "✓ Assignment" : "Assignment"}
                                                            </Badge>
                                                        )}
                                                        {overview.courseId === 'linux' && tut.number <= 2 ? (
                                                            <Badge
                                                                variant="outline"
                                                                className={cn(
                                                                    "text-[10px] px-2 py-0.5 font-medium transition-colors",
                                                                    p.reflectionSubmitted
                                                                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                                                                        : "text-muted-foreground/60 border-dashed border-border/80 bg-muted/20"
                                                                )}
                                                                title="Hands-on installation verification"
                                                            >
                                                                {p.reflectionSubmitted ? "✓ Setup Done" : "Setup Task"}
                                                            </Badge>
                                                        ) : (
                                                            <Badge
                                                                variant="outline"
                                                                className={cn(
                                                                    "text-[10px] px-2 py-0.5 font-medium transition-colors",
                                                                    p.quizPassed 
                                                                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30" 
                                                                        : "text-muted-foreground/60 border-dashed border-border/80 bg-muted/20"
                                                                )}
                                                                title="5-Question Automated Quiz"
                                                            >
                                                                {p.quizPassed ? `✓ Quiz (${p.quizScore}/5)` : "Quiz"}
                                                            </Badge>
                                                        )}
                                                    </div>

                                                    <Button
                                                        size="sm"
                                                        variant={isCompleted ? "outline" : "default"}
                                                        onClick={() => openTutorialModal(tut.id, isCompleted ? 'video' : getNextStepInfo(tut).tab)}
                                                        className={cn(
                                                            "text-xs font-semibold h-8.5 px-3.5 transition-all shadow-2xs hover:shadow-xs",
                                                            !isCompleted && "bg-primary text-primary-foreground hover:bg-primary/90"
                                                        )}
                                                    >
                                                        <span>{isCompleted ? 'Review' : (p.watched || p.reflectionSubmitted) ? 'Continue' : 'Open Tutorial'}</span>
                                                        <ArrowRight className="h-3.5 w-3.5 ml-1.5 group-hover:translate-x-0.5 transition-transform" />
                                                    </Button>
                                                </div>
                                            </div>
                                        )
                                    })}
                                </CollapsibleContent>
                            </Collapsible>
                        </Card>
                    )
                })}
            </div>

            {/* Tutorial Interactive Workspace Modal (Wide, Spacious & Simplified UX) */}
            <Dialog open={!!activeTutorialId} onOpenChange={(open) => !open && setActiveTutorialId(null)}>
                <DialogContent className="sm:max-w-5xl w-[98vw] max-w-full h-[95vh] max-h-[95vh] flex flex-col p-0 overflow-hidden gap-0 rounded-2xl border shadow-2xl bg-card">
                    {isLoadingDetail || !tutorialDetail ? (
                        <div className="p-12 text-center space-y-4 my-auto">
                            <div className="h-6 w-1/4 bg-muted animate-pulse mx-auto rounded" />
                            <div className="h-4 w-1/2 bg-muted/60 animate-pulse mx-auto rounded" />
                            <div className="h-64 bg-muted/30 animate-pulse rounded-2xl max-w-2xl mx-auto" />
                        </div>
                    ) : (
                        <>
                            {/* Modal Header */}
                            <div className="px-5 sm:px-8 py-4 border-b bg-card shrink-0">
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pr-8 sm:pr-10">
                                    <div className="space-y-1.5">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            {/* Previous & Next Tutorial Navigation */}
                                            <div className="flex items-center gap-1">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    disabled={!prevTutorial}
                                                    onClick={() => prevTutorial && openTutorialModal(prevTutorial.id)}
                                                    className="h-7 px-2 text-xs font-semibold gap-1 text-muted-foreground hover:text-foreground cursor-pointer disabled:opacity-30 disabled:pointer-events-none"
                                                    title={prevTutorial ? `Back to Tutorial ${prevTutorial.number}: ${prevTutorial.title}` : "First tutorial"}
                                                >
                                                    <ChevronLeft className="h-3.5 w-3.5" />
                                                    <span>Prev</span>
                                                </Button>

                                                <Badge variant="outline" className="text-xs font-semibold bg-primary/10 text-primary border-primary/25">
                                                    Tutorial {tutorialDetail.tutorialNumber}
                                                </Badge>

                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    disabled={!nextTutorial}
                                                    onClick={() => nextTutorial && openTutorialModal(nextTutorial.id)}
                                                    className="h-7 px-2 text-xs font-semibold gap-1 text-muted-foreground hover:text-foreground cursor-pointer disabled:opacity-30 disabled:pointer-events-none"
                                                    title={nextTutorial ? `Next to Tutorial ${nextTutorial.number}: ${nextTutorial.title}` : "Last tutorial"}
                                                >
                                                    <span>Next</span>
                                                    <ChevronRight className="h-3.5 w-3.5" />
                                                </Button>
                                            </div>

                                            <span className="text-xs text-muted-foreground font-medium hidden sm:inline">
                                                • Week {tutorialDetail.content?.weekNumber || 1} • {getWeekTitle(tutorialDetail.content?.weekNumber || 1, overview?.courseId)?.split(':')[1]?.trim() || tutorialDetail.title}
                                            </span>
                                        </div>
                                        <DialogTitle className="text-xl sm:text-2xl font-bold tracking-tight text-foreground font-sans">
                                            {tutorialDetail.title}
                                        </DialogTitle>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="flex items-center gap-1.5 font-sans text-xs text-amber-600 dark:text-amber-400 font-semibold bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-full shrink-0">
                                            <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                                            <span>+25 XP Total</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Modern Step Navigation Tabs: Video First! */}
                                <div id="tutorial-tab-bar" className="flex items-center gap-1.5 mt-4 p-1 rounded-xl bg-muted/60 border border-border/60 overflow-x-auto no-scrollbar shadow-inner scroll-smooth">
                                    <button
                                        id="tab-btn-video"
                                        onClick={() => switchTab('video')}
                                        className={cn(
                                            "flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer",
                                            activeTab === 'video'
                                                ? "bg-primary text-primary-foreground shadow-sm shadow-primary/25"
                                                : "text-muted-foreground hover:text-foreground hover:bg-background/60 font-medium"
                                        )}
                                    >
                                        <PlayCircle className={cn("h-4 w-4", activeTab === 'video' ? "text-primary-foreground" : "text-muted-foreground")} />
                                        <span>1. Watch Video</span>
                                        {tutorialDetail.userTutorial.watched === 'yes' && (
                                            <span className={cn(
                                                "size-4 rounded-full flex items-center justify-center text-[10px] font-bold",
                                                activeTab === 'video'
                                                    ? "bg-primary-foreground/20 text-primary-foreground"
                                                    : "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                                            )}>✓</span>
                                        )}
                                    </button>
                                    <button
                                        id="tab-btn-reading"
                                        onClick={() => switchTab('reading')}
                                        className={cn(
                                            "flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer",
                                            activeTab === 'reading'
                                                ? "bg-primary text-primary-foreground shadow-sm shadow-primary/25"
                                                : "text-muted-foreground hover:text-foreground hover:bg-background/60 font-medium"
                                        )}
                                    >
                                        <BookOpen className={cn("h-4 w-4", activeTab === 'reading' ? "text-primary-foreground" : "text-muted-foreground")} />
                                        <span>2. Reading Notes</span>
                                        {tutorialDetail.userTutorial.watched === 'yes' && (
                                            <span className={cn(
                                                "size-4 rounded-full flex items-center justify-center text-[10px] font-bold",
                                                activeTab === 'reading'
                                                    ? "bg-primary-foreground/20 text-primary-foreground"
                                                    : "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                                            )}>✓</span>
                                        )}
                                    </button>
                                    <button
                                        id="tab-btn-activity"
                                        onClick={() => switchTab('activity')}
                                        className={cn(
                                            "flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer",
                                            activeTab === 'activity'
                                                ? "bg-primary text-primary-foreground shadow-sm shadow-primary/25"
                                                : "text-muted-foreground hover:text-foreground hover:bg-background/60 font-medium"
                                        )}
                                    >
                                        {isLinux ? (
                                            isSetupTutorial ? (
                                                <UploadCloud className={cn("h-4 w-4", activeTab === 'activity' ? "text-primary-foreground" : "text-muted-foreground")} />
                                            ) : (
                                                <Terminal className={cn("h-4 w-4", activeTab === 'activity' ? "text-primary-foreground" : "text-muted-foreground")} />
                                            )
                                        ) : (
                                            <PenTool className={cn("h-4 w-4", activeTab === 'activity' ? "text-primary-foreground" : "text-muted-foreground")} />
                                        )}
                                        <span>
                                            {isLinux
                                                ? (isSetupTutorial ? '3. Setup Verification' : '3. Terminal Lab')
                                                : '3. Activity & Reflection'}
                                        </span>
                                        {(tutorialDetail.userReflection || tutorialDetail.userTutorial.assignmentDone === 'yes' || tutorialDetail.userTutorial.minitaskOpted === 'yes') && (
                                            <span className={cn(
                                                "size-4 rounded-full flex items-center justify-center text-[10px] font-bold",
                                                activeTab === 'activity'
                                                    ? "bg-primary-foreground/20 text-primary-foreground"
                                                    : "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                                            )}>✓</span>
                                        )}
                                    </button>
                                    {(tutorialDetail.assignmentInstructions || tutorialDetail.assignmentUrl) && (
                                        <button
                                            id="tab-btn-assignment"
                                            onClick={() => switchTab('assignment')}
                                            className={cn(
                                                "flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer",
                                                activeTab === 'assignment'
                                                    ? "bg-primary text-primary-foreground shadow-sm shadow-primary/25"
                                                    : "text-muted-foreground hover:text-foreground hover:bg-background/60 font-medium"
                                            )}
                                        >
                                            <FileText className={cn("h-4 w-4", activeTab === 'assignment' ? "text-primary-foreground" : "text-muted-foreground")} />
                                            <span>4. Assignment</span>
                                            {(tutorialDetail.userTutorial.assignmentDone === 'yes' || (tutorialDetail.userTutorial.assignmentDone as any) === true) && (
                                                <span className={cn(
                                                    "size-4 rounded-full flex items-center justify-center text-[10px] font-bold",
                                                    activeTab === 'assignment'
                                                        ? "bg-primary-foreground/20 text-primary-foreground"
                                                        : "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                                                )}>✓</span>
                                            )}
                                        </button>
                                    )}
                                    {tutorialDetail.quiz.questions && tutorialDetail.quiz.questions.length > 0 ? (
                                        <button
                                            id="tab-btn-quiz"
                                            onClick={() => switchTab('quiz')}
                                            className={cn(
                                                "flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer",
                                                activeTab === 'quiz'
                                                    ? "bg-primary text-primary-foreground shadow-sm shadow-primary/25"
                                                    : "text-muted-foreground hover:text-foreground hover:bg-background/60 font-medium"
                                            )}
                                        >
                                            <HelpCircle className={cn("h-4 w-4", activeTab === 'quiz' ? "text-primary-foreground" : "text-muted-foreground")} />
                                            <span>{(tutorialDetail.assignmentInstructions || tutorialDetail.assignmentUrl) ? '5. Quiz (5 MCQs)' : '4. Quiz (5 MCQs)'}</span>
                                            {tutorialDetail.quiz.hasAttempted && (
                                                <span className={cn(
                                                    "size-4 rounded-full flex items-center justify-center text-[10px] font-bold",
                                                    activeTab === 'quiz'
                                                        ? "bg-primary-foreground/20 text-primary-foreground"
                                                        : ((tutorialDetail.quiz.score ?? 0) >= 3) ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400' : 'bg-amber-500/20 text-amber-600'
                                                )}>✓</span>
                                            )}
                                        </button>
                                    ) : (
                                        <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 shrink-0">
                                            <CheckCircle2 className="h-3.5 w-3.5" />
                                            <span>Setup Verified (No Quiz)</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Modal Body / Tab Content */}
                            {/* TAB 1: VIDEO (FIRST) */}
                            {activeTab === 'video' && (
                                <div id="tutorial-modal-body" className="flex-1 overflow-y-auto p-4 sm:p-8 flex flex-col items-center bg-background/50 min-h-0">
                                    <div className="w-full max-w-4xl space-y-4 my-auto">
                                        {tutorialDetail.videoUrl ? (
                                            <div className="space-y-4">
                                                <div className="relative aspect-video w-full rounded-2xl bg-black border border-border/80 overflow-hidden shadow-2xl flex items-center justify-center">
                                                    <video
                                                        key={tutorialDetail.videoUrl}
                                                        controls
                                                        playsInline
                                                        preload="auto"
                                                        poster={tutorialDetail.videoPosterUrl || undefined}
                                                        className="w-full h-full object-contain"
                                                        onWaiting={() => setIsVideoBuffering(true)}
                                                        onPlaying={() => setIsVideoBuffering(false)}
                                                        onCanPlay={() => setIsVideoBuffering(false)}
                                                        onTimeUpdate={(e) => {
                                                            const v = e.currentTarget
                                                            if (v.duration > 0) {
                                                                const pct = Math.round((v.currentTime / v.duration) * 100)
                                                                setVideoWatchPercent(prev => {
                                                                    const highest = Math.max(prev, pct)
                                                                    if (highest >= 80 && tutorialDetail.userTutorial.watched !== 'yes') {
                                                                        handleMarkVideoWatched()
                                                                    }
                                                                    return highest
                                                                })
                                                            }
                                                        }}
                                                        onEnded={handleVideoEnded}
                                                    >
                                                        <source src={tutorialDetail.videoUrl} type="video/webm" />
                                                        {tutorialDetail.videoUrl && tutorialDetail.videoUrl.endsWith('-English.webm') && (
                                                            <source src={tutorialDetail.videoUrl.replace('-English.webm', '-English-sample.webm')} type="video/webm" />
                                                        )}
                                                        Your browser does not support WebM video streaming.
                                                    </video>
                                                </div>

                                                <div className="flex items-center justify-between gap-3 p-3 sm:p-4 rounded-xl bg-card border border-border/80 shadow-xs">
                                                    <div>
                                                        {tutorialDetail.userTutorial.watched === 'yes' ? (
                                                            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-600 dark:text-emerald-400 text-xs font-semibold shadow-2xs">
                                                                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                                                                <span>Watched (+10 XP)</span>
                                                            </div>
                                                        ) : isVideoBuffering ? (
                                                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/25 text-xs font-medium text-amber-600 dark:text-amber-400 shadow-2xs">
                                                                <Loader2 className="size-3.5 animate-spin" />
                                                                <span>Buffering stream... {videoWatchPercent > 0 ? `(${videoWatchPercent}%)` : ''}</span>
                                                            </div>
                                                        ) : (
                                                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-muted/60 border border-border/80 text-xs font-medium text-muted-foreground shadow-2xs">
                                                                <div className="size-2 rounded-full bg-primary animate-pulse" />
                                                                <span>Watched: {videoWatchPercent}%</span>
                                                            </div>
                                                        )}
                                                    </div>

                                                    <div className="flex items-center gap-2 ml-auto">
                                                        <Button
                                                            onClick={() => switchTab('reading')}
                                                            className="text-xs font-bold gap-1.5 shadow-2xs hover:shadow-xs cursor-pointer"
                                                        >
                                                            <span>Next: Reading Notes</span>
                                                            <ArrowRight className="h-4 w-4" />
                                                        </Button>
                                                    </div>
                                                </div>

                                                {/* Companion Resource Sub-Tabs Directly Under Video */}
                                                {(tutorialDetail.codeFilesUrl || tutorialDetail.instructionSheetUrl || tutorialDetail.installationSheetUrl) && (
                                                    <div className="space-y-4 pt-1">
                                                        {/* Sub-tab segmented pill bar */}
                                                        <div className="flex items-center justify-between gap-2 p-1.5 rounded-2xl bg-card border border-border/80 shadow-2xs">
                                                            <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
                                                                <button
                                                                    type="button"
                                                                    onClick={() => setVideoSubTab('stream')}
                                                                    className={cn(
                                                                        "flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all shrink-0 cursor-pointer",
                                                                        videoSubTab === 'stream'
                                                                            ? "bg-primary text-primary-foreground shadow-xs"
                                                                            : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                                                                    )}
                                                                >
                                                                    <PlayCircle className="h-3.5 w-3.5" />
                                                                    <span>Video Overview</span>
                                                                </button>
                                                                {tutorialDetail.codeFilesUrl && (
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => setVideoSubTab('code')}
                                                                        className={cn(
                                                                            "flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all shrink-0 cursor-pointer",
                                                                            videoSubTab === 'code'
                                                                                ? "bg-amber-600 text-white shadow-xs dark:bg-amber-500"
                                                                                : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                                                                        )}
                                                                    >
                                                                        <FolderArchive className="h-3.5 w-3.5" />
                                                                        <span>Course Files (.zip)</span>
                                                                    </button>
                                                                )}
                                                                {tutorialDetail.instructionSheetUrl && (
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => setVideoSubTab('instruction')}
                                                                        className={cn(
                                                                            "flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all shrink-0 cursor-pointer",
                                                                            videoSubTab === 'instruction'
                                                                                ? "bg-blue-600 text-white shadow-xs dark:bg-blue-500"
                                                                                : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                                                                        )}
                                                                    >
                                                                        <FileText className="h-3.5 w-3.5" />
                                                                        <span>Instruction Sheet (.pdf)</span>
                                                                    </button>
                                                                )}
                                                                {tutorialDetail.installationSheetUrl && (
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => setVideoSubTab('installation')}
                                                                        className={cn(
                                                                            "flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all shrink-0 cursor-pointer",
                                                                            videoSubTab === 'installation'
                                                                                ? "bg-emerald-600 text-white shadow-xs dark:bg-emerald-500"
                                                                                : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                                                                        )}
                                                                    >
                                                                        <Wrench className="h-3.5 w-3.5" />
                                                                        <span>Installation Sheet (.pdf)</span>
                                                                    </button>
                                                                )}
                                                            </div>
                                                        </div>

                                                        {/* Sub-tab 1: Stream overview info */}
                                                        {videoSubTab === 'stream' && (
                                                            <div className="p-4 sm:p-5 rounded-2xl bg-card border border-border/80 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                                                                <div className="space-y-1">
                                                                    <h4 className="text-sm font-bold text-foreground">Interactive Audiovisual Tutorial</h4>
                                                                    <p className="text-xs text-muted-foreground leading-relaxed">
                                                                        Follow along with the terminal demonstration. You can download companion code files and view the official instruction & installation sheets using the sub-tabs above.
                                                                    </p>
                                                                </div>
                                                                <div className="flex items-center gap-2 shrink-0">
                                                                    <a
                                                                        href="https://spoken-tutorial.org"
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-border/80 bg-background hover:bg-muted text-xs font-semibold text-foreground transition-all shadow-2xs"
                                                                    >
                                                                        <span>Spoken Tutorial Library</span>
                                                                        <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
                                                                    </a>
                                                                </div>
                                                            </div>
                                                        )}

                                                        {/* Sub-tab 2: Course Code Files (.zip) */}
                                                        {videoSubTab === 'code' && tutorialDetail.codeFilesUrl && (
                                                            <div className="p-4 sm:p-5 rounded-2xl bg-card border border-border/80 shadow-xs space-y-4 animate-in fade-in-50 duration-200">
                                                                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-border/60">
                                                                    <div className="space-y-0.5">
                                                                        <div className="flex items-center gap-2">
                                                                            <FolderArchive className="h-4 w-4 text-amber-500" />
                                                                            <h4 className="text-sm font-bold text-foreground">Companion Course Files</h4>
                                                                            <Badge variant="outline" className="text-[10px] font-mono">.zip archive</Badge>
                                                                        </div>
                                                                        <p className="text-xs text-muted-foreground">
                                                                            Sample datasets, test text files, and demonstration scripts for hands-on terminal commands.
                                                                        </p>
                                                                    </div>
                                                                    <a
                                                                        href={tutorialDetail.codeFilesUrl}
                                                                        download
                                                                        className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-all shadow-2xs shrink-0 cursor-pointer"
                                                                    >
                                                                        <Download className="h-3.5 w-3.5" />
                                                                        <span>Download All Files (.zip)</span>
                                                                    </a>
                                                                </div>

                                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                                                                    <div className="p-2.5 rounded-xl bg-muted/40 border border-border/50 flex items-start gap-2">
                                                                        <FileText className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                                                                        <div>
                                                                            <div className="font-semibold text-foreground font-mono">students.txt</div>
                                                                            <div className="text-[11px] text-muted-foreground">Pipe-delimited student records for filtering, sorting & capstone.</div>
                                                                        </div>
                                                                    </div>
                                                                    <div className="p-2.5 rounded-xl bg-muted/40 border border-border/50 flex items-start gap-2">
                                                                        <FileText className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                                                                        <div>
                                                                            <div className="font-semibold text-foreground font-mono">numbers.txt</div>
                                                                            <div className="text-[11px] text-muted-foreground">Unsorted numbers for numeric sort & unique deduplication.</div>
                                                                        </div>
                                                                    </div>
                                                                    <div className="p-2.5 rounded-xl bg-muted/40 border border-border/50 flex items-start gap-2">
                                                                        <FileText className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                                                                        <div>
                                                                            <div className="font-semibold text-foreground font-mono">grepdemo.txt</div>
                                                                            <div className="text-[11px] text-muted-foreground">Pattern matching dataset for <code className="font-mono text-primary font-bold">grep</code> tutorials.</div>
                                                                        </div>
                                                                    </div>
                                                                    <div className="p-2.5 rounded-xl bg-muted/40 border border-border/50 flex items-start gap-2">
                                                                        <FileText className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                                                                        <div>
                                                                            <div className="font-semibold text-foreground font-mono">seddemo.txt</div>
                                                                            <div className="text-[11px] text-muted-foreground">Stream editing sample text for <code className="font-mono text-primary font-bold">sed</code> tutorials.</div>
                                                                        </div>
                                                                    </div>
                                                                </div>

                                                                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-muted/60 border border-border/70 text-[11px] text-muted-foreground font-mono">
                                                                    <Terminal className="h-3.5 w-3.5 text-primary shrink-0" />
                                                                    <span>Unpack in terminal: <strong className="text-foreground">unzip linux-companion-files.zip -d ~/practice</strong></span>
                                                                </div>
                                                            </div>
                                                        )}

                                                        {/* Sub-tab 3: Instruction Sheet (.pdf) */}
                                                        {videoSubTab === 'instruction' && tutorialDetail.instructionSheetUrl && (
                                                            <div className="p-4 sm:p-5 rounded-2xl bg-card border border-border/80 shadow-xs space-y-4 animate-in fade-in-50 duration-200">
                                                                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-border/60">
                                                                    <div className="space-y-0.5">
                                                                        <div className="flex items-center gap-2">
                                                                            <FileText className="h-4 w-4 text-blue-500" />
                                                                            <h4 className="text-sm font-bold text-foreground">Official Instruction Sheet</h4>
                                                                            <Badge variant="outline" className="text-[10px] font-mono">PDF Document</Badge>
                                                                        </div>
                                                                        <p className="text-xs text-muted-foreground">
                                                                            Official Spoken Tutorial command reference and lab guidelines from IIT Bombay.
                                                                        </p>
                                                                    </div>
                                                                    <div className="flex items-center gap-2 shrink-0">
                                                                        <a
                                                                            href={tutorialDetail.instructionSheetUrl}
                                                                            target="_blank"
                                                                            rel="noopener noreferrer"
                                                                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-border/80 bg-background hover:bg-muted text-xs font-semibold text-foreground transition-all shadow-2xs"
                                                                        >
                                                                            <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
                                                                            <span>Open in New Tab</span>
                                                                        </a>
                                                                        <a
                                                                            href={tutorialDetail.instructionSheetUrl}
                                                                            download
                                                                            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-all shadow-2xs"
                                                                        >
                                                                            <Download className="h-3.5 w-3.5" />
                                                                            <span>Download PDF</span>
                                                                        </a>
                                                                    </div>
                                                                </div>
                                                                <div className="w-full h-[520px] rounded-xl overflow-hidden border border-border/70 bg-muted/20">
                                                                    <iframe
                                                                        src={`${tutorialDetail.instructionSheetUrl}#toolbar=0`}
                                                                        className="w-full h-full border-0"
                                                                        title="Instruction Sheet PDF Preview"
                                                                    />
                                                                </div>
                                                            </div>
                                                        )}

                                                        {/* Sub-tab 4: Installation Sheet (.pdf) */}
                                                        {videoSubTab === 'installation' && tutorialDetail.installationSheetUrl && (
                                                            <div className="p-4 sm:p-5 rounded-2xl bg-card border border-border/80 shadow-xs space-y-4 animate-in fade-in-50 duration-200">
                                                                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-border/60">
                                                                    <div className="space-y-0.5">
                                                                        <div className="flex items-center gap-2">
                                                                            <Wrench className="h-4 w-4 text-emerald-500" />
                                                                            <h4 className="text-sm font-bold text-foreground">Ubuntu & VirtualBox Installation Sheet</h4>
                                                                            <Badge variant="outline" className="text-[10px] font-mono">PDF Document</Badge>
                                                                        </div>
                                                                        <p className="text-xs text-muted-foreground">
                                                                            Step-by-step installation instructions for VirtualBox and Ubuntu Linux 24.04 LTS.
                                                                        </p>
                                                                    </div>
                                                                    <div className="flex items-center gap-2 shrink-0">
                                                                        <a
                                                                            href={tutorialDetail.installationSheetUrl}
                                                                            target="_blank"
                                                                            rel="noopener noreferrer"
                                                                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-border/80 bg-background hover:bg-muted text-xs font-semibold text-foreground transition-all shadow-2xs"
                                                                        >
                                                                            <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
                                                                            <span>Open in New Tab</span>
                                                                        </a>
                                                                        <a
                                                                            href={tutorialDetail.installationSheetUrl}
                                                                            download
                                                                            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-all shadow-2xs"
                                                                        >
                                                                            <Download className="h-3.5 w-3.5" />
                                                                            <span>Download PDF</span>
                                                                        </a>
                                                                    </div>
                                                                </div>
                                                                <div className="w-full h-[520px] rounded-xl overflow-hidden border border-border/70 bg-muted/20">
                                                                    <iframe
                                                                        src={`${tutorialDetail.installationSheetUrl}#toolbar=0`}
                                                                        className="w-full h-full border-0"
                                                                        title="Installation Sheet PDF Preview"
                                                                    />
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        ) : (
                                            <div className="max-w-lg mx-auto text-center space-y-5 p-8 rounded-2xl bg-card border shadow-sm">
                                                <div className="h-16 w-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto shadow-2xs">
                                                    <PlayCircle className="h-9 w-9" />
                                                </div>
                                                <div className="space-y-2">
                                                    <h3 className="text-xl font-bold text-foreground">
                                                        Spoken Tutorial Audiovisual Video
                                                    </h3>
                                                    <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                                                        This tutorial is accompanied by an audiovisual Spoken Tutorial. You can watch it in English or dubbed into Indian regional languages (Hindi, Marathi, Tamil, Telugu, and more).
                                                    </p>
                                                </div>
                                                <div className="pt-3 flex flex-col sm:flex-row justify-center gap-3">
                                                    <a
                                                        href="https://spoken-tutorial.org"
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs sm:text-sm font-semibold hover:bg-primary/90 transition-colors shadow-2xs"
                                                    >
                                                        Open Spoken Tutorial Player
                                                        <ExternalLink className="h-4 w-4" />
                                                    </a>
                                                    <Button
                                                        variant="outline"
                                                        onClick={handleMarkVideoWatched}
                                                        disabled={tutorialDetail.userTutorial.watched === 'yes'}
                                                        className="text-xs"
                                                    >
                                                        {tutorialDetail.userTutorial.watched === 'yes' ? '✓ Watched' : 'Mark as Watched (+10 XP)'}
                                                    </Button>
                                                </div>
                                                <div className="pt-2">
                                                    <Button
                                                        variant="ghost"
                                                        onClick={() => setActiveTab('reading')}
                                                        className="text-xs font-semibold gap-1"
                                                    >
                                                        <span>Continue to Reading Notes</span>
                                                        <ArrowRight className="h-3.5 w-3.5" />
                                                    </Button>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* TAB 2: READING — Full Width Clean Reader Canvas */}
                            {activeTab === 'reading' && (
                                <div id="tutorial-modal-body" className="flex-1 overflow-y-auto px-4 py-6 sm:px-10 sm:py-10 bg-background/50 min-h-0">
                                    <div className="max-w-3xl mx-auto space-y-8">
                                        <div className="prose prose-slate dark:prose-invert max-w-none text-foreground/90 font-sans leading-relaxed text-sm sm:text-base space-y-5">
                                            <ReactMarkdown
                                                remarkPlugins={[remarkGfm]}
                                                components={{
                                                    h1: ({ ...props }) => <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground border-b pb-3 mt-8 mb-4 font-sans" {...props} />,
                                                    h2: ({ ...props }) => <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground border-b pb-2.5 mt-8 mb-4 text-primary font-sans" {...props} />,
                                                    h3: ({ ...props }) => <h3 className="text-lg sm:text-xl font-bold text-foreground mt-6 mb-3 font-sans" {...props} />,
                                                    h4: ({ ...props }) => <h4 className="text-base sm:text-lg font-semibold text-foreground/90 mt-5 mb-2 font-sans" {...props} />,
                                                    p: ({ ...props }) => <p className="leading-relaxed mb-4 text-foreground/90 text-sm sm:text-base font-sans" {...props} />,
                                                    ul: ({ ...props }) => <ul className="list-disc pl-6 mb-4 space-y-2 text-sm sm:text-base text-foreground/90" {...props} />,
                                                    ol: ({ ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-sm sm:text-base text-foreground/90" {...props} />,
                                                    li: ({ ...props }) => <li className="leading-relaxed" {...props} />,
                                                    blockquote: ({ ...props }) => <blockquote className="border-l-4 border-primary/60 pl-4 py-3 my-5 italic bg-primary/5 rounded-r-xl text-foreground/90 text-sm sm:text-base shadow-2xs font-sans" {...props} />,
                                                    table: ({ ...props }) => <div className="my-6 overflow-x-auto rounded-xl border border-border/80 shadow-2xs"><table className="w-full border-collapse text-left" {...props} /></div>,
                                                    thead: ({ ...props }) => <thead className="bg-muted/80 text-foreground text-xs sm:text-sm font-semibold border-b border-border/80" {...props} />,
                                                    th: ({ ...props }) => <th className="px-4 py-3 text-left font-bold border-r border-border/40 last:border-r-0" {...props} />,
                                                    td: ({ ...props }) => <td className="px-4 py-3 text-xs sm:text-sm text-foreground/85 border-t border-border/40 border-r border-border/30 last:border-r-0" {...props} />,
                                                    hr: ({ ...props }) => <hr className="my-8 border-border/60" {...props} />,
                                                    strong: ({ ...props }) => <strong className="font-semibold text-foreground" {...props} />,
                                                }}
                                            >
                                                {tutorialDetail.content?.readingMarkdown || ''}
                                            </ReactMarkdown>
                                        </div>

                                        {/* Completion Banner at bottom of reading */}
                                        <div className="mt-12 p-6 rounded-2xl bg-card border border-border/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
                                            <div className="space-y-1 text-center sm:text-left">
                                                <h4 className="font-bold text-foreground text-sm sm:text-base">
                                                    {tutorialDetail.userTutorial.watched === 'yes' ? 'Lesson Reading Complete' : 'Finished this reading?'}
                                                </h4>
                                                <p className="text-xs text-muted-foreground">
                                                    {tutorialDetail.userTutorial.watched === 'yes'
                                                        ? 'Core lesson completed (+10 XP earned). Move directly to the notebook activity & reflection.'
                                                        : 'Mark as read to claim +10 XP and move directly to the personal notebook exercise & reflection.'}
                                                </p>
                                            </div>
                                            <Button
                                                size="lg"
                                                onClick={async () => {
                                                    if (tutorialDetail.userTutorial.watched !== 'yes') {
                                                        await handleMarkReadingComplete()
                                                    }
                                                    switchTab('activity')
                                                }}
                                                className="font-semibold text-xs sm:text-sm shrink-0 gap-1.5 w-full sm:w-auto cursor-pointer"
                                            >
                                                {tutorialDetail.userTutorial.watched === 'yes'
                                                    ? 'Proceed to Activity & Reflection'
                                                    : 'Mark Complete (+10 XP) & Continue'}
                                                <ArrowRight className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* TAB 3: ACTIVITY / TERMINAL LAB — Dynamic by Course */}
                            {activeTab === 'activity' && (() => {
                                const rawTryIt = tutorialDetail.content?.tryItInstructions || ''
                                const stepRegex = /(?:\*\*Step\s+\d+:\*\*|\b\d+\.\s+)/
                                const tryItParts = rawTryIt.split(stepRegex).map(s => s.trim()).filter(Boolean)
                                const tryItIntro = tryItParts.length > 1 ? tryItParts[0] : ''
                                const tryItSteps = tryItParts.length > 1 ? tryItParts.slice(1) : (rawTryIt ? [rawTryIt] : [])

                                // LINUX SETUP LAB: Tutorials 1 & 2 Screenshot Verification
                                if (isLinux && isSetupTutorial) {
                                    return (
                                        <div id="tutorial-modal-body" className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-muted/10 min-h-0">
                                            <div className="max-w-4xl mx-auto space-y-6">
                                                {/* Header Banner */}
                                                <div className="p-5 sm:p-6 rounded-2xl bg-gradient-to-r from-blue-600/10 via-primary/5 to-emerald-600/10 border border-border/80 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                                    <div className="space-y-1">
                                                        <div className="flex items-center gap-2">
                                                            <Badge variant="outline" className="text-[11px] font-mono font-bold px-2.5 py-0.5 bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30">
                                                                🛠️ LAB ENVIRONMENT SETUP
                                                            </Badge>
                                                            <span className="text-xs text-muted-foreground font-semibold">
                                                                Tutorial {tutorialDetail.tutorialNumber}
                                                            </span>
                                                        </div>
                                                        <h2 className="text-lg sm:text-xl font-bold text-foreground">
                                                            {tutorialDetail.title}
                                                        </h2>
                                                        <p className="text-xs text-muted-foreground">
                                                            Set up your virtual machine locally. Submit a verification screenshot to complete this milestone and unlock subsequent hands-on tutorials.
                                                        </p>
                                                    </div>
                                                    <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-1.5 shrink-0 bg-background/80 p-3 rounded-xl border border-border/60">
                                                        <span className="text-[11px] text-muted-foreground font-medium">Completion Award</span>
                                                        <Badge className="bg-emerald-600 text-white font-bold text-xs px-3 py-1">+15 XP</Badge>
                                                    </div>
                                                </div>

                                                {/* 3 Step Flow Cards */}
                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                                                    <div className="p-4 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1.5">
                                                        <div className="flex items-center gap-2">
                                                            <span className="size-6 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center">1</span>
                                                            <span className="text-xs font-bold text-foreground">Prepare & Install</span>
                                                        </div>
                                                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                                                            {tutorialDetail.tutorialNumber === 1
                                                                ? 'Check CPU virtualization in Task Manager, then download and install VirtualBox.'
                                                                : 'Download Ubuntu 24.04 ISO, create a VirtualBox VM, and boot the installer.'}
                                                        </p>
                                                    </div>
                                                    <div className="p-4 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1.5">
                                                        <div className="flex items-center gap-2">
                                                            <span className="size-6 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center">2</span>
                                                            <span className="text-xs font-bold text-foreground">Open Verification View</span>
                                                        </div>
                                                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                                                            {tutorialDetail.tutorialNumber === 1
                                                                ? 'In VirtualBox Manager, open Help → About VirtualBox to show the version.'
                                                                : 'Boot into Ubuntu and open the desktop screen inside the VM window.'}
                                                        </p>
                                                    </div>
                                                    <div className="p-4 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1.5">
                                                        <div className="flex items-center gap-2">
                                                            <span className="size-6 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center">3</span>
                                                            <span className="text-xs font-bold text-foreground">Upload Proof</span>
                                                        </div>
                                                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                                                            Take a screenshot of the window and upload it below. No MCQ quiz is required for setup tutorials!
                                                        </p>
                                                    </div>
                                                </div>

                                                {/* Main Verification & Proof Area */}
                                                <div className="p-6 rounded-2xl bg-card border border-border/90 shadow-sm space-y-5">
                                                    {/* If Already Submitted */}
                                                    {tutorialDetail.userReflection?.imageUrl && !screenshotFile ? (
                                                        <div className="space-y-4">
                                                            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                                                <div className="space-y-0.5">
                                                                    <div className="flex items-center gap-2 text-sm font-bold text-emerald-700 dark:text-emerald-400">
                                                                        <CheckCircle2 className="h-4 w-4" />
                                                                        <span>Setup Screenshot Submitted & Recorded</span>
                                                                    </div>
                                                                    <p className="text-[11px] text-muted-foreground">
                                                                        Submitted on {new Date(tutorialDetail.userReflection.submittedAt).toLocaleDateString()} • Recorded in your student lab portfolio (reviewed during course evaluation)
                                                                    </p>
                                                                </div>
                                                                <Badge variant="outline" className="bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border-emerald-500/40 text-xs font-semibold px-2.5 py-1 shrink-0 self-start sm:self-auto">
                                                                    ✓ Milestone Complete (+15 XP)
                                                                </Badge>
                                                            </div>

                                                            {/* Screenshot Preview with clean framing and full-size link */}
                                                            <div className="rounded-xl overflow-hidden border border-border/80 bg-slate-950/5 dark:bg-black/30 p-3 text-center space-y-2">
                                                                <a
                                                                    href={resolveMediaUrl(tutorialDetail.userReflection.imageUrl)}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="block group relative"
                                                                    title="Click to view full image in new tab"
                                                                >
                                                                    <img
                                                                        src={resolveMediaUrl(tutorialDetail.userReflection.imageUrl)}
                                                                        alt="Setup Verification Screenshot"
                                                                        className="max-h-80 mx-auto rounded-lg object-contain shadow-xs group-hover:opacity-95 transition-opacity"
                                                                    />
                                                                    <div className="absolute bottom-2 right-2 px-2.5 py-1 rounded-md bg-black/70 text-white text-[10px] font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                        <ExternalLink className="h-3 w-3" />
                                                                        <span>Open full size</span>
                                                                    </div>
                                                                </a>
                                                                {tutorialDetail.userReflection.reflectionText && (
                                                                    <p className="text-xs text-muted-foreground pt-1 italic font-sans">
                                                                        "{tutorialDetail.userReflection.reflectionText}"
                                                                    </p>
                                                                )}
                                                            </div>

                                                            {/* Footer Actions */}
                                                            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t">
                                                                <label className="text-xs font-semibold text-muted-foreground hover:text-foreground flex items-center gap-1.5 cursor-pointer">
                                                                    <UploadCloud className="h-4 w-4" />
                                                                    <span>Replace with another screenshot</span>
                                                                    <input
                                                                        type="file"
                                                                        accept="image/png,image/jpeg,image/webp"
                                                                        className="hidden"
                                                                        onChange={(e) => {
                                                                            const file = e.target.files?.[0]
                                                                            if (file) {
                                                                                if (file.size > 5 * 1024 * 1024) {
                                                                                    toast.error('File size exceeds 5 MB limit.')
                                                                                    return
                                                                                }
                                                                                setScreenshotFile(file)
                                                                                setScreenshotPreview(URL.createObjectURL(file))
                                                                            }
                                                                        }}
                                                                    />
                                                                </label>
                                                                {nextTutorial && (
                                                                    <Button
                                                                        onClick={() => openTutorialModal(nextTutorial.id)}
                                                                        className="font-semibold text-xs gap-1.5 w-full sm:w-auto cursor-pointer"
                                                                    >
                                                                        <span>Proceed to Tutorial {nextTutorial.number}: {nextTutorial.title}</span>
                                                                        <ArrowRight className="h-3.5 w-3.5" />
                                                                    </Button>
                                                                )}
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        /* If Not Yet Submitted or Re-uploading */
                                                        <div className="space-y-4">
                                                            <div className="flex items-center justify-between border-b pb-3">
                                                                <div>
                                                                    <h3 className="text-sm font-bold text-foreground">Upload Proof of Installation</h3>
                                                                    <p className="text-xs text-muted-foreground">
                                                                        {tutorialDetail.tutorialNumber === 1
                                                                            ? 'Screenshot of VirtualBox Manager with Help → About window open showing installed version.'
                                                                            : 'Screenshot of Ubuntu 24.04 desktop running inside your Oracle VirtualBox window.'}
                                                                    </p>
                                                                </div>
                                                                <Badge className="bg-emerald-600 text-white font-semibold text-xs">+15 XP</Badge>
                                                            </div>

                                                            {/* Modern Upload Dropzone */}
                                                            <label className={cn(
                                                                "border-2 border-dashed rounded-2xl p-6 sm:p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all",
                                                                screenshotPreview
                                                                    ? "border-primary/50 bg-primary/5"
                                                                    : "border-border/80 hover:border-primary/60 hover:bg-muted/40"
                                                            )}>
                                                                <input
                                                                    type="file"
                                                                    accept="image/png,image/jpeg,image/webp"
                                                                    className="hidden"
                                                                    onChange={(e) => {
                                                                        const file = e.target.files?.[0]
                                                                        if (file) {
                                                                            if (file.size > 5 * 1024 * 1024) {
                                                                                toast.error('File size exceeds 5 MB limit.')
                                                                                return
                                                                            }
                                                                            setScreenshotFile(file)
                                                                            setScreenshotPreview(URL.createObjectURL(file))
                                                                        }
                                                                    }}
                                                                />
                                                                {screenshotPreview ? (
                                                                    <div className="space-y-3">
                                                                        <img
                                                                            src={screenshotPreview}
                                                                            alt="Preview"
                                                                            className="max-h-64 mx-auto rounded-xl object-contain shadow-xs border"
                                                                        />
                                                                        <div className="text-xs text-foreground font-semibold flex items-center justify-center gap-2">
                                                                            <span>{screenshotFile?.name}</span>
                                                                            <Badge variant="outline" className="text-[10px]">
                                                                                {screenshotFile ? (screenshotFile.size / 1024).toFixed(0) + ' KB' : ''}
                                                                            </Badge>
                                                                        </div>
                                                                        <span className="text-[11px] text-primary hover:underline">Click to choose a different image</span>
                                                                    </div>
                                                                ) : (
                                                                    <div className="space-y-2.5">
                                                                        <div className="size-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto shadow-2xs">
                                                                            <UploadCloud className="h-7 w-7" />
                                                                        </div>
                                                                        <div className="text-sm font-semibold text-foreground">
                                                                            Click to select screenshot or drag and drop here
                                                                        </div>
                                                                        <p className="text-xs text-muted-foreground">
                                                                            Supports PNG, JPG, or WEBP (Maximum size: 5 MB)
                                                                        </p>
                                                                    </div>
                                                                )}
                                                            </label>

                                                            <div className="space-y-1.5">
                                                                <label className="text-xs font-semibold text-muted-foreground">
                                                                    Setup Notes / Machine Details (Optional)
                                                                </label>
                                                                <input
                                                                    type="text"
                                                                    value={screenshotNotes}
                                                                    onChange={(e) => setScreenshotNotes(e.target.value)}
                                                                    placeholder="e.g. Windows 11 64-bit, VirtualBox 7.0 installed smoothly"
                                                                    className="w-full text-xs p-2.5 rounded-xl border bg-background text-foreground"
                                                                />
                                                            </div>

                                                            <div className="flex items-center justify-between pt-2">
                                                                {screenshotFile && (
                                                                    <Button
                                                                        type="button"
                                                                        variant="ghost"
                                                                        size="sm"
                                                                        onClick={() => {
                                                                            setScreenshotFile(null)
                                                                            setScreenshotPreview(tutorialDetail.userReflection?.imageUrl || null)
                                                                        }}
                                                                        className="text-xs text-muted-foreground cursor-pointer"
                                                                    >
                                                                        Cancel
                                                                    </Button>
                                                                )}
                                                                <Button
                                                                    onClick={handleScreenshotUpload}
                                                                    disabled={!screenshotFile || isSubmittingLab}
                                                                    className="font-semibold text-xs ml-auto gap-2 cursor-pointer"
                                                                >
                                                                    {isSubmittingLab ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <UploadCloud className="h-3.5 w-3.5" />}
                                                                    <span>{isSubmittingLab ? 'Uploading...' : 'Submit Setup Screenshot (+15 XP)'}</span>
                                                                </Button>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    )
                                }

                                // LINUX TERMINAL LAB: Tutorials 3 to 20
                                if (isLinux && !isSetupTutorial) {
                                    const charCount = terminalOutput.length
                                    const isOverLimit = charCount > 20000

                                    return (
                                        <div id="tutorial-modal-body" className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-muted/10 min-h-0">
                                            <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
                                                {/* Left Column: Command Instructions */}
                                                <div className="lg:col-span-5 space-y-4">
                                                    <div className="flex items-center gap-2.5">
                                                        <div className="p-2.5 rounded-xl bg-slate-900 text-emerald-400 border border-emerald-500/30">
                                                            <Terminal className="h-5 w-5" />
                                                        </div>
                                                        <div>
                                                            <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-muted-foreground">Lab Task</span>
                                                            <h3 className="text-base font-bold text-foreground">Terminal Practice</h3>
                                                        </div>
                                                    </div>

                                                    {/* Security Notice */}
                                                    <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-foreground space-y-1 shadow-2xs">
                                                        <div className="flex items-center gap-2 font-bold text-amber-600 dark:text-amber-400">
                                                            <AlertCircle className="h-3.5 w-3.5" />
                                                            <span>Run in your Ubuntu Terminal</span>
                                                        </div>
                                                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                                                            Execute these commands in your Ubuntu VM. Copy and paste the commands you ran and their terminal output into the console box on the right. <strong>Never paste real passwords.</strong>
                                                        </p>
                                                    </div>

                                                    {/* Step Cards */}
                                                    <div className="space-y-2.5">
                                                        {tryItSteps.map((step, idx) => (
                                                            <div key={idx} className="p-3.5 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1">
                                                                <Badge variant="outline" className="text-[10px] font-mono font-bold px-2 py-0.5 bg-muted text-foreground">
                                                                    Step {idx + 1}
                                                                </Badge>
                                                                <p className="text-xs text-foreground/90 leading-relaxed font-mono text-[11px] pt-1 whitespace-pre-line">
                                                                    {step}
                                                                </p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Right Column: Dark Monospace Terminal Console Box */}
                                                <div className="lg:col-span-7 space-y-4">
                                                    <div className="rounded-2xl border border-slate-800 bg-slate-950 shadow-xl overflow-hidden flex flex-col">
                                                        {/* Terminal Window Header Bar */}
                                                        <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800 select-none">
                                                            <div className="flex items-center gap-2">
                                                                <span className="size-3 rounded-full bg-red-500/80 inline-block" />
                                                                <span className="size-3 rounded-full bg-amber-500/80 inline-block" />
                                                                <span className="size-3 rounded-full bg-emerald-500/80 inline-block" />
                                                                <span className="text-[11px] font-mono text-slate-400 font-semibold ml-2">
                                                                    ubuntu@spoken-tutorial: ~
                                                                </span>
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <Badge variant="outline" className="text-[10px] font-mono text-emerald-400 border-emerald-500/30 bg-emerald-500/10">
                                                                    bash 80×24
                                                                </Badge>
                                                                <Badge className="bg-emerald-600 text-white font-semibold text-[10px]">
                                                                    +10 XP
                                                                </Badge>
                                                            </div>
                                                        </div>

                                                        {/* Monospace Code Editor Area */}
                                                        <div className="p-4 bg-slate-950 flex-1 flex flex-col">
                                                            <Textarea
                                                                rows={10}
                                                                value={terminalOutput}
                                                                onChange={(e) => setTerminalOutput(e.target.value)}
                                                                placeholder={"$ type exit\nexit is a shell builtin\n$ type cp\ncp is /usr/bin/cp\n$ ls\nDesktop Documents Downloads..."}
                                                                className="w-full bg-transparent text-emerald-400 font-mono text-xs sm:text-sm leading-relaxed border-0 focus-visible:ring-0 focus-visible:ring-offset-0 resize-none p-0 selection:bg-emerald-500/30 placeholder:text-slate-600 min-h-[220px]"
                                                            />
                                                        </div>

                                                        {/* Terminal Footer Bar */}
                                                        <div className="px-4 py-3 bg-slate-900/90 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                                                            <div className="flex items-center gap-2 text-slate-400 font-mono text-[11px]">
                                                                <span className={cn(
                                                                    isOverLimit ? "text-red-400 font-bold" : charCount > 18000 ? "text-amber-400 font-bold" : "text-slate-400"
                                                                )}>
                                                                    {charCount.toLocaleString()} / 20,000 characters
                                                                </span>
                                                                {tutorialDetail.userReflection && (
                                                                    <span className="text-emerald-400 font-semibold">• ✓ Submitted</span>
                                                                )}
                                                            </div>
                                                            <div className="flex items-center gap-2 w-full sm:w-auto">
                                                                <Button
                                                                    size="sm"
                                                                    onClick={handleTerminalSubmit}
                                                                    disabled={isSubmittingLab || !terminalOutput.trim() || isOverLimit}
                                                                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs gap-1.5 flex-1 sm:flex-none cursor-pointer"
                                                                >
                                                                    {isSubmittingLab ? <Loader2 className="h-3 w-3 animate-spin" /> : <Terminal className="h-3 w-3" />}
                                                                    <span>
                                                                        {isSubmittingLab ? 'Submitting...' : tutorialDetail.userReflection ? 'Update Output' : 'Submit Commands (+10 XP)'}
                                                                    </span>
                                                                </Button>
                                                                {tutorialDetail.userReflection && (
                                                                    <Button
                                                                        size="sm"
                                                                        variant="outline"
                                                                        onClick={() => switchTab('quiz')}
                                                                        className="text-xs text-slate-200 border-slate-700 hover:bg-slate-800 gap-1 cursor-pointer"
                                                                    >
                                                                        <span>Take Quiz</span>
                                                                        <ArrowRight className="h-3 w-3" />
                                                                    </Button>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )
                                }

                                // PERSONALITY DEV: Standard Notebook & Reflection Studio
                                const rawPrompt = tutorialDetail.content?.reflectionPrompt || ''
                                const promptParts = rawPrompt.split(/(?:\n\*\s*|\n?•\s*)/).map(s => s.trim()).filter(Boolean)
                                const promptIntro = promptParts.length > 1 ? promptParts[0] : rawPrompt
                                const promptQuestions = promptParts.length > 1 ? promptParts.slice(1) : []
                                const isActivityDone = (tutorialDetail.userTutorial.minitaskOpted as any) === true || tutorialDetail.userTutorial.minitaskOpted === 'yes'

                                return (
                                    <div id="tutorial-modal-body" className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-muted/10 min-h-0">
                                        <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
                                            {/* Left Column (5 cols on lg, full width on mobile): Personal Notebook Exercise */}
                                            <div className="lg:col-span-5 space-y-4 flex flex-col justify-between">
                                                <div className="space-y-4">
                                                    <div className="flex items-center gap-2.5">
                                                        <div className="p-2.5 rounded-xl bg-muted text-foreground border border-border/70">
                                                            <PenTool className="h-5 w-5" />
                                                        </div>
                                                        <div>
                                                            <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-muted-foreground">Part 1</span>
                                                            <h3 className="text-base font-bold text-foreground">
                                                                {tutorialDetail.codeFilesUrl || tutorialDetail.assignmentUrl ? 'Hands-On Practice / Assignment' : 'Personal Notebook Exercise'}
                                                            </h3>
                                                        </div>
                                                    </div>

                                                    {/* Explicit callout: Personal notebook & No upload needed */}
                                                    <div className="p-3.5 rounded-xl bg-muted/60 border border-border/80 text-xs text-foreground/90 space-y-1.5 shadow-2xs">
                                                        <div className="flex items-center gap-2 font-bold text-foreground">
                                                            <Lock className="h-3.5 w-3.5 text-primary" />
                                                            <span>Personal Notebook • No Upload Needed</span>
                                                        </div>
                                                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                                                            This exercise is for your own personal reflection and self-growth. You <strong>do not need to upload or submit any files</strong> here. Complete the exercise in your physical notebook, diary, or notes app, then check off the exercise below.
                                                        </p>
                                                    </div>

                                                    {/* Optional Code Files Download Tile */}
                                                    {tutorialDetail.codeFilesUrl && (
                                                        <div className="p-3 rounded-xl bg-card border border-border/80 flex items-center justify-between gap-3 text-xs shadow-2xs">
                                                            <div className="flex items-center gap-2 text-foreground font-medium">
                                                                <Code2 className="h-4 w-4 text-primary" />
                                                                <span>Companion Code Files (.zip)</span>
                                                            </div>
                                                            <a
                                                                href={tutorialDetail.codeFilesUrl}
                                                                download
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="px-3 py-1.5 rounded-lg bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/90 transition-all shadow-2xs cursor-pointer"
                                                            >
                                                                Download .zip
                                                            </a>
                                                        </div>
                                                    )}

                                                    {/* Intro description */}
                                                    {tryItIntro && (
                                                        <p className="text-xs text-muted-foreground leading-relaxed bg-card p-3 rounded-xl border border-border/60">
                                                            {tryItIntro}
                                                        </p>
                                                    )}

                                                    {/* Numbered Step Cards */}
                                                    <div className="space-y-2.5">
                                                        {tryItSteps.map((step, idx) => (
                                                            <div
                                                                key={idx}
                                                                className="p-3.5 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1 hover:border-primary/40 transition-colors"
                                                            >
                                                                <div className="flex items-center gap-2">
                                                                    <Badge variant="outline" className="text-[10px] font-mono font-bold px-2 py-0.5 bg-muted text-foreground border-border/80">
                                                                        Step {idx + 1}
                                                                    </Badge>
                                                                </div>
                                                                <p className="text-xs text-foreground/90 leading-relaxed font-sans pt-1">
                                                                    {step}
                                                                </p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Interactive Completion Trigger for Private Exercise */}
                                                <div className="space-y-3 pt-2">
                                                    <div className={`p-4 rounded-xl border transition-all ${isActivityDone
                                                        ? 'bg-emerald-500/10 border-emerald-500/30 shadow-2xs'
                                                        : 'bg-card border-border hover:border-primary/40'
                                                        }`}>
                                                        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                                                            <div className="space-y-0.5">
                                                                <div className="flex items-center gap-2">
                                                                    <CheckCircle2 className={`h-4 w-4 ${isActivityDone ? 'text-emerald-600' : 'text-muted-foreground'}`} />
                                                                    <span className="text-xs font-bold text-foreground">
                                                                        {isActivityDone ? 'Completed in Notebook' : 'Mark Exercise as Done'}
                                                                    </span>
                                                                </div>
                                                                <p className="text-[11px] text-muted-foreground">
                                                                    {isActivityDone
                                                                        ? 'Personal notebook exercise verified! +5 XP awarded.'
                                                                        : 'Click when finished writing in your personal notebook. No upload needed.'}
                                                                </p>
                                                            </div>
                                                            <Button
                                                                size="sm"
                                                                onClick={handleMarkActivityComplete}
                                                                disabled={isActivityDone || isMarkingActivity}
                                                                className={`text-xs font-semibold shrink-0 w-full sm:w-auto cursor-pointer ${isActivityDone
                                                                    ? 'bg-emerald-600 hover:bg-emerald-600 text-white shadow-2xs'
                                                                    : ''
                                                                    }`}
                                                            >
                                                                {isActivityDone
                                                                    ? '✓ Completed (+5 XP)'
                                                                    : isMarkingActivity
                                                                        ? 'Saving...'
                                                                        : 'Mark Done (+5 XP)'}
                                                            </Button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Right Column (7 cols on lg, full width on mobile): Written Reflection */}
                                            <div className="lg:col-span-7 space-y-4">
                                                <div className="p-6 rounded-2xl bg-card border shadow-sm space-y-4">
                                                    <div className="space-y-3">
                                                        <div className="flex items-center justify-between">
                                                            <div className="flex items-center gap-2.5">
                                                                <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
                                                                    <Lightbulb className="h-5 w-5" />
                                                                </div>
                                                                <div>
                                                                    <span className="text-[11px] font-bold uppercase tracking-wider text-primary">Part 2</span>
                                                                    <h3 className="text-base font-bold text-foreground">Written Reflection</h3>
                                                                </div>
                                                            </div>
                                                            <div className="flex items-center gap-1.5 font-sans text-xs text-amber-600 dark:text-amber-400 font-semibold bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-full">
                                                                <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                                                                <span>+5 XP</span>
                                                            </div>
                                                        </div>

                                                        {/* Formatted Reflection Prompt */}
                                                        <div className="space-y-2 bg-primary/5 p-4 rounded-xl border border-primary/15">
                                                            <p className="text-xs font-semibold text-primary">
                                                                {promptIntro}
                                                            </p>
                                                            {promptQuestions.length > 0 && (
                                                                <div className="space-y-1.5 pt-1">
                                                                    {promptQuestions.map((q, idx) => (
                                                                        <div key={idx} className="flex items-start gap-2 text-xs text-foreground/90">
                                                                            <span className="h-4 w-4 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                                                                                {idx + 1}
                                                                            </span>
                                                                            <span className="leading-snug">{q}</span>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Textarea */}
                                                    <div className="space-y-2">
                                                        <label className="text-xs font-semibold text-muted-foreground flex items-center justify-between">
                                                            <span>Your Reflection</span>
                                                            <span className="text-[11px] text-muted-foreground font-mono">
                                                                {reflectionText.trim() ? reflectionText.trim().split(/\s+/).length : 0} words
                                                            </span>
                                                        </label>
                                                        <Textarea
                                                            rows={7}
                                                            value={reflectionText}
                                                            onChange={(e) => setReflectionText(e.target.value)}
                                                            placeholder="Write your reflection here. Address the questions above..."
                                                            className="text-sm font-sans leading-relaxed resize-none p-3.5"
                                                        />

                                                        <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
                                                            <span className="flex items-center gap-1 text-[11px]">
                                                                <Lock className="h-3.5 w-3.5 text-emerald-600" />
                                                                Visible only to you and academic evaluators
                                                            </span>
                                                            <span className="text-[11px] text-muted-foreground">
                                                                {tutorialDetail.userReflection ? '✓ Previously submitted' : 'Personal reflection'}
                                                            </span>
                                                        </div>
                                                    </div>

                                                    {/* Submit Button */}
                                                    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t">
                                                        <span className="text-xs text-muted-foreground">
                                                            {tutorialDetail.userReflection ? 'Reflection recorded in portfolio' : 'Awarded +5 XP upon submission'}
                                                        </span>
                                                        <div className="flex items-center gap-2 w-full sm:w-auto">
                                                            <Button
                                                                onClick={handleSubmitReflection}
                                                                disabled={isSubmittingReflection || !reflectionText.trim()}
                                                                className="font-semibold text-xs flex-1 sm:flex-none cursor-pointer"
                                                            >
                                                                {isSubmittingReflection ? 'Saving...' : tutorialDetail.userReflection ? 'Update Reflection' : 'Submit Reflection (+5 XP)'}
                                                            </Button>
                                                            {tutorialDetail.userReflection && (
                                                                <Button
                                                                    variant="outline"
                                                                    onClick={() => switchTab((tutorialDetail.assignmentInstructions || tutorialDetail.assignmentUrl) ? 'assignment' : 'quiz')}
                                                                    className="text-xs gap-1 cursor-pointer"
                                                                >
                                                                    <span>{(tutorialDetail.assignmentInstructions || tutorialDetail.assignmentUrl) ? 'Next: Assignment' : 'Take Quiz'}</span>
                                                                    <ArrowRight className="h-3.5 w-3.5" />
                                                                </Button>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })()}

                            {/* TAB 4: OFFICIAL ASSIGNMENT */}
                            {activeTab === 'assignment' && (() => {
                                const rawAssignment = tutorialDetail.assignmentInstructions || ''
                                const assignmentLines = rawAssignment.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n')
                                const cleanedLines = assignmentLines.filter((l) => {
                                    const s = l.trim()
                                    if (s.startsWith('Personality and Human Development') && s.includes('Assignment')) return false
                                    if (s.toLowerCase().startsWith('as an assignment')) return false
                                    return true
                                })
                                const cleanedAssignmentText = cleanedLines.join('\n').trim()

                                const isDone = Boolean(
                                    (tutorialDetail.userTutorial.assignmentDone as any) === true ||
                                    tutorialDetail.userTutorial.assignmentDone === 'yes' ||
                                    tutorialDetail.userReflection
                                )

                                return (
                                    <div id="tutorial-modal-body" className="flex-1 overflow-y-auto px-4 py-6 sm:px-10 sm:py-10 bg-background/50 min-h-0">
                                        <div className="max-w-4xl mx-auto space-y-6">
                                            {/* Assignment Body Content */}
                                            <div className="p-6 sm:p-8 rounded-2xl bg-card border border-border/80 shadow-xs space-y-6">
                                                <div className="flex items-center justify-between gap-4 pb-4 border-b border-border/60">
                                                    <h3 className="text-xl sm:text-2xl font-bold text-foreground tracking-tight">Assignment</h3>
                                                    {tutorialDetail.assignmentUrl && (
                                                        <a
                                                            href={tutorialDetail.assignmentUrl}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-border/80 bg-background hover:bg-muted text-xs sm:text-sm font-semibold text-foreground transition-all shadow-2xs cursor-pointer shrink-0"
                                                        >
                                                            <Download className="h-4 w-4 text-primary" />
                                                            <span>Download Assignment</span>
                                                            <ExternalLink className="h-3 w-3 text-muted-foreground/60" />
                                                        </a>
                                                    )}
                                                </div>

                                                {cleanedAssignmentText ? (
                                                    <div className="prose prose-slate dark:prose-invert max-w-none text-foreground/90 font-sans leading-relaxed text-sm sm:text-base space-y-4">
                                                        <ReactMarkdown
                                                            remarkPlugins={[remarkGfm]}
                                                            components={{
                                                                h3: ({ ...props }) => <h3 className="text-base sm:text-lg font-bold text-foreground mt-4 mb-2 font-sans" {...props} />,
                                                                p: ({ ...props }) => <p className="leading-relaxed mb-3 text-foreground/90 text-sm sm:text-base font-sans" {...props} />,
                                                                ul: ({ ...props }) => <ul className="list-disc pl-6 mb-4 space-y-2 text-sm sm:text-base text-foreground/90" {...props} />,
                                                                ol: ({ ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-sm sm:text-base text-foreground/90" {...props} />,
                                                                li: ({ ...props }) => <li className="leading-relaxed" {...props} />,
                                                                strong: ({ ...props }) => <strong className="font-bold text-foreground" {...props} />,
                                                            }}
                                                        >
                                                            {cleanedAssignmentText}
                                                        </ReactMarkdown>
                                                    </div>
                                                ) : (
                                                    <p className="text-sm text-muted-foreground italic">
                                                        Assignment instructions will be available shortly.
                                                    </p>
                                                )}

                                                {/* Helpful Tip */}
                                                <div className="p-4 rounded-xl bg-muted/60 border border-border/70 text-xs text-foreground/90 flex items-start gap-3 shadow-2xs">
                                                    <Sparkles className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                                                    <div className="space-y-1">
                                                        <p className="font-semibold text-foreground">How to Complete</p>
                                                        <p className="text-muted-foreground leading-relaxed">
                                                            Complete this practical task in your physical notebook or discuss it with friends or classmates.
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Completion and Next Action Footer */}
                                            <div className="p-6 rounded-2xl bg-card border border-border/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
                                                <div className="space-y-1 text-center sm:text-left">
                                                    <h4 className="font-bold text-foreground text-sm sm:text-base">
                                                        {isDone ? 'Assignment Completed' : 'Completed this assignment?'}
                                                    </h4>
                                                    <p className="text-xs text-muted-foreground">
                                                        {isDone
                                                            ? 'Assignment has been marked as completed (+5 XP earned). Next step: 5-Question Quiz.'
                                                            : 'Mark as completed to earn +5 XP toward your course progress.'}
                                                    </p>
                                                </div>

                                                <div className="flex items-center gap-3 w-full sm:w-auto">
                                                    {!isDone ? (
                                                        <Button
                                                            size="lg"
                                                            variant="outline"
                                                            onClick={handleMarkAssignmentComplete}
                                                            disabled={isMarkingAssignment}
                                                            className="font-semibold text-xs sm:text-sm gap-1.5 flex-1 sm:flex-none cursor-pointer"
                                                        >
                                                            {isMarkingAssignment ? (
                                                                <>
                                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                                    <span>Saving...</span>
                                                                </>
                                                            ) : (
                                                                <>
                                                                    <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                                                                    <span>Mark Completed (+5 XP)</span>
                                                                </>
                                                            )}
                                                        </Button>
                                                    ) : (
                                                        <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-xs px-3 py-1.5 font-semibold gap-1.5">
                                                            <Check className="h-3.5 w-3.5" />
                                                            <span>Completed (+5 XP)</span>
                                                        </Badge>
                                                    )}

                                                    <Button
                                                        size="lg"
                                                        onClick={() => switchTab('quiz')}
                                                        className="font-semibold text-xs sm:text-sm gap-2 flex-1 sm:flex-none cursor-pointer shadow-xs"
                                                    >
                                                        <span>Proceed to Quiz</span>
                                                        <ArrowRight className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })()}

                            {/* TAB 4: QUIZ (5 MCQs) — Spacious Assessment */}
                            {activeTab === 'quiz' && (() => {
                                const nextTutorial = overview?.tutorials.find(t => t.number === tutorialDetail.tutorialNumber + 1)

                                return (
                                    <div id="tutorial-modal-body" className="flex-1 overflow-y-auto p-6 sm:p-8 bg-muted/10 min-h-0">
                                        <div className="max-w-4xl mx-auto space-y-6">
                                            {/* Quiz Overview Banner */}
                                            <div className="p-6 rounded-2xl bg-card border shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                                                <div className="space-y-1">
                                                    <div className="flex items-center gap-2">
                                                        <h3 className="text-lg font-bold text-foreground">Tutorial Knowledge Quiz</h3>
                                                        <Badge variant="outline" className="text-xs font-mono">5 Questions</Badge>
                                                    </div>
                                                    <p className="text-xs text-muted-foreground">
                                                        5 multiple-choice questions. Full rationales and explanations will be unlocked upon submission.
                                                    </p>
                                                </div>

                                                {tutorialDetail.quiz.hasAttempted ? (
                                                    <div className={cn(
                                                        "px-4 py-2 rounded-xl border flex flex-col items-center sm:items-end justify-center min-w-[90px]",
                                                        ((tutorialDetail.quiz.score ?? 0) >= 3)
                                                            ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-600 dark:text-emerald-400'
                                                            : 'bg-amber-500/10 border-amber-500/25 text-amber-600 dark:text-amber-400'
                                                    )}>
                                                        <div className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground">
                                                            Score
                                                        </div>
                                                        <div className="text-xl font-bold font-mono">
                                                            {tutorialDetail.quiz.score} / {tutorialDetail.quiz.totalQuestions}
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-2 text-xs font-mono font-semibold text-amber-600 dark:text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-xl">
                                                        <Sparkles className="h-4 w-4 text-amber-500" />
                                                        +10 XP
                                                    </div>
                                                )}
                                            </div>

                                            {/* Questions */}
                                            <div className="space-y-5">
                                                {tutorialDetail.quiz.questions.map((q) => {
                                                    const selected = quizAnswers[String(q.questionNumber)] || q.selectedOption
                                                    const isSubmitted = tutorialDetail.quiz.hasAttempted

                                                    return (
                                                        <div key={q.id} className="p-6 rounded-2xl border bg-card shadow-sm space-y-4">
                                                            <div className="flex items-start gap-3">
                                                                <div className="h-7 w-7 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                                                                    {q.questionNumber}
                                                                </div>
                                                                <h4 className="text-sm sm:text-base font-semibold text-foreground leading-relaxed flex-1">
                                                                    {q.questionText}
                                                                </h4>
                                                            </div>

                                                            {/* Options */}
                                                            <RadioGroup
                                                                value={selected || ''}
                                                                onValueChange={(val) => setQuizAnswers({ ...quizAnswers, [String(q.questionNumber)]: val })}
                                                                disabled={isSubmitted}
                                                                className="space-y-2.5 pt-1 pl-10"
                                                            >
                                                                {q.options.map((opt) => {
                                                                    const isCorrect = isSubmitted && q.correctOption === opt.id
                                                                    const isChosen = selected === opt.id
                                                                    const isWrong = isSubmitted && isChosen && !isCorrect

                                                                    return (
                                                                        <label
                                                                            key={opt.id}
                                                                            className={`flex items-start gap-3 p-3.5 rounded-xl border text-xs sm:text-sm cursor-pointer transition-all ${isCorrect
                                                                                ? 'border-emerald-500 bg-emerald-500/10 text-emerald-900 dark:text-emerald-200 font-medium'
                                                                                : isWrong
                                                                                    ? 'border-destructive bg-destructive/10 text-destructive font-medium'
                                                                                    : isChosen
                                                                                        ? 'border-primary bg-primary/5 text-foreground ring-1 ring-primary/20'
                                                                                        : 'border-border hover:bg-muted/40 text-muted-foreground hover:text-foreground'
                                                                                }`}
                                                                        >
                                                                            <RadioGroupItem value={opt.id} className="mt-0.5" />
                                                                            <span className="flex-1 leading-relaxed">
                                                                                <strong className="mr-1.5 font-bold uppercase">{opt.id}.</strong>
                                                                                {opt.text}
                                                                            </span>
                                                                            {isCorrect && <Check className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />}
                                                                        </label>
                                                                    )
                                                                })}
                                                            </RadioGroup>

                                                            {/* Explanation Box */}
                                                            {isSubmitted && q.explanation && (
                                                                <div className="mt-4 p-4 rounded-xl bg-muted/60 border border-border/80 text-xs sm:text-sm space-y-1.5 ml-10">
                                                                    <span className="font-bold text-primary flex items-center gap-1.5 text-xs uppercase tracking-wider">
                                                                        <Lightbulb className="h-3.5 w-3.5" />
                                                                        Psychological Rationale & Explanation
                                                                    </span>
                                                                    <p className="text-foreground/80 leading-relaxed font-sans">
                                                                        {q.explanation}
                                                                    </p>
                                                                </div>
                                                            )}
                                                        </div>
                                                    )
                                                })}
                                            </div>

                                            {/* Submit or Completed Actions */}
                                            {!tutorialDetail.quiz.hasAttempted ? (
                                                <div className="pt-2 pb-6 flex justify-end">
                                                    <Button
                                                        size="lg"
                                                        onClick={handleSubmitQuiz}
                                                        disabled={isSubmittingQuiz}
                                                        className="font-bold text-sm px-6 cursor-pointer shadow-sm"
                                                    >
                                                        {isSubmittingQuiz
                                                            ? 'Evaluating Answers...'
                                                            : 'Submit Answers (+10 XP)'}
                                                    </Button>
                                                </div>
                                            ) : (
                                                <div className="space-y-4 pt-2 pb-6">
                                                    {/* Prompt to move directly to next tutorial */}
                                                    <div className="p-6 rounded-2xl bg-gradient-to-br from-emerald-500/10 via-card to-primary/5 border-2 border-emerald-500/30 shadow-md flex flex-col sm:flex-row items-center justify-between gap-4 animate-in fade-in duration-300">
                                                        <div className="space-y-1.5 text-center sm:text-left">
                                                            <div className="flex items-center gap-2 justify-center sm:justify-start">
                                                                <span className="text-xl">🎉</span>
                                                                <h4 className="font-bold text-foreground text-base sm:text-lg">
                                                                    Tutorial {tutorialDetail.tutorialNumber} Completed!
                                                                </h4>
                                                                <Badge variant="outline" className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-xs font-bold">
                                                                    +25 XP Total
                                                                </Badge>
                                                            </div>
                                                            <p className="text-xs text-muted-foreground">
                                                                {nextTutorial
                                                                    ? `Ready for the next lesson? Continue directly to Tutorial ${nextTutorial.number}: ${nextTutorial.title}`
                                                                    : "Outstanding! You have completed all 17 tutorials in this curriculum."}
                                                            </p>
                                                        </div>

                                                        {nextTutorial ? (
                                                            <Button
                                                                size="lg"
                                                                onClick={() => openTutorialModal(nextTutorial.id)}
                                                                className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold text-xs sm:text-sm px-6 py-3 rounded-xl shadow-md shadow-primary/25 cursor-pointer shrink-0 gap-2 w-full sm:w-auto hover:scale-[1.02] active:scale-[0.98] transition-all"
                                                            >
                                                                <span>Continue to Tutorial {nextTutorial.number}</span>
                                                                <ArrowRight className="h-4 w-4" />
                                                            </Button>
                                                        ) : (
                                                            <Button
                                                                size="lg"
                                                                variant="outline"
                                                                onClick={() => setActiveTutorialId(null)}
                                                                className="font-bold text-xs sm:text-sm px-6 py-3 rounded-xl border-emerald-500/30 text-emerald-600 cursor-pointer"
                                                            >
                                                                <span>Back to Dashboard</span>
                                                            </Button>
                                                        )}
                                                    </div>

                                                    <div className="flex justify-end">
                                                        <Button
                                                            size="sm"
                                                            variant="ghost"
                                                            onClick={() => {
                                                                setQuizAnswers({})
                                                                setTutorialDetail({
                                                                    ...tutorialDetail,
                                                                    quiz: {
                                                                        ...tutorialDetail.quiz,
                                                                        hasAttempted: false
                                                                    }
                                                                })
                                                            }}
                                                            className="text-xs text-muted-foreground hover:text-foreground cursor-pointer"
                                                        >
                                                            Retake Quiz
                                                        </Button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )
                            })()}
                        </>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    )
}
