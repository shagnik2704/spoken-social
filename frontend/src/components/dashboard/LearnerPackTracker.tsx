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
    Check, ArrowRight, ExternalLink
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
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
    const [activeTab, setActiveTab] = useState<'reading' | 'activity' | 'quiz' | 'video'>('reading')

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

    const fetchOverview = async () => {
        if (!activeCourseId) return
        try {
            setIsLoading(true)
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
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchOverview()
    }, [activeCourseId])

    const openTutorialModal = async (tutId: string) => {
        setActiveTutorialId(tutId)
        setIsLoadingDetail(true)
        setActiveTab('reading')
        setQuizAnswers({})
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

    const handleMarkReadingComplete = async () => {
        if (!activeTutorialId) return
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
            fetchOverview()
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
            fetchOverview()
        } catch (err) {
            toast.error('Failed to mark exercise status.')
        } finally {
            setIsMarkingActivity(false)
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
            fetchOverview()
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

            if (passed) {
                toast.success(`Quiz passed with ${score}/${totalQuestions}! +${xpGained} XP 🎉`)
            } else {
                toast.warning(`Scored ${score}/${totalQuestions}. Review the explanations below!`)
            }
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
            fetchOverview()
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
            fetchOverview()
        } catch (err) {
            toast.error('Failed to record habit check-in.')
        } finally {
            setIsCheckingIn(false)
        }
    }

    if (isLoading) {
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
            <Card className="border-primary/20 bg-gradient-to-br from-primary/5 via-background to-background">
                <CardContent className="p-6">
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                        <div className="space-y-1">
                            <div className="flex items-center gap-2">
                                <Compass className="h-6 w-6 text-primary" />
                                <h2 className="text-xl font-bold tracking-tight">{overview.title}</h2>
                            </div>
                            <p className="text-sm text-muted-foreground">
                                12-Week SWAYAM Plus Life-Skills & Human Development Workspace
                            </p>
                        </div>
                        <Badge variant="outline" className="px-3 py-1 font-mono text-xs border-primary/30 text-primary bg-primary/10">
                            {completedTuts} / {totalTuts} Completed ({progressPercent}%)
                        </Badge>
                    </div>

                    <div className="mt-4 space-y-1.5">
                        <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Course Completion Progress</span>
                            <span>{progressPercent}%</span>
                        </div>
                        <Progress value={progressPercent} className="h-2.5 bg-muted" />
                    </div>

                    <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-muted-foreground pt-4 border-t">
                        <div className="flex items-center gap-1.5">
                            <PlayCircle className="h-4 w-4 text-primary" />
                            <span>17 Videos (+10 XP)</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <BookOpen className="h-4 w-4 text-emerald-500" />
                            <span>17 Readings (+10 XP)</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <PenTool className="h-4 w-4 text-amber-500" />
                            <span>17 Reflections (+5 XP)</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <HelpCircle className="h-4 w-4 text-purple-500" />
                            <span>17 Quizzes (85 MCQs)</span>
                        </div>
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
                                                className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3.5 rounded-xl border bg-card hover:bg-muted/20 transition-all gap-3"
                                            >
                                                <div className="space-y-1 min-w-0">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs font-mono font-bold text-primary">
                                                            #{tut.number}
                                                        </span>
                                                        <h4 className="text-sm font-semibold truncate text-foreground">
                                                            {tut.title}
                                                        </h4>
                                                    </div>
                                                    {tut.readingTitle && (
                                                        <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                                                            <BookOpen className="h-3.5 w-3.5 text-muted-foreground/60 shrink-0" />
                                                            {tut.readingTitle} ({tut.readingTimeMinutes || 15} mins)
                                                        </p>
                                                    )}
                                                </div>

                                                <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-between sm:justify-end">
                                                    {/* Step Badges */}
                                                    <div className="flex items-center gap-1">
                                                        <Badge
                                                            variant="outline"
                                                            className={`text-[10px] px-1.5 py-0 ${p.watched ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/30' : 'text-muted-foreground/50 border-dashed'}`}
                                                            title="Reading / Video Watched"
                                                        >
                                                            {p.watched ? '✓ Read' : 'Read'}
                                                        </Badge>
                                                        <Badge
                                                            variant="outline"
                                                            className={`text-[10px] px-1.5 py-0 ${p.reflectionSubmitted ? 'bg-amber-500/10 text-amber-600 border-amber-500/30' : 'text-muted-foreground/50 border-dashed'}`}
                                                            title="Written Reflection Submitted"
                                                        >
                                                            {p.reflectionSubmitted ? '✓ Reflection' : 'Reflection'}
                                                        </Badge>
                                                        <Badge
                                                            variant="outline"
                                                            className={`text-[10px] px-1.5 py-0 ${p.quizPassed ? 'bg-purple-500/10 text-purple-600 border-purple-500/30' : 'text-muted-foreground/50 border-dashed'}`}
                                                            title="5-Question Automated Quiz"
                                                        >
                                                            {p.quizPassed ? `✓ Quiz (${p.quizScore}/5)` : 'Quiz'}
                                                        </Badge>
                                                    </div>

                                                    <Button
                                                        size="sm"
                                                        variant={isCompleted ? "outline" : "default"}
                                                        onClick={() => openTutorialModal(tut.id)}
                                                        className="text-xs font-medium h-8"
                                                    >
                                                        {isCompleted ? 'Review' : (p.watched || p.reflectionSubmitted) ? 'Continue' : 'Open Tutorial'}
                                                        <ArrowRight className="h-3.5 w-3.5 ml-1" />
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
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-2">
                                            <Badge variant="outline" className="text-xs font-semibold bg-primary/10 text-primary border-primary/25">
                                                Tutorial {tutorialDetail.tutorialNumber}
                                            </Badge>
                                            <span className="text-xs text-muted-foreground font-medium">
                                                Week {tutorialDetail.content?.weekNumber || 1} • {WEEK_TITLES[tutorialDetail.content?.weekNumber || 1]?.split(':')[1]?.trim() || 'Personality & Human Development'}
                                            </span>
                                        </div>
                                        <DialogTitle className="text-xl sm:text-2xl font-bold tracking-tight text-foreground font-sans">
                                            {tutorialDetail.title}
                                        </DialogTitle>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="flex items-center gap-1.5 font-sans text-xs text-amber-600 dark:text-amber-400 font-semibold bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-full">
                                            <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                                            <span>+25 XP Total</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Modern Step Navigation Tabs */}
                                <div className="flex items-center gap-2 mt-4 pt-2 border-t border-border/50 overflow-x-auto no-scrollbar">
                                    <button
                                        onClick={() => setActiveTab('reading')}
                                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all shrink-0 ${activeTab === 'reading'
                                            ? 'bg-primary text-primary-foreground shadow-sm'
                                            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                                            }`}
                                    >
                                        <BookOpen className="h-4 w-4" />
                                        <span>1. Reading</span>
                                        {tutorialDetail.userTutorial.watched === 'yes' && (
                                            <span className="h-4 w-4 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-[10px] font-bold">✓</span>
                                        )}
                                    </button>
                                    <button
                                        onClick={() => setActiveTab('activity')}
                                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all shrink-0 ${activeTab === 'activity'
                                            ? 'bg-primary text-primary-foreground shadow-sm'
                                            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                                            }`}
                                    >
                                        <PenTool className="h-4 w-4" />
                                        <span>2. Activity & Reflection</span>
                                        {(tutorialDetail.userReflection || tutorialDetail.userTutorial.minitaskOpted === 'yes') && (
                                            <span className="h-4 w-4 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-[10px] font-bold">✓</span>
                                        )}
                                    </button>
                                    <button
                                        onClick={() => setActiveTab('quiz')}
                                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all shrink-0 ${activeTab === 'quiz'
                                            ? 'bg-primary text-primary-foreground shadow-sm'
                                            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                                            }`}
                                    >
                                        <HelpCircle className="h-4 w-4" />
                                        <span>3. Quiz (5 MCQs)</span>
                                        {tutorialDetail.quiz.hasAttempted && (
                                            <span className={`h-4 w-4 rounded-full flex items-center justify-center text-[10px] font-bold ${tutorialDetail.quiz.passed ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400' : 'bg-amber-500/20 text-amber-600'
                                                }`}>✓</span>
                                        )}
                                    </button>
                                    <button
                                        onClick={() => setActiveTab('video')}
                                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all shrink-0 ${activeTab === 'video'
                                            ? 'bg-primary text-primary-foreground shadow-sm'
                                            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                                            }`}
                                    >
                                        <PlayCircle className="h-4 w-4" />
                                        <span>Video Link</span>
                                    </button>
                                </div>
                            </div>

                            {/* Modal Body / Tab Content */}
                            {/* TAB 1: READING — Full Width Clean Reader Canvas */}
                            {activeTab === 'reading' && (
                                <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-10 sm:py-10 bg-background/50 min-h-0">
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
                                        <div className="mt-12 p-6 rounded-2xl bg-card border shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
                                            <div className="space-y-1 text-center sm:text-left">
                                                <h4 className="font-bold text-foreground text-sm sm:text-base">Finished this reading?</h4>
                                                <p className="text-xs text-muted-foreground">
                                                    Mark as read to claim +10 XP and move directly to the private notebook activity & reflection.
                                                </p>
                                            </div>
                                            <Button
                                                size="lg"
                                                onClick={async () => {
                                                    await handleMarkReadingComplete()
                                                    setActiveTab('activity')
                                                }}
                                                className="font-semibold text-xs sm:text-sm shrink-0 gap-1.5 w-full sm:w-auto"
                                            >
                                                {tutorialDetail.userTutorial.watched === 'yes' ? 'Proceed to Activity & Reflection' : 'Mark Complete (+10 XP) & Continue'}
                                                <ArrowRight className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* TAB 2: ACTIVITY & REFLECTION — Responsive Two-Column Studio */}
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
                                    <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-muted/10 min-h-0">
                                        <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
                                            {/* Left Column (5 cols on lg, full width on mobile): Private Notebook Exercise */}
                                            <div className="lg:col-span-5 space-y-4 flex flex-col justify-between">
                                                <div className="space-y-4">
                                                    <div className="flex items-center gap-2.5">
                                                        <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-600 border border-amber-500/20">
                                                            <PenTool className="h-5 w-5" />
                                                        </div>
                                                        <div>
                                                            <span className="text-[11px] font-bold uppercase tracking-wider text-amber-600">Part 1</span>
                                                            <h3 className="text-base font-bold text-foreground">Private Notebook Exercise</h3>
                                                        </div>
                                                    </div>

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
                                                                className="p-3.5 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1 hover:border-amber-500/30 transition-colors"
                                                            >
                                                                <div className="flex items-center gap-2">
                                                                    <Badge variant="outline" className="text-[10px] font-bold px-2 py-0.5 bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/20">
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
                                                                        ? 'Private notebook exercise verified! +5 XP awarded.'
                                                                        : 'Click when finished writing in your personal notebook.'}
                                                                </p>
                                                            </div>
                                                            <Button
                                                                size="sm"
                                                                onClick={handleMarkActivityComplete}
                                                                disabled={isActivityDone || isMarkingActivity}
                                                                className={`text-xs font-semibold shrink-0 w-full sm:w-auto ${isActivityDone
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

                                                    <div className="p-2.5 rounded-lg bg-background/80 border text-[11px] text-muted-foreground flex items-center gap-2">
                                                        <Lock className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                                                        <span>Your notebook is private and physical/digital. It is never uploaded or viewed by anyone.</span>
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
                                                                className="font-semibold text-xs flex-1 sm:flex-none"
                                                            >
                                                                {isSubmittingReflection ? 'Saving...' : tutorialDetail.userReflection ? 'Update Reflection' : 'Submit Reflection (+5 XP)'}
                                                            </Button>
                                                            {tutorialDetail.userReflection && (
                                                                <Button
                                                                    variant="outline"
                                                                    onClick={() => setActiveTab('quiz')}
                                                                    className="text-xs gap-1"
                                                                >
                                                                    Take Quiz
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

                            {/* TAB 3: QUIZ (5 MCQs) — Spacious Assessment */}
                            {activeTab === 'quiz' && (
                                <div className="flex-1 overflow-y-auto p-6 sm:p-8 bg-muted/10 min-h-0">
                                    <div className="max-w-4xl mx-auto space-y-6">
                                        {/* Quiz Overview Banner */}
                                        <div className="p-6 rounded-2xl bg-card border shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                                            <div className="space-y-1">
                                                <div className="flex items-center gap-2">
                                                    <h3 className="text-lg font-bold text-foreground">Tutorial Knowledge Quiz</h3>
                                                    <Badge variant="outline" className="text-xs font-mono">5 Questions</Badge>
                                                </div>
                                                <p className="text-xs text-muted-foreground">
                                                    Passing grade: 60% (3 / 5). Full rationales and explanations will be unlocked upon submission.
                                                </p>
                                            </div>

                                            {tutorialDetail.quiz.hasAttempted ? (
                                                <div className={`px-4 py-2 rounded-xl border flex items-center gap-3 ${tutorialDetail.quiz.passed
                                                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-600'
                                                    : 'bg-amber-500/10 border-amber-500/20 text-amber-600'
                                                    }`}>
                                                    <div className="text-right">
                                                        <div className="text-xs uppercase font-bold tracking-wider">
                                                            {tutorialDetail.quiz.passed ? 'Passed 🎉' : 'Needs Review'}
                                                        </div>
                                                        <div className="text-lg font-black font-mono">
                                                            {tutorialDetail.quiz.score} / {tutorialDetail.quiz.totalQuestions}
                                                        </div>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="flex items-center gap-2 text-xs font-mono font-semibold text-xp-gold bg-xp-gold/10 border border-xp-gold/20 px-3 py-1.5 rounded-xl">
                                                    <Sparkles className="h-4 w-4" />
                                                    +10 XP on Pass
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

                                        {/* Submit Button */}
                                        <div className="pt-2 pb-6 flex justify-end">
                                            <Button
                                                size="lg"
                                                onClick={handleSubmitQuiz}
                                                disabled={isSubmittingQuiz || tutorialDetail.quiz.hasAttempted}
                                                className="font-bold text-sm px-6"
                                            >
                                                {tutorialDetail.quiz.hasAttempted
                                                    ? '✓ Quiz Attempt Completed'
                                                    : isSubmittingQuiz
                                                        ? 'Evaluating Answers...'
                                                        : 'Submit Answers (+10 XP)'}
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* TAB 4: VIDEO */}
                            {activeTab === 'video' && (
                                <div className="flex-1 overflow-y-auto p-12 flex items-center justify-center bg-muted/10 min-h-0">
                                    <div className="max-w-lg mx-auto text-center space-y-5 p-8 rounded-2xl bg-card border shadow-sm">
                                        <div className="h-16 w-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto shadow-2xs">
                                            <PlayCircle className="h-9 w-9" />
                                        </div>
                                        <div className="space-y-2">
                                            <h3 className="text-xl font-bold text-foreground">
                                                Watch on Spoken Tutorial
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
                                                onClick={handleMarkReadingComplete}
                                                disabled={tutorialDetail.userTutorial.watched === 'yes'}
                                                className="text-xs"
                                            >
                                                {tutorialDetail.userTutorial.watched === 'yes' ? '✓ Watched' : 'Mark as Watched (+10 XP)'}
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    )
}
