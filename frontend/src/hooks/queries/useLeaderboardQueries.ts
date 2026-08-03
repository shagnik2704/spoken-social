import { useQuery } from '@tanstack/react-query'
import api from '@/lib/axios'
import type { LeaderboardResponse } from '@/types'

/**
 * Leaderboard + XP-history data via React Query, replacing the old Zustand store.
 * A shared query key dedups the TopBar prefetch and the Leaderboard page (previously
 * two concurrent identical requests), and inherits the global 5-min staleTime so
 * navigating back doesn't refetch.
 */
export interface LeaderboardScope {
    scope?: 'global' | 'college'
    scopeId?: string | null
}

export function useLeaderboard({ scope = 'global', scopeId }: LeaderboardScope = {}) {
    return useQuery<LeaderboardResponse>({
        queryKey: ['leaderboard', scope, scopeId ?? null],
        queryFn: async () =>
            (await api.get('/api/leaderboard', {
                params: scope === 'global' ? undefined : { scope, scope_id: scopeId },
            })).data,
        enabled: scope === 'global' || Boolean(scopeId),
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
