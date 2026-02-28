import { create } from 'zustand'
import type { LeaderboardUser } from '@/types'
import api from '@/lib/axios'
import { useUserStore } from './userStore'

interface LeaderboardState {
    leaderboardData: LeaderboardUser[]
    isLoading: boolean
    eventSource: EventSource | null

    fetchLeaderboard: () => Promise<void>
    connectSSE: () => void
    disconnectSSE: () => void
    handleXPUpdate: (data: { userId: string; xpTotal: number; level: number; levelTitle: string }) => void
}

export const useLeaderboardStore = create<LeaderboardState>((set, get) => ({
    leaderboardData: [],
    isLoading: false,
    eventSource: null,

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

    handleXPUpdate: (data) => {
        const { leaderboardData } = get()

        // Update the user's XP in the leaderboard array
        let updated = leaderboardData.map(u =>
            u.id === data.userId
                ? { ...u, xp: data.xpTotal, level: data.level, levelTitle: data.levelTitle }
                : u
        )

        // Re-sort by XP descending and re-assign ranks
        updated.sort((a, b) => b.xp - a.xp)
        updated = updated.map((u, i) => ({ ...u, rank: i + 1 }))

        set({ leaderboardData: updated })

        // If this is the current user, sync userStore too
        const currentUser = useUserStore.getState().user
        if (currentUser && currentUser.id === data.userId) {
            useUserStore.getState().updateProfile({
                xpTotal: data.xpTotal,
                level: data.level,
                levelTitle: data.levelTitle,
            })
        }
    },

    connectSSE: () => {
        const { eventSource } = get()
        // Don't double-connect
        if (eventSource) return

        const es = new EventSource('http://localhost:8000/api/events')

        es.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                if (data.type === 'xp_update') {
                    get().handleXPUpdate(data)
                }
            } catch (err) {
                console.error('SSE parse error:', err)
            }
        }

        es.onerror = () => {
            // EventSource will automatically reconnect
            console.warn('SSE connection error — will retry automatically')
        }

        set({ eventSource: es })
    },

    disconnectSSE: () => {
        const { eventSource } = get()
        if (eventSource) {
            eventSource.close()
            set({ eventSource: null })
        }
    },
}))
