import { create } from 'zustand'
import type { LeaderboardUser } from '@/types'
import api from '@/lib/axios'

interface XPHistoryDay {
    day: number
    xp: number
}

interface LeaderboardState {
    leaderboardData: LeaderboardUser[]
    isLoading: boolean
    xpHistory: XPHistoryDay[]
    xpHistoryMonth: string

    fetchLeaderboard: () => Promise<void>
    fetchXPHistory: (month: string) => Promise<void>
}

export const useLeaderboardStore = create<LeaderboardState>((set) => ({
    leaderboardData: [],
    isLoading: false,
    xpHistory: [],
    xpHistoryMonth: '',

    fetchLeaderboard: async () => {
        set({ isLoading: true })
        try {
            const { data } = await api.get('/api/leaderboard')
            set({ leaderboardData: data, isLoading: false })
        } catch (error) {
            console.error('Failed to fetch leaderboard:', error)
            set({ isLoading: false })
        }
    },

    fetchXPHistory: async (month: string) => {
        try {
            const { data } = await api.get('/api/xp-history', { params: { month } })
            set({ xpHistory: data.days, xpHistoryMonth: data.month })
        } catch (error) {
            console.error('Failed to fetch XP history:', error)
        }
    },
}))


