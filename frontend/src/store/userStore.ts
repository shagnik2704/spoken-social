import { create } from 'zustand'
import type { User, WeeklyGoal, Course, Badge } from '@/types'
import api from '@/lib/axios'

// ----- Define the shape of the store -----

interface UserState {

    user: User | null
    isAuthenticated: boolean

    weeklyGoal: WeeklyGoal
    courses: Course[]
    badges: Badge[]



    fetchUser: () => Promise<void>
    login: (user: User) => void
    logout: () => void
    updateProfile: (updates: Partial<User>) => void
    addXP: (amount: number) => void
}

export const useUserStore = create<UserState>((set, get) => ({

    user: null,
    isAuthenticated: false,

    weeklyGoal: { target: 0, completed: 0, days: [], dayLabels: [] },
    courses: [],
    badges: [],


    fetchUser: async () => {
        try {
            const { data } = await api.get('/api/me')
            set({
                user: data.user,
                weeklyGoal: data.weeklyGoal,
                courses: data.courses,
                badges: data.badges,
                isAuthenticated: true,
            })
        }
        catch (error) {
            console.error('Failed to fetch user:', error)
        }
    },
    login: (user) => {
        // set() shallow-merges into the state
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
        const { user } = get() // read current state with get()
        if (!user) return

        set({
            // Spread old user, overlay new fields
            user: { ...user, ...updates },
        })
    },

    addXP: (amount) => {
        const { user } = get()
        if (!user) return

        const newXP = user.xpTotal + amount
        const newXPToday = user.xpToday + amount
        const newXPWeek = user.xpThisWeek + amount

        // Simple level calculation based on DESIGN.md thresholds
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

