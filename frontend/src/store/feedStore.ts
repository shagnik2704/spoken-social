// ============================================================
// FEED STORE — Zustand
// ============================================================
//
// This store manages the social feed:
//   - All posts
//   - Active filter (all, following, achievements, questions, trending)
//   - Creating new posts
//   - Toggling likes and bookmarks
//
// 🧠 ZUSTAND PATTERN: Derived state
//
// Notice `filteredPosts` is NOT in the store — it's a SELECTOR.
// We compute it on-the-fly from `posts` + `activeFilter`.
// This is a key Zustand pattern: store raw state, derive the rest.
//
// ============================================================

import { create } from 'zustand'
import type { Post, PostType } from '@/types'
import { MOCK_POSTS } from '@/data/mockData'

// ----- Filter types -----

export type FeedFilter = 'all' | 'following' | 'achievements' | 'questions' | 'trending'

// ----- Store shape -----

interface FeedState {
    // State
    posts: Post[]
    activeFilter: FeedFilter

    // Actions
    setFilter: (filter: FeedFilter) => void
    addPost: (post: { content: string; type: PostType; tags?: string[]; courseName?: string; authorId: string; authorName: string; authorInitials: string; authorLevel: number; authorTitle: string }) => void
    toggleLike: (postId: string) => void
    toggleBookmark: (postId: string) => void
}

// ----- Create the store -----

export const useFeedStore = create<FeedState>((set, get) => ({
    posts: MOCK_POSTS,
    activeFilter: 'all',

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

// ============================================================
// SELECTORS — Derived state computed from the store
// ============================================================
//
// 🧠 ZUSTAND PATTERN: Selectors
//
// Instead of storing `filteredPosts` in the store (which would be
// redundant and could get out of sync), we compute it on read.
//
// Usage in components:
//   const posts = useFeedStore(selectFilteredPosts)
//
// This is equivalent to React's `useMemo`, but cleaner because
// the logic lives with the store, not scattered across components.
//
// ============================================================

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
