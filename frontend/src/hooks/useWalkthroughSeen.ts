import { useCallback, useState } from 'react'

const STORAGE_PREFIX = 'spoken-social-walkthrough-seen'

const readFlag = (key: string): boolean => {
    try {
        return localStorage.getItem(key) === '1'
    } catch {
        return false
    }
}

const writeFlag = (key: string): void => {
    try {
        localStorage.setItem(key, '1')
    } catch {
        return
    }
}

export const useWalkthroughSeen = (userId?: string | null, courseId?: string | null): [boolean, () => void] => {
    const storageKey = userId && courseId ? `${STORAGE_PREFIX}:${userId}:${courseId}` : null
    const [markedKey, setMarkedKey] = useState<string | null>(null)
    const seen = storageKey !== null && (markedKey === storageKey || readFlag(storageKey))

    const markSeen = useCallback((): void => {
        if (!storageKey) return
        writeFlag(storageKey)
        setMarkedKey(storageKey)
    }, [storageKey])

    return [seen, markSeen]
}
