import { useUserStore } from '@/store/userStore'
import { Badge } from '@/components/ui/badge'
import api from '@/lib/axios'
import { useEffect, useState } from 'react'

export function CourseBatchSelector() {
    const user = useUserStore(state => state.user)
    const activeCourseId = useUserStore(state => state.activeCourseId)
    const activeBatchId = useUserStore(state => state.activeBatchId)
    const setActiveCourse = useUserStore(state => state.setActiveCourse)
    const setActiveBatch = useUserStore(state => state.setActiveBatch)

    const [batches, setBatches] = useState<any[]>([])
    const courses = useUserStore(state => state.courses)

    // Show for all authenticated users
    if (!user) {
        return null
    }

    useEffect(() => {
        if (activeCourseId) {
            api.get(`/api/courses/${activeCourseId}/batches`).then(({ data }) => {
                setBatches(data)
                // If no active batch selected, default to the most recent active one
                if (!activeBatchId && data.length > 0) {
                    const active = data.find((b: any) => b.is_active) || data[0]
                    setActiveBatch(active.id, active.is_active)
                }
            })
        }
    }, [activeCourseId])

    const activeBatch = batches.find(b => b.id === activeBatchId)

    return (
        <div className="flex items-center gap-2">
            {/* Course Selector */}
            <select 
                value={activeCourseId} 
                onChange={(e) => setActiveCourse(e.target.value)}
                className="h-8 bg-muted border border-input rounded-md px-2 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-ring"
            >
                {courses.length > 0 ? (
                    courses.map(c => (
                        <option key={c.id} value={c.id}>{c.title}</option>
                    ))
                ) : (
                    <option value="linux">LINUX</option>
                )}
            </select>

            {/* Batch Selector */}
            <select 
                value={activeBatchId || ''} 
                onChange={(e) => {
                    const batchId = e.target.value
                    const batch = batches.find(b => b.id === batchId)
                    setActiveBatch(batchId, batch?.is_active)
                }}
                className="h-8 bg-muted border border-input rounded-md px-2 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-ring"
            >
                <option value="" disabled>Select Batch</option>
                {batches.map(b => (
                    <option key={b.id} value={b.id}>
                        Batch {b.batch_number} {!b.is_active ? '(Archived)' : ''}
                    </option>
                ))}
            </select>

            {activeBatch && !activeBatch.is_active && (
                <Badge variant="destructive" className="text-[10px] px-1.5 h-5 animate-pulse">
                    READ ONLY
                </Badge>
            )}
        </div>
    )
}
