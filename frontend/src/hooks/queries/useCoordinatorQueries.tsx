import { useQuery } from "@tanstack/react-query";
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

const fetchCollegeDetails = async (
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

const fetchCollegeAnalytics = async (collegeId: string, courseId?: string, batchId?: string | null) => {
    let url = `/api/coordinator/colleges/${collegeId}/analytics`
    const params = new URLSearchParams()
    if (courseId) params.set('course_id', courseId)
    if (batchId) params.set('batch_id', batchId)
    const qs = params.toString()
    if (qs) url += `?${qs}`

    const { data } = await api.get(url)
    return data
}


export function useCoordinatorColleges(courseId?: string, batchId?: string | null, enabled: boolean = true) {
    return useQuery({
        queryKey: ['coordinator', 'colleges', courseId, batchId],
        queryFn: () => fetchColleges(courseId, batchId),
        enabled
    })
}

export function useCoordinatorCollegeDetails(
    collegeId: string | null,
    page: number,
    sortBy: string,
    statusFilter: string,
    searchQuery: string,
    courseId?: string,
    batchId?: string | null,
    enabled: boolean = true
) {
    return useQuery({
        queryKey: ['coordinator', 'college-details', collegeId, page, sortBy, statusFilter, searchQuery, courseId, batchId],
        queryFn: () => fetchCollegeDetails(collegeId!, page, sortBy, statusFilter, searchQuery, courseId, batchId),
        enabled: enabled && !!collegeId
    })
}

export function useCoordinatorCollegeAnalytics(
    collegeId: string | null,
    courseId?: string,
    batchId?: string | null,
    enabled: boolean = true
) {
    return useQuery({
        queryKey: ['coordinator', 'college-analytics', collegeId, courseId, batchId],
        queryFn: () => fetchCollegeAnalytics(collegeId!, courseId, batchId),
        enabled: enabled && !!collegeId
    })
}

const fetchCoordinatorFeedbackSummary = async (
    collegeId: string,
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
    const url = qs
        ? `/api/coordinator/colleges/${collegeId}/feedback-summary?${qs}`
        : `/api/coordinator/colleges/${collegeId}/feedback-summary`
    const { data } = await api.get(url)
    return data
}

export function useCoordinatorFeedbackSummary(
    collegeId: string | null,
    filters: { tutorialId: string; stepType: string; reason: string },
    courseId?: string,
    batchId?: string | null,
    enabled: boolean = true
) {
    return useQuery({
        queryKey: ['coordinator', 'feedback-summary', collegeId, filters, courseId, batchId],
        queryFn: () => fetchCoordinatorFeedbackSummary(collegeId!, filters, courseId, batchId),
        enabled: enabled && !!collegeId
    })
}
