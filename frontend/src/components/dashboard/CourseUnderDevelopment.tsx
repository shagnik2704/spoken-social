import React from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
    Sparkles,
    Clock,
    BookOpen,
    Video,
    FileCode,
    HelpCircle,
    CheckCircle2,
    ArrowRight,
    GraduationCap,
    ExternalLink,
} from 'lucide-react'

export interface CoursePreviewMeta {
    id: string
    title: string
    credits: number
    description: string
    category: string
    topics: string[]
    forumCategory?: string
}

export const KNOWN_SWAYAM_COURSES: Record<string, CoursePreviewMeta> = {
    'empathy-growth-mindset': {
        id: 'empathy-growth-mindset',
        title: 'Developing Empathy and Growth Mindset',
        credits: 2,
        description:
            'A 2-credit life-skills course covering emotional intelligence, self-awareness, cognitive reframing, active empathy, and developing a growth mindset through scientific neuroplasticity principles.',
        category: 'Life Skills & Mindset',
        forumCategory: 'Developing Empathy and Growth Mindset',
        topics: [
            'Origin of Emotions & Navigating Fear and Anger',
            'Understanding Sadness, Guilt & Reframing Jealousy',
            'Reality vs. Interpretations & Changing Beliefs',
            'Judgment, Constructive Feedback & 7-Day Empathy Practice',
            'Brain Neuroplasticity, Magic of Failures & Growth Mindset Plan',
        ],
    },
    'being-creative-with-ai': {
        id: 'being-creative-with-ai',
        title: 'Being Creative with AI',
        credits: 2,
        description:
            'A 2-credit course exploring modern generative AI, prompt engineering, persona-based prompting, image synthesis, Python in Google Colab, and building Retrieval-Augmented Generation (RAG) systems.',
        category: 'Artificial Intelligence',
        forumCategory: 'Being Creative with AI',
        topics: [
            'Generative AI Fundamentals & Model Capabilities',
            'Prompt Engineering (3 Cs, Personas & Iterative Design)',
            'Prompting for Images & Multimodal Generation',
            'Python & Colab Workflows for AI Experiments',
            'Gemini API Keys, RAG Pipelines & Colab Implementations',
        ],
    },
    'deep-learning-frameworks': {
        id: 'deep-learning-frameworks',
        title: 'Introduction to Deep Learning Frameworks',
        credits: 3,
        description:
            'A 3-credit comprehensive course covering modern deep learning frameworks including PyTorch, TensorFlow, and essential Python machine learning libraries for building and evaluating neural networks.',
        category: 'Machine Learning & AI',
        forumCategory: 'Deep Learning',
        topics: [
            'PyTorch Tensors, Dimension Operations & Computations',
            'TensorFlow Model Architecture & Datasets',
            'Loss Functions, Optimizers & Building Training Loops',
            'Model Evaluation, Debugging & Performance Visualization',
            'GPU Acceleration, Image Basics & Saving/Loading Models',
        ],
    },
    'interactive-ai-tools': {
        id: 'interactive-ai-tools',
        title: 'Interactive AI Tools',
        credits: 2,
        description:
            'A 2-credit hands-on course covering interactive development environments, Jupyter Notebooks, and Visual Studio Code (VS Code) for agile data science and AI workflows.',
        category: 'Developer Tools & Environments',
        forumCategory: 'Interactive AI Tools',
        topics: [
            'Jupyter Notebook Installation, Architecture & Kernel Management',
            'Interactive Data Exploration & Inline Visualizations',
            'VS Code Setup for AI & Essential Extensions',
            'Virtual Environments, Package Management & Debugging',
            'Reproducible Research & Exporting Interactive Workflows',
        ],
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
    const credits = meta?.credits || 2
    const description =
        meta?.description ||
        'This course is part of the SWAYAM Plus initiative by Spoken Tutorial, IIT Bombay. Course curriculum, interactive screencasts, and assignments are being prepared.'
    const topics = meta?.topics || [
        'High-Definition Spoken Tutorial Screencasts',
        'Hands-on Practical Assignments & Lab Work',
        'Weekly Reflection Activities & Check-ins',
        'Self-Assessment Quizzes with Instant Scoring',
        'Academic Credits & Course Completion Certificate',
    ]

    const forumUrl = meta?.forumCategory
        ? `https://spoken-tutorial.org/forum/categories/${encodeURIComponent(meta.forumCategory)}`
        : 'https://spoken-tutorial.org/forum/'

    return (
        <div className="max-w-3xl mx-auto space-y-6 pb-12 animate-in fade-in-50 duration-300">
            {/* Top Breadcrumb & Status Badges */}
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Link to="/landing" className="hover:text-primary transition-colors">
                        SWAYAM Plus
                    </Link>
                    <span>/</span>
                    <span className="font-medium text-foreground">{title}</span>
                </div>
                <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs font-semibold px-2.5 py-0.5 border-primary/30 text-primary bg-primary/5">
                        <Sparkles className="w-3 h-3 mr-1 inline" /> {credits} Credits
                    </Badge>
                    <Badge variant="secondary" className="text-xs font-semibold px-2.5 py-0.5 bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                        <Clock className="w-3 h-3 mr-1 inline" /> Under Development
                    </Badge>
                </div>
            </div>

            {/* Main Hero Card with Priya */}
            <Card className="overflow-hidden border-border/80 bg-gradient-to-br from-card via-card to-primary/5 shadow-sm">
                <CardContent className="p-6 md:p-8">
                    <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
                        {/* Priya Mentor Photo */}
                        <div className="relative shrink-0">
                            <div className="w-28 h-28 md:w-36 md:h-36 rounded-2xl overflow-hidden shadow-md border-2 border-primary/20 ring-4 ring-primary/10">
                                <img
                                    src="/priya-waving.jpg"
                                    alt="Priya - Course Mentor"
                                    className="w-full h-full object-cover object-top hover:scale-105 transition-transform duration-300"
                                    onError={(e) => {
                                        // Fallback to transparent girl studying if jpg fails
                                        const target = e.currentTarget
                                        if (!target.src.endsWith('girl-studying-transparent.png')) {
                                            target.src = '/girl-studying-transparent.png'
                                        }
                                    }}
                                />
                            </div>
                            <div className="absolute -bottom-2 -right-2 bg-primary text-primary-foreground text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm flex items-center gap-1">
                                <GraduationCap className="w-3 h-3" /> Mentor
                            </div>
                        </div>

                        {/* Speech Bubble / Welcome Message */}
                        <div className="flex-1 text-center md:text-left space-y-3">
                            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                                <span>👋 Namaste! I&apos;m Priya, your mentor</span>
                            </div>

                            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
                                {title}
                            </h1>

                            <p className="text-sm md:text-base text-muted-foreground leading-relaxed">
                                Welcome! Our team at Spoken Tutorial, IIT Bombay is putting the finishing touches on this course for the upcoming SWAYAM Plus session. Interactive video screencasts, try-it activities, and quizzes will be launched shortly.
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

            {/* Course Overview & Preview */}
            <Card className="border-border/70 shadow-xs">
                <CardContent className="p-6 space-y-5">
                    <div>
                        <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                            <BookOpen className="w-4 h-4 text-primary" /> About This Course
                        </h2>
                        <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                            {description}
                        </p>
                    </div>

                    <div className="border-t border-border/60 pt-5">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">
                            What You Will Learn
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                            {topics.map((topic, i) => (
                                <div
                                    key={i}
                                    className="flex items-start gap-2.5 p-2.5 rounded-lg bg-muted/40 border border-border/50 text-xs font-medium text-foreground/90"
                                >
                                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                                    <span>{topic}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="border-t border-border/60 pt-5">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">
                            Course Features Included
                        </h3>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                            <div className="p-3 rounded-xl bg-card border border-border/60 shadow-2xs">
                                <Video className="w-5 h-5 mx-auto text-primary mb-1.5" />
                                <div className="text-xs font-bold text-foreground">Screencasts</div>
                                <div className="text-[10px] text-muted-foreground">English Audio & Subs</div>
                            </div>
                            <div className="p-3 rounded-xl bg-card border border-border/60 shadow-2xs">
                                <FileCode className="w-5 h-5 mx-auto text-primary mb-1.5" />
                                <div className="text-xs font-bold text-foreground">Assignments</div>
                                <div className="text-[10px] text-muted-foreground">Practical Hands-on</div>
                            </div>
                            <div className="p-3 rounded-xl bg-card border border-border/60 shadow-2xs">
                                <HelpCircle className="w-5 h-5 mx-auto text-primary mb-1.5" />
                                <div className="text-xs font-bold text-foreground">Weekly Quizzes</div>
                                <div className="text-[10px] text-muted-foreground">Instant XP & Scoring</div>
                            </div>
                            <div className="p-3 rounded-xl bg-card border border-border/60 shadow-2xs">
                                <GraduationCap className="w-5 h-5 mx-auto text-primary mb-1.5" />
                                <div className="text-xs font-bold text-foreground">{credits} Credits</div>
                                <div className="text-[10px] text-muted-foreground">SWAYAM Plus Certified</div>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
