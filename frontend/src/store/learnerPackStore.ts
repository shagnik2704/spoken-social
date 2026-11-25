import { create } from 'zustand'
import api from '@/lib/axios'
import { isTutorialCompleted } from '@/lib/learnerPack'
import { useUserStore } from '@/store/userStore'
import type { LearnerPackOverview } from '@/types'

interface LearnerPackState {
    overview: LearnerPackOverview | null
    overviewCourseId: string | null
    isLoadingOverview: boolean
    fetchOverview: (courseId: string) => Promise<boolean>
}

export const useLearnerPackStore = create<LearnerPackState>((set, get) => ({
    overview: null,
    overviewCourseId: null,
    isLoadingOverview: false,

    fetchOverview: async (courseId) => {
        if (get().overviewCourseId !== courseId) {
            set({ overview: null, overviewCourseId: courseId, isLoadingOverview: true })
        }
        try {
            const res = await api.get<LearnerPackOverview>(`/api/learner-pack/course/${courseId}/overview`)
            if (get().overviewCourseId !== courseId) return true
            const total = res.data.tutorials.length
            if (total > 0) {
                const completed = res.data.tutorials.filter(t => isTutorialCompleted(res.data.courseId, t)).length
                useUserStore.getState().setCourseProgress(res.data.courseId, Math.round((completed / total) * 100))
            }
            set({ overview: res.data, isLoadingOverview: false })
            return true
        } catch {
            if (get().overviewCourseId === courseId) set({ isLoadingOverview: false })
            return false
        }
    },
}))
