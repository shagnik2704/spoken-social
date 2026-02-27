import { create } from 'zustand'
import type { Post, PostType } from '@/types'
import api from '@/lib/axios'

export type FeedFilter = 'all' | 'following' | 'achievements' | 'questions' | 'trending'


interface FeedState {

    posts: Post[]
    activeFilter: FeedFilter
    isLoading: boolean

    fetchPosts: () => Promise<void>
    setFilter: (filter: FeedFilter) => void
    addPost: (post: { content: string; type: PostType; tags?: string[]; courseName?: string; authorId: string; authorName: string; authorInitials: string; authorLevel: number; authorTitle: string }) => void
    toggleLike: (postId: string) => void
    toggleBookmark: (postId: string) => void
}



export const useFeedStore = create<FeedState>((set, get) => ({
    posts: [],
    activeFilter: 'all',
    isLoading: false,

    fetchPosts: async () => {
        set({ isLoading: true })
        try {
            const { data } = await api.get('/api/feed')
            set({
                posts: data,
                isLoading: false
            })
        }
        catch (error) {
            console.error('Failed to fetch feed', error)
            set({ isLoading: false })
        }
    },
    setFilter: (filter) => {
        set({ activeFilter: filter })
    },

    addPost: (newPostData) => {
        const post: Post = {
            id: `post-${Date.now()}`,  // simple unique ID
            author: {
                id: newPostData.authorId,
                name: newPostData.authorName,
                initials: newPostData.authorInitials,
                level: newPostData.authorLevel,
                title: newPostData.authorTitle,
            },
            type: newPostData.type,
            content: newPostData.content,
            courseName: newPostData.courseName,
            timestamp: 'Just now',
            createdAt: Date.now(),
            likes: 0,
            comments: 0,
            shares: 0,
            isLiked: false,
            isBookmarked: false,
            tags: newPostData.tags || [],
        }

        // 🧠 ZUSTAND PATTERN: Immutable update
        // We create a NEW array with the new post prepended.
        // Zustand detects the reference change and re-renders subscribers.
        set({ posts: [post, ...get().posts] })
    },

    toggleLike: (postId) => {
        set({
            posts: get().posts.map(post =>
                post.id === postId
                    ? {
                        ...post,
                        isLiked: !post.isLiked,
                        likes: post.isLiked ? post.likes - 1 : post.likes + 1,
                    }
                    : post
            ),
        })
    },

    toggleBookmark: (postId) => {
        set({
            posts: get().posts.map(post =>
                post.id === postId
                    ? { ...post, isBookmarked: !post.isBookmarked }
                    : post
            ),
        })
    },
}))

export const selectFilteredPosts = (state: FeedState): Post[] => {
    const { posts, activeFilter } = state

    switch (activeFilter) {
        case 'achievements':
            return posts.filter(p => p.type === 'achievement' || p.type === 'milestone')
        case 'questions':
            return posts.filter(p => p.type === 'question')
        case 'trending':
            // Sort by engagement (likes + comments + shares), descending
            return [...posts].sort((a, b) =>
                (b.likes + b.comments + b.shares) - (a.likes + a.comments + a.shares)
            )
        case 'following':
            // TODO: When backend is ready, filter by followed users
            // For now, show all posts
            return posts
        case 'all':
        default:
            return posts
    }
}
