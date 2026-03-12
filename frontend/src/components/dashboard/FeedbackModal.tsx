import { useState } from 'react'
import { X, MessageCircleQuestion } from 'lucide-react'
import api from '@/lib/axios'

// ===== REASON OPTIONS PER STEP TYPE =====

const REASONS_BY_STEP: Record<string, { key: string; label: string }[]> = {
    watched: [
        { key: 'electricity', label: 'Electricity / power supply problem' },
        { key: 'network', label: 'Unstable or no internet connection' },
        { key: 'mobile_data', label: 'Insufficient mobile data' },
        { key: 'video_quality', label: 'Video quality issues (audio/video sync, buffering)' },
        { key: 'access_issues', label: 'Login or access problem on Spoken Tutorial website' },
        { key: 'language_preference', label: "I'd prefer the video in my regional language" },
        { key: 'other', label: 'Other' },
    ],
    practiced: [
        { key: 'no_computer', label: 'No access to a computer or laptop' },
        { key: 'practice_confusion', label: "I don't know how to practice using the side-by-side method" },
        { key: 'no_facilitator_support', label: 'No guidance from the facilitator' },
        { key: 'no_college_support', label: 'No guidance from my college coordinator' },
        { key: 'workload', label: 'Too much academic workload' },
        { key: 'forum_unanswered', label: 'My questions on the forum are not being answered' },
        { key: 'other', label: 'Other' },
    ],
    assignmentDone: [
        { key: 'assignment_help', label: "I need help but can't find any" },
        { key: 'too_difficult', label: 'The assignment is too difficult' },
        { key: 'no_facilitator_support', label: 'No guidance from the facilitator' },
        { key: 'no_college_support', label: 'No guidance from my college coordinator' },
        { key: 'workload', label: 'Too much academic workload' },
        { key: 'forum_unanswered', label: 'My questions on the forum are not being answered' },
        { key: 'other', label: 'Other' },
    ],
    forumAsked: [
        { key: 'didnt_know_forum', label: "I didn't know about the forum" },
        { key: 'forum_unanswered', label: 'My previous forum questions were not answered' },
        { key: 'other', label: 'Other' },
    ],
    forumAnswered: [
        { key: 'didnt_know_forum', label: "I didn't know about the forum" },
        { key: 'not_confident', label: "I don't feel confident answering others' questions" },
        { key: 'other', label: 'Other' },
    ],
}


// ===== COMPONENT =====

interface FeedbackModalProps {
    tutorialId: string
    tutorialTitle: string
    stepType: string
    onClose: () => void
    onSubmitted?: () => void
}

export function FeedbackModal({ tutorialId, tutorialTitle, stepType, onClose, onSubmitted }: FeedbackModalProps) {
    const [selectedReasons, setSelectedReasons] = useState<Set<string>>(new Set())
    const [otherText, setOtherText] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)

    const reasons = REASONS_BY_STEP[stepType] || []

    const toggleReason = (key: string) => {
        setSelectedReasons(prev => {
            const next = new Set(prev)
            if (next.has(key)) {
                next.delete(key)
            } else {
                next.add(key)
            }
            return next
        })
    }

    const handleSubmit = async () => {
        if (selectedReasons.size === 0) return  // Must select at least one reason

        setIsSubmitting(true)
        try {
            await api.post('/api/me/feedback', {
                tutorialId,
                stepType,
                reasons: Array.from(selectedReasons),
                otherText: selectedReasons.has('other') ? otherText : null,
            })
            onSubmitted?.()  // This saves the "No" in the parent
        } catch (error) {
            console.error('Failed to submit feedback:', error)
            onSubmitted?.()  // Still save the "No" even if feedback API fails
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop — no click-to-close since feedback is required */}
            <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" />

            {/* Modal */}
            <div className="relative w-full max-w-md bg-card border border-border rounded-2xl shadow-xl animate-in fade-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="flex items-center justify-between px-5 pt-5 pb-3">
                    <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-warning/10">
                            <MessageCircleQuestion className="h-4 w-4 text-warning" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold">What's stopping you?</h3>
                            <p className="text-[11px] text-muted-foreground">
                                Please tell us why — your feedback helps us improve!
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 rounded-lg hover:bg-muted/50 transition-colors"
                    >
                        <X className="h-4 w-4 text-muted-foreground" />
                    </button>
                </div>

                {/* Tutorial name */}
                <div className="px-5 pb-3">
                    <p className="text-xs text-muted-foreground bg-muted/30 rounded-lg px-3 py-1.5 truncate">
                        📖 {tutorialTitle}
                    </p>
                </div>

                {/* Checkbox list */}
                <div className="px-5 pb-3 space-y-1 max-h-[300px] overflow-y-auto">
                    {reasons.map(reason => (
                        <label
                            key={reason.key}
                            className={`flex items-start gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors
                                ${selectedReasons.has(reason.key)
                                    ? 'bg-primary/5 border border-primary/20'
                                    : 'hover:bg-muted/30 border border-transparent'
                                }`}
                        >
                            <input
                                type="checkbox"
                                checked={selectedReasons.has(reason.key)}
                                onChange={() => toggleReason(reason.key)}
                                className="mt-0.5 h-4 w-4 rounded border-border accent-primary shrink-0"
                            />
                            <span className="text-sm text-foreground/90">{reason.label}</span>
                        </label>
                    ))}
                </div>

                {/* "Other" text field — only when "other" is checked */}
                {selectedReasons.has('other') && (
                    <div className="px-5 pb-3">
                        <textarea
                            value={otherText}
                            onChange={(e) => setOtherText(e.target.value)}
                            placeholder="Please describe your issue..."
                            rows={2}
                            className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-muted/20 resize-none focus:outline-none focus:ring-1 focus:ring-primary/30 placeholder:text-muted-foreground/50"
                        />
                    </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-between px-5 py-4 border-t border-border/30">
                    <p className="text-[10px] text-muted-foreground">
                        Select at least one reason to continue
                    </p>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-muted-foreground rounded-lg hover:bg-muted/50 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSubmit}
                            disabled={isSubmitting || selectedReasons.size === 0}
                            className="px-4 py-2 text-sm font-medium bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isSubmitting ? 'Submitting...' : 'Submit'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
