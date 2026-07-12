import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useUserStore } from '@/store/userStore'
import api from '@/lib/axios'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Loader2, GraduationCap, BookOpen, Laptop, ArrowRight } from 'lucide-react'

interface Programme {
    id: string
    name: string
    description: string
    icon: string
    color: string
    isActive: boolean
    courseCount: number
}

const iconMap: Record<string, any> = {
    'graduation-cap': GraduationCap,
    'book-open': BookOpen,
    'laptop': Laptop,
}

export function ProgrammeSelector() {
    const user = useUserStore(state => state.user)
    const setActiveProgramme = useUserStore(state => state.setActiveProgramme)
    const logout = useUserStore(state => state.logout)
    const navigate = useNavigate()

    const { data: programmes = [], isLoading, isError } = useQuery<Programme[]>({
        queryKey: ['programmes', 'me'],
        queryFn: async () => (await api.get('/api/programmes/me')).data,
    })
    const error = isError ? 'Could not fetch accessible programmes. Please try again.' : null

    const handleSelect = (p: Programme) => {
        setActiveProgramme(p.id, p.name)
        // Reset course/batch selections to force landing page selection under the new programme
        useUserStore.setState({ activeCourseId: '', activeBatchId: null })
        navigate('/')
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/10 via-background to-background flex flex-col items-center justify-center p-4 lg:p-8">
            <div className="w-full max-w-4xl space-y-8 animate-in fade-in zoom-in duration-500">
                {/* Header */}
                <div className="text-center space-y-4">
                    <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20 px-3 py-1 text-xs font-semibold uppercase tracking-wider">
                        Welcome, {user?.displayName || 'Learner'}
                    </Badge>
                    <h1 className="text-4xl lg:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
                        Select a Programme
                    </h1>
                    <p className="text-muted-foreground max-w-md mx-auto text-sm sm:text-base">
                        Choose the learning track you wish to enter. Your dashboard and course selection will be scoped to this programme.
                    </p>
                </div>

                {error && (
                    <div className="bg-destructive/15 text-destructive border border-destructive/20 p-4 rounded-xl text-center text-sm font-medium">
                        {error}
                    </div>
                )}

                {/* Cards Grid */}
                <div className="grid md:grid-cols-3 gap-6">
                    {programmes.map((p) => {
                        const IconComponent = iconMap[p.icon] || GraduationCap
                        return (
                            <button
                                key={p.id}
                                onClick={() => handleSelect(p)}
                                className="w-full text-left group focus:outline-none"
                            >
                                <Card className="h-full border border-border bg-card/50 backdrop-blur-md hover:border-primary/50 hover:bg-card hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 overflow-hidden relative">
                                    {/* Top decorative gradient bar */}
                                    <div className={`h-1.5 w-full bg-gradient-to-r ${p.color}`} />
                                    
                                    <CardContent className="p-6 space-y-4 flex flex-col h-full justify-between">
                                        <div className="space-y-4">
                                            {/* Icon */}
                                            <div className={`inline-flex p-3 rounded-xl bg-gradient-to-r ${p.color} text-white shadow-lg shadow-primary/10`}>
                                                <IconComponent className="w-6 h-6" />
                                            </div>

                                            {/* Details */}
                                            <div className="space-y-2">
                                                <h3 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
                                                    {p.name}
                                                    <span className="text-xs text-muted-foreground font-normal">
                                                        ({p.courseCount} {p.courseCount === 1 ? 'course' : 'courses'})
                                                    </span>
                                                </h3>
                                                <p className="text-sm text-muted-foreground line-clamp-3 font-medium leading-relaxed">
                                                    {p.description}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="pt-4 flex items-center text-sm font-bold text-primary group-hover:translate-x-1 transition-transform">
                                            Select Programme
                                            <ArrowRight className="w-4 h-4 ml-1.5" />
                                        </div>
                                    </CardContent>
                                </Card>
                            </button>
                        )
                    })}
                </div>

                {/* Footer and Logout */}
                <div className="pt-6 text-center space-y-4">
                    <button
                        onClick={logout}
                        className="text-sm font-semibold text-muted-foreground hover:text-foreground underline underline-offset-4 decoration-border hover:decoration-foreground transition-all"
                    >
                        Sign out of account
                    </button>
                    <p className="text-xs text-muted-foreground font-medium uppercase tracking-[0.2em] pt-4">
                        Spoken Social • Empowering Open Source Education
                    </p>
                </div>
            </div>
        </div>
    )
}
