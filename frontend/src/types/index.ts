// ============================================================
// Spoken Social — Shared Types
// ============================================================
// All types live here. Components import from '@/types'.
// This prevents the same type being redefined in 5 files.
// ============================================================

// ----- User & Auth -----

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
    xpLastWeek: number
    followers: number
    following: number
    postsCount: number
}

// ----- Courses -----

export type CourseStatus = 'in_progress' | 'completed' | 'not_started'

export interface Course {
    id: string
    title: string
    status: CourseStatus
    progressPercent: number
    completedAt?: string | null
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
    xpLastWeek: number
    trend: 'up' | 'down' | 'same'
    trendDelta: number
    isCurrentUser: boolean
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

export type RadioValue = boolean | null

export type TutorialField = 'watched' | 'practiced' | 'assignmentDone' | 'forumAsked' | 'forumAnswered'

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
    xpEarned: number
}
