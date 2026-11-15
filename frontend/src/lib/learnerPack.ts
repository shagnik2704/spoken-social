import { FileText, FolderArchive, Wrench, type LucideIcon } from 'lucide-react'
import type { CourseMaterialUrls, LearnerPackOverviewTutorial, QuizOption, RadioValue, XpRewards } from '@/types'

export type TutorialStepId = 'video' | 'reading' | 'activity' | 'assignment' | 'quiz'

const TUTORIAL_STEP_IDS: readonly TutorialStepId[] = ['video', 'reading', 'activity', 'assignment', 'quiz']

export const isTutorialStepId = (value?: string): value is TutorialStepId =>
    TUTORIAL_STEP_IDS.includes(value as TutorialStepId)

export const LINUX_COURSE_ID = 'linux'
const SETUP_TUTORIAL_COUNT = 2

export const QUIZ_PASS_SCORE = 3
export const TERMINAL_MAX_CHARS = 20000
export const SCREENSHOT_MAX_BYTES = 5 * 1024 * 1024

export const isLinuxCourse = (courseId?: string | null): boolean => courseId === LINUX_COURSE_ID

export const isSetupTutorial = (courseId: string | null | undefined, tutorialNumber: number): boolean =>
    isLinuxCourse(courseId) && tutorialNumber <= SETUP_TUTORIAL_COUNT

export const isDone = (value: RadioValue | boolean | undefined): boolean => value === true || value === 'yes'

const PERSONALITY_DEV_WEEK_TOPICS: Record<number, string> = {
    1: 'Introduction to Emotions & Understanding Fear',
    2: 'Understanding Anger & Sadness',
    3: 'Happiness, Guilt & 7-Day Emotion Log',
    4: 'Jealousy, Admiration & Emotion Log Wrap-up',
    5: 'Reality, Interpretations & Understanding Beliefs',
    6: 'How to Change Beliefs & 7-Day Belief Log',
    7: 'Judgment, Feedback & 7-Day Empathy Log',
    8: 'Catch-up, Live Session 1 & Midterm Revision',
    9: 'Neuroplasticity & The Magic of Failures',
    10: 'The Word "Yet" & Mindful Breathing Log',
    11: 'Practising Growth Mindset & Growth Plan',
    12: 'Personal Growth Portfolio & Final Exam Prep',
}

const LINUX_WEEK_TOPICS: Record<number, string> = {
    1: 'VirtualBox & Ubuntu Linux Installation',
    2: 'Ubuntu Desktop, Synaptic & Lab 1',
    3: 'Basic Commands, Date & Time',
    4: 'Command Structure, Utilities & Lab 2',
    5: 'File System & Regular Files',
    6: 'Streams, Pipes, Processes & Lab 3',
    7: 'Linux Environment & System Administration',
    8: 'Permissions, Ownership & Lab 4',
    9: 'Simple Filters & Introduction to grep',
    10: 'Mastering grep & Introduction to sed',
    11: 'sed Text Editing, Lab 5 & Capstone Start',
    12: 'Capstone Project Submission & Final Exam Revision',
}

export const getWeekTopic = (weekNumber: number, courseId?: string | null): string => {
    const topics = isLinuxCourse(courseId) ? LINUX_WEEK_TOPICS : PERSONALITY_DEV_WEEK_TOPICS
    return topics[weekNumber] || `Week ${weekNumber}`
}

export const resolveMediaUrl = (url?: string | null): string => {
    if (!url) return ''
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('blob:')) return url
    const apiUrl: string = import.meta.env.VITE_API_URL || ''
    if (apiUrl && !apiUrl.startsWith('/')) {
        return `${apiUrl.replace(/\/$/, '')}${url}`
    }
    return url
}

export interface ForumAskUrlOptions {
    courseId?: string | null
    forumCategory?: string | null
    courseTitle?: string | null
    tutorialTitle?: string | null
    videoPositionSeconds?: number
}

export const FORUM_SECOND_BUCKET = 10

const FORUM_TUTORIAL_NAMES: Record<string, string> = {
    'Date and Time Commands in Linux': 'Date and Time Commands',
}

const forumTimeRanges = (positionSeconds: number): { minuteRange: string; secondRange: string } => {
    const total = Math.max(0, Math.floor(positionSeconds))
    const minute = Math.floor(total / 60)
    const second = Math.floor((total % 60) / FORUM_SECOND_BUCKET) * FORUM_SECOND_BUCKET
    return { minuteRange: `${minute}-${minute + 1}`, secondRange: `${second}-${second + FORUM_SECOND_BUCKET}` }
}

export const getForumAskUrl = (options: ForumAskUrlOptions): string => {
    const {
        courseId,
        forumCategory,
        courseTitle,
        tutorialTitle,
        videoPositionSeconds = 0,
    } = options
    const { minuteRange, secondRange } = forumTimeRanges(videoPositionSeconds)

    let category = forumCategory
    if (isLinuxCourse(courseId) || forumCategory?.toLowerCase() === 'linux' || courseTitle?.toLowerCase().includes('linux')) {
        category = 'Linux Ubuntu'
    } else if (category) {
        category = category.replace(/-/g, ' ')
    } else if (courseTitle) {
        category = courseTitle
    }

    const parts: string[] = []
    if (category) {
        parts.push(`category=${encodeURIComponent(category)}`)
    }
    if (tutorialTitle) {
        parts.push(`tutorial=${encodeURIComponent(FORUM_TUTORIAL_NAMES[tutorialTitle] ?? tutorialTitle)}`)
    }
    parts.push(`minute_range=${encodeURIComponent(minuteRange)}`)
    parts.push(`second_range=${encodeURIComponent(secondRange)}`)

    return parts.length > 0
        ? `https://forums.spoken-tutorial.org/new-question/?${parts.join('&')}`
        : 'https://forums.spoken-tutorial.org/new-question/'
}

export const getForumCategoryUrl = (forumCategory?: string | null, courseTitle?: string | null): string => {
    let category = forumCategory
    if (!category && courseTitle?.toLowerCase().includes('linux')) {
        category = 'Linux'
    }
    if (category) {
        return `https://forums.spoken-tutorial.org/filter/${encodeURIComponent(category.replace(/ /g, '-'))}/`
    }
    return 'https://forums.spoken-tutorial.org/'
}

export const coursePath = (courseId: string): string => `/courses/${courseId}`

export const tutorialPath = (courseId: string, tutorialNumber: number, step?: TutorialStepId): string =>
    `${coursePath(courseId)}/tutorials/${tutorialNumber}${step ? `/${step}` : ''}`

export const getActivityLabel = (courseId: string | null | undefined, _tutorialNumber?: number): string => {
    if (isLinuxCourse(courseId)) return 'Assignment'
    return 'Activity & reflection'
}

export const isTutorialCompleted = (courseId: string | null | undefined, tutorial: LearnerPackOverviewTutorial): boolean => {
    const progress = tutorial.userProgress
    return (
        progress.status === 'completed' ||
        progress.quizPassed ||
        (isSetupTutorial(courseId, tutorial.number) && progress.reflectionSubmitted)
    )
}

export type OverviewStepKind = 'lesson' | 'setup' | 'lab' | 'activity' | 'assignment' | 'quiz'

export interface OverviewStep {
    kind: OverviewStepKind
    label: string
    done: boolean
}

const getActivityKind = (courseId: string | null | undefined, _tutorialNumber?: number): OverviewStepKind => {
    if (isLinuxCourse(courseId)) return 'assignment'
    return 'activity'
}

export const getOverviewSteps = (courseId: string | null | undefined, tutorial: LearnerPackOverviewTutorial): OverviewStep[] => {
    const progress = tutorial.userProgress
    const steps: OverviewStep[] = [
        { kind: 'lesson', label: 'Lesson', done: progress.watched },
        { kind: getActivityKind(courseId, tutorial.number), label: getActivityLabel(courseId, tutorial.number), done: progress.reflectionSubmitted },
    ]
    if (tutorial.hasAssignment) {
        steps.push({ kind: 'assignment', label: 'Assignment', done: Boolean(progress.assignmentDone) })
    }
    if (!isSetupTutorial(courseId, tutorial.number)) {
        steps.push({ kind: 'quiz', label: 'Quiz', done: progress.quizPassed })
    }
    return steps
}

export type XpFlag = 'watched' | 'activityDone' | 'assignmentDone' | 'practiced'
export type XpFlags = Record<XpFlag, boolean>

const STEP_XP_FLAGS: Record<TutorialStepId, XpFlag[]> = {
    video: ['watched'],
    reading: ['watched'],
    activity: ['activityDone', 'assignmentDone'],
    assignment: ['assignmentDone'],
    quiz: ['practiced'],
}

export interface TutorialXp {
    earned: number
    total: number
    forumBonus: number
    available: XpFlag[]
}

export const getTutorialXpFlags = (courseId: string | null | undefined, hasQuiz: boolean): XpFlag[] => {
    const flags: XpFlag[] = ['watched']
    if (!isLinuxCourse(courseId)) flags.push('activityDone')
    flags.push('assignmentDone')
    if (hasQuiz) flags.push('practiced')
    return flags
}

export const getTutorialXp = (rewards: XpRewards, available: XpFlag[], earned: XpFlags, serverXp: number): TutorialXp => {
    const coreEarned = available.reduce((sum, flag) => sum + (earned[flag] ? rewards[flag] : 0), 0)
    return {
        earned: coreEarned,
        total: available.reduce((sum, flag) => sum + rewards[flag], 0),
        forumBonus: Math.max(0, serverXp - coreEarned),
        available,
    }
}

export const getOverviewTutorialXp = (
    courseId: string | null | undefined,
    tutorial: LearnerPackOverviewTutorial,
    rewards: XpRewards,
): TutorialXp => {
    const progress = tutorial.userProgress
    return getTutorialXp(
        rewards,
        getTutorialXpFlags(courseId, !isSetupTutorial(courseId, tutorial.number)),
        {
            watched: progress.watched,
            activityDone: Boolean(progress.activityDone),
            assignmentDone: Boolean(progress.assignmentDone),
            practiced: Boolean(progress.practiced),
        },
        progress.xpEarned,
    )
}

export const getStepXp = (
    stepIds: TutorialStepId[],
    available: XpFlag[],
    earned: XpFlags,
    rewards: XpRewards,
): Partial<Record<TutorialStepId, number>> => {
    const result: Partial<Record<TutorialStepId, number>> = {}
    const claimed = new Set<XpFlag>()
    for (const stepId of stepIds) {
        for (const flag of STEP_XP_FLAGS[stepId]) {
            if (!available.includes(flag) || earned[flag] || claimed.has(flag)) continue
            claimed.add(flag)
            result[stepId] = (result[stepId] ?? 0) + rewards[flag]
        }
    }
    return result
}

export const withXp = (label: string, xp: number): string => (xp > 0 ? `${label} (+${xp} XP)` : label)

export interface NextStepInfo {
    stepLabel: string
    step: TutorialStepId
    isStarted: boolean
}

export const getNextStep = (courseId: string | null | undefined, tutorial: LearnerPackOverviewTutorial): NextStepInfo => {
    const progress = tutorial.userProgress
    if (isTutorialCompleted(courseId, tutorial)) {
        return { stepLabel: 'Review', step: 'video', isStarted: true }
    }
    if (!progress.watched) {
        return { stepLabel: 'Watch video', step: 'video', isStarted: false }
    }
    if (!progress.reflectionSubmitted) {
        return { stepLabel: getActivityLabel(courseId, tutorial.number), step: 'activity', isStarted: true }
    }
    if (tutorial.hasAssignment && !progress.assignmentDone) {
        return { stepLabel: 'Assignment', step: 'assignment', isStarted: true }
    }
    return { stepLabel: 'Quiz', step: 'quiz', isStarted: true }
}

const optionText = (value: unknown): string => {
    if (typeof value === 'string') return value
    if (value && typeof value === 'object' && 'text' in value && typeof value.text === 'string') return value.text
    return ''
}

export const normalizeQuizOptions = (raw: unknown): QuizOption[] => {
    if (Array.isArray(raw)) {
        return raw.map((option: unknown) => {
            if (typeof option === 'string') return { id: option, text: option }
            const id = option && typeof option === 'object' && 'id' in option && typeof option.id === 'string' ? option.id : ''
            return { id, text: optionText(option) }
        })
    }
    if (raw && typeof raw === 'object') {
        return Object.entries(raw)
            .map(([id, value]) => ({ id, text: optionText(value) }))
            .sort((a, b) => a.id.localeCompare(b.id))
    }
    return []
}

export const fileNameFromUrl = (url: string): string => url.split('/').pop()?.split('?')[0] || url

export interface TryItInstructions {
    intro: string
    steps: string[]
}

export const parseTryItInstructions = (raw: string): TryItInstructions => {
    const parts = raw.split(/(?:\*\*Step\s+\d+:\*\*|\b\d+\.\s+)/).map(part => part.trim()).filter(Boolean)
    if (parts.length > 1) return { intro: parts[0], steps: parts.slice(1) }
    return { intro: '', steps: raw ? [raw] : [] }
}

export interface CourseMaterial {
    key: 'code' | 'instruction' | 'installation'
    title: string
    format: 'ZIP' | 'PDF'
    description: string
    url: string
    isDownload: boolean
    icon: LucideIcon
}

export const buildMaterials = (urls?: CourseMaterialUrls | null): CourseMaterial[] => {
    if (!urls) return []
    const materials: CourseMaterial[] = []
    if (urls.codeFilesUrl) {
        const isTutorialSpecific = urls.codeFilesUrl.includes('tutorial-')
        materials.push({
            key: 'code',
            format: 'ZIP',
            title: isTutorialSpecific ? 'Lab practice files' : 'Course files',
            description: isTutorialSpecific ? 'Practice datasets for this tutorial (.zip)' : 'Practice files used in the labs (.zip)',
            url: urls.codeFilesUrl,
            isDownload: true,
            icon: FolderArchive,
        })
    }
    if (urls.instructionSheetUrl) {
        materials.push({
            key: 'instruction',
            format: 'PDF',
            title: 'Instruction sheet',
            description: 'Command reference and lab guidelines (PDF)',
            url: urls.instructionSheetUrl,
            isDownload: false,
            icon: FileText,
        })
    }
    if (urls.installationSheetUrl) {
        materials.push({
            key: 'installation',
            format: 'PDF',
            title: 'Installation sheet',
            description: 'Step-by-step setup instructions (PDF)',
            url: urls.installationSheetUrl,
            isDownload: false,
            icon: Wrench,
        })
    }
    return materials
}

export interface LabTaskItem {
    text: string
    commands: string[]
}

export interface LabTask {
    intro: string
    items: LabTaskItem[]
    submit: string
}

const TASK_PREAMBLE = /^This is the practice task for Tutorial \d+\.\s*/i
const SUBMIT_PREFIX = /^Submit:\s*/i
const COMMAND_LINE = /^(?:\$ |\.\/|[a-z]).{0,160}$/

const isCommandLine = (line: string): boolean => COMMAND_LINE.test(line) && !/[.:?!]$/.test(line)

export const parseLabTask = (raw: string): LabTask => {
    const task: LabTask = { intro: '', items: [], submit: '' }
    const paragraphs = raw.replace(/\r\n?/g, '\n').split(/\n\s*\n/).map(part => part.trim()).filter(Boolean)
    paragraphs.forEach((paragraph, index) => {
        if (SUBMIT_PREFIX.test(paragraph)) {
            task.submit = paragraph.replace(SUBMIT_PREFIX, '')
            return
        }
        const text = index === 0 ? paragraph.replace(TASK_PREAMBLE, '') : paragraph
        if (!text) return
        const lines = text.split('\n').map(line => line.trim()).filter(Boolean)
        if (lines.every(isCommandLine)) {
            const commands = lines.map(line => line.replace(/^\$ /, ''))
            const lastItem = task.items[task.items.length - 1]
            if (lastItem) lastItem.commands.push(...commands)
            else task.items.push({ text: task.intro, commands })
            if (!lastItem) task.intro = ''
            return
        }
        if (index === 0 && text !== paragraph) task.intro = text
        else task.items.push({ text, commands: [] })
    })
    return task
}
