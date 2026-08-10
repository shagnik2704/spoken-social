import { create } from 'zustand'
import type { User, Course, Badge, Tutorial, RadioValue, TutorialField, ForumActivityMap } from '@/types'
import api from '@/lib/axios'
import {queryClient} from '@/lib/queryClient'


interface UserState {
    user: User | null
    isLoading: boolean
    error: string | null
    isAuthenticated: boolean
    courses: Course[]
    badges: Badge[]
    tutorials: Tutorial[]
    forumActivity: ForumActivityMap
    activeCourseId: string
    activeBatchId: string | null
    activeBatchIsActive: boolean
    weeklyGoal: any
    activeProgrammeId: string
    activeProgrammeName: string
    programmes: any[]

    fetchTutorials: (courseId: string) => Promise<void>
    fetchForumActivity: (courseId: string) => Promise<void>
    updateTutorials: (courseId: string, tutorialId: string, field: TutorialField, value: RadioValue) => void
    fetchUser: () => Promise<void>
    login: (user: User) => void
    logout: () => void
    updateProfile: (updates: Partial<User>) => void
    addXP: (amount: number) => void
    setActiveCourse: (courseId: string) => void
    setActiveBatch: (batchId: string | null, isActive?: boolean) => void
    setActiveProgramme: (id: string, name: string) => void
    switchProgramme: (id: string, name: string) => Promise<any[]>
}

export const useUserStore = create<UserState>((set, get) => ({
    user: null,
    isLoading: false,
    error: null,
    isAuthenticated: false,
    courses: [],
    badges: [],
    tutorials: [],
    forumActivity: {},
    activeCourseId: localStorage.getItem('activeCourseId') || '',
    activeBatchId: null,
    activeBatchIsActive: true,
    weeklyGoal: null,
    activeProgrammeId: localStorage.getItem('activeProgrammeId') || '',
    activeProgrammeName: localStorage.getItem('activeProgrammeName') || '',
    programmes: [],


    fetchUser: async () => {
        set({ isLoading: true, error: null })
        try {
            const activeProgrammeId = get().activeProgrammeId
            const endpoint = activeProgrammeId ? `/api/me?programme_id=${activeProgrammeId}` : '/api/me'
            const [meRes, progRes] = await Promise.all([
                api.get(endpoint),
                api.get('/api/programmes/me')
            ])
            // Validate activeProgrammeId against fetched programmes
            const fetchedProgrammes = progRes.data || []
            const savedProgrammeId = activeProgrammeId
            const programmeIsValid = savedProgrammeId && fetchedProgrammes.some((p: any) => p.id === savedProgrammeId)
            let effectiveProgrammeId = savedProgrammeId
            let effectiveProgrammeName = get().activeProgrammeName

            if (!programmeIsValid && fetchedProgrammes.length > 0) {
                // Auto-select first programme and re-fetch courses for it
                effectiveProgrammeId = fetchedProgrammes[0].id
                effectiveProgrammeName = fetchedProgrammes[0].name
                localStorage.setItem('activeProgrammeId', effectiveProgrammeId)
                localStorage.setItem('activeProgrammeName', effectiveProgrammeName)
            }

            // Restore saved courseId if it's still valid, otherwise fall back to first course
            const savedCourseId = get().activeCourseId || localStorage.getItem('activeCourseId') || ''
            const fetchedCourses = meRes.data.courses || []
            const restoredCourse = fetchedCourses.find((c: any) => c.id === savedCourseId)
            const effectiveCourse = restoredCourse || fetchedCourses[0]
            const effectiveCourseId = effectiveCourse?.id || ''

            // Persist the effective courseId
            if (effectiveCourseId) {
                localStorage.setItem('activeCourseId', effectiveCourseId)
            }

            set({
                user: meRes.data.user,
                isLoading: false,
                weeklyGoal: meRes.data.weeklyGoal,
                courses: fetchedCourses,
                badges: meRes.data.badges,
                programmes: fetchedProgrammes,
                isAuthenticated: true,
                activeProgrammeId: effectiveProgrammeId,
                activeProgrammeName: effectiveProgrammeName,
                activeCourseId: effectiveCourseId,
                activeBatchId: effectiveCourse?.batchId || null,
                activeBatchIsActive: effectiveCourse?.batchStatus !== 'inactive',
            })
        }
        catch (error) {
            console.error('Failed to fetch user:', error)
            set({ error: 'Failed to load', isLoading: false })
        }
    },


    fetchTutorials: async (courseId) => {
        try {
            const { data } = await api.get(`/api/me/courses/${courseId}/tutorials`)
            const fields = ['watched', 'practiced', 'assignmentDone', 'forumAsked', 'forumAnswered', 'minitaskOpted'] as const
            const converted = data.map((t: any) => {
                const out = { ...t }
                for (const f of fields) {
                    out[f] = t[f] === true ? 'yes' : null
                }
                return out
            })
            set({ tutorials: converted })
        }
        catch (error) {
            console.error('Failed to fetch tutorials', error)
        }
    },

    fetchForumActivity: async (courseId) => {
        try {
            const { data } = await api.get(`/api/me/courses/${courseId}/forum-activity`)
            set({ forumActivity: data })
        } catch (error) {
            console.error('Failed to fetch forum activity', error)
        }
    },

    updateTutorials(courseId, tutorialId, field, value) {
        if (!get().activeBatchIsActive) return

        const boolValue = value === 'yes' ? true : value === 'no' ? false : null

        set({
            tutorials: get().tutorials.map(t => {
                if (t.id !== tutorialId) return t
                const updated = { ...t, [field]: value }
                if (field === 'practiced' && value === 'yes') updated.completed = true

                const XP: Record<string, number> = { watched: 10, practiced: 10, assignmentDone: 5, forumAsked: 5, forumAnswered: 10 }
                updated.xpEarned = Object.entries(XP).reduce((sum, [f, pts]) => sum + (updated[f as TutorialField] === 'yes' ? pts : 0), 0)
                return updated
            })
        })

        api.put(`/api/me/courses/${courseId}/tutorials/${tutorialId}`, { field, value: boolValue }).then(()=>{
            queryClient.invalidateQueries({queryKey:['leaderboard']})
            queryClient.invalidateQueries({queryKey:['xp-history']})
        })
    },

    login: (user) => {
        set({
            user,
            isAuthenticated: true,
        })
    },

    logout: () => {
        localStorage.removeItem('activeProgrammeId')
        localStorage.removeItem('activeProgrammeName')
        localStorage.removeItem('activeCourseId')
        set({
            user: null,
            isAuthenticated: false,
            activeProgrammeId: '',
            activeProgrammeName: '',
            activeCourseId: '',
        })
    },

    updateProfile: (updates) => {
        const { user } = get()
        if (!user) return

        set({
            user: { ...user, ...updates },
        })
    },

    addXP: (amount) => {
        if (!get().activeBatchIsActive) return
        const { user } = get()
        if (!user) return

        const newXP = user.xpTotal + amount
        set({
            user: {
                ...user,
                xpTotal: newXP,
            },
        })
    },

    setActiveCourse: (courseId) => {
        const courses = get().courses
        const course = courses.find(c => c.id === courseId)
        localStorage.setItem('activeCourseId', courseId)
        set({
            activeCourseId: courseId,
            activeBatchId: course?.batchId || null,
            activeBatchIsActive: course?.batchStatus !== 'inactive',
        })
    },

    setActiveBatch: (batchId, isActive = true) => {
        set({ activeBatchId: batchId, activeBatchIsActive: isActive })
    },

    setActiveProgramme: (id, name) => {
        localStorage.setItem('activeProgrammeId', id)
        localStorage.setItem('activeProgrammeName', name)
        set({ activeProgrammeId: id, activeProgrammeName: name })
    },

    switchProgramme: async (id, name) => {
        localStorage.setItem('activeProgrammeId', id)
        localStorage.setItem('activeProgrammeName', name)
        set({ activeProgrammeId: id, activeProgrammeName: name, isLoading: true })
        try {
            const { data } = await api.get(`/api/me?programme_id=${id}`)
            const newCourses = data.courses || []
            const firstCourseId = newCourses[0]?.id || ''
            if (firstCourseId) {
                localStorage.setItem('activeCourseId', firstCourseId)
            } else {
                localStorage.removeItem('activeCourseId')
            }
            set({
                courses: newCourses,
                activeCourseId: firstCourseId,
                activeBatchId: newCourses[0]?.batchId || null,
                activeBatchIsActive: newCourses[0]?.batchStatus !== 'inactive',
                isLoading: false,
            })
            return newCourses
        } catch (error) {
            console.error('Failed to switch programme:', error)
            set({ isLoading: false })
            return []
        }
    }
}))
