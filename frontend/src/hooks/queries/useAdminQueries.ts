import { useQuery, keepPreviousData } from "@tanstack/react-query"
import api from '@/lib/axios'

const fetchColleges = async (courseId?: string, batchId?: string | null) => {
    let url = '/api/coordinator/colleges'
    const params = new URLSearchParams()
    if (courseId) params.set('course_id', courseId)
    if (batchId) params.set('batch_id', batchId)
    const qs = params.toString()
    if (qs) url += `?${qs}`

    const { data } = await api.get(url)
    return data
}

const fetchPlatformSummary = async (state?: string, courseId?: string, batchId?: string | null) => {
    const params = new URLSearchParams()
    if (state && state !== 'all') params.set('state', state)
    if (courseId) params.set('course_id', courseId)
    if (batchId) params.set('batch_id', batchId)
    
    const qs = params.toString()
    const url = qs ? `/api/admin/platform-summary?${qs}` : '/api/admin/platform-summary'
    const { data } = await api.get(url)
    return data
}

const fetchCollegeDailyXP = async (month: string, collegesId: string[], courseId?: string) => {
    let url = `/api/admin/college-daily-xp?month=${month}`
    if (collegesId.length > 0) url += `&college_ids=${collegesId.join(',')}`
    if (courseId) url += `&course_id=${courseId}`
    const { data } = await api.get(url)
    return data
}

const fetchCollegesDetails = async (
    collegeId: string, 
    page: number, 
    sortBy: string, 
    statusFilter: string, 
    searchQuery: string,
    courseId?: string,
    batchId?: string | null
) => {
    const params = new URLSearchParams({
        page: String(page),
        limit: '10',
        sort: sortBy,
        status: statusFilter,
        search: searchQuery
    })
    if (courseId) params.set('course_id', courseId)
    if (batchId) params.set('batch_id', batchId)

    const { data } = await api.get(`/api/coordinator/colleges/${collegeId}?${params.toString()}`)
    return data
}

const fetchStudentFeedback = async (studentId: string) => {
    const { data } = await api.get(`/api/admin/students/${studentId}/feedback`)
    return data
}

const fetchFeedbackSummary = async (
    filters: { tutorialId: string; stepType: string; reason: string },
    courseId?: string,
    batchId?: string | null
) => {
    const params = new URLSearchParams()
    if (filters.tutorialId) params.set('tutorial_id', filters.tutorialId)
    if (filters.stepType) params.set('step_type', filters.stepType)
    if (filters.reason) params.set('reason', filters.reason)
    if (courseId) params.set('course_id', courseId)
    if (batchId) params.set('batch_id', batchId)

    const qs = params.toString()
    const url = qs ? `/api/admin/feedback-summary?${qs}` : '/api/admin/feedback-summary'
    const { data } = await api.get(url)
    return data
}

export function useColleges(courseId?: string, batchId?: string | null, enabled: boolean = true) {
    return useQuery({
        queryKey: ['colleges', courseId, batchId],
        queryFn: () => fetchColleges(courseId, batchId),
        enabled
    })
}

export function usePlatformSummary(state?: string, courseId?: string, batchId?: string | null, enabled: boolean = true) {
    return useQuery({
        queryKey: ['admin', 'platform-summary', state || 'all', courseId, batchId],
        queryFn: () => fetchPlatformSummary(state, courseId, batchId),
        enabled
    })
}

export function useCollegesDailyXP(month: string, courseId?: string) {
    // Fetch the full (all-colleges) dataset once; the chart filters colleges client-side.
    // College selection is NOT in the key, so toggling checkboxes triggers zero refetches.
    return useQuery({
        queryKey: ['admin', 'college-daily-xp', month, courseId],
        queryFn: () => fetchCollegeDailyXP(month, [], courseId),
        enabled: !!month
    })
}


export function useCollegeDetails(
    collegeId: string | null,
    page: number,
    sortBy: string,
    statusFilter: string,
    searchQuery: string,
    courseId?: string,
    batchId?: string | null
) {
    return useQuery({
        queryKey: ['admin', 'college-details', collegeId, page, sortBy, statusFilter, searchQuery, courseId, batchId],
        queryFn: () => fetchCollegesDetails(collegeId!, page, sortBy, statusFilter, searchQuery, courseId, batchId),
        enabled: !!collegeId,
        placeholderData: keepPreviousData, // keep the prior page/search visible instead of flashing empty
    })
}

const fetchMinitaskAnalysis = async (courseId?: string, batchId?: string | null) => {
    const params = new URLSearchParams()
    if (courseId) params.set('course_id', courseId)
    if (batchId) params.set('batch_id', batchId)
    const qs = params.toString()
    const { data } = await api.get(`/api/admin/minitask-analysis${qs ? `?${qs}` : ''}`)
    return data
}

export function useMinitaskAnalysis(courseId?: string, batchId?: string | null) {
    return useQuery<Record<string, Record<number, number>>>({
        queryKey: ['admin', 'minitask-analysis', courseId, batchId],
        queryFn: () => fetchMinitaskAnalysis(courseId, batchId),
    })
}

export function useStudentFeedback(studentId: string) {
    return useQuery({
        queryKey: ['admin', 'student-feedback', studentId],
        queryFn: () => fetchStudentFeedback(studentId)
    })
}

export function useFeedbackSummary(
    filters: { tutorialId: string; stepType: string; reason: string },
    courseId?: string,
    batchId?: string | null,
    enabled: boolean = true
) {
    return useQuery({
        queryKey: ['admin', 'feedback-summary', filters, courseId, batchId],
        queryFn: () => fetchFeedbackSummary(filters, courseId, batchId),
        enabled
    })
}

export function useComparisonMetrics(state?: string, useMock?: boolean) {
    return useQuery({
        queryKey: ['admin', 'comparison-metrics', state || 'all', useMock],
        queryFn: async () => {
            const params = new URLSearchParams()
            if (state && state !== 'all') params.set('state', state)
            if (useMock) params.set('use_mock', 'true')
            const qs = params.toString()
            const url = qs ? `/api/admin/comparison-metrics?${qs}` : '/api/admin/comparison-metrics'
            const { data } = await api.get(url)
            return data
        }
    })
}

