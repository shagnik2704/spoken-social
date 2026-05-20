import { useQuery } from "@tanstack/react-query"
import api from '@/lib/axios'

const fetchColleges = async () => {
    const { data } = await api.get('/api/coordinator/colleges')
    return data
}

const fetchPlatformSummary = async (state?: string) => {
    const url = state && state !== 'all' ? `/api/admin/platform-summary?state=${encodeURIComponent(state)}` : '/api/admin/platform-summary'
    const { data } = await api.get(url)
    return data
}

const fetchCollegeDailyXP = async (month: string, collegesId: string[]) => {
    const { data } = await api.get(`/api/admin/college-daily-xp?month=${month}&college_ids=${collegesId.join(',')}`)
    return data
}

const fetchCollegesDetails = async (collegeId: string, page: number, sortBy: string, statusFilter: string, searchQuery: string) => {
    const { data } = await api.get(`/api/coordinator/colleges/${collegeId}?page=${page}&limit=10&sort=${sortBy}&status=${statusFilter}&search=${searchQuery}`)
    return data
}

const fetchStudentFeedback = async (studentId: string) => {
    const { data } = await api.get(`/api/admin/students/${studentId}/feedback`)
    return data
}

const fetchFeedbackSummary = async (filters: { tutorialId: string; stepType: string; reason: string }) => {
    const params = new URLSearchParams()
    if (filters.tutorialId) params.set('tutorial_id', filters.tutorialId)
    if (filters.stepType) params.set('step_type', filters.stepType)
    if (filters.reason) params.set('reason', filters.reason)
    const qs = params.toString()
    const url = qs ? `/api/admin/feedback-summary?${qs}` : '/api/admin/feedback-summary'
    const { data } = await api.get(url)
    return data
}





export function useColleges() {
    return useQuery({
        queryKey: ['colleges'],
        queryFn: fetchColleges
    })
}

export function usePlatformSummary(state?: string) {
    return useQuery({
        queryKey: ['admin', 'platform-summary', state || 'all'],
        queryFn: () => fetchPlatformSummary(state)
    })
}

export function useCollegesDailyXP(month: string, collegesIds: string[]) {
    return useQuery({
        queryKey: ['admin', 'college-daily-xp', month, collegesIds],
        queryFn: () => fetchCollegeDailyXP(month, collegesIds),
        enabled: collegesIds.length > 0
    })
}


export function useCollegeDetails(
    collegeId: string | null,
    page: number,
    sortBy: string,
    statusFilter: string,
    searchQuery: string
) {
    return useQuery({
        queryKey: ['admin', 'college-details', collegeId, page, sortBy, statusFilter, searchQuery],
        queryFn: () => fetchCollegesDetails(collegeId!, page, sortBy, statusFilter, searchQuery),
        enabled: !!collegeId
    })
}

export function useStudentFeedback(studentId: string) {
    return useQuery({
        queryKey: ['admin', 'student-feedback'],
        queryFn: () => fetchStudentFeedback(studentId)
    })
}

export function useFeedbackSummary(filters: { tutorialId: string; stepType: string; reason: string }) {
    return useQuery({
        queryKey: ['admin', 'feedback-summary', filters],
        queryFn: () => fetchFeedbackSummary(filters),
    })
}
