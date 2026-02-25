// ============================================================
// Spoken Social — Shared Types
// ============================================================
// All types live here. Components import from '@/types'.
// This prevents the same type being redefined in 5 files.
// ============================================================

// ----- User & Auth -----

export interface User {
    id: string
    name: string
    username: string
    initials: string
    bio: string
    level: number
    levelTitle: string
    xpTotal: number
    xpForNextLevel: number
    xpToday: number
    xpThisWeek: number
    joinDate: string
    location: string
    website: string
    followers: number
    following: number
    postsCount: number
    avatar?: string
    college?: string
    department?: string
}

export interface Streak {
    current: number
    longest: number
    isActiveToday: boolean
}

export interface WeeklyGoal {
    target: number
    completed: number
    days: boolean[]
    dayLabels: string[]
}

// ----- Courses -----

export type CourseStatus = 'in_progress' | 'completed' | 'not_started'

export interface Course {
    id: string
    title: string
    progress: number
    completed: number
    total: number
    status: CourseStatus
    completedDate?: string
}

// ----- Badges -----

export interface Badge {
    id: string
    name: string
    description: string
    icon: string          // icon key, e.g. 'flame', 'book-open'
    color: string         // tailwind color class
    bgColor: string       // tailwind bg class
    earned: boolean
    earnedDate?: string
    // for upcoming/locked badges:
    progress?: string
    daysAway?: number | null
}

// ----- Posts & Feed -----

export type PostType = 'achievement' | 'question' | 'discussion' | 'milestone'

export interface Post {
    id: string
    author: {
        id: string
        name: string
        avatar?: string
        initials: string
        level: number
        title: string
    }
    type: PostType
    content: string
    details?: string
    courseName?: string
    timestamp: string
    createdAt: number     // epoch ms for sorting
    likes: number
    comments: number
    shares: number
    isLiked: boolean
    isBookmarked: boolean
    tags?: string[]
    image?: string
}

// ----- Leaderboard -----

export interface LeaderboardUser {
    id: string
    rank: number
    name: string
    initials: string
    level: number
    levelTitle: string
    xp: number
    xpThisWeek: number
    streak: number
    coursesCompleted: number
    trend: 'up' | 'down' | 'same'
    trendDelta: number
    isCurrentUser: boolean
    college?: string
    courseProgress?: number
}

// ----- Activity -----

export type ActivityType = 'achievement' | 'post' | 'streak' | 'badge' | 'course' | 'answer'

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
    initials: string
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
