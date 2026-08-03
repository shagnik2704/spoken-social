import { useQuery } from '@tanstack/react-query'
import api from '@/lib/axios'
import type { LeaderboardResponse } from '@/types'

/**
 * Leaderboard + XP-history data via React Query, replacing the old Zustand store.
 * A shared query key dedups the TopBar prefetch and the Leaderboard page (previously
 * two concurrent identical requests), and inherits the global 5-min staleTime so
 * navigating back doesn't refetch.
 */
export type LeaderboardWindow = 'all' | 'monthly' | 'weekly'

export interface LeaderboardScope {
    scope?: 'global' | 'college' | 'course'
    scopeId?: string | null
    window?: LeaderboardWindow
}

export function useLeaderboard({ scope = 'global', scopeId, window = 'all' }: LeaderboardScope = {}) {
    return useQuery<LeaderboardResponse>({
        queryKey: ['leaderboard', scope, scopeId ?? null, window],
        queryFn: async () =>
            (await api.get('/api/leaderboard', {
                params: {
                    ...(scope !== 'global' && { scope, scope_id: scopeId }),
                    ...(window !== 'all' && { window }),
                },
            })).data,
        enabled: scope === 'global' || Boolean(scopeId),
    })
}

interface EnrolledCourse {
    id: string
    title: string
}

/** The signed-in student's own courses, for scoping the leaderboard. */
export function useMyCourses() {
    return useQuery<EnrolledCourse[]>({
        queryKey: ['my-courses'],
        queryFn: async () => (await api.get('/api/courses/me')).data,
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
