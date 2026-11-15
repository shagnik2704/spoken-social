import { LINUX_COURSE_ID } from '@/lib/learnerPack'

export interface CourseWalkthrough {
    videoUrl: string
    posterUrl: string
    captionsUrl?: string
    durationLabel: string
    summary: string
    published: boolean
}

const WALKTHROUGHS: Record<string, CourseWalkthrough> = {
    [LINUX_COURSE_ID]: {
        videoUrl: '/walkthroughs/linux.mp4',
        posterUrl: '/walkthroughs/linux-poster.svg',
        durationLabel: '3:40',
        summary: 'Weeks, steps, XP and the forum',
        published: false,
    },
}

export const getCourseWalkthrough = (courseId?: string | null): CourseWalkthrough | null => {
    if (!courseId) return null
    const walkthrough = WALKTHROUGHS[courseId]
    if (!walkthrough || !(walkthrough.published || import.meta.env.DEV)) return null
    return walkthrough
}

export const WALKTHROUGH_WATCHED_FRACTION = 0.8
