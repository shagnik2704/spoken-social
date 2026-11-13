import { useCallback, useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { toast } from 'sonner'
import api from '@/lib/axios'
import { isDone, SCREENSHOT_MAX_BYTES, TERMINAL_MAX_CHARS, type TutorialStepId } from '@/lib/learnerPack'
import { useLearnerPackStore } from '@/store/learnerPackStore'
import { useUserStore } from '@/store/userStore'
import type { LearnerPackTutorialDetail } from '@/types'

const VIDEO_WATCHED_THRESHOLD = 80

const errorDetail = (err: unknown): string | null => {
    if (!axios.isAxiosError(err)) return null
    const detail: unknown = err.response?.data?.detail
    return typeof detail === 'string' ? detail : null
}

export interface TutorialCelebration {
    xpEarned: number
}

export interface TutorialWorkspace {
    detail: LearnerPackTutorialDetail | null
    loadFailed: boolean
    justCompletedStep: TutorialStepId | null
    celebration: TutorialCelebration | null
    dismissCelebration: () => void

    videoWatchPercent: number
    isVideoBuffering: boolean
    setIsVideoBuffering: (isBuffering: boolean) => void
    reportVideoProgress: (percent: number) => void
    markVideoWatched: () => Promise<void>
    markReadingComplete: () => Promise<void>

    reflectionText: string
    setReflectionText: (text: string) => void
    isSubmittingReflection: boolean
    submitReflection: () => Promise<void>
    isMarkingActivity: boolean
    markActivityComplete: () => Promise<void>
    isMarkingAssignment: boolean
    markAssignmentComplete: () => Promise<void>

    terminalOutput: string
    setTerminalOutput: (text: string) => void
    screenshotFile: File | null
    screenshotPreview: string | null
    screenshotNotes: string
    setScreenshotNotes: (notes: string) => void
    selectScreenshot: (file: File | undefined) => void
    clearScreenshot: () => void
    isSubmittingLab: boolean
    submitTerminal: () => Promise<void>
    submitScreenshot: () => Promise<void>

    quizAnswers: Record<string, string>
    answerQuestion: (questionNumber: number, optionId: string) => void
    isSubmittingQuiz: boolean
    submitQuiz: () => Promise<void>
    retakeQuiz: () => void
}

export const useTutorialWorkspace = (tutorialId: string, courseId: string): TutorialWorkspace => {
    const addXP = useUserStore(state => state.addXP)
    const fetchOverview = useLearnerPackStore(state => state.fetchOverview)

    const [detail, setDetail] = useState<LearnerPackTutorialDetail | null>(null)
    const [loadFailed, setLoadFailed] = useState(false)
    const [justCompletedStep, setJustCompletedStep] = useState<TutorialStepId | null>(null)
    const [celebration, setCelebration] = useState<TutorialCelebration | null>(null)

    const [videoWatchPercent, setVideoWatchPercent] = useState(0)
    const [isVideoBuffering, setIsVideoBuffering] = useState(false)
    const watchRequestedRef = useRef(false)

    const [reflectionText, setReflectionText] = useState('')
    const [isSubmittingReflection, setIsSubmittingReflection] = useState(false)
    const [isMarkingActivity, setIsMarkingActivity] = useState(false)
    const [isMarkingAssignment, setIsMarkingAssignment] = useState(false)

    const [terminalOutput, setTerminalOutput] = useState('')
    const [screenshotFile, setScreenshotFile] = useState<File | null>(null)
    const [screenshotPreview, setScreenshotPreview] = useState<string | null>(null)
    const [screenshotNotes, setScreenshotNotes] = useState('')
    const [isSubmittingLab, setIsSubmittingLab] = useState(false)

    const [quizAnswers, setQuizAnswers] = useState<Record<string, string>>({})
    const [isSubmittingQuiz, setIsSubmittingQuiz] = useState(false)

    const endpoint = `/api/learner-pack/tutorials/${tutorialId}`

    const refreshOverview = useCallback((): void => {
        void fetchOverview(courseId)
    }, [fetchOverview, courseId])

    useEffect(() => {
        let isCancelled = false
        api.get<LearnerPackTutorialDetail>(endpoint)
            .then((res) => {
                if (isCancelled) return
                const data = res.data
                setDetail(data)
                const submittedText = data.userReflection?.reflectionText || ''
                setReflectionText(submittedText)
                setTerminalOutput(submittedText)
                setScreenshotNotes(submittedText)
                setScreenshotPreview(data.userReflection?.imageUrl || null)
            })
            .catch(() => {
                if (isCancelled) return
                setLoadFailed(true)
                toast.error('Failed to load tutorial content.')
            })
        return () => {
            isCancelled = true
        }
    }, [endpoint])

    const markVideoWatched = async (): Promise<void> => {
        if (!detail || isDone(detail.userTutorial.watched) || watchRequestedRef.current) return
        watchRequestedRef.current = true
        try {
            await api.post(`${endpoint}/video-watched`)
            toast.success('Video watched! +10 XP awarded')
            addXP(10)
            setJustCompletedStep('video')
            setDetail(prev => prev && { ...prev, userTutorial: { ...prev.userTutorial, watched: 'yes' } })
            refreshOverview()
        } catch {
            watchRequestedRef.current = false
            toast.error('Failed to update video progress.')
        }
    }

    const reportVideoProgress = (percent: number): void => {
        setVideoWatchPercent(prev => Math.max(prev, percent))
        if (percent >= VIDEO_WATCHED_THRESHOLD) void markVideoWatched()
    }

    const markReadingComplete = async (): Promise<void> => {
        if (!detail || isDone(detail.userTutorial.watched)) return
        try {
            await api.post(`${endpoint}/reading-complete`)
            toast.success('Reading completed! +10 XP awarded')
            addXP(10)
            setJustCompletedStep('reading')
            setDetail(prev => prev && { ...prev, userTutorial: { ...prev.userTutorial, watched: 'yes' } })
            refreshOverview()
        } catch {
            toast.error('Failed to update reading status.')
        }
    }

    const markActivityComplete = async (): Promise<void> => {
        try {
            setIsMarkingActivity(true)
            await api.post(`${endpoint}/activity-complete`)
            toast.success('Private notebook exercise completed! +5 XP awarded')
            addXP(5)
            setJustCompletedStep('activity')
            setDetail(prev => prev && { ...prev, userTutorial: { ...prev.userTutorial, minitaskOpted: 'yes' } })
            refreshOverview()
        } catch {
            toast.error('Failed to mark exercise status.')
        } finally {
            setIsMarkingActivity(false)
        }
    }

    const markAssignmentComplete = async (): Promise<void> => {
        try {
            setIsMarkingAssignment(true)
            await api.post(`${endpoint}/assignment-complete`)
            toast.success('Official assignment marked completed! +5 XP awarded')
            addXP(5)
            setJustCompletedStep('assignment')
            setDetail(prev => prev && { ...prev, userTutorial: { ...prev.userTutorial, assignmentDone: 'yes' } })
            refreshOverview()
        } catch {
            toast.error('Failed to update assignment status.')
        } finally {
            setIsMarkingAssignment(false)
        }
    }

    const submitReflection = async (): Promise<void> => {
        if (!reflectionText.trim()) {
            toast.error('Please enter your reflection before submitting.')
            return
        }
        try {
            setIsSubmittingReflection(true)
            const res = await api.post(`${endpoint}/reflection`, { reflection_text: reflectionText })
            toast.success('Reflection submitted! +5 XP awarded')
            addXP(5)
            setJustCompletedStep('activity')
            setDetail(prev => prev && {
                ...prev,
                userReflection: res.data.reflection,
                userTutorial: { ...prev.userTutorial, assignmentDone: 'yes' },
            })
            refreshOverview()
        } catch {
            toast.error('Failed to submit reflection.')
        } finally {
            setIsSubmittingReflection(false)
        }
    }

    const submitTerminal = async (): Promise<void> => {
        const text = terminalOutput.trim()
        if (!text) {
            toast.error('Please paste your terminal commands and output before submitting.')
            return
        }
        if (text.length > TERMINAL_MAX_CHARS) {
            toast.error(`Submission exceeds the ${TERMINAL_MAX_CHARS.toLocaleString()} character limit. Please paste only relevant command output.`)
            return
        }
        try {
            setIsSubmittingLab(true)
            const res = await api.post(`${endpoint}/terminal-submission`, { commands_output: text })
            toast.success('Assignment submission verified! +10 XP awarded')
            addXP(res.data.xpGained || 10)
            setJustCompletedStep('activity')
            setDetail(prev => prev && { ...prev, userReflection: res.data.submission, userTutorial: res.data.userTutorial })
            refreshOverview()
        } catch (err) {
            toast.error(errorDetail(err) ?? 'Failed to submit terminal output.')
        } finally {
            setIsSubmittingLab(false)
        }
    }

    const selectScreenshot = (file: File | undefined): void => {
        if (!file) return
        if (file.size > SCREENSHOT_MAX_BYTES) {
            toast.error('File size exceeds 5 MB limit.')
            return
        }
        setScreenshotFile(file)
        setScreenshotPreview(URL.createObjectURL(file))
    }

    const clearScreenshot = (): void => {
        setScreenshotFile(null)
        setScreenshotPreview(detail?.userReflection?.imageUrl || null)
    }

    const submitScreenshot = async (): Promise<void> => {
        if (!screenshotFile) {
            toast.error('Please select an image file first.')
            return
        }
        try {
            setIsSubmittingLab(true)
            const formData = new FormData()
            formData.append('file', screenshotFile)
            if (screenshotNotes.trim()) {
                formData.append('notes', screenshotNotes.trim())
            }
            const res = await api.post(`${endpoint}/screenshot-submission`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            })
            const xpGained: number = res.data.xpGained || 15
            toast.success('Installation screenshot verified! +15 XP awarded')
            addXP(xpGained)
            setJustCompletedStep('activity')
            if (!detail?.userReflection) setCelebration({ xpEarned: xpGained })
            setScreenshotPreview(res.data.submission?.imageUrl || null)
            setScreenshotFile(null)
            setDetail(prev => prev && { ...prev, userReflection: res.data.submission, userTutorial: res.data.userTutorial })
            refreshOverview()
        } catch (err) {
            toast.error(errorDetail(err) ?? 'Failed to upload screenshot.')
        } finally {
            setIsSubmittingLab(false)
        }
    }

    const answerQuestion = (questionNumber: number, optionId: string): void => {
        setQuizAnswers(prev => ({ ...prev, [String(questionNumber)]: optionId }))
    }

    const submitQuiz = async (): Promise<void> => {
        if (!detail) return
        const questionCount = detail.quiz.questions.length
        if (Object.keys(quizAnswers).length < questionCount) {
            toast.error(`Please answer all ${questionCount} questions before submitting.`)
            return
        }
        try {
            setIsSubmittingQuiz(true)
            const res = await api.post(`${endpoint}/quiz`, { answers: quizAnswers })
            const { score, totalQuestions, passed, results, xpGained } = res.data
            toast.success(`Quiz completed! Scored ${score}/${totalQuestions}${xpGained > 0 ? ` (+${xpGained} XP)` : ''}`)
            if (xpGained > 0) addXP(xpGained)
            setJustCompletedStep('quiz')
            if (passed && !detail.quiz.passed) setCelebration({ xpEarned: xpGained })
            setDetail(prev => prev && {
                ...prev,
                quiz: {
                    hasAttempted: true,
                    score,
                    totalQuestions,
                    passed,
                    submittedAt: new Date().toISOString(),
                    questions: results,
                },
                userTutorial: { ...prev.userTutorial, practiced: 'yes', completed: true },
            })
            refreshOverview()
        } catch {
            toast.error('Failed to submit quiz.')
        } finally {
            setIsSubmittingQuiz(false)
        }
    }

    const retakeQuiz = (): void => {
        setQuizAnswers({})
        setDetail(prev => prev && { ...prev, quiz: { ...prev.quiz, hasAttempted: false } })
    }

    return {
        detail,
        loadFailed,
        justCompletedStep,
        celebration,
        dismissCelebration: () => setCelebration(null),
        videoWatchPercent,
        isVideoBuffering,
        setIsVideoBuffering,
        reportVideoProgress,
        markVideoWatched,
        markReadingComplete,
        reflectionText,
        setReflectionText,
        isSubmittingReflection,
        submitReflection,
        isMarkingActivity,
        markActivityComplete,
        isMarkingAssignment,
        markAssignmentComplete,
        terminalOutput,
        setTerminalOutput,
        screenshotFile,
        screenshotPreview,
        screenshotNotes,
        setScreenshotNotes,
        selectScreenshot,
        clearScreenshot,
        isSubmittingLab,
        submitTerminal,
        submitScreenshot,
        quizAnswers,
        answerQuestion,
        isSubmittingQuiz,
        submitQuiz,
        retakeQuiz,
    }
}
