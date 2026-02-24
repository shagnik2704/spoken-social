// ============================================================
// USER STORE — Zustand
// ============================================================
//
// 🧠 ZUSTAND CRASH COURSE:
//
// Zustand is dead simple. Here's the mental model:
//
//   1. You call `create()` and give it a function.
//   2. That function receives `set` — the ONLY way to update state.
//   3. The function returns an object: your state + your actions.
//   4. In components, you use `useUserStore(state => state.whatever)`.
//
// That's it. No providers, no reducers, no boilerplate.
//
// WHY ZUSTAND over Context?
// - Context re-renders ALL consumers when ANY part of state changes.
// - Zustand only re-renders consumers of the SPECIFIC slice that changed.
// - Context needs a Provider wrapper. Zustand doesn't.
// - Zustand has built-in devtools, persistence, middleware.
//
// ============================================================

import { create } from 'zustand'
import type { User, Streak, WeeklyGoal, Course, Badge } from '@/types'
import {
    CURRENT_USER, MOCK_STREAK, MOCK_WEEKLY_GOAL,
    MOCK_COURSES, MOCK_BADGES,
} from '@/data/mockData'

// ----- Define the shape of the store -----

interface UserState {
    // State (data)
    user: User | null
    isAuthenticated: boolean
    streak: Streak
    weeklyGoal: WeeklyGoal
    courses: Course[]
    badges: Badge[]

    // Actions (functions that modify state)
    login: (user: User) => void
    logout: () => void
    updateProfile: (updates: Partial<User>) => void
    addXP: (amount: number) => void
}

// ----- Create the store -----
//
// `set` is the ONLY way to update state.
// `get` lets you READ current state inside an action.
//
// IMPORTANT: `set` does a SHALLOW MERGE by default.
// So `set({ user: newUser })` only replaces `user`, not the entire state.
// If you need to update nested state, spread it yourself.

export const useUserStore = create<UserState>((set, get) => ({
    // ----- Initial state -----
    // Pre-loaded with mock data. When backend is ready,
    // these start as null/empty and get filled by login().
    user: CURRENT_USER,
    isAuthenticated: true,
    streak: MOCK_STREAK,
    weeklyGoal: MOCK_WEEKLY_GOAL,
    courses: MOCK_COURSES,
    badges: MOCK_BADGES,

    // ----- Actions -----

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

// ============================================================
// HOW TO USE IN A COMPONENT:
//
//   import { useUserStore } from '@/store/userStore'
//
//   function MyComponent() {
//     // ✅ GOOD: Select only what you need (minimal re-renders)
//     const userName = useUserStore(state => state.user?.name)
//     const addXP = useUserStore(state => state.addXP)
//
//     // ❌ BAD: Selecting everything (re-renders on ANY state change)
//     // const store = useUserStore()
//
//     return <h1>Hi {userName}!</h1>
//   }
//
// ============================================================
