import { useState, useCallback, useEffect } from 'react'
import {
    CheckCircle2, ChevronDown, Sparkles, Lock,
    Zap, Code, Terminal, BarChart3, Settings, FileText,
    BookOpenCheck, Link2, ShieldCheck, ArrowUpRight, Circle, Clock,
    ClipboardList,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { CelebrationModal, type CelebrationType } from './CelebrationModal'
import { FeedbackModal } from './FeedbackModal'
import { useUserStore } from '@/store/userStore'
import type { RadioValue, Tutorial, TutorialField, ForumPost } from '@/types'

// ===== POINTS =====

const XP_WATCHED = 10
const XP_PRACTICED = 10
const XP_ASSIGNMENT = 5
const XP_FORUM_ASK = 5
const XP_FORUM_ANS = 10

function calcXP(t: Tutorial): number {
    return (
        (t.watched === 'yes' ? XP_WATCHED : 0) +
        (t.practiced === 'yes' ? XP_PRACTICED : 0) +
        (t.assignmentDone === 'yes' ? XP_ASSIGNMENT : 0)
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
    points?: number
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
                {points != null && points > 0 && (
                    <span className={`text-[11px] ${isBonus ? 'text-primary' : 'text-xp-gold'}`}>
                        +{points}
                    </span>
                )}
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

// ===== FORUM POST CARD (individual verified post) =====

function ForumPostCard({ post, label, points }: { post: ForumPost; label: string; points: number }) {
    const postedDate = post.postedAt
        ? new Date(post.postedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        : null

    const isPending = !post.xpAwarded

    return (
        <div className={`py-1.5 ${isPending ? 'opacity-70' : ''}`}>
            <div className="flex items-center gap-2">
                {isPending ? (
                    <Clock className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                ) : (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                )}
                <span className="text-sm text-foreground font-medium flex-1">{label}</span>
                <span className={`text-[11px] font-medium ${isPending ? 'text-muted-foreground' : 'text-emerald-500'}`}>
                    +{points} {isPending && '(Pending)'}
                </span>
            </div>
            {post.title && (
                <p className="text-[12px] text-muted-foreground pl-6 truncate mt-0.5">
                    &ldquo;{post.title}&rdquo;
                </p>
            )}
            <div className="flex items-center gap-2 pl-6 mt-0.5">
                {postedDate && (
                    <span className="text-[10px] text-muted-foreground/60">{postedDate}</span>
                )}
                {postedDate && post.forumUrl && (
                    <span className="text-muted-foreground/30">&middot;</span>
                )}
                {post.forumUrl && (
                    <a
                        href={post.forumUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] text-primary/70 hover:text-primary flex items-center gap-0.5 transition-colors"
                    >
                        View on forum
                        <ArrowUpRight className="h-2.5 w-2.5" />
                    </a>
                )}
            </div>
        </div>
    )
}

// ===== FORUM ACTIVITY SECTION (replaces the old radio buttons) =====

function ForumActivitySection({
    forumCategory,
    forumPosts,
}: {
    forumCategory?: string | null
    forumPosts: ForumPost[]
}) {
    const questions = forumPosts.filter(p => p.activityType === 'question')
    const answers = forumPosts.filter(p => p.activityType === 'answer')
    const hasAsked = questions.length > 0
    const hasAnswered = answers.length > 0
    const hasAnyActivity = hasAsked || hasAnswered
    const isFullyPending = forumPosts.length > 0 && forumPosts.every(p => !p.xpAwarded)
    const hasPending = forumPosts.some(p => !p.xpAwarded)

    const forumDeepLink = forumCategory
        ? `https://forums.spoken-tutorial.org/filter/${forumCategory.replace(/ /g, '-')}/`
        : 'https://forums.spoken-tutorial.org/'

    return (
        <div
            className={`mt-2.5 rounded-lg border transition-colors ${
                hasAnyActivity
                    ? isFullyPending ? 'border-border/60 bg-muted/10' : 'border-emerald-500/25 bg-emerald-500/[0.03]'
                    : 'border-border/40 bg-muted/[0.06]'
            } px-3 pt-3 pb-5`}
        >
            {/* Section header */}
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                    <Link2 className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                        Forum Activity
                    </span>
                </div>
                {hasAnyActivity && (
                    <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${
                        isFullyPending ? 'text-muted-foreground bg-muted' : 'text-emerald-500 bg-emerald-500/10'
                    }`}>
                        {isFullyPending ? <Clock className="h-3 w-3" /> : <ShieldCheck className="h-3 w-3" />}
                        {isFullyPending ? 'pending' : 'verified'}
                    </span>
                )}
            </div>

            {/* Helper message for pending posts */}
            {hasPending && (
                <p className="text-[10px] text-muted-foreground/70 mb-2 leading-snug">
                    <strong className="font-semibold text-muted-foreground">Pending Admin Review:</strong> Xp will be awarded after verifying the relevance of the post (about 24 hours).
                </p>
            )}

            {/* Verified question cards */}
            {questions.map(post => (
                <ForumPostCard key={post.id} post={post} label="Asked a question" points={XP_FORUM_ASK} />
            ))}

            {/* Verified answer cards */}
            {answers.map(post => (
                <ForumPostCard key={post.id} post={post} label="Answered a question" points={XP_FORUM_ANS} />
            ))}

            {/* Unearned: Ask */}
            {!hasAsked && (
                <div className="flex items-center gap-2 py-1.5">
                    <Circle className="h-3.5 w-3.5 text-muted-foreground/30 shrink-0" />
                    <span className="text-sm text-muted-foreground/50">Ask a question</span>
                    <span className="text-[11px] text-primary/60 ml-auto">+{XP_FORUM_ASK}</span>
                </div>
            )}

            {/* Unearned: Answer */}
            {!hasAnswered && (
                <div className="flex items-center gap-2 py-1.5">
                    <Circle className="h-3.5 w-3.5 text-muted-foreground/30 shrink-0" />
                    <span className="text-sm text-muted-foreground/50">Answer a question</span>
                    <span className="text-[11px] text-primary/60 ml-auto">+{XP_FORUM_ANS}</span>
                </div>
            )}

            {/* Nudge + CTA when no activity yet */}
            {!hasAnyActivity && (
                <div className="mt-2 pt-2 border-t border-border/20">
                    <p className="text-[11px] text-muted-foreground/50 leading-relaxed mb-2.5">
                        Participate in the Spoken Tutorial Forum to earn bonus XP.
                        Your activity will be detected automatically.
                    </p>
                </div>
            )}

            {/* Partial activity: show CTA for what's missing */}
            {hasAnyActivity && (!hasAsked || !hasAnswered) && (
                <div className="mt-1.5 pt-1.5 border-t border-emerald-500/10">
                    <a
                        href={forumDeepLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] text-primary/60 hover:text-primary flex items-center gap-1 transition-colors"
                    >
                        Visit forum to earn more XP
                        <ArrowUpRight className="h-2.5 w-2.5" />
                    </a>
                </div>
            )}
        </div>
    )
}

// ===== TUTORIAL CARD =====

interface TutorialCardProps {
    tutorial: Tutorial
    courseTitle: string
    onRadioChange: (tutorialId: string, field: TutorialField, value: RadioValue) => void
    forumPosts: ForumPost[]
    forumCategory?: string | null
}

function TutorialCard({ tutorial, courseTitle, onRadioChange, forumPosts, forumCategory }: TutorialCardProps) {
    const activeBatchIsActive = useUserStore(state => state.activeBatchIsActive)
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
                                        disabled={!activeBatchIsActive}
                                    />
                                )}

                                {/* Mini-Task Opt-In Question */}
                                <div className="mt-1.5 pt-1.5 border-t border-dashed border-border/30">
                                    <QuestionRow
                                        label="Interested in doing a minitask mentored by an expert?"
                                        value={tutorial.minitaskOpted}
                                        fieldId={`t${tutorial.id}-minitask`}
                                        onChange={(v) => onRadioChange(tutorial.id, 'minitaskOpted', v)}
                                        disabled={true}
                                    />
                                    {tutorial.minitaskOpted === 'yes' && (
                                        <div className="flex items-center gap-2 pb-2 pl-1 animate-in fade-in slide-in-from-top-1 duration-300">
                                            <ClipboardList className="h-3.5 w-3.5 text-primary shrink-0" />
                                            <span className="text-[12px] text-primary font-medium">Great! You've opted in to do a mentored mini-task.</span>
                                        </div>
                                    )}
                                    {tutorial.minitaskOpted === 'no' && (
                                        <div className="flex items-center gap-2 pb-2 pl-1 animate-in fade-in slide-in-from-top-1 duration-300">
                                            <ClipboardList className="h-3.5 w-3.5 text-muted-foreground/50 shrink-0" />
                                            <span className="text-[12px] text-muted-foreground">Okay, you will not be assigned a mini-task.</span>
                                        </div>
                                    )}
                                </div>

                                {/* New Forum Intent Question */}
                                <div className="mt-1.5 pt-1.5 border-t border-dashed border-border/30">
                                    {tutorial.forumAsked === 'yes' ? (
                                        <div className="pb-1">
                                            <AnswerSummary label="Wants to ask a question" value="yes" />
                                            <div className="pl-2 pt-1">
                                                <a
                                                    href={forumCategory ? `https://forums.spoken-tutorial.org/filter/${forumCategory.replace(/ /g, '-')}/` : 'https://forums.spoken-tutorial.org/'}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-colors"
                                                >
                                                    Go to Forum: {forumCategory || courseTitle}
                                                    <ArrowUpRight className="h-3 w-3" />
                                                </a>
                                            </div>
                                        </div>
                                    ) : (
                                        <QuestionRow
                                            label="Do you want to ask a question in the forum?"
                                            value={tutorial.forumAsked}
                                            fieldId={`t${tutorial.id}-forumAsked`}
                                            onChange={(v) => onRadioChange(tutorial.id, 'forumAsked', v)}
                                            disabled={true}
                                        />
                                    )}

                                    <ForumActivitySection
                                        forumCategory={forumCategory}
                                        forumPosts={forumPosts}
                                    />
                                </div>
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
                            disabled={!activeBatchIsActive}
                        />

                        {/* STEP 2: Practice — locked until watched */}
                        <QuestionRow
                            label="Have you practiced the tutorial?"
                            points={XP_PRACTICED}
                            value={tutorial.practiced}
                            fieldId={`t${tutorial.id}-practiced`}
                            onChange={(v) => onRadioChange(tutorial.id, 'practiced', v)}
                            disabled={!activeBatchIsActive || !isWatched}
                        />

                        {/* BONUS — assignment locked until practiced */}
                        <QuestionRow
                            label="Have you finished the assignment?"
                            points={XP_ASSIGNMENT}
                            isBonus
                            value={tutorial.assignmentDone}
                            fieldId={`t${tutorial.id}-assign`}
                            onChange={(v) => onRadioChange(tutorial.id, 'assignmentDone', v)}
                            disabled={!activeBatchIsActive || !isPracticed}
                        />

                        {/* Mini-Task Opt-In Question */}
                        <div className="mt-1.5 pt-1.5 border-t border-dashed border-border/30">
                            <QuestionRow
                                label="Interested in doing a minitask mentored by an expert?"
                                value={tutorial.minitaskOpted}
                                fieldId={`t${tutorial.id}-minitask`}
                                onChange={(v) => onRadioChange(tutorial.id, 'minitaskOpted', v)}
                                disabled={true}
                            />
                            {tutorial.minitaskOpted === 'yes' && (
                                <div className="flex items-center gap-2 pb-2 pl-1 animate-in fade-in slide-in-from-top-1 duration-300">
                                    <ClipboardList className="h-3.5 w-3.5 text-primary shrink-0" />
                                    <span className="text-[12px] text-primary font-medium">Great! You've opted in to do a mentored mini-task.</span>
                                </div>
                            )}
                            {tutorial.minitaskOpted === 'no' && (
                                <div className="flex items-center gap-2 pb-2 pl-1 animate-in fade-in slide-in-from-top-1 duration-300">
                                    <ClipboardList className="h-3.5 w-3.5 text-muted-foreground/50 shrink-0" />
                                    <span className="text-[12px] text-muted-foreground">Okay, you will not be assigned a mini-task.</span>
                                </div>
                            )}
                        </div>

                        {/* New Forum Intent Question */}
                        <div className="mt-1.5 pt-1.5 border-t border-dashed border-border/30">
                            <QuestionRow
                                label="Do you want to ask a question in the forum?"
                                value={tutorial.forumAsked}
                                fieldId={`t${tutorial.id}-forumAsked`}
                                onChange={(v) => onRadioChange(tutorial.id, 'forumAsked', v)}
                                disabled={true}
                            />
                            {tutorial.forumAsked === 'yes' && (
                                <div className="pl-8 pb-3 pt-1">
                                    <a
                                        href={forumCategory ? `https://forums.spoken-tutorial.org/filter/${forumCategory.replace(/ /g, '-')}/` : 'https://forums.spoken-tutorial.org/'}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-colors"
                                    >
                                        Go to Forum: {forumCategory || courseTitle}
                                        <ArrowUpRight className="h-3 w-3" />
                                    </a>
                                </div>
                            )}

                            <ForumActivitySection
                                forumCategory={forumCategory}
                                forumPosts={forumPosts}
                            />
                        </div>
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
        fetchForumActivity,
        forumActivity,
        updateTutorials,
        addXP,
        courses,
        activeBatchIsActive
    } = useUserStore()

    const currentCourse = courses.find(c => c.id == activeCourseId)
    const courseTitle = currentCourse?.title || 'Course'
    const forumCategory = currentCourse?.forumCategory || null

    useEffect(() => {
        if (activeCourseId) {
            fetchTutorials(activeCourseId)
            fetchForumActivity(activeCourseId)
        }
    }, [activeCourseId, fetchTutorials, fetchForumActivity])


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
    const overallProgress = tutorials.length > 0 ? Math.round((completedCount / tutorials.length) * 100) : 0
    const totalXP = tutorials.reduce((sum, t) => sum + t.xpEarned, 0)

    const handleRadioChange = useCallback((tutorialId: string, field: TutorialField, value: RadioValue) => {
        if (!activeBatchIsActive) return
        const tutorial = tutorials.find(t => t.id === tutorialId)
        if (!tutorial) return

        const oldValue = tutorial[field]

        // Mini-task opt-in: save immediately for both yes and no (no feedback needed)
        if (field === 'minitaskOpted') {
            updateTutorials(activeCourseId, tutorialId, field, value)
            return
        }

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

            if (xpEarned > 0) {
                addXP(xpEarned)

                if (field === 'practiced') {
                    const isLastTutorial = completedCount + 1 === tutorials.length
                    if (isLastTutorial) {
                        setCelebration({
                            type: 'course_complete',
                            xpEarned,
                            title: `${courseTitle} Complete!`,
                            subtitle: `You've mastered all ${tutorials.length} tutorials!`,
                        })
                    } else {
                        setCelebration({
                            type: 'tutorial_complete',
                            xpEarned,
                            title: 'Tutorial Complete!',
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

        if (feedbackModal.oldValue === 'yes') {
            let xpLost = 0;
            if (feedbackModal.field === 'watched') xpLost = XP_WATCHED;
            else if (feedbackModal.field === 'practiced') xpLost = XP_PRACTICED;
            else if (feedbackModal.field === 'assignmentDone') xpLost = XP_ASSIGNMENT;

            if (xpLost > 0) {
                // Deduct XP on the frontend to match the backend updates
                addXP(-xpLost);
            }
        }

        setFeedbackModal(null)
    }, [feedbackModal, activeCourseId, updateTutorials, addXP])

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
                                +{bonusFeedback.xp} bonus XP earned for &ldquo;{bonusFeedback.title}&rdquo;!
                            </span>
                        </div>
                    )}

                    {/* All complete */}
                    {allDone && (
                        <div className="mb-3 p-4 rounded-lg bg-gradient-to-r from-success/10 to-primary/10 border border-success/20 text-center">
                            <CheckCircle2 className="h-8 w-8 text-success mx-auto mb-1" />
                            <h3 className="font-bold text-sm">Course Complete!</h3>
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
                                courseTitle={courseTitle}
                                onRadioChange={handleRadioChange}
                                forumPosts={forumActivity[tutorial.id] || []}
                                forumCategory={forumCategory}
                            />
                        ))}
                    </div>

                    {/* Legend */}
                    <div className="flex items-center justify-center gap-3 mt-3 text-[9px] text-muted-foreground flex-wrap">
                        <span>Watch = +{XP_WATCHED}</span>
                        <span>Practice = +{XP_PRACTICED}</span>
                        <span className="text-primary">Assignment = +{XP_ASSIGNMENT}</span>
                        <span className="text-emerald-500">Ask = +{XP_FORUM_ASK}</span>
                        <span className="text-emerald-500">Answer = +{XP_FORUM_ANS}</span>
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
