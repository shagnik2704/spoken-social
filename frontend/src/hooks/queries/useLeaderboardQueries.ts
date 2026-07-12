import { useQuery } from '@tanstack/react-query'
import api from '@/lib/axios'
import type { LeaderboardUser } from '@/types'

/**
 * Leaderboard + XP-history data via React Query, replacing the old Zustand store.
 * A shared query key dedups the TopBar prefetch and the Leaderboard page (previously
 * two concurrent identical requests), and inherits the global 5-min staleTime so
 * navigating back doesn't refetch.
 */
export function useLeaderboard() {
    return useQuery<LeaderboardUser[]>({
        queryKey: ['leaderboard'],
        queryFn: async () => (await api.get('/api/leaderboard')).data,
    })
}

interface XPHistoryResponse {
    month: string
    days: { day: number; xp: number }[]
}

export function useXPHistory(month: string) {
    return useQuery<XPHistoryResponse>({
        queryKey: ['xp-history', month],
        queryFn: async () => (await api.get('/api/xp-history', { params: { month } })).data,
        enabled: !!month,
    })
}
