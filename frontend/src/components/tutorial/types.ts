import type { TutorialStepId, TutorialXp, XpFlag } from '@/lib/learnerPack'
import type { LearnerPackOverviewTutorial, LearnerPackTutorialDetail } from '@/types'
import type { TutorialWorkspace } from './useTutorialWorkspace'

export interface TutorialNav {
    isLinux: boolean
    isCreativeAi: boolean
    isInteractiveAi: boolean
    isSetup: boolean
    hasAssignment: boolean
    nextTutorial: LearnerPackOverviewTutorial | null
    totalTutorials: number
    tutorialXp: TutorialXp | null
    xpFor: (flag: XpFlag) => number
    goToStep: (step: TutorialStepId) => void
    goToTutorial: (tutorialNumber: number) => void
    backToCourse: () => void
}

export interface TutorialStepProps {
    detail: LearnerPackTutorialDetail
    workspace: TutorialWorkspace
    nav: TutorialNav
}
