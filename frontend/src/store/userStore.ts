import { create } from 'zustand'
import type { User, Course, Badge, Tutorial, RadioValue, TutorialField, ForumActivityMap } from '@/types'
import api from '@/lib/axios'


interface UserState {
    user: User | null
    isLoading: boolean
    error: string | null
    isAuthenticated: boolean
    courses: Course[]
    badges: Badge[]
    tutorials: Tutorial[]
    forumActivity: ForumActivityMap
    activeCourseId: string
    activeBatchId: string | null
    activeBatchIsActive: boolean
    weeklyGoal: any

    fetchTutorials: (courseId: string) => Promise<void>
    fetchForumActivity: (courseId: string) => Promise<void>
    updateTutorials: (courseId: string, tutorialId: string, field: TutorialField, value: RadioValue) => void
    fetchUser: () => Promise<void>
    login: (user: User) => void
    logout: () => void
    updateProfile: (updates: Partial<User>) => void
    addXP: (amount: number) => void
    setActiveCourse: (courseId: string) => void
    setActiveBatch: (batchId: string | null, isActive?: boolean) => void
}

export const useUserStore = create<UserState>((set, get) => ({
    user: null,
    isLoading: false,
    error: null,
    isAuthenticated: false,
    courses: [],
    badges: [],
    tutorials: [],
    forumActivity: {},
    activeCourseId: 'linux',
    activeBatchId: null,
    activeBatchIsActive: true,
    weeklyGoal: null,


    fetchUser: async () => {
        set({ isLoading: true, error: null })
        try {
            const { data } = await api.get('/api/me')
            set({
                user: data.user,
                isLoading: false,
                weeklyGoal: data.weeklyGoal,
                courses: data.courses,
                badges: data.badges,
                isAuthenticated: true,
                activeCourseId: data.courses?.[0]?.id || 'linux',
                activeBatchId: data.active_batch_id || null,
                activeBatchIsActive: data.active_batch_is_active ?? true
            })
        }
        catch (error) {
            console.error('Failed to fetch user:', error)
            set({ error: 'Failed to load', isLoading: false })
        }
    },


    fetchTutorials: async (courseId) => {
        try {
            const { data } = await api.get(`/api/me/courses/${courseId}/tutorials`)
            const fields = ['watched', 'practiced', 'assignmentDone', 'forumAsked', 'forumAnswered', 'minitaskOpted'] as const
            const converted = data.map((t: any) => {
                const out = { ...t }
                for (const f of fields) {
                    out[f] = t[f] === true ? 'yes' : null
                }
                return out
            })
            set({ tutorials: converted })
        }
        catch (error) {
            console.error('Failed to fetch tutorials', error)
        }
    },

    fetchForumActivity: async (courseId) => {
        try {
            const { data } = await api.get(`/api/me/courses/${courseId}/forum-activity`)
            set({ forumActivity: data })
        } catch (error) {
            console.error('Failed to fetch forum activity', error)
        }
    },

    updateTutorials(courseId, tutorialId, field, value) {
        if (!get().activeBatchIsActive) return

        const boolValue = value === 'yes' ? true : value === 'no' ? false : null

        set({
            tutorials: get().tutorials.map(t => {
                if (t.id !== tutorialId) return t
                const updated = { ...t, [field]: value }
                if (field === 'practiced' && value === 'yes') updated.completed = true

                const XP: Record<string, number> = { watched: 10, practiced: 10, assignmentDone: 5, forumAsked: 5, forumAnswered: 10 }
                updated.xpEarned = Object.entries(XP).reduce((sum, [f, pts]) => sum + (updated[f as TutorialField] === 'yes' ? pts : 0), 0)
                return updated
            })
        })

        api.put(`/api/me/courses/${courseId}/tutorials/${tutorialId}`, { field, value: boolValue })
    },

    login: (user) => {
        set({
            user,
            isAuthenticated: true,
        })
    },

    logout: () => {
        set({
            user: null,
            isAuthenticated: false,
        })
    },

    updateProfile: (updates) => {
        const { user } = get()
        if (!user) return

        set({
            user: { ...user, ...updates },
        })
    },

    addXP: (amount) => {
        if (!get().activeBatchIsActive) return
        const { user } = get()
        if (!user) return

        const newXP = user.xpTotal + amount
        set({
            user: {
                ...user,
                xpTotal: newXP,
            },
        })
    },

    setActiveCourse: (courseId) => {
        set({ activeCourseId: courseId, activeBatchId: null })
    },

    setActiveBatch: (batchId, isActive = true) => {
        set({ activeBatchId: batchId, activeBatchIsActive: isActive })
    }
}))
