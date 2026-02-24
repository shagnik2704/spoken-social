import {
    Heart, MessageCircle, Share2, MoreHorizontal, Send,
    Trophy, HelpCircle, BookOpen, Flame, Image, Smile,
    TrendingUp, Users, Bookmark, ChevronRight,
    Code, Terminal, GraduationCap, Star,
    Sparkles
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'

// 🧠 ZUSTAND: Import the stores
import { useUserStore } from '@/store/userStore'
import { useFeedStore, type FeedFilter } from '@/store/feedStore'
import { MOCK_TRENDING, MOCK_SUGGESTED_USERS } from '@/data/mockData'
import type { Post, PostType } from '@/types'
import { useState, useMemo } from 'react'

// ===== HELPER FUNCTIONS =====

function getPostTypeConfig(type: PostType) {
    switch (type) {
        case 'achievement':
            return {
                icon: Trophy,
                label: 'Achievement',
                gradient: 'from-xp-gold/10 to-warning/5',
                borderColor: 'border-xp-gold/20',
                iconColor: 'text-xp-gold',
                badgeBg: 'bg-xp-gold/10 text-xp-gold',
            }
        case 'question':
            return {
                icon: HelpCircle,
                label: 'Question',
                gradient: 'from-primary/10 to-primary-light/5',
                borderColor: 'border-primary/20',
                iconColor: 'text-primary',
                badgeBg: 'bg-primary/10 text-primary',
            }
        case 'discussion':
            return {
                icon: BookOpen,
                label: 'Discussion',
                gradient: 'from-secondary/10 to-secondary/5',
                borderColor: 'border-secondary/20',
                iconColor: 'text-secondary',
                badgeBg: 'bg-secondary/10 text-secondary',
            }
        case 'milestone':
            return {
                icon: Flame,
                label: 'Milestone',
                gradient: 'from-danger/10 to-warning/5',
                borderColor: 'border-danger/20',
                iconColor: 'text-danger',
                badgeBg: 'bg-danger/10 text-danger',
            }
    }
}

function getCourseIcon(courseName?: string) {
    switch (courseName) {
        case 'Python': return <Code className="h-3.5 w-3.5" />
        case 'Linux': return <Terminal className="h-3.5 w-3.5" />
        case 'C/C++': return <Code className="h-3.5 w-3.5" />
        case 'Scilab': return <GraduationCap className="h-3.5 w-3.5" />
        default: return null
    }
}

// ===== COMPONENTS =====

/** Post Composer — now reads user from store */
function PostComposer() {
    const [postText, setPostText] = useState('')

    // 🧠 ZUSTAND: Reading user data from the store
    const user = useUserStore(state => state.user)

    // 🧠 ZUSTAND: Getting the addPost action from feed store
    const addPost = useFeedStore(state => state.addPost)

    const handlePost = () => {
        if (!postText.trim() || !user) return

        addPost({
            content: postText,
            type: 'discussion',
            authorId: user.id,
            authorName: user.name,
            authorInitials: user.initials,
            authorLevel: user.level,
            authorTitle: user.levelTitle,
        })

        setPostText('')
    }

    return (
        <Card className="border-border/50">
            <CardContent className="p-4 sm:p-5">
                <div className="flex gap-3">
                    <Avatar className="h-10 w-10 shrink-0">
                        <AvatarFallback className="bg-primary/10 text-primary text-sm font-semibold">
                            {user?.initials || '??'}
                        </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                        <textarea
                            value={postText}
                            onChange={(e) => setPostText(e.target.value)}
                            placeholder="Share something with the community..."
                            className="w-full bg-muted/30 border border-border/50 rounded-xl px-4 py-3 text-sm 
                                       placeholder:text-muted-foreground/60 resize-none focus:outline-none 
                                       focus:ring-2 focus:ring-primary/30 focus:border-primary/50
                                       transition-all duration-200 min-h-[80px]"
                            rows={3}
                        />
                        <div className="flex items-center justify-between mt-3">
                            <div className="flex items-center gap-1">
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                                    <Image className="h-4 w-4" />
                                </Button>
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                                    <Code className="h-4 w-4" />
                                </Button>
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                                    <HelpCircle className="h-4 w-4" />
                                </Button>
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-warning">
                                    <Smile className="h-4 w-4" />
                                </Button>
                            </div>
                            <Button
                                size="sm"
                                disabled={!postText.trim()}
                                onClick={handlePost}
                                className="rounded-full px-5 gap-1.5 bg-primary hover:bg-primary-hover text-white"
                            >
                                <Send className="h-3.5 w-3.5" />
                                Post
                            </Button>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

/** Individual Feed Post — now uses store for likes/bookmarks */
function FeedPost({ post }: { post: Post }) {
    // 🧠 ZUSTAND: Actions from the store
    // We DON'T use local useState for liked/bookmarked anymore.
    // The store is the source of truth, and the component just reads it.
    const toggleLike = useFeedStore(state => state.toggleLike)
    const toggleBookmark = useFeedStore(state => state.toggleBookmark)

    const config = getPostTypeConfig(post.type)
    const TypeIcon = config.icon

    return (
        <Card className={`border-border/40 hover:border-border/70 transition-all duration-300 hover:shadow-md`}>
            <CardContent className="p-4 sm:p-5">
                {/* Post Header */}
                <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-start gap-3 min-w-0">
                        <Avatar className="h-10 w-10 shrink-0 ring-2 ring-background">
                            <AvatarFallback className="bg-muted text-foreground text-xs font-semibold">
                                {post.author.initials}
                            </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-semibold text-sm">{post.author.name}</span>
                                <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4 font-normal">
                                    Lv.{post.author.level}
                                </Badge>
                            </div>
                            <div className="flex items-center gap-2 mt-0.5">
                                <span className="text-xs text-muted-foreground">{post.author.title}</span>
                                <span className="text-muted-foreground/40">•</span>
                                <span className="text-xs text-muted-foreground">{post.timestamp}</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                        <Badge className={`${config.badgeBg} border-0 text-[10px] px-2 py-0.5 gap-1 font-medium`}>
                            <TypeIcon className="h-3 w-3" />
                            {config.label}
                        </Badge>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground">
                            <MoreHorizontal className="h-4 w-4" />
                        </Button>
                    </div>
                </div>

                {/* Post Content */}
                <div className="mb-3">
                    <p className="text-sm leading-relaxed whitespace-pre-line">{post.content}</p>
                    {post.details && (
                        <div className={`mt-3 p-3 rounded-lg bg-gradient-to-r ${config.gradient} border ${config.borderColor}`}>
                            <p className="text-xs font-medium flex items-center gap-2">
                                {post.courseName && getCourseIcon(post.courseName)}
                                {post.details}
                            </p>
                        </div>
                    )}
                </div>

                {/* Tags */}
                {post.tags && post.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-3">
                        {post.tags.map(tag => (
                            <span
                                key={tag}
                                className="text-[11px] text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-full
                                           hover:bg-muted hover:text-foreground cursor-pointer transition-colors"
                            >
                                #{tag}
                            </span>
                        ))}
                    </div>
                )}

                {/* Interaction Bar — now wired to the store */}
                <div className="flex items-center justify-between pt-2 border-t border-border/30">
                    <div className="flex items-center gap-1">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleLike(post.id)}
                            className={`h-8 gap-1.5 px-3 rounded-full text-xs transition-all duration-200
                                        ${post.isLiked ? 'text-danger hover:text-danger/80' : 'text-muted-foreground hover:text-danger'}`}
                        >
                            <Heart className={`h-4 w-4 ${post.isLiked ? 'fill-danger' : ''}`} />
                            {post.likes > 0 && post.likes}
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 gap-1.5 px-3 rounded-full text-xs text-muted-foreground hover:text-primary"
                        >
                            <MessageCircle className="h-4 w-4" />
                            {post.comments > 0 && post.comments}
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 gap-1.5 px-3 rounded-full text-xs text-muted-foreground hover:text-success"
                        >
                            <Share2 className="h-4 w-4" />
                            {post.shares > 0 && post.shares}
                        </Button>
                    </div>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => toggleBookmark(post.id)}
                        className={`h-8 w-8 transition-all duration-200
                                    ${post.isBookmarked ? 'text-primary' : 'text-muted-foreground hover:text-primary'}`}
                    >
                        <Bookmark className={`h-4 w-4 ${post.isBookmarked ? 'fill-primary' : ''}`} />
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}

/** Feed Filter Tabs — now actually filter posts! */
function FeedFilters() {
    // 🧠 ZUSTAND: Reading & setting the active filter
    const activeFilter = useFeedStore(state => state.activeFilter)
    const setFilter = useFeedStore(state => state.setFilter)

    const filters: { id: FeedFilter; label: string; icon: React.ElementType }[] = [
        { id: 'all', label: 'All Posts', icon: Sparkles },
        { id: 'following', label: 'Following', icon: Users },
        { id: 'achievements', label: 'Achievements', icon: Trophy },
        { id: 'questions', label: 'Questions', icon: HelpCircle },
        { id: 'trending', label: 'Trending', icon: TrendingUp },
    ]

    return (
        <div className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-hide">
            {filters.map(filter => {
                const Icon = filter.icon
                const isActive = activeFilter === filter.id
                return (
                    <button
                        key={filter.id}
                        onClick={() => setFilter(filter.id)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
                                    whitespace-nowrap transition-all duration-200 shrink-0
                                    ${isActive
                                ? 'bg-primary text-white shadow-sm'
                                : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground'
                            }`}
                    >
                        <Icon className="h-3.5 w-3.5" />
                        {filter.label}
                    </button>
                )
            })}
        </div>
    )
}

/** Trending Topics Sidebar Widget */
function TrendingTopics() {
    return (
        <Card className="border-border/40">
            <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-3">
                    <TrendingUp className="h-4 w-4 text-primary" />
                    <h3 className="font-semibold text-sm">Trending Topics</h3>
                </div>
                <div className="space-y-2.5">
                    {MOCK_TRENDING.map((topic, index) => (
                        <button
                            key={topic.tag}
                            className="flex items-center justify-between w-full p-2 rounded-lg
                                       hover:bg-muted/50 transition-colors group text-left"
                        >
                            <div className="flex items-center gap-2.5">
                                <span className="text-xs font-mono text-muted-foreground/60 w-4">
                                    {index + 1}
                                </span>
                                <div>
                                    <p className="text-sm font-medium group-hover:text-primary transition-colors">
                                        #{topic.tag}
                                    </p>
                                    <p className="text-[11px] text-muted-foreground">
                                        {topic.posts} posts
                                    </p>
                                </div>
                            </div>
                            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/40 group-hover:text-primary transition-colors" />
                        </button>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}

/** Suggested Users Sidebar Widget */
function SuggestedPeople() {
    return (
        <Card className="border-border/40">
            <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <Star className="h-4 w-4 text-xp-gold" />
                        <h3 className="font-semibold text-sm">People to Follow</h3>
                    </div>
                    <Button variant="ghost" size="sm" className="text-xs text-muted-foreground h-6 px-2">
                        See All
                    </Button>
                </div>
                <div className="space-y-3">
                    {MOCK_SUGGESTED_USERS.map(user => (
                        <div key={user.name} className="flex items-center justify-between">
                            <div className="flex items-center gap-2.5 min-w-0">
                                <Avatar className="h-8 w-8 shrink-0">
                                    <AvatarFallback className="bg-muted text-foreground text-[10px] font-semibold">
                                        {user.initials}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="min-w-0">
                                    <p className="text-xs font-medium truncate">{user.name}</p>
                                    <p className="text-[10px] text-muted-foreground truncate">{user.title}</p>
                                </div>
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                className="h-7 px-3 text-[11px] rounded-full shrink-0"
                            >
                                Follow
                            </Button>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}

// ===== MAIN FEED PAGE =====

export function Feed() {
    // 🧠 ZUSTAND LESSON: Why we DON'T use a selector here
    //
    // Selectors that create new arrays (via .filter()/.sort()) return a
    // new reference every time. Zustand compares with Object.is(), sees
    // the new reference ≠ old reference, and triggers a re-render.
    // That re-render calls the selector again → new array → re-render → 💥 infinite loop.
    //
    // FIX: Read raw state from the store, then derive with useMemo.
    // useMemo caches the result and only recomputes when deps change.
    const posts = useFeedStore(state => state.posts)
    const activeFilter = useFeedStore(state => state.activeFilter)

    const filteredPosts = useMemo(() => {
        switch (activeFilter) {
            case 'achievements':
                return posts.filter(p => p.type === 'achievement' || p.type === 'milestone')
            case 'questions':
                return posts.filter(p => p.type === 'question')
            case 'trending':
                return [...posts].sort((a, b) =>
                    (b.likes + b.comments + b.shares) - (a.likes + a.comments + a.shares)
                )
            case 'following':
                // TODO: filter by followed users when backend is ready
                return posts
            case 'all':
            default:
                return posts
        }
    }, [posts, activeFilter])

    return (
        <div className="max-w-5xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6">
                {/* Main Feed Column */}
                <div className="space-y-4">
                    {/* Composer */}
                    <PostComposer />

                    {/* Filters */}
                    <FeedFilters />

                    {/* Posts — now filtered! */}
                    <div className="space-y-4">
                        {filteredPosts.length > 0 ? (
                            filteredPosts.map(post => (
                                <FeedPost key={post.id} post={post} />
                            ))
                        ) : (
                            <Card className="border-border/40">
                                <CardContent className="p-8 text-center">
                                    <p className="text-muted-foreground text-sm">
                                        No posts match this filter yet.
                                    </p>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </div>

                {/* Right Sidebar — hidden on mobile */}
                <aside className="hidden lg:block space-y-4">
                    <TrendingTopics />
                    <SuggestedPeople />
                </aside>
            </div>
        </div>
    )
}
