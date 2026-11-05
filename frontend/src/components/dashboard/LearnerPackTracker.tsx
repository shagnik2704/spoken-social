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
    Download, ChevronLeft, ChevronRight
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

// Week titles mapping
const WEEK_TITLES: Record<number, string> = {
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

    // Assignment state
    const [isMarkingAssignment, setIsMarkingAssignment] = useState(false)

    // Reflection submission state
    const [reflectionText, setReflectionText] = useState('')
    const [isSubmittingReflection, setIsSubmittingReflection] = useState(false)

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

    const openTutorialModal = async (tutId: string) => {
        setActiveTutorialId(tutId)
        setIsLoadingDetail(true)
        setActiveTab('video')
        setVideoWatchPercent(0)
        setIsVideoBuffering(false)
        setQuizAnswers({})
        requestAnimationFrame(() => {
            const btn = document.getElementById('tab-btn-video')
            if (btn) btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
        })
        try {
            const res = await api.get(`/api/learner-pack/tutorials/${tutId}`)
            const data: LearnerPackTutorialDetail = res.data
            setTutorialDetail(data)
            if (data.userReflection) {
                setReflectionText(data.userReflection.reflectionText)
            } else {
                setReflectionText('')
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
        const words = reflectionText.trim().split(/\s+/).length
        if (words < 10) {
            toast.error('Please write a complete reflection (at least 3 sentences).')
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
                                                    {WEEK_TITLES[weekNum] || `Week ${weekNum}`}
                                                </h3>
                                                <p className="text-xs text-muted-foreground">
                                                    {tuts.length > 0 ? `${tuts.length} Tutorials` : 'Special Milestone Week'}
                                                    {milestone && ` • ${milestone.title}`}
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
                                        const isCompleted = p.status === 'completed' || p.quizPassed

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
                                                        <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
                                                            {tut.readingTitle && (
                                                                <span className="flex items-center gap-1.5">
                                                                    <BookOpen className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
                                                                    <span>{tut.readingTimeMinutes || 15}m read</span>
                                                                </span>
                                                            )}
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
                                                            {tut.hasAssignment && (
                                                                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 dark:text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/25">
                                                                    <FileText className="h-3 w-3 text-amber-500" />
                                                                    Assignment
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-2.5 shrink-0 w-full sm:w-auto justify-between sm:justify-end">
                                                    {/* Step Badges */}
                                                    <div className="flex items-center gap-1.5">
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
                                                    </div>

                                                    <Button
                                                        size="sm"
                                                        variant={isCompleted ? "outline" : "default"}
                                                        onClick={() => openTutorialModal(tut.id)}
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
                                                • Week {tutorialDetail.content?.weekNumber || 1} • {WEEK_TITLES[tutorialDetail.content?.weekNumber || 1]?.split(':')[1]?.trim() || 'Personality & Human Development'}
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
                                        <PenTool className={cn("h-4 w-4", activeTab === 'activity' ? "text-primary-foreground" : "text-muted-foreground")} />
                                        <span>3. Activity & Reflection</span>
                                        {(tutorialDetail.userReflection || tutorialDetail.userTutorial.minitaskOpted === 'yes') && (
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
                                                        {tutorialDetail.videoUrl && (
                                                            <a
                                                                href={tutorialDetail.videoUrl}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                title="Open direct video stream in new tab"
                                                                className="hidden sm:inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors px-2.5 py-1.5 rounded-lg border border-border/60 hover:bg-muted/50"
                                                            >
                                                                <ExternalLink className="h-3 w-3" />
                                                                <span>Direct Stream</span>
                                                            </a>
                                                        )}
                                                        <Button
                                                            onClick={() => switchTab('reading')}
                                                            className="text-xs font-bold gap-1.5 shadow-2xs hover:shadow-xs cursor-pointer"
                                                        >
                                                            <span>Next: Reading Notes</span>
                                                            <ArrowRight className="h-4 w-4" />
                                                        </Button>
                                                    </div>
                                                </div>
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

                            {/* TAB 3: ACTIVITY & REFLECTION — Responsive Two-Column Studio */}
                            {activeTab === 'activity' && (() => {
                                const rawTryIt = tutorialDetail.content?.tryItInstructions || ''
                                const stepRegex = /(?:\*\*Step\s+\d+:\*\*|\b\d+\.\s+)/
                                const tryItParts = rawTryIt.split(stepRegex).map(s => s.trim()).filter(Boolean)
                                const tryItIntro = tryItParts.length > 1 ? tryItParts[0] : ''
                                const tryItSteps = tryItParts.length > 1 ? tryItParts.slice(1) : (rawTryIt ? [rawTryIt] : [])

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
                                                            <span>Your Reflection (3–5 complete sentences)</span>
                                                            <span className="text-[11px] text-muted-foreground font-mono">
                                                                {reflectionText.trim() ? reflectionText.trim().split(/\s+/).length : 0} words
                                                            </span>
                                                        </label>
                                                        <Textarea
                                                            rows={7}
                                                            value={reflectionText}
                                                            onChange={(e) => setReflectionText(e.target.value)}
                                                            placeholder="Write your reflection here. Address the questions above in 3 to 5 clear sentences..."
                                                            className="text-sm font-sans leading-relaxed resize-none p-3.5"
                                                        />

                                                        <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
                                                            <span className="flex items-center gap-1 text-[11px]">
                                                                <Lock className="h-3.5 w-3.5 text-emerald-600" />
                                                                Visible only to you and academic evaluators
                                                            </span>
                                                            <span className="text-[11px] text-muted-foreground">
                                                                {tutorialDetail.userReflection ? '✓ Previously submitted' : 'Min 3 sentences required'}
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
