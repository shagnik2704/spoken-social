import { useEffect, useMemo } from 'react'
import { useUserStore } from '@/store/userStore'

export const useSyncActiveCourse = (targetCourseId?: string | null): string | null => {
    const courses = useUserStore(state => state.courses)
    const activeCourseId = useUserStore(state => state.activeCourseId)
    const setActiveCourse = useUserStore(state => state.setActiveCourse)

    const matchedCourseId = useMemo((): string | null => {
        if (!targetCourseId || !courses || courses.length === 0) return null
        const target = targetCourseId.trim().toLowerCase()
        const normalized = target.replace('swayam_plus-', '').replace('swayam_', '')
        const matched = courses.find(course => {
            const id = course.id.toLowerCase()
            return id === target || id === normalized || course.title.toLowerCase() === target
        })
        return matched?.id ?? null
    }, [targetCourseId, courses])

    useEffect(() => {
        if (matchedCourseId && matchedCourseId !== activeCourseId) {
            setActiveCourse(matchedCourseId)
        }
    }, [matchedCourseId, activeCourseId, setActiveCourse])

    return matchedCourseId
}
