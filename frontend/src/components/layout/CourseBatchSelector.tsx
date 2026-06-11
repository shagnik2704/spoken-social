import { useUserStore } from '@/store/userStore'
import { Layers, BookOpen } from 'lucide-react'

export function CourseBatchSelector() {
    const user = useUserStore(state => state.user)
    const activeProgrammeId = useUserStore(state => state.activeProgrammeId)
    const switchProgramme = useUserStore(state => state.switchProgramme)
    const programmes = useUserStore(state => state.programmes)

    const activeCourseId = useUserStore(state => state.activeCourseId)
    const setActiveCourse = useUserStore(state => state.setActiveCourse)
    const courses = useUserStore(state => state.courses)

    if (!user) {
        return null
    }

    const handleProgrammeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const id = e.target.value
        const selected = programmes.find(p => p.id === id)
        if (selected) {
            switchProgramme(id, selected.name)
        }
    }

    return (
        <div className="flex items-center gap-3">
            {/* Programme Dropdown */}
            {programmes.length > 0 && (
                <div className="flex items-center gap-2">
                    <Layers className="h-3.5 w-3.5 text-primary shrink-0" />
                    <select 
                        value={activeProgrammeId} 
                        onChange={handleProgrammeChange}
                        className="h-8 bg-muted border border-input rounded-md px-2 pr-7 text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-ring appearance-none cursor-pointer text-foreground"
                        style={{
                            backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                            backgroundPosition: 'right 0.25rem center',
                            backgroundRepeat: 'no-repeat',
                            backgroundSize: '1.25em 1.25em',
                        }}
                    >
                        {programmes.map(p => (
                            <option key={p.id} value={p.id}>
                                {p.name}
                            </option>
                        ))}
                    </select>
                </div>
            )}

            {/* Course Dropdown */}
            <div className="flex items-center gap-2">
                <BookOpen className="h-3.5 w-3.5 text-primary shrink-0" />
                <select 
                    value={activeCourseId} 
                    onChange={(e) => setActiveCourse(e.target.value)}
                    disabled={courses.length === 0}
                    className="h-8 bg-muted border border-input rounded-md px-2 pr-7 text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-ring appearance-none cursor-pointer disabled:opacity-50 text-foreground"
                    style={{
                        backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                        backgroundPosition: 'right 0.25rem center',
                        backgroundRepeat: 'no-repeat',
                        backgroundSize: '1.25em 1.25em',
                    }}
                >
                    {courses.length > 0 ? (
                        courses.map(c => (
                            <option key={c.id} value={c.id}>
                                {c.title}{c.batchName ? ` — ${c.batchName}` : ''}
                            </option>
                        ))
                    ) : (
                        <option value="">No courses available</option>
                    )}
                </select>
            </div>
        </div>
    )
}
