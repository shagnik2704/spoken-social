// ============================================================
// Spoken Social — Shared Types
// ============================================================
// All types live here. Components import from '@/types'.
// This prevents the same type being redefined in 5 files.
// ============================================================

// ----- User & Auth -----

export type UserRole = 'student' | 'coordinator' | 'admin'

export interface User {
    id: string
    username: string
    displayName: string
    email: string
    bio: string
    departmentYear: string
    location: string
    website: string
    level: number
    levelTitle: string
    xpTotal: number
    xpForNextLevel: number
    xpToday: number
    xpThisWeek: number
    followers: number
    following: number
    postsCount: number
    role: UserRole
    effectiveRole: UserRole
    isImpersonating: boolean
    collegeId?: string | null
}

// ----- Courses -----

export type CourseStatus = 'in_progress' | 'completed' | 'not_started'

export interface Course {
    id: string
    title: string
    status: CourseStatus
    progressPercent: number
    completedAt?: string | null
    forumCategory?: string | null
    batchId?: string | null
    batchName?: string | null
    batchStatus?: string
}

// ----- Badges -----

export interface Badge {
    id: string
    name: string
    description: string
    icon: string
    color: string
    earnedAt?: string | null
}

// ----- Posts & Feed -----

export type PostType = 'achievement' | 'question' | 'discussion' | 'milestone'

export interface Post {
    id: string
    author: {
        id: string
        name: string
        username: string
        level: number
        title: string
    }
    type: PostType
    content: string
    courseId?: string
    timestamp: string
    createdAt: number
    likes: number
    comments: number
    shares: number
    isLiked: boolean
    isBookmarked: boolean
    tags?: string[]
}

// ----- Leaderboard -----

export interface LeaderboardUser {
    id: string
    rank: number
    name: string
    username: string
    level: number
    levelTitle: string
    xp: number
    isCurrentUser: boolean
}

/**
 * The leaderboard endpoint returns an envelope rather than a bare array, so a
 * caller can page through the board and — crucially — see their own standing
 * even when they fall outside the page. The top-100 cutoff sits well above most
 * students' XP, so `yourEntry` is the only way the majority ever see a rank.
 * `yourRank` is null for students with no XP: they aren't ranked yet.
 */
export interface LeaderboardResponse {
    scope: { type: string; id: string | null }
    window: string
    entries: LeaderboardUser[]
    total: number
    limit: number
    offset: number
    yourRank: number | null
    yourEntry: LeaderboardUser | null
    generatedAt: string
}

// ----- Activity -----

export type ActivityType = 'achievement' | 'post' | 'badge' | 'course' | 'answer' | 'earned_badge' | 'completed_tutorial' | 'posted'

export interface Activity {
    id: string
    type: ActivityType
    text: string
    time: string
}



// ----- Upcoming Events -----

export type EventType = 'test' | 'workshop'

export interface UpcomingEvent {
    id: string
    type: EventType
    title: string
    date: string
    daysAway: number
    location: string
}

// ----- Trending & Suggestions -----

export interface TrendingTopic {
    tag: string
    posts: number
}

export interface SuggestedUser {
    name: string
    username: string
    title: string
    level: number
}

// ----- Stats -----

export interface ProfileStat {
    label: string
    value: string
    iconKey: string
    color: string
}

// Tutorial

export type RadioValue = 'yes' | 'no' | null

export type TutorialField = 'watched' | 'practiced' | 'assignmentDone' | 'forumAsked' | 'forumAnswered' | 'minitaskOpted'

export interface Tutorial {
    id: string
    number: number
    title: string
    status: string
    completed: boolean
    watched: RadioValue
    practiced: RadioValue
    assignmentDone: RadioValue
    forumAsked: RadioValue
    forumAnswered: RadioValue
    minitaskOpted: RadioValue
    xpEarned: number
}

// ----- Forum Activity (verified via webhooks) -----

export interface ForumPost {
    id: number
    forumPostId: number
    activityType: 'question' | 'answer'
    title: string | null
    forumUrl: string
    postedAt: string | null
    xpAwarded: boolean
    xpAmount: number
}

export type ForumActivityMap = Record<string, ForumPost[]>
