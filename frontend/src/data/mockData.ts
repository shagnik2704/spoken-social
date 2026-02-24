// ============================================================
// Spoken Social — Mock Data
// ============================================================
// ALL mock data lives here. Components never define their own.
// When the real backend arrives, we swap this file for API calls.
// ============================================================

import type {
    User, Streak, WeeklyGoal, Course, Badge,
    Post, LeaderboardUser, Activity, UpcomingEvent,
    TrendingTopic, SuggestedUser,
} from '@/types'

// ===== CURRENT USER (the "logged-in" user) =====

export const CURRENT_USER: User = {
    id: 'user-priya',
    name: 'Priya Singh',
    username: '@priya_learns',
    initials: 'PS',
    bio: 'Computer Science student passionate about open-source and Python. Learning one tutorial at a time 🚀',
    level: 12,
    levelTitle: 'Practitioner',
    xpTotal: 2450,
    xpForNextLevel: 3500,
    xpToday: 25,
    xpThisWeek: 180,
    joinDate: 'August 2025',
    location: 'Mumbai, India',
    website: 'github.com/priyasingh',
    followers: 42,
    following: 78,
    postsCount: 15,
    college: 'VJTI Mumbai',
    department: 'B.Tech CSE, Year 2',
}

// ===== STREAK =====

export const MOCK_STREAK: Streak = {
    current: 15,
    longest: 23,
    isActiveToday: true,
}

// ===== WEEKLY GOAL =====

export const MOCK_WEEKLY_GOAL: WeeklyGoal = {
    target: 5,
    completed: 4,
    days: [true, true, true, true, false, false, false],
    dayLabels: ['M', 'T', 'W', 'T', 'F', 'S', 'S'],
}

// ===== COURSES =====

export const MOCK_COURSES: Course[] = [
    { id: '1', title: 'Python', progress: 70, completed: 7, total: 10, status: 'in_progress', testPassed: false },
    { id: '2', title: 'Linux', progress: 45, completed: 5, total: 11, status: 'in_progress', testPassed: false },
    { id: '3', title: 'Scilab', progress: 10, completed: 1, total: 10, status: 'in_progress', testPassed: false },
    { id: '4', title: 'C/C++', progress: 100, completed: 8, total: 8, status: 'completed', testPassed: true, testScore: 85, completedDate: 'Feb 5, 2026' },
    { id: '5', title: 'LibreOffice', progress: 0, completed: 0, total: 12, status: 'not_started', testPassed: false },
]

// ===== BADGES =====

export const MOCK_BADGES: Badge[] = [
    { id: '1', name: '7-Day Streak', description: 'Maintained a 7-day learning streak', icon: 'flame', color: 'text-warning', bgColor: 'bg-warning/10', earned: true, earnedDate: 'Feb 22' },
    { id: '2', name: '5 Courses', description: 'Enrolled in 5 different courses', icon: 'book-open', color: 'text-primary', bgColor: 'bg-primary/10', earned: true, earnedDate: 'Feb 17' },
    { id: '3', name: 'First Post', description: 'Shared your first post with the community', icon: 'message-circle', color: 'text-secondary', bgColor: 'bg-secondary/10', earned: true, earnedDate: 'Feb 10' },
    { id: '4', name: 'Test Passer', description: 'Passed your first online test', icon: 'check-circle', color: 'text-success', bgColor: 'bg-success/10', earned: true, earnedDate: 'Feb 5' },
    { id: '5', name: 'Helpful', description: 'Received 10 likes on your answers', icon: 'heart', color: 'text-danger', bgColor: 'bg-danger/10', earned: true, earnedDate: 'Jan 28' },
    { id: '6', name: '30-Day Streak', description: 'Maintain a 30-day learning streak', icon: 'flame', color: 'text-warning', bgColor: 'bg-warning/10', earned: false, progress: '15/30 days', daysAway: 15 },
    { id: '7', name: 'Python Master', description: 'Complete all Python tutorials', icon: 'code', color: 'text-primary', bgColor: 'bg-primary/10', earned: false, progress: '7/10 tutorials', daysAway: null },
    { id: '8', name: 'Mentor', description: 'Help 20 learners with their questions', icon: 'users', color: 'text-secondary', bgColor: 'bg-secondary/10', earned: false },
    { id: '9', name: 'Top Contributor', description: 'Be in the top 10 weekly leaderboard', icon: 'trophy', color: 'text-xp-gold', bgColor: 'bg-xp-gold/10', earned: false },
]

// ===== POSTS (Feed) =====

export const MOCK_POSTS: Post[] = [
    {
        id: '1',
        author: { id: 'user-rahul', name: 'Rahul Sharma', initials: 'RS', level: 15, title: 'Python Pro' },
        type: 'achievement',
        content: 'Just completed the entire Python course with a perfect score on the online test! 🎉',
        details: 'Python — 10/10 tutorials completed • Online Test: 92%',
        courseName: 'Python',
        timestamp: '2h ago',
        createdAt: Date.now() - 2 * 60 * 60 * 1000,
        likes: 24, comments: 8, shares: 3,
        isLiked: false, isBookmarked: false,
        tags: ['Python', 'Achievement'],
    },
    {
        id: '2',
        author: { id: 'user-ananya', name: 'Ananya Patel', initials: 'AP', level: 8, title: 'Learner' },
        type: 'question',
        content: 'Can someone explain the difference between lists and tuples in Python? I keep mixing them up in my tutorials.',
        details: 'I understand lists are mutable but when should I actually prefer tuples over lists in practice?',
        courseName: 'Python',
        timestamp: '4h ago',
        createdAt: Date.now() - 4 * 60 * 60 * 1000,
        likes: 12, comments: 15, shares: 1,
        isLiked: true, isBookmarked: true,
        tags: ['Python', 'Question', 'Data Structures'],
    },
    {
        id: '3',
        author: { id: 'user-vikram', name: 'Vikram Desai', initials: 'VD', level: 22, title: 'Mentor' },
        type: 'discussion',
        content: 'Pro tip for everyone learning Linux: Start by mastering these 10 commands and you\'ll be able to handle 80% of daily tasks.\n\n1. cd, ls, pwd\n2. grep, find\n3. chmod, chown\n4. cat, head, tail\n5. pipe (|) and redirect (>)',
        timestamp: '6h ago',
        createdAt: Date.now() - 6 * 60 * 60 * 1000,
        likes: 67, comments: 23, shares: 18,
        isLiked: false, isBookmarked: false,
        tags: ['Linux', 'Tips', 'Beginner'],
    },
    {
        id: '4',
        author: { id: 'user-meera', name: 'Meera Joshi', initials: 'MJ', level: 10, title: 'Practitioner' },
        type: 'milestone',
        content: 'Hit a 30-day learning streak! Consistency is the key. 🔥',
        details: '30 days of continuous learning without missing a single day',
        timestamp: '8h ago',
        createdAt: Date.now() - 8 * 60 * 60 * 1000,
        likes: 89, comments: 31, shares: 7,
        isLiked: true, isBookmarked: false,
        tags: ['Streak', 'Milestone'],
    },
    {
        id: '5',
        author: { id: 'user-arjun', name: 'Arjun Nair', initials: 'AN', level: 6, title: 'Explorer' },
        type: 'question',
        content: 'I\'m stuck on Scilab Tutorial 5 — the matrix operations part. Has anyone found a good way to visualize what\'s happening with matrix multiplication?',
        courseName: 'Scilab',
        timestamp: '12h ago',
        createdAt: Date.now() - 12 * 60 * 60 * 1000,
        likes: 5, comments: 9, shares: 0,
        isLiked: false, isBookmarked: false,
        tags: ['Scilab', 'Help Needed'],
    },
    {
        id: '6',
        author: { id: 'user-priya', name: 'Priya Singh', initials: 'PS', level: 12, title: 'Practitioner' },
        type: 'achievement',
        content: 'Passed my C/C++ online test! That pointer chapter was brutal but I made it through 💪',
        details: 'C/C++ — Online Test: 85% • All tutorials completed',
        courseName: 'C/C++',
        timestamp: '1d ago',
        createdAt: Date.now() - 24 * 60 * 60 * 1000,
        likes: 34, comments: 12, shares: 5,
        isLiked: false, isBookmarked: false,
        tags: ['C/C++', 'Online Test'],
    },
]

// ===== LEADERBOARD =====

export const MOCK_LEADERBOARD: LeaderboardUser[] = [
    { id: '1', rank: 1, name: 'Vikram Desai', initials: 'VD', level: 22, levelTitle: 'Mentor', xp: 8940, xpThisWeek: 420, streak: 45, coursesCompleted: 8, trend: 'same', trendDelta: 0, isCurrentUser: false, college: 'IIT Bombay' },
    { id: '2', rank: 2, name: 'Sneha Gupta', initials: 'SG', level: 25, levelTitle: 'Expert', xp: 8720, xpThisWeek: 380, streak: 60, coursesCompleted: 9, trend: 'up', trendDelta: 1, isCurrentUser: false, college: 'NIT Trichy' },
    { id: '3', rank: 3, name: 'Dr. Kannan', initials: 'DK', level: 30, levelTitle: 'Master', xp: 8500, xpThisWeek: 210, streak: 120, coursesCompleted: 12, trend: 'down', trendDelta: 1, isCurrentUser: false, college: 'IIT Madras' },
    { id: '4', rank: 4, name: 'Amit Kumar', initials: 'AK', level: 18, levelTitle: 'Advanced', xp: 6200, xpThisWeek: 350, streak: 30, coursesCompleted: 6, trend: 'up', trendDelta: 2, isCurrentUser: false, college: 'BITS Pilani' },
    { id: '5', rank: 5, name: 'Meera Joshi', initials: 'MJ', level: 10, levelTitle: 'Practitioner', xp: 5100, xpThisWeek: 290, streak: 30, coursesCompleted: 4, trend: 'up', trendDelta: 3, isCurrentUser: false, college: 'VIT Vellore' },
    { id: '6', rank: 6, name: 'Rahul Sharma', initials: 'RS', level: 15, levelTitle: 'Advanced', xp: 4800, xpThisWeek: 310, streak: 21, coursesCompleted: 5, trend: 'down', trendDelta: 2, isCurrentUser: false, college: 'IIT Bombay' },
    { id: '7', rank: 7, name: 'Ananya Patel', initials: 'AP', level: 8, levelTitle: 'Learner', xp: 3200, xpThisWeek: 280, streak: 14, coursesCompleted: 3, trend: 'up', trendDelta: 1, isCurrentUser: false, college: 'NIT Surathkal' },
    { id: '8', rank: 8, name: 'Priya Singh', initials: 'PS', level: 12, levelTitle: 'Practitioner', xp: 2450, xpThisWeek: 180, streak: 15, coursesCompleted: 1, trend: 'up', trendDelta: 4, isCurrentUser: true, college: 'VJTI Mumbai' },
    { id: '9', rank: 9, name: 'Arjun Nair', initials: 'AN', level: 6, levelTitle: 'Explorer', xp: 1800, xpThisWeek: 150, streak: 7, coursesCompleted: 1, trend: 'same', trendDelta: 0, isCurrentUser: false, college: 'NIT Calicut' },
    { id: '10', rank: 10, name: 'Kavitha R', initials: 'KR', level: 5, levelTitle: 'Explorer', xp: 1200, xpThisWeek: 120, streak: 5, coursesCompleted: 0, trend: 'down', trendDelta: 3, isCurrentUser: false, college: 'Anna University' },
]

// ===== ACTIVITY TIMELINE =====

export const MOCK_ACTIVITY: Activity[] = [
    { id: '1', type: 'achievement', text: 'Completed C/C++ course with 85% test score', time: '3 days ago' },
    { id: '2', type: 'post', text: 'Shared a tip about Python dictionaries', time: '5 days ago' },
    { id: '3', type: 'streak', text: 'Hit a 15-day learning streak!', time: '1 week ago' },
    { id: '4', type: 'badge', text: 'Earned the "7-Day Streak" badge', time: '1 week ago' },
    { id: '5', type: 'course', text: 'Started learning Scilab', time: '2 weeks ago' },
    { id: '6', type: 'answer', text: 'Answered a question about Linux file permissions', time: '2 weeks ago' },
]

// ===== UPCOMING EVENTS =====

export const MOCK_UPCOMING: UpcomingEvent[] = [
    { id: '1', type: 'test', title: 'Python Online Test', date: 'Feb 28', daysAway: 4, location: 'Lab 201, 10:00 AM' },
    { id: '2', type: 'workshop', title: 'Linux Training Workshop', date: 'Mar 5', daysAway: 9, location: 'Computer Lab, 2:00 PM' },
    { id: '3', type: 'test', title: 'Scilab Online Test', date: 'Mar 12', daysAway: 16, location: 'TBD' },
]

// ===== TRENDING & SUGGESTIONS =====

export const MOCK_TRENDING: TrendingTopic[] = [
    { tag: 'Python', posts: 234 },
    { tag: 'Linux', posts: 189 },
    { tag: 'Online Test Tips', posts: 156 },
    { tag: 'Scilab', posts: 98 },
    { tag: 'Study Group', posts: 67 },
]

export const MOCK_SUGGESTED_USERS: SuggestedUser[] = [
    { name: 'Dr. Kannan', initials: 'DK', title: 'Mentor • Python Expert', level: 30 },
    { name: 'Sneha Gupta', initials: 'SG', title: 'Top Contributor', level: 25 },
    { name: 'Amit Kumar', initials: 'AK', title: '60-Day Streak', level: 18 },
]

// ===== COURSE OPTIONS (for tagging in compose) =====

export const COURSE_OPTIONS = [
    { id: 'python', name: 'Python' },
    { id: 'linux', name: 'Linux' },
    { id: 'scilab', name: 'Scilab' },
    { id: 'cpp', name: 'C/C++' },
    { id: 'libreoffice', name: 'LibreOffice' },
] as const
