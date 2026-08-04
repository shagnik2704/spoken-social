// ===== Shared feedback reason labels =====
// Used by both the FeedbackModal (student side) and FeedbackPanel (admin side)

export const REASON_LABELS: Record<string, string> = {
    // Watched
    electricity: 'Electricity / power supply problem',
    network: 'Unstable or no internet connection',
    mobile_data: 'Insufficient mobile data',
    video_quality: 'Video quality issues (audio/video sync, buffering)',
    access_issues: 'Login or access problem on Spoken Tutorial website',
    language_preference: "Prefer video in regional language",

    // Practiced
    no_computer: 'No access to a computer or laptop',
    practice_confusion: "Don't know how to practice (side-by-side method)",

    // Guidance
    no_facilitator_support: 'No guidance from the facilitator',
    no_college_support: 'No guidance from college coordinator',
    forum_unanswered: 'Forum questions not answered',

    // Assignment
    assignment_help: "Need help but can't find any",
    too_difficult: 'Assignment is too difficult',

    // Personal
    workload: 'Too much academic workload',

    // Forum
    didnt_know_forum: "Didn't know about the forum",
    not_confident: "Not confident answering others' questions",
    no_questions: "Had no doubts or questions to ask",
    found_answer_search: 'Found the answer by searching the forum',
    found_answer_elsewhere: 'Found the answer on Google or documentation',
    difficult_to_use: 'Forum is difficult to use or navigate',
    prefer_offline: 'Prefers asking teachers or peers directly',

    // Other
    other: 'Other reason',
}

export const STEP_TYPE_LABELS: Record<string, string> = {
    watched: 'Didn\'t watch',
    practiced: 'Didn\'t practice',
    assignmentDone: 'Didn\'t do assignment',
    forumAsked: 'Didn\'t ask on forum',
    forumAnswered: 'Didn\'t answer on forum',
}

// ===== Reason categories for grouped display =====

export interface ReasonCategory {
    id: string
    label: string
    icon: string             // lucide icon name
    color: string            // tailwind color classes
    bgColor: string          // background color for the card
    borderColor: string      // border accent
    reasons: string[]        // reason keys that belong here
}

export const REASON_CATEGORIES: ReasonCategory[] = [
    {
        id: 'infrastructure',
        label: 'Infrastructure',
        icon: 'Wifi',
        color: 'text-foreground',
        bgColor: 'bg-muted/5',
        borderColor: 'border-border/30',
        reasons: ['electricity', 'network', 'mobile_data', 'video_quality', 'access_issues', 'no_computer'],
    },
    {
        id: 'support',
        label: 'Support & Guidance',
        icon: 'LifeBuoy',
        color: 'text-foreground',
        bgColor: 'bg-muted/5',
        borderColor: 'border-border/30',
        reasons: ['no_facilitator_support', 'no_college_support', 'forum_unanswered', 'assignment_help'],
    },
    {
        id: 'academic',
        label: 'Academic',
        icon: 'GraduationCap',
        color: 'text-foreground',
        bgColor: 'bg-muted/5',
        borderColor: 'border-border/30',
        reasons: ['too_difficult', 'workload', 'practice_confusion'],
    },
    {
        id: 'awareness',
        label: 'Awareness',
        icon: 'Lightbulb',
        color: 'text-foreground',
        bgColor: 'bg-muted/5',
        borderColor: 'border-border/30',
        reasons: ['didnt_know_forum', 'not_confident', 'language_preference'],
    },
    {
        id: 'other',
        label: 'Other',
        icon: 'HelpCircle',
        color: 'text-foreground',
        bgColor: 'bg-muted/5',
        borderColor: 'border-border/30',
        reasons: ['other'],
    },
]
