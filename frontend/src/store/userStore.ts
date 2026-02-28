import { create } from 'zustand'
import type { User, Course, Badge, Tutorial, RadioValue, TutorialField } from '@/types'
import api from '@/lib/axios'


interface UserState {

    user: User | null
    isAuthenticated: boolean
    courses: Course[]
    badges: Badge[]
    tutorials: Tutorial[]
    activeCourseId: string

    fetchTutorials: (courseId: string) => Promise<void>
    updateTutorials: (courseId: string, tutorialId: string, field: TutorialField, value: RadioValue) => void
    fetchUser: () => Promise<void>
    login: (user: User) => void
    logout: () => void
    updateProfile: (updates: Partial<User>) => void
    addXP: (amount: number) => void
}

export const useUserStore = create<UserState>((set, get) => ({

    user: null,
    isAuthenticated: false,
    courses: [],
    badges: [],
    tutorials: [],
    activeCourseId: 'linux',


    fetchUser: async () => {
        try {
            const { data } = await api.get('/api/me')
            set({
                user: data.user,
                courses: data.courses,
                badges: data.badges,
                isAuthenticated: true,
            })
        }
        catch (error) {
            console.error('Failed to fetch user:', error)
        }
    },


    fetchTutorials: async (courseId) => {
        try {
            const { data } = await api.get(`/api/me/courses/${courseId}/tutorials`)
            set({ tutorials: data })
        }
        catch (error) {
            console.error('Failed to fetch tutorials', error)
        }
    },

    updateTutorials(courseId, tutorialId, field, value) {
        set({
            tutorials: get().tutorials.map(t => {
                if (t.id !== tutorialId) return t
                const updated = { ...t, [field]: value }
                if (field === 'practiced' && value === true) updated.completed = true

                const XP: Record<string, number> = { watched: 10, practiced: 10, assignmentDone: 5, forumAsked: 5, forumAnswered: 5 }
                updated.xpEarned = Object.entries(XP).reduce((sum, [f, pts]) => sum + (updated[f as TutorialField] === true ? pts : 0), 0)
                return updated
            })
        })

        api.put(`/api/me/courses/${courseId}/tutorials/${tutorialId}`, { field, value })
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
        const { user } = get()
        if (!user) return

        const newXP = user.xpTotal + amount
        const newXPToday = user.xpToday + amount
        const newXPWeek = user.xpThisWeek + amount

        let newLevel = user.level
        let newTitle = user.levelTitle
        if (newXP >= 12000) { newLevel = 26; newTitle = 'Spoken Legend' }
        else if (newXP >= 7000) { newLevel = 21; newTitle = 'Master' }
        else if (newXP >= 3500) { newLevel = 16; newTitle = 'Expert' }
        else if (newXP >= 1500) { newLevel = 11; newTitle = 'Practitioner' }
        else if (newXP >= 500) { newLevel = 6; newTitle = 'Explorer' }
        else { newLevel = 1; newTitle = 'Beginner' }

        set({
            user: {
                ...user,
                xpTotal: newXP,
                xpToday: newXPToday,
                xpThisWeek: newXPWeek,
                level: newLevel,
                levelTitle: newTitle,
            },
        })
    },
}))
