import { useState, useCallback, useEffect, } from 'react'
import {
    CheckCircle2, ChevronDown, Sparkles, Lock,
    Zap, Code, Terminal, BarChart3, Settings, FileText,
    BookOpenCheck
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { CelebrationModal, type CelebrationType } from './CelebrationModal'
import { FeedbackModal } from './FeedbackModal'
import { useUserStore } from '@/store/userStore'
import type { RadioValue, Tutorial, TutorialField } from '@/types'

// ===== POINTS =====

const XP_WATCHED = 10
const XP_PRACTICED = 10
const XP_ASSIGNMENT = 5
const XP_FORUM_ASK = 5
const XP_FORUM_ANSWER = 5

function calcXP(t: Tutorial): number {
    return (
        (t.watched === 'yes' ? XP_WATCHED : 0) +
        (t.practiced === 'yes' ? XP_PRACTICED : 0) +
        (t.assignmentDone === 'yes' ? XP_ASSIGNMENT : 0) +
        (t.forumAsked === 'yes' ? XP_FORUM_ASK : 0) +
        (t.forumAnswered === 'yes' ? XP_FORUM_ANSWER : 0)
    )
}

// ===== COURSE ICON MAP =====
const courseIconMap: Record<string, React.ReactNode> = {
    'Python': <Code className="h-5 w-5" />,
    'Linux': <Terminal className="h-5 w-5" />,
    'Scilab': <BarChart3 className="h-5 w-5" />,
    'C/C++': <Settings className="h-5 w-5" />,
    'LibreOffice': <FileText className="h-5 w-5" />,
}



// ===== ANSWER DISPLAY (read-only, for completed tutorials) =====

function AnswerSummary({ label, value, isBonus }: { label: string; value: RadioValue; isBonus?: boolean }) {
    const isYes = value === 'yes'
    const isAnswered = value !== null
    return (
        <div className="flex items-center justify-between py-1">
            <span className="text-[13px] text-muted-foreground">{label}</span>
            {isAnswered ? (
                <span className={`text-xs font-medium px-2 py-0.5 rounded ${isYes
                    ? (isBonus ? 'bg-primary/10 text-primary' : 'bg-success/10 text-success')
                    : 'bg-muted text-muted-foreground'
                    }`}>
                    {isYes ? '✓ Yes' : '✗ No'}
                </span>
            ) : (
                <span className="text-[10px] text-muted-foreground/50">—</span>
            )}
        </div>
    )
}

// ===== QUESTION ROW =====

interface QuestionRowProps {
    label: string
    points: number
    isBonus?: boolean
    value: RadioValue
    fieldId: string
    onChange: (value: RadioValue) => void
    disabled?: boolean
}

function QuestionRow({ label, points, isBonus, value, fieldId, onChange, disabled }: QuestionRowProps) {
    return (
        <div className={`flex items-center gap-3 py-2.5 transition-opacity ${disabled ? 'opacity-35 pointer-events-none' : ''}`}>
            {/* Label + points */}
            <div className="flex-1 min-w-0 flex items-center gap-1.5">
                {disabled && <Lock className="h-3.5 w-3.5 text-muted-foreground/50 shrink-0" />}
                <span className={`text-sm text-muted-foreground ${value === 'yes' ? 'text-success font-medium' : ''}`}>
                    {label}
                </span>
                {isBonus && (
                    <span className="text-[10px] font-semibold uppercase tracking-wide bg-primary/10 text-primary px-1.5 py-0.5 rounded">Bonus</span>
                )}
                <span className={`text-[11px] ${isBonus ? 'text-primary' : 'text-xp-gold'}`}>
                    +{points}
                </span>
            </div>

            {/* Radio: Yes / No */}
            <RadioGroup
                value={value ?? ''}
                onValueChange={(v) => onChange(v as RadioValue)}
                className="flex items-center gap-2"
            >
                <label htmlFor={`${fieldId}-yes`} className="flex items-center gap-1.5 px-3 py-2 rounded-md cursor-pointer hover:bg-muted/50 transition-colors">
                    <RadioGroupItem value="yes" id={`${fieldId}-yes`} className="h-4 w-4" />
                    <span className="text-sm text-muted-foreground">Yes</span>
                </label>
                <label htmlFor={`${fieldId}-no`} className="flex items-center gap-1.5 px-3 py-2 rounded-md cursor-pointer hover:bg-muted/50 transition-colors">
                    <RadioGroupItem value="no" id={`${fieldId}-no`} className="h-4 w-4" />
                    <span className="text-sm text-muted-foreground">No</span>
                </label>
            </RadioGroup>
        </div>
    )
}

// ===== TUTORIAL CARD =====

interface TutorialCardProps {
    tutorial: Tutorial
    onRadioChange: (tutorialId: string, field: TutorialField, value: RadioValue) => void
}

function TutorialCard({ tutorial, onRadioChange }: TutorialCardProps) {
    const [isOpen, setIsOpen] = useState(!tutorial.completed)
    const currentXP = calcXP(tutorial)
    const isWatched = tutorial.watched === 'yes'
    const isPracticed = tutorial.practiced === 'yes'

    // Count how many bonus stars earned
    const bonusCount = [tutorial.assignmentDone, tutorial.forumAsked, tutorial.forumAnswered]
        .filter(v => v === 'yes').length

    // ======= COMPLETED CARD =======
    if (tutorial.completed) {
        return (
            <Collapsible open={isOpen} onOpenChange={setIsOpen}>
                <div className="rounded-lg border border-border/40 bg-card">
                    <CollapsibleTrigger asChild>
                        <button className="flex items-center gap-2.5 w-full px-4 py-3 text-left hover:bg-muted/20 transition-colors rounded-lg">
                            <CheckCircle2 className="h-4.5 w-4.5 text-success shrink-0" />
                            <span className="text-sm font-semibold flex-1 truncate">
                                {tutorial.number}. {tutorial.title}
                            </span>
                            <span className="text-[11px] text-xp-gold font-medium flex items-center gap-0.5 shrink-0">
                                <Zap className="h-3 w-3" />
                                {tutorial.xpEarned}
                            </span>
                            {bonusCount > 0 && (
                                <span className="text-[9px] bg-primary/10 text-primary px-1.5 py-0.5 rounded font-medium">
                                    {'★'.repeat(bonusCount)}
                                </span>
                            )}
                            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform duration-200 shrink-0 ${isOpen ? 'rotate-180' : ''}`} />
                        </button>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                        <div className="px-4 pb-3 border-t border-border/20 pt-2">
                            {/* Read-only: required answers */}
                            <AnswerSummary label="Watched the tutorial" value={tutorial.watched} />
                            <AnswerSummary label="Practiced the tutorial" value={tutorial.practiced} />

                            {/* Bonus questions — answerable even after completion */}
                            <div className="mt-1.5 pt-1.5 border-t border-dashed border-border/30">
                                {tutorial.assignmentDone === 'yes' ? (
                                    <AnswerSummary label="Finished the assignment" value="yes" isBonus />
                                ) : (
                                    <QuestionRow
                                        label="Have you finished the assignment?"
                                        points={XP_ASSIGNMENT}
                                        isBonus
                                        value={tutorial.assignmentDone}
                                        fieldId={`t${tutorial.id}-assign`}
                                        onChange={(v) => onRadioChange(tutorial.id, 'assignmentDone', v)}
                                    />
                                )}
                                {tutorial.forumAsked === 'yes' ? (
                                    <AnswerSummary label="Asked a question in the forum" value="yes" isBonus />
                                ) : (
                                    <QuestionRow
                                        label="Have you asked a question in the forum?"
                                        points={XP_FORUM_ASK}
                                        isBonus
                                        value={tutorial.forumAsked}
                                        fieldId={`t${tutorial.id}-forum-ask`}
                                        onChange={(v) => onRadioChange(tutorial.id, 'forumAsked', v)}
                                    />
                                )}
                                {tutorial.forumAnswered === 'yes' ? (
                                    <AnswerSummary label="Answered a question in the forum" value="yes" isBonus />
                                ) : (
                                    <QuestionRow
                                        label="Have you answered a question in the forum?"
                                        points={XP_FORUM_ANSWER}
                                        isBonus
                                        value={tutorial.forumAnswered}
                                        fieldId={`t${tutorial.id}-forum-ans`}
                                        onChange={(v) => onRadioChange(tutorial.id, 'forumAnswered', v)}
                                    />
                                )}
                            </div>
                        </div>
                    </CollapsibleContent>
                </div>
            </Collapsible>
        )
    }

    // ======= ACTIVE CARD =======
    return (
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
            <div className="rounded-lg border border-border/60 bg-card transition-all hover:border-primary/30">
                {/* Header row — clickable to toggle */}
                <CollapsibleTrigger asChild>
                    <button className="flex items-center justify-between w-full px-4 py-3 bg-muted/30 rounded-t-lg border-b border-border/30 text-left hover:bg-muted/40 transition-colors">
                        <div className="flex items-center gap-2 min-w-0">
                            <BookOpenCheck className="h-4 w-4 text-primary shrink-0" />
                            <span className="text-sm font-semibold truncate">
                                {tutorial.number}. {tutorial.title}
                            </span>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                            {currentXP > 0 && (
                                <Badge className="bg-xp-gold/10 text-xp-gold border-0 text-[9px] px-1.5 py-0 h-4 gap-0.5">
                                    <Zap className="h-2.5 w-2.5" />
                                    {currentXP}
                                </Badge>
                            )}
                            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
                        </div>
                    </button>
                </CollapsibleTrigger>

                {/* Collapsible questions */}
                <CollapsibleContent>
                    <div className="px-4 py-2">
                        {/* STEP 1: Watch — always enabled */}
                        <QuestionRow
                            label="Have you watched the tutorial?"
                            points={XP_WATCHED}
                            value={tutorial.watched}
                            fieldId={`t${tutorial.id}-watched`}
                            onChange={(v) => onRadioChange(tutorial.id, 'watched', v)}
                        />

                        {/* STEP 2: Practice — locked until watched */}
                        <QuestionRow
                            label="Have you practiced the tutorial?"
                            points={XP_PRACTICED}
                            value={tutorial.practiced}
                            fieldId={`t${tutorial.id}-practiced`}
                            onChange={(v) => onRadioChange(tutorial.id, 'practiced', v)}
                            disabled={!isWatched}
                        />

                        {/* BONUS — locked until practiced */}
                        {!isPracticed && (
                            <div className="flex items-center gap-1.5 py-2 text-[11px] text-muted-foreground/60">
                                <Lock className="h-3 w-3" />
                                <span>{!isWatched ? 'Watch and practice the tutorial to unlock bonus questions' : 'Practice the tutorial to unlock bonus questions'}</span>
                            </div>
                        )}
                        <QuestionRow
                            label="Have you finished the assignment?"
                            points={XP_ASSIGNMENT}
                            isBonus
                            value={tutorial.assignmentDone}
                            fieldId={`t${tutorial.id}-assign`}
                            onChange={(v) => onRadioChange(tutorial.id, 'assignmentDone', v)}
                            disabled={!isPracticed}
                        />
                        <QuestionRow
                            label="Have you asked a question in the forum?"
                            points={XP_FORUM_ASK}
                            isBonus
                            value={tutorial.forumAsked}
                            fieldId={`t${tutorial.id}-forum-ask`}
                            onChange={(v) => onRadioChange(tutorial.id, 'forumAsked', v)}
                            disabled={!isPracticed}
                        />
                        <QuestionRow
                            label="Have you answered a question in the forum?"
                            points={XP_FORUM_ANSWER}
                            isBonus
                            value={tutorial.forumAnswered}
                            fieldId={`t${tutorial.id}-forum-ans`}
                            onChange={(v) => onRadioChange(tutorial.id, 'forumAnswered', v)}
                            disabled={!isPracticed}
                        />
                    </div>
                </CollapsibleContent>
            </div>
        </Collapsible>
    )
}

// ===== MAIN COMPONENT =====

export function ActiveCourseTracker() {
    const {
        tutorials,
        activeCourseId,
        fetchTutorials,
        updateTutorials,
        addXP,
        courses
    } = useUserStore()

    const currentCourse = courses.find(c => c.id == activeCourseId)
    const courseTitle = currentCourse?.title || 'Course'

    useEffect(() => {
        if (activeCourseId) {
            fetchTutorials(activeCourseId)
        }
    }, [])


    // Bonus feedback toast
    const [bonusFeedback, setBonusFeedback] = useState<{ title: string; xp: number } | null>(null)

    const [celebration, setCelebration] = useState<{
        type: CelebrationType
        xpEarned: number
        title?: string
        subtitle?: string
    } | null>(null)

    // Feedback modal state — includes pending "No" info so we can save or revert
    const [feedbackModal, setFeedbackModal] = useState<{
        tutorialId: string
        tutorialTitle: string
        stepType: string
        field: TutorialField
        oldValue: RadioValue
    } | null>(null)

    const completedCount = tutorials.filter(t => t.completed).length
    const overallProgress = Math.round((completedCount / tutorials.length) * 100)
    const totalXP = tutorials.reduce((sum, t) => sum + t.xpEarned, 0)

    const handleRadioChange = useCallback((tutorialId: string, field: TutorialField, value: RadioValue) => {
        const tutorial = tutorials.find(t => t.id === tutorialId)
        if (!tutorial) return

        const oldValue = tutorial[field]

        // When "No" is selected: DON'T save yet — open feedback modal first
        if (value === 'no') {
            setFeedbackModal({
                tutorialId: tutorial.id,
                tutorialTitle: tutorial.title,
                stepType: field,
                field,
                oldValue,
            })
            return  // <-- Don't call updateTutorials yet!
        }

        // "Yes" is saved immediately as before
        updateTutorials(activeCourseId, tutorialId, field, value)

        if (value === 'yes' && oldValue !== 'yes') {
            let xpEarned = 0;
            if (field === 'watched') xpEarned = XP_WATCHED;
            else if (field === 'practiced') xpEarned = XP_PRACTICED;
            else if (field === 'assignmentDone') xpEarned = XP_ASSIGNMENT;
            else if (field === 'forumAsked') xpEarned = XP_FORUM_ASK;
            else if (field === 'forumAnswered') xpEarned = XP_FORUM_ANSWER;

            if (xpEarned > 0) {
                addXP(xpEarned)

                if (field === 'practiced') {
                    const isLastTutorial = completedCount + 1 === tutorials.length
                    if (isLastTutorial) {
                        setCelebration({
                            type: 'course_complete',
                            xpEarned,
                            title: `${courseTitle} Complete! 🏆`,
                            subtitle: `You've mastered all ${tutorials.length} tutorials!`,
                        })
                    } else {
                        setCelebration({
                            type: 'tutorial_complete',
                            xpEarned,
                            title: 'Tutorial Complete! ✨',
                            subtitle: `+${xpEarned} XP earned`,
                        })
                    }
                } else {
                    setBonusFeedback({ title: tutorial.title, xp: xpEarned })
                    setTimeout(() => setBonusFeedback(null), 3000)
                }
            }
        }
    }, [tutorials, activeCourseId, updateTutorials, completedCount, courseTitle, addXP])

    // Called when feedback is successfully submitted — NOW save the "No"
    const handleFeedbackSubmitted = useCallback(() => {
        if (!feedbackModal) return
        updateTutorials(activeCourseId, feedbackModal.tutorialId, feedbackModal.field, 'no')
        setFeedbackModal(null)
    }, [feedbackModal, activeCourseId, updateTutorials])

    // Called when modal is closed without submitting — revert, don't save "No"
    const handleFeedbackCancelled = useCallback(() => {
        setFeedbackModal(null)
        // Nothing to revert — we never saved the "No" in the first place
    }, [])

    const allDone = completedCount === tutorials.length

    return (
        <>
            <Card className="border-primary/20 bg-gradient-to-br from-primary/[0.03] via-transparent to-transparent overflow-hidden">
                <CardContent className="p-4 sm:p-5">
                    {/* Header */}
                    <div className="flex items-center justify-between gap-3 mb-4">
                        <div className="flex items-center gap-3 min-w-0">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                                {courseIconMap[courseTitle] || <Code className="h-5 w-5 text-primary" />}
                            </div>
                            <div className="min-w-0">
                                <div className="flex items-center gap-2">
                                    <h2 className="text-lg font-bold">{courseTitle}</h2>
                                    <Badge variant="secondary" className="text-[10px] px-1.5 h-4">
                                        {completedCount}/{tutorials.length}
                                    </Badge>
                                </div>
                                <div className="flex items-center gap-2 mt-0.5">
                                    <Progress value={overallProgress} className="h-1.5 flex-1 max-w-[120px]" />
                                    <span className="text-[10px] text-muted-foreground font-mono">{overallProgress}%</span>
                                </div>
                            </div>
                        </div>
                        <span className="text-xs text-xp-gold font-semibold flex items-center gap-0.5 shrink-0">
                            <Zap className="h-4 w-4" />
                            {totalXP} XP
                        </span>
                    </div>

                    {/* Bonus feedback toast */}
                    {bonusFeedback && (
                        <div className="mb-3 flex items-center gap-2 px-3 py-2 rounded-lg bg-primary/10 border border-primary/20 animate-in fade-in slide-in-from-top-2 duration-300">
                            <Sparkles className="h-4 w-4 text-primary shrink-0" />
                            <span className="text-xs text-primary font-medium">
                                +{bonusFeedback.xp} bonus XP earned for "{bonusFeedback.title}"!
                            </span>
                        </div>
                    )}

                    {/* All complete */}
                    {allDone && (
                        <div className="mb-3 p-4 rounded-lg bg-gradient-to-r from-success/10 to-primary/10 border border-success/20 text-center">
                            <CheckCircle2 className="h-8 w-8 text-success mx-auto mb-1" />
                            <h3 className="font-bold text-sm">Course Complete! 🏆</h3>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                All {tutorials.length} tutorials · {totalXP} XP earned
                            </p>
                        </div>
                    )}

                    {/* ---- ALL TUTORIALS ---- */}
                    <div className="space-y-1.5">
                        {tutorials.map(tutorial => (
                            <TutorialCard
                                key={tutorial.id}
                                tutorial={tutorial}
                                onRadioChange={handleRadioChange}
                            />
                        ))}
                    </div>

                    {/* Legend */}
                    <div className="flex items-center justify-center gap-3 mt-3 text-[9px] text-muted-foreground flex-wrap">
                        <span>Watch = +{XP_WATCHED}</span>
                        <span>Practice = +{XP_PRACTICED}</span>
                        <span className="text-primary">★ Assignment = +{XP_ASSIGNMENT}</span>
                        <span className="text-primary">★ Forum = +{XP_FORUM_ASK}</span>
                    </div>
                </CardContent>
            </Card>

            {celebration && (
                <CelebrationModal
                    type={celebration.type}
                    xpEarned={celebration.xpEarned}
                    title={celebration.title}
                    subtitle={celebration.subtitle}
                    onClose={() => setCelebration(null)}
                    onShare={() => setCelebration(null)}
                />
            )}

            {feedbackModal && (
                <FeedbackModal
                    tutorialId={feedbackModal.tutorialId}
                    tutorialTitle={feedbackModal.tutorialTitle}
                    stepType={feedbackModal.stepType}
                    onClose={handleFeedbackCancelled}
                    onSubmitted={handleFeedbackSubmitted}
                />
            )}
        </>
    )
}
