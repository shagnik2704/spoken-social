import { useUserStore } from '@/store/userStore'
import { BookOpen } from 'lucide-react'

export function CourseBatchSelector() {
    const user = useUserStore(state => state.user)
    const activeCourseId = useUserStore(state => state.activeCourseId)
    const setActiveCourse = useUserStore(state => state.setActiveCourse)
    const courses = useUserStore(state => state.courses)

// Only show for authenticated users with enrolled courses
    if (!user || courses.length === 0) {
        return null
    }

    // Don't show selector if only one course enrolled
    if (courses.length === 1) {
        const c = courses[0]
        return (
            <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 h-8 bg-primary/10 border border-primary/20 rounded-md px-2.5">
                    <BookOpen className="h-3.5 w-3.5 text-primary" />
                    <span className="text-xs font-semibold text-primary">{c.title}</span>
                    {c.batchName && (
                        <span className="text-[10px] text-muted-foreground ml-1">
                            — {c.batchName}
                        </span>
                    )}
                </div>
            </div>
        )
    }


    
    return (
        <div className="flex items-center gap-2">
            <BookOpen className="h-3.5 w-3.5 text-primary shrink-0" />
            <select 
                value={activeCourseId} 
                onChange={(e) => setActiveCourse(e.target.value)}
                className="h-8 bg-muted border border-input rounded-md px-2 pr-7 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-ring appearance-none cursor-pointer"
                style={{
                    backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                    backgroundPosition: 'right 0.25rem center',
                    backgroundRepeat: 'no-repeat',
                    backgroundSize: '1.25em 1.25em',
                }}
            >
                {courses.map(c => (
                    <option key={c.id} value={c.id}>
                        {c.title}{c.batchName ? ` — ${c.batchName}` : ''}
                    </option>
                ))}
            </select>
        </div>
    )
}
