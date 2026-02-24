import { useState, useCallback } from 'react'
import {
    CheckCircle2, Lock, ChevronDown, ChevronUp,
    Upload, FileCheck, Zap, X, ArrowRight,
    Code, Terminal, BarChart3, Settings, FileText,
    CircleDot, PlayCircle, HelpCircle, Award, Sparkles,
    BookOpenCheck
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { CelebrationModal, type CelebrationType } from './CelebrationModal'

// ===== TYPES =====

type TutorialStatus = 'completed' | 'available' | 'locked'
type TutorialStep = 'watch' | 'quiz' | 'assignment' | 'done'

interface Tutorial {
    id: string
    number: number
    title: string
    status: TutorialStatus
    quizScore: number | null
    quizTotal: number
    assignmentUploaded: boolean
    xpEarned: number
}

interface QuizQuestion {
    id: string
    question: string
    options: string[]
    correctIndex: number
}

// ===== COURSE ICON MAP =====
const courseIconMap: Record<string, React.ReactNode> = {
    'Python': <Code className="h-5 w-5" />,
    'Linux': <Terminal className="h-5 w-5" />,
    'Scilab': <BarChart3 className="h-5 w-5" />,
    'C/C++': <Settings className="h-5 w-5" />,
    'LibreOffice': <FileText className="h-5 w-5" />,
}

// ===== MOCK DATA =====

const ACTIVE_COURSE = {
    title: 'Python',
    totalTutorials: 10,
}

const initialTutorials: Tutorial[] = [
    { id: '1', number: 1, title: 'Getting Started with IPython', status: 'completed', quizScore: 4, quizTotal: 5, assignmentUploaded: true, xpEarned: 45 },
    { id: '2', number: 2, title: 'Basic Data Types in Python', status: 'completed', quizScore: 5, quizTotal: 5, assignmentUploaded: true, xpEarned: 50 },
    { id: '3', number: 3, title: 'Input & Output', status: 'completed', quizScore: 3, quizTotal: 5, assignmentUploaded: true, xpEarned: 35 },
    { id: '4', number: 4, title: 'Lists and List Operations', status: 'completed', quizScore: 5, quizTotal: 5, assignmentUploaded: true, xpEarned: 50 },
    { id: '5', number: 5, title: 'Conditionals', status: 'completed', quizScore: 4, quizTotal: 5, assignmentUploaded: false, xpEarned: 35 },
    { id: '6', number: 6, title: 'Loops and Iterations', status: 'completed', quizScore: 4, quizTotal: 5, assignmentUploaded: true, xpEarned: 45 },
    { id: '7', number: 7, title: 'Working with Dictionaries', status: 'available', quizScore: null, quizTotal: 5, assignmentUploaded: false, xpEarned: 0 },
    { id: '8', number: 8, title: 'Sets and Tuples', status: 'locked', quizScore: null, quizTotal: 5, assignmentUploaded: false, xpEarned: 0 },
    { id: '9', number: 9, title: 'Functions', status: 'locked', quizScore: null, quizTotal: 5, assignmentUploaded: false, xpEarned: 0 },
    { id: '10', number: 10, title: 'File Handling', status: 'locked', quizScore: null, quizTotal: 5, assignmentUploaded: false, xpEarned: 0 },
]

const mockQuizQuestions: QuizQuestion[] = [
    {
        id: '1',
        question: 'What is the correct way to create an empty dictionary in Python?',
        options: ['my_dict = []', 'my_dict = {}', 'my_dict = ()', 'my_dict = set()'],
        correctIndex: 1,
    },
    {
        id: '2',
        question: 'How do you access the value associated with key "name" in a dictionary?',
        options: ['dict.name', 'dict[name]', 'dict["name"]', 'dict.get[name]'],
        correctIndex: 2,
    },
    {
        id: '3',
        question: 'Which method returns all the keys of a dictionary?',
        options: ['.values()', '.items()', '.get()', '.keys()'],
        correctIndex: 3,
    },
    {
        id: '4',
        question: "What happens when you access a key that doesn't exist using square brackets?",
        options: ['Returns None', 'Returns 0', 'Raises KeyError', 'Returns empty string'],
        correctIndex: 2,
    },
    {
        id: '5',
        question: 'Which of the following is NOT a valid dictionary operation?',
        options: ['del dict["key"]', 'dict.pop("key")', 'dict.append("key")', 'dict.update({"key": "val"})'],
        correctIndex: 2,
    },
]

// ===== XP CONSTANTS =====
const XP_TUTORIAL_COMPLETE = 10
const XP_PER_CORRECT = 5
const XP_ASSIGNMENT = 25

// ===== QUIZ MODAL COMPONENT =====

interface QuizModalProps {
    questions: QuizQuestion[]
    onClose: () => void
    onComplete: (score: number, total: number) => void
}

function QuizModal({ questions, onClose, onComplete }: QuizModalProps) {
    const [currentQ, setCurrentQ] = useState(0)
    const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
    const [answers, setAnswers] = useState<(number | null)[]>(new Array(questions.length).fill(null))
    const [showResults, setShowResults] = useState(false)
    const [score, setScore] = useState(0)

    const question = questions[currentQ]
    const isLast = currentQ === questions.length - 1

    const handleSelect = (optionIndex: number) => {
        setSelectedAnswer(optionIndex)
        const newAnswers = [...answers]
        newAnswers[currentQ] = optionIndex
        setAnswers(newAnswers)
    }

    const handleNext = () => {
        if (selectedAnswer === null) return

        if (isLast) {
            // Calculate score
            let correct = 0
            const finalAnswers = [...answers]
            finalAnswers[currentQ] = selectedAnswer
            finalAnswers.forEach((ans, i) => {
                if (ans === questions[i].correctIndex) correct++
            })
            setScore(correct)
            setShowResults(true)
        } else {
            setCurrentQ(currentQ + 1)
            setSelectedAnswer(answers[currentQ + 1])
        }
    }

    const handlePrev = () => {
        if (currentQ > 0) {
            setCurrentQ(currentQ - 1)
            setSelectedAnswer(answers[currentQ - 1])
        }
    }

    const handleFinish = () => {
        onComplete(score, questions.length)
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

            {/* Modal */}
            <div className="relative w-full max-w-lg bg-card border border-border rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="flex items-center justify-between p-5 border-b border-border">
                    <div className="flex items-center gap-2">
                        <HelpCircle className="h-5 w-5 text-primary" />
                        <span className="font-semibold text-sm">Tutorial Quiz</span>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 rounded-lg hover:bg-muted transition-colors"
                    >
                        <X className="h-4 w-4 text-muted-foreground" />
                    </button>
                </div>

                {!showResults ? (
                    <>
                        {/* Progress */}
                        <div className="px-5 pt-4">
                            <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                                <span>Question {currentQ + 1} of {questions.length}</span>
                                <span className="font-mono">{Math.round(((currentQ + 1) / questions.length) * 100)}%</span>
                            </div>
                            <Progress value={((currentQ + 1) / questions.length) * 100} className="h-1.5" />
                        </div>

                        {/* Question */}
                        <div className="p-5">
                            <h3 className="text-base font-semibold leading-relaxed mb-5">
                                {question.question}
                            </h3>

                            {/* Options */}
                            <div className="space-y-2.5">
                                {question.options.map((option, i) => (
                                    <button
                                        key={i}
                                        onClick={() => handleSelect(i)}
                                        className={`w-full flex items-center gap-3 p-3.5 rounded-xl border text-left text-sm transition-all duration-150
                                            ${selectedAnswer === i
                                                ? 'border-primary bg-primary/5 text-foreground ring-1 ring-primary/20'
                                                : 'border-border bg-muted/20 text-foreground hover:border-primary/30 hover:bg-muted/40'
                                            }`}
                                    >
                                        <span className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold shrink-0 transition-colors
                                            ${selectedAnswer === i
                                                ? 'bg-primary text-primary-foreground'
                                                : 'bg-muted text-muted-foreground'
                                            }`}
                                        >
                                            {String.fromCharCode(65 + i)}
                                        </span>
                                        <span className="font-mono text-[13px]">{option}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="flex items-center justify-between p-5 border-t border-border bg-muted/20">
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handlePrev}
                                disabled={currentQ === 0}
                                className="text-muted-foreground"
                            >
                                Previous
                            </Button>
                            <Button
                                size="sm"
                                onClick={handleNext}
                                disabled={selectedAnswer === null}
                                className="gap-1.5"
                            >
                                {isLast ? 'Submit' : 'Next'}
                                <ArrowRight className="h-3.5 w-3.5" />
                            </Button>
                        </div>
                    </>
                ) : (
                    /* Results Screen */
                    <div className="p-8 text-center">
                        <div className="flex justify-center mb-4">
                            <div className={`flex h-20 w-20 items-center justify-center rounded-full ${score >= questions.length * 0.8
                                ? 'bg-success/10'
                                : score >= questions.length * 0.5
                                    ? 'bg-warning/10'
                                    : 'bg-destructive/10'
                                }`}>
                                {score >= questions.length * 0.8 ? (
                                    <Sparkles className="h-10 w-10 text-success" />
                                ) : score >= questions.length * 0.5 ? (
                                    <Award className="h-10 w-10 text-warning" />
                                ) : (
                                    <HelpCircle className="h-10 w-10 text-destructive" />
                                )}
                            </div>
                        </div>

                        <h3 className="text-xl font-bold mb-1">
                            {score >= questions.length * 0.8
                                ? 'Excellent!'
                                : score >= questions.length * 0.5
                                    ? 'Good Job!'
                                    : 'Keep Practicing!'}
                        </h3>
                        <p className="text-sm text-muted-foreground mb-6">
                            You scored {score} out of {questions.length}
                        </p>

                        {/* Score breakdown */}
                        <div className="bg-muted/30 rounded-xl p-4 space-y-3 mb-6 text-left">
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">Correct Answers</span>
                                <span className="font-semibold text-success">{score}/{questions.length}</span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">Quiz XP</span>
                                <span className="font-semibold text-xp-gold flex items-center gap-1">
                                    <Zap className="h-3.5 w-3.5" />
                                    +{score * XP_PER_CORRECT} XP
                                </span>
                            </div>
                            <div className="border-t border-border pt-2 flex items-center justify-between text-sm">
                                <span className="font-medium">Total XP Earned</span>
                                <Badge className="bg-xp-gold/15 text-xp-gold font-mono text-xs">
                                    +{XP_TUTORIAL_COMPLETE + score * XP_PER_CORRECT} XP
                                </Badge>
                            </div>
                        </div>

                        <Button onClick={handleFinish} className="w-full gap-2">
                            Continue
                            <ArrowRight className="h-4 w-4" />
                        </Button>
                    </div>
                )}
            </div>
        </div>
    )
}

// ===== STEP PROGRESS INDICATORS =====

interface StepIndicatorsProps {
    currentStep: TutorialStep
}

function StepIndicators({ currentStep }: StepIndicatorsProps) {
    const steps = [
        { key: 'watch', label: 'Complete Tutorial', icon: PlayCircle },
        { key: 'quiz', label: 'Take Quiz', icon: HelpCircle },
        { key: 'assignment', label: 'Upload Assignment', icon: Upload },
    ]

    const stepOrder = ['watch', 'quiz', 'assignment', 'done']
    const currentIndex = stepOrder.indexOf(currentStep)

    return (
        <div className="flex items-center gap-1 sm:gap-2 mb-5">
            {steps.map((step, i) => {
                const isDone = currentIndex > i
                const isActive = currentIndex === i
                const Icon = step.icon

                return (
                    <div key={step.key} className="flex items-center gap-1 sm:gap-2">
                        <div className="flex items-center gap-1.5">
                            <div className={`flex h-7 w-7 items-center justify-center rounded-full transition-all duration-300
                                ${isDone
                                    ? 'bg-success text-success-foreground'
                                    : isActive
                                        ? 'bg-primary text-primary-foreground animate-pulse'
                                        : 'bg-muted text-muted-foreground'
                                }`}
                            >
                                {isDone ? (
                                    <CheckCircle2 className="h-3.5 w-3.5" />
                                ) : (
                                    <Icon className="h-3.5 w-3.5" />
                                )}
                            </div>
                            <span className={`text-[11px] hidden sm:inline transition-colors
                                ${isDone ? 'text-success font-medium' : isActive ? 'text-primary font-medium' : 'text-muted-foreground'}`}
                            >
                                {step.label}
                            </span>
                        </div>
                        {i < steps.length - 1 && (
                            <div className={`w-4 sm:w-8 h-0.5 rounded-full transition-colors duration-300
                                ${currentIndex > i ? 'bg-success' : 'bg-muted'}`}
                            />
                        )}
                    </div>
                )
            })}
        </div>
    )
}

// ===== ASSIGNMENT UPLOAD COMPONENT =====

interface AssignmentUploadProps {
    onUpload: () => void
    uploaded: boolean
}

function AssignmentUpload({ onUpload, uploaded }: AssignmentUploadProps) {
    const [fileName, setFileName] = useState<string | null>(null)

    const handleFakeUpload = () => {
        setFileName('dictionary_practice.py')
        setTimeout(() => onUpload(), 500)
    }

    if (uploaded || fileName) {
        return (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-success/5 border border-success/20">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-success/10">
                    <FileCheck className="h-5 w-5 text-success" />
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-success">Assignment Uploaded!</p>
                    <p className="text-xs text-muted-foreground font-mono truncate mt-0.5">{fileName || 'assignment.py'}</p>
                </div>
                <Badge className="bg-xp-gold/15 text-xp-gold text-xs font-mono shrink-0">
                    <Zap className="h-3 w-3 mr-1" />
                    +{XP_ASSIGNMENT} XP
                </Badge>
            </div>
        )
    }

    return (
        <button
            onClick={handleFakeUpload}
            className="w-full flex flex-col items-center gap-2 p-6 rounded-xl border-2 border-dashed border-primary/20 bg-primary/[0.02] hover:border-primary/40 hover:bg-primary/5 transition-all duration-200 cursor-pointer group"
        >
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-primary/10 group-hover:bg-primary/15 transition-colors">
                <Upload className="h-5 w-5 text-primary" />
            </div>
            <div className="text-center">
                <p className="text-sm font-medium">Upload Assignment</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                    Click to upload your practice file · Earn <span className="text-xp-gold font-semibold">+{XP_ASSIGNMENT} XP</span>
                </p>
            </div>
        </button>
    )
}

// ===== TUTORIAL TIMELINE ITEM =====

interface TimelineItemProps {
    tutorial: Tutorial
    isLast: boolean
}

function TimelineItem({ tutorial, isLast }: TimelineItemProps) {
    return (
        <div className="flex gap-3">
            {/* Timeline connector */}
            <div className="flex flex-col items-center">
                <div className={`flex h-8 w-8 items-center justify-center rounded-full shrink-0 transition-all
                    ${tutorial.status === 'completed'
                        ? 'bg-success text-success-foreground'
                        : tutorial.status === 'available'
                            ? 'bg-primary text-primary-foreground ring-4 ring-primary/20'
                            : 'bg-muted text-muted-foreground'
                    }`}
                >
                    {tutorial.status === 'completed' ? (
                        <CheckCircle2 className="h-4 w-4" />
                    ) : tutorial.status === 'available' ? (
                        <CircleDot className="h-4 w-4" />
                    ) : (
                        <Lock className="h-3.5 w-3.5" />
                    )}
                </div>
                {!isLast && (
                    <div className={`w-0.5 flex-1 min-h-[20px] transition-colors
                        ${tutorial.status === 'completed' ? 'bg-success/40' : 'bg-muted'}`}
                    />
                )}
            </div>

            {/* Content */}
            <div className={`flex-1 pb-4 min-w-0 ${tutorial.status === 'locked' ? 'opacity-50' : ''}`}>
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium truncate">
                        {tutorial.number}. {tutorial.title}
                    </span>
                    {tutorial.status === 'completed' && tutorial.quizScore !== null && (
                        <Badge variant="secondary" className="bg-success/10 text-success text-[10px] px-1.5 h-5 gap-0.5 shrink-0">
                            {tutorial.quizScore}/{tutorial.quizTotal}
                        </Badge>
                    )}
                    {tutorial.status === 'completed' && tutorial.assignmentUploaded && (
                        <Badge variant="secondary" className="bg-primary/10 text-primary text-[10px] px-1.5 h-5 gap-0.5 shrink-0">
                            <FileCheck className="h-2.5 w-2.5" />
                        </Badge>
                    )}
                </div>
                {tutorial.status === 'completed' && (
                    <p className="text-[11px] text-muted-foreground mt-0.5 flex items-center gap-1">
                        <Zap className="h-3 w-3 text-xp-gold" />
                        {tutorial.xpEarned} XP earned
                    </p>
                )}
                {tutorial.status === 'available' && (
                    <p className="text-[11px] text-primary mt-0.5 font-medium">
                        Current tutorial
                    </p>
                )}
            </div>
        </div>
    )
}

// ===== MAIN COMPONENT =====

export function ActiveCourseTracker() {
    const [tutorials, setTutorials] = useState<Tutorial[]>(initialTutorials)
    const [currentStep, setCurrentStep] = useState<TutorialStep>('watch')
    const [showQuiz, setShowQuiz] = useState(false)
    const [showTimeline, setShowTimeline] = useState(false)

    // Celebration state
    const [celebration, setCelebration] = useState<{
        type: CelebrationType
        xpEarned: number
        title?: string
        subtitle?: string
    } | null>(null)

    const currentTutorial = tutorials.find(t => t.status === 'available')
    const completedCount = tutorials.filter(t => t.status === 'completed').length
    const overallProgress = Math.round((completedCount / tutorials.length) * 100)

    const handleShare = useCallback(() => {
        // TODO: Wire up to ComposeModal with pre-filled achievement text
        setCelebration(null)
        console.log('Share achievement — will open compose modal')
    }, [])

    const handleCloseCelebration = useCallback(() => {
        setCelebration(null)
    }, [])

    const handleMarkComplete = useCallback(() => {
        setCurrentStep('quiz')
    }, [])

    const handleStartQuiz = useCallback(() => {
        setShowQuiz(true)
    }, [])

    const handleQuizComplete = useCallback((score: number, _total: number) => {
        setShowQuiz(false)
        const quizXP = score * XP_PER_CORRECT

        if (currentTutorial) {
            setTutorials(prev => prev.map(t =>
                t.id === currentTutorial.id
                    ? { ...t, quizScore: score, xpEarned: XP_TUTORIAL_COMPLETE + quizXP }
                    : t
            ))
        }

        setCurrentStep('assignment')
    }, [currentTutorial])

    const handleAssignmentUpload = useCallback(() => {
        if (!currentTutorial) return

        const totalXP = XP_TUTORIAL_COMPLETE + (currentTutorial.quizScore || 0) * XP_PER_CORRECT + XP_ASSIGNMENT

        // Check if this completes the course (last tutorial)
        const isLastTutorial = currentTutorial.number === tutorials.length

        setTutorials(prev => {
            const updated = prev.map(t => {
                if (t.id === currentTutorial.id) {
                    return { ...t, assignmentUploaded: true, status: 'completed' as const, xpEarned: totalXP }
                }
                // Unlock next tutorial
                if (t.number === currentTutorial.number + 1 && t.status === 'locked') {
                    return { ...t, status: 'available' as const }
                }
                return t
            })
            return updated
        })

        setCurrentStep('done')

        // Show appropriate celebration
        if (isLastTutorial) {
            // Course complete! Big celebration
            setCelebration({
                type: 'course_complete',
                xpEarned: totalXP,
                title: `${ACTIVE_COURSE.title} Complete! 🏆`,
                subtitle: `You've mastered all ${tutorials.length} tutorials. Share your achievement!`,
            })
        } else {
            // Tutorial complete
            setCelebration({
                type: 'tutorial_complete',
                xpEarned: totalXP,
                title: 'Tutorial Mastered! ✨',
                subtitle: `You earned ${totalXP} XP — next tutorial is unlocked!`,
            })
        }

        // Reset step for next tutorial after celebration
        setTimeout(() => {
            setCurrentStep('watch')
        }, 500)
    }, [currentTutorial, tutorials.length])

    const handleQuizClose = useCallback(() => {
        setShowQuiz(false)
    }, [])

    // All tutorials completed
    const allDone = completedCount === tutorials.length

    return (
        <>
            <Card className="border-primary/20 bg-gradient-to-br from-primary/[0.03] via-transparent to-transparent overflow-hidden">
                <CardContent className="p-5 sm:p-6">
                    {/* Header */}
                    <div className="flex items-center justify-between gap-3 mb-5">
                        <div className="flex items-center gap-3 min-w-0">
                            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 shrink-0">
                                {courseIconMap[ACTIVE_COURSE.title] || <Code className="h-5 w-5 text-primary" />}
                            </div>
                            <div className="min-w-0">
                                <div className="flex items-center gap-2">
                                    <h2 className="text-sm font-bold">{ACTIVE_COURSE.title}</h2>
                                    <Badge variant="secondary" className="text-[10px] px-1.5 h-5">
                                        {completedCount}/{tutorials.length}
                                    </Badge>
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                    <Progress value={overallProgress} className="h-1.5 flex-1 max-w-[120px]" />
                                    <span className="text-[11px] text-muted-foreground font-mono">{overallProgress}%</span>
                                </div>
                            </div>
                        </div>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowTimeline(!showTimeline)}
                            className="shrink-0 text-xs text-muted-foreground hover:text-foreground gap-1"
                        >
                            {showTimeline ? 'Hide' : 'All Tutorials'}
                            {showTimeline ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                        </Button>
                    </div>

                    {/* Current Tutorial Interaction */}
                    {currentTutorial && !allDone && currentStep !== 'done' && (
                        <div className="mb-4">
                            {/* Step Indicators */}
                            <StepIndicators currentStep={currentStep} />

                            {/* Current tutorial info */}
                            <div className="bg-muted/30 rounded-xl p-4 border border-border/50">
                                <div className="flex items-center gap-2 mb-1">
                                    <BookOpenCheck className="h-4 w-4 text-primary" />
                                    <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
                                        Tutorial {currentTutorial.number}
                                    </span>
                                </div>
                                <h3 className="text-base font-semibold mb-4">{currentTutorial.title}</h3>

                                {/* Step content */}
                                {currentStep === 'watch' && (
                                    <Button
                                        onClick={handleMarkComplete}
                                        className="w-full gap-2 bg-primary hover:bg-primary/90"
                                    >
                                        <CheckCircle2 className="h-4 w-4" />
                                        I've Completed This Tutorial
                                    </Button>
                                )}

                                {currentStep === 'quiz' && (
                                    <div className="space-y-3">
                                        <div className="flex items-center gap-2 p-3 rounded-lg bg-success/5 border border-success/20">
                                            <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
                                            <span className="text-sm text-success">
                                                Tutorial marked as complete!
                                            </span>
                                            <Badge className="bg-xp-gold/15 text-xp-gold text-[10px] font-mono ml-auto shrink-0">
                                                +{XP_TUTORIAL_COMPLETE} XP
                                            </Badge>
                                        </div>
                                        <Button
                                            onClick={handleStartQuiz}
                                            className="w-full gap-2"
                                        >
                                            <HelpCircle className="h-4 w-4" />
                                            Take Quiz · Earn up to +{currentTutorial.quizTotal * XP_PER_CORRECT} XP
                                        </Button>
                                    </div>
                                )}

                                {currentStep === 'assignment' && (
                                    <div className="space-y-3">
                                        <div className="flex items-center gap-2 p-3 rounded-lg bg-success/5 border border-success/20">
                                            <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
                                            <span className="text-sm text-success">
                                                Quiz completed! {currentTutorial.quizScore}/{currentTutorial.quizTotal}
                                            </span>
                                            <Badge className="bg-xp-gold/15 text-xp-gold text-[10px] font-mono ml-auto shrink-0">
                                                +{(currentTutorial.quizScore || 0) * XP_PER_CORRECT} XP
                                            </Badge>
                                        </div>
                                        <AssignmentUpload
                                            onUpload={handleAssignmentUpload}
                                            uploaded={currentTutorial.assignmentUploaded}
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* All complete inline indicator */}
                    {allDone && (
                        <div className="mb-4 p-5 rounded-xl bg-gradient-to-r from-success/10 to-primary/10 border border-success/20 text-center">
                            <Award className="h-10 w-10 text-success mx-auto mb-2" />
                            <h3 className="font-bold text-lg">Course Complete! 🏆</h3>
                            <p className="text-sm text-muted-foreground mt-1">
                                You've finished all {tutorials.length} tutorials in {ACTIVE_COURSE.title}!
                            </p>
                        </div>
                    )}

                    {/* Expandable Timeline */}
                    {showTimeline && (
                        <div className="mt-4 pt-4 border-t border-border">
                            <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-4">
                                All Tutorials
                            </p>
                            <div>
                                {tutorials.map((tutorial, i) => (
                                    <TimelineItem
                                        key={tutorial.id}
                                        tutorial={tutorial}
                                        isLast={i === tutorials.length - 1}
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Quiz Modal Portal */}
            {showQuiz && (
                <QuizModal
                    questions={mockQuizQuestions}
                    onClose={handleQuizClose}
                    onComplete={handleQuizComplete}
                />
            )}

            {/* Celebration Modal */}
            {celebration && (
                <CelebrationModal
                    type={celebration.type}
                    xpEarned={celebration.xpEarned}
                    title={celebration.title}
                    subtitle={celebration.subtitle}
                    onClose={handleCloseCelebration}
                    onShare={handleShare}
                />
            )}
        </>
    )
}
