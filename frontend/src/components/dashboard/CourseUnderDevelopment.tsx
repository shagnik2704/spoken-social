import React from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowRight, ExternalLink } from 'lucide-react'

export interface CoursePreviewMeta {
    id: string
    title: string
    forumCategory?: string
}

export const KNOWN_SWAYAM_COURSES: Record<string, CoursePreviewMeta> = {
    'being-creative-with-ai': {
        id: 'being-creative-with-ai',
        title: 'Being Creative with AI',
        forumCategory: 'Being Creative with AI',
    },
    'deep-learning-frameworks': {
        id: 'deep-learning-frameworks',
        title: 'Introduction to Deep Learning Frameworks',
        forumCategory: 'Deep Learning',
    },
    'interactive-ai-tools': {
        id: 'interactive-ai-tools',
        title: 'Interactive AI Tools',
        forumCategory: 'Interactive AI Tools',
    },
}

interface CourseUnderDevelopmentProps {
    courseId?: string
    courseTitle?: string
}

export const CourseUnderDevelopment: React.FC<CourseUnderDevelopmentProps> = ({
    courseId = '',
    courseTitle,
}) => {
    const slug = courseId.toLowerCase().replace(/_/g, '-')
    const meta = KNOWN_SWAYAM_COURSES[slug]
    const title = courseTitle || meta?.title || 'Course'

    const forumUrl = meta?.forumCategory
        ? `https://spoken-tutorial.org/forum/categories/${encodeURIComponent(meta.forumCategory)}`
        : 'https://spoken-tutorial.org/forum/'

    return (
        <div className="max-w-3xl mx-auto space-y-4 pb-12 animate-in fade-in-50 duration-300">
            {/* Top Breadcrumb (pills removed) */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Link to="/landing" className="hover:text-primary transition-colors">
                    SWAYAM Plus
                </Link>
                <span>/</span>
                <span className="font-medium text-foreground">{title}</span>
            </div>

            {/* Main Card with Character */}
            <Card className="overflow-hidden border-border/80 bg-gradient-to-br from-card via-card to-primary/5 shadow-sm">
                <CardContent className="p-6 md:p-8">
                    <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
                        {/* Character Photo */}
                        <div className="shrink-0">
                            <div className="w-28 h-28 md:w-36 md:h-36 rounded-2xl overflow-hidden shadow-md border-2 border-primary/20 ring-4 ring-primary/10">
                                <img
                                    src="/priya-waving.jpg"
                                    alt="Course Mentor"
                                    className="w-full h-full object-cover object-top hover:scale-105 transition-transform duration-300"
                                    onError={(e) => {
                                        const target = e.currentTarget
                                        if (!target.src.endsWith('girl-studying-transparent.png')) {
                                            target.src = '/girl-studying-transparent.png'
                                        }
                                    }}
                                />
                            </div>
                        </div>

                        {/* Content */}
                        <div className="flex-1 text-center md:text-left space-y-3">
                            <div className="text-sm font-semibold text-primary flex items-center justify-center md:justify-start gap-1.5">
                                <span>👋 Namaste & Welcome!</span>
                            </div>

                            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
                                {title}
                            </h1>

                            <p className="text-sm md:text-base text-muted-foreground leading-relaxed">
                                Welcome to our platform! Our team at{' '}
                                <span className="font-bold">
                                    <span className="text-[#F26C25]">Edu</span>
                                    <span className="text-[#1A237E] dark:text-[#60a5fa]">Pyramids</span>
                                </span>{' '}
                                is currently putting the finishing touches on this course to get everything ready for you. Interactive screencasts, hands-on practice, and quizzes will be uploaded right here shortly. We are thrilled to have you here — stay tuned!
                            </p>

                            <div className="pt-2 flex flex-wrap items-center justify-center md:justify-start gap-3">
                                <Button asChild size="sm" className="font-semibold shadow-xs">
                                    <Link to="/courses/linux">
                                        Explore Active Course: Linux <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                                    </Link>
                                </Button>
                                <Button asChild variant="outline" size="sm" className="font-medium">
                                    <a href={forumUrl} target="_blank" rel="noopener noreferrer">
                                        Ask on Forum <ExternalLink className="w-3.5 h-3.5 ml-1.5" />
                                    </a>
                                </Button>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
