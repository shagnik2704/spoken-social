import { useState } from 'react'
import {
    X, Send, Image, Code, HelpCircle, Trophy, MessageSquare,
    Hash, Terminal, BarChart3, FileText,
    GraduationCap, Smile, AtSign
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { useComposeModal } from '@/hooks/useComposeModal'
import { useUserStore } from '@/store/userStore'
import { useFeedStore } from '@/store/feedStore'
import type { PostType } from '@/types'



interface PostTypeOption {
    id: PostType
    label: string
    description: string
    icon: React.ElementType
    color: string
    bgColor: string
}

const postTypes: PostTypeOption[] = [
    {
        id: 'discussion',
        label: 'Discussion',
        description: 'Share a tip, thought, or resource',
        icon: MessageSquare,
        color: 'text-teal-700 dark:text-teal-300',
        bgColor: 'bg-teal-100 dark:bg-teal-900/40',
    },
    {
        id: 'question',
        label: 'Question',
        description: 'Ask the community for help',
        icon: HelpCircle,
        color: 'text-primary',
        bgColor: 'bg-primary/15',
    },
    {
        id: 'achievement',
        label: 'Achievement',
        description: 'Celebrate a milestone',
        icon: Trophy,
        color: 'text-amber-700 dark:text-amber-300',
        bgColor: 'bg-amber-100 dark:bg-amber-900/40',
    },
]

const courseOptions = [
    { id: 'python', name: 'Python', icon: Code },
    { id: 'linux', name: 'Linux', icon: Terminal },
    { id: 'scilab', name: 'Scilab', icon: BarChart3 },
    { id: 'cpp', name: 'C/C++', icon: GraduationCap },
    { id: 'libreoffice', name: 'LibreOffice', icon: FileText },
]

// ===== COMPONENT =====

export function ComposeModal() {
    const { isOpen, close } = useComposeModal()
    const [postType, setPostType] = useState<PostType>('discussion')
    const [content, setContent] = useState('')
    const [selectedCourses, setSelectedCourses] = useState<string[]>([])
    const [showCourseSelector, setShowCourseSelector] = useState(false)

    // 🧠 ZUSTAND: Read user from store, get addPost action from feed store
    const user = useUserStore(state => state.user)
    const addPost = useFeedStore(state => state.addPost)

    if (!isOpen) return null

    const activePostType = postTypes.find(t => t.id === postType)!
    const ActiveIcon = activePostType.icon

    const toggleCourse = (courseId: string) => {
        setSelectedCourses(prev =>
            prev.includes(courseId) ? prev.filter(c => c !== courseId) : [...prev, courseId]
        )
    }

    const handleSubmit = () => {
        if (!content.trim() || !user) return

        // 🧠 ZUSTAND: Dispatch the addPost action
        addPost({
            content,
            type: postType,
            tags: selectedCourses.map(id => {
                const course = courseOptions.find(c => c.id === id)
                return course?.name || id
            }),
            courseName: selectedCourses.length === 1
                ? courseOptions.find(c => c.id === selectedCourses[0])?.name
                : undefined,
            authorId: user.id,
            authorName: user.name,
            authorInitials: user.initials,
            authorLevel: user.level,
            authorTitle: user.levelTitle,
        })

        setContent('')
        setSelectedCourses([])
        setPostType('discussion')
        close()
    }

    const getPlaceholder = () => {
        switch (postType) {
            case 'question': return 'What do you need help with? Be specific so others can assist you...'
            case 'achievement': return 'What did you accomplish? Share your achievement with the community!'
            default: return 'Share a thought, tip, or resource with the community...'
        }
    }

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-in fade-in duration-200"
                onClick={close}
            />

            {/* Modal */}
            <div className="fixed inset-x-4 top-[10vh] sm:inset-x-auto sm:left-1/2 sm:-translate-x-1/2 
                            sm:w-full sm:max-w-xl z-50 animate-in fade-in slide-in-from-bottom-4 duration-300">
                <div className="bg-card border border-border rounded-2xl shadow-2xl overflow-hidden">
                    {/* Header */}
                    <div className="flex items-center justify-between p-4 border-b border-border/50">
                        <div className="flex items-center gap-2">
                            <div className={`h-8 w-8 rounded-lg ${activePostType.bgColor} flex items-center justify-center`}>
                                <ActiveIcon className={`h-4 w-4 ${activePostType.color}`} />
                            </div>
                            <div>
                                <h2 className="font-semibold text-sm">Create {activePostType.label}</h2>
                                <p className="text-[10px] text-muted-foreground">{activePostType.description}</p>
                            </div>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 rounded-full"
                            onClick={close}
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </div>

                    {/* Post Type Selector */}
                    <div className="flex gap-1 p-3 border-b border-border/30">
                        {postTypes.map(type => {
                            const Icon = type.icon
                            const isActive = postType === type.id
                            return (
                                <button
                                    key={type.id}
                                    onClick={() => setPostType(type.id)}
                                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
                                                transition-all duration-200 flex-1 justify-center
                                                ${isActive
                                            ? `${type.bgColor} ${type.color} font-semibold`
                                            : 'text-muted-foreground hover:bg-muted/50'
                                        }`}
                                >
                                    <Icon className="h-3.5 w-3.5" />
                                    {type.label}
                                </button>
                            )
                        })}
                    </div>

                    {/* Compose Area */}
                    <div className="p-4">
                        <div className="flex gap-3">
                            <Avatar className="h-9 w-9 shrink-0">
                                <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
                                    {user?.initials || '??'}
                                </AvatarFallback>
                            </Avatar>

                            <div className="flex-1 min-w-0">
                                <textarea
                                    value={content}
                                    onChange={(e) => setContent(e.target.value)}
                                    placeholder={getPlaceholder()}
                                    className="w-full bg-transparent text-sm placeholder:text-muted-foreground/50
                                               resize-none focus:outline-none min-h-[120px] leading-relaxed"
                                    autoFocus
                                />
                            </div>
                        </div>

                        {/* Tagged Courses */}
                        {selectedCourses.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-3 ml-12">
                                {selectedCourses.map(courseId => {
                                    const course = courseOptions.find(c => c.id === courseId)
                                    if (!course) return null
                                    const Icon = course.icon
                                    return (
                                        <Badge
                                            key={courseId}
                                            variant="secondary"
                                            className="text-[11px] gap-1 pr-1 cursor-pointer hover:bg-destructive/10 
                                                       hover:text-destructive transition-colors"
                                            onClick={() => toggleCourse(courseId)}
                                        >
                                            <Icon className="h-3 w-3" />
                                            {course.name}
                                            <X className="h-3 w-3 ml-0.5" />
                                        </Badge>
                                    )
                                })}
                            </div>
                        )}
                    </div>

                    {/* Course Selector Dropdown */}
                    {showCourseSelector && (
                        <div className="px-4 pb-3">
                            <div className="bg-muted/30 rounded-lg border border-border/50 p-2">
                                <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold mb-2 px-1">
                                    Tag a course
                                </p>
                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-1">
                                    {courseOptions.map(course => {
                                        const Icon = course.icon
                                        const isSelected = selectedCourses.includes(course.id)
                                        return (
                                            <button
                                                key={course.id}
                                                onClick={() => toggleCourse(course.id)}
                                                className={`flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs
                                                            transition-all duration-150
                                                            ${isSelected
                                                        ? 'bg-primary/10 text-primary border border-primary/20'
                                                        : 'hover:bg-muted/50 text-foreground'
                                                    }`}
                                            >
                                                <Icon className="h-3.5 w-3.5" />
                                                {course.name}
                                            </button>
                                        )
                                    })}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Footer - Actions + Submit */}
                    <div className="flex items-center justify-between p-3 border-t border-border/50">
                        <div className="flex items-center gap-0.5">
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                                <Image className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                                <Code className="h-4 w-4" />
                            </Button>
                            <Button
                                variant="ghost"
                                size="icon"
                                className={`h-8 w-8 ${showCourseSelector ? 'text-primary bg-primary/10' : 'text-muted-foreground hover:text-primary'}`}
                                onClick={() => setShowCourseSelector(!showCourseSelector)}
                            >
                                <Hash className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                                <AtSign className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-warning">
                                <Smile className="h-4 w-4" />
                            </Button>
                        </div>

                        <div className="flex items-center gap-2">
                            <span className={`text-[11px] font-mono ${content.length > 500 ? 'text-danger' : 'text-muted-foreground'}`}>
                                {content.length}/500
                            </span>
                            <Button
                                size="sm"
                                disabled={!content.trim() || content.length > 500}
                                onClick={handleSubmit}
                                className="rounded-full px-5 gap-1.5 bg-primary hover:bg-primary-hover text-white"
                            >
                                <Send className="h-3.5 w-3.5" />
                                Post
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}
