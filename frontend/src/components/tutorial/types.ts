import type { TutorialStepId } from '@/lib/learnerPack'
import type { LearnerPackOverviewTutorial, LearnerPackTutorialDetail } from '@/types'
import type { TutorialWorkspace } from './useTutorialWorkspace'

export interface TutorialNav {
    isLinux: boolean
    isSetup: boolean
    hasAssignment: boolean
    nextTutorial: LearnerPackOverviewTutorial | null
    totalTutorials: number
    goToStep: (step: TutorialStepId) => void
    goToTutorial: (tutorialNumber: number) => void
    backToCourse: () => void
}

export interface TutorialStepProps {
    detail: LearnerPackTutorialDetail
    workspace: TutorialWorkspace
    nav: TutorialNav
}
