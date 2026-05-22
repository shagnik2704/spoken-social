import { useQuery } from "@tanstack/react-query"
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

const fetchCollegeDailyXP = async (month: string, collegesId: string[]) => {
    const { data } = await api.get(`/api/admin/college-daily-xp?month=${month}&college_ids=${collegesId.join(',')}`)
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

export function useColleges(courseId?: string, batchId?: string | null) {
    return useQuery({
        queryKey: ['colleges', courseId, batchId],
        queryFn: () => fetchColleges(courseId, batchId)
    })
}

export function usePlatformSummary(state?: string, courseId?: string, batchId?: string | null) {
    return useQuery({
        queryKey: ['admin', 'platform-summary', state || 'all', courseId, batchId],
        queryFn: () => fetchPlatformSummary(state, courseId, batchId)
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
    searchQuery: string,
    courseId?: string,
    batchId?: string | null
) {
    return useQuery({
        queryKey: ['admin', 'college-details', collegeId, page, sortBy, statusFilter, searchQuery, courseId, batchId],
        queryFn: () => fetchCollegesDetails(collegeId!, page, sortBy, statusFilter, searchQuery, courseId, batchId),
        enabled: !!collegeId
    })
}

export function useStudentFeedback(studentId: string) {
    return useQuery({
        queryKey: ['admin', 'student-feedback'],
        queryFn: () => fetchStudentFeedback(studentId)
    })
}

export function useFeedbackSummary(
    filters: { tutorialId: string; stepType: string; reason: string },
    courseId?: string,
    batchId?: string | null
) {
    return useQuery({
        queryKey: ['admin', 'feedback-summary', filters, courseId, batchId],
        queryFn: () => fetchFeedbackSummary(filters, courseId, batchId),
    })
}
