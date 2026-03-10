import { useQuery } from "@tanstack/react-query"
import api from '@/lib/axios'

const fetchColleges = async () => {
    const { data } = await api.get('/api/coordinator/colleges')
    return data
}

const fetchPlatformSummary = async () => {
    const { data } = await api.get('/api/admin/platform-summary')
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





export function useColleges() {
    return useQuery({
        queryKey: ['colleges'],
        queryFn: fetchColleges
    })
}

export function usePlatformSummary() {
    return useQuery({
        queryKey: ['admin', 'platform-summary'],
        queryFn: fetchPlatformSummary
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




