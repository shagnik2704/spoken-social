import {create} from 'zustand'
import api from  '@/lib/axios'
import { useUserStore } from './userStore'

interface AuthState {
    token: string | null
    isLoading: boolean
    isAuthenticated: boolean
    isImpersonating: boolean
    error: string | null

    login: (email: string, password: string, role?: string, collegeId?: string) => Promise<boolean>
    logout: () => void
    impersonate: (collegeId: string, targetRole: string, targetUserId?: string) => Promise<boolean>
    exitImpersonation: () => Promise<boolean>
}

export const useAuthStore = create<AuthState>((set) => ({
    token: localStorage.getItem('token'),
    isLoading: false,
    isAuthenticated: !!localStorage.getItem('token'),
    isImpersonating: localStorage.getItem('isImpersonating') === 'true',
    error: null,

    login: async (email, password, role?: string, collegeId?: string) => {
        set({ error: null, isLoading: true })
        try {
            const payload: any = { email, password }
            if (role) payload.role = role
            if (collegeId) payload.college_id = collegeId
            
            const { data } = await api.post('/api/auth/login', payload)
            localStorage.setItem('token', data.access_token)
            localStorage.removeItem('isImpersonating')
            localStorage.removeItem('activeProgrammeId')
            localStorage.removeItem('activeProgrammeName')
            localStorage.removeItem('activeCourseId')
            
            useUserStore.setState({
                activeProgrammeId: '',
                activeProgrammeName: '',
                activeCourseId: '',
                courses: [],
                badges: [],
                tutorials: [],
                programmes: [],
            })

            set({
                token: data.access_token,
                isLoading: false,
                isAuthenticated: true,
                isImpersonating: false,
            })
            return true
        }
        catch (error) {
            set({
                isLoading: false,
                error: 'Login failed',
            })
            return false
        }
    },

    logout: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('isImpersonating')
        localStorage.removeItem('activeProgrammeId')
        localStorage.removeItem('activeProgrammeName')
        localStorage.removeItem('activeCourseId')
        
        useUserStore.setState({
            user: null,
            isAuthenticated: false,
            activeProgrammeId: '',
            activeProgrammeName: '',
            activeCourseId: '',
            courses: [],
            badges: [],
            tutorials: [],
            programmes: [],
        })

        set({
            token: null,
            isLoading: false,
            isAuthenticated: false,
            isImpersonating: false,
        })
    },

    impersonate: async (collegeId, targetRole, targetUserId?: string) => {
        try {
            const payload: any = { 
                college_id: collegeId, 
                target_role: targetRole 
            }
            if (targetUserId) {
                payload.target_user_id = targetUserId
            }
            const { data } = await api.post('/api/auth/impersonate', payload)
            localStorage.setItem('token', data.access_token)
            localStorage.setItem('isImpersonating', 'true')
            // Don't clear activeProgrammeId/activeCourseId — the subsequent 
            // fetchUser() call will load the impersonated user's data and 
            // auto-select the first programme/course if the current ones aren't valid.
            
            useUserStore.setState({
                courses: [],
                badges: [],
                tutorials: [],
            })

            set({
                token: data.access_token,
                isImpersonating: true,
                error: null,
            })
            return true
        } catch (error: any) {
            console.error('Impersonation failed:', error)
            const detail = error?.response?.data?.detail || 'Impersonation failed'
            set({ error: detail })
            return false
        }
    },

    exitImpersonation: async () => {
        try {
            const { data } = await api.post('/api/auth/exit-impersonation')
            localStorage.setItem('token', data.access_token)
            localStorage.removeItem('isImpersonating')
            localStorage.removeItem('activeProgrammeId')
            localStorage.removeItem('activeProgrammeName')
            localStorage.removeItem('activeCourseId')
            
            useUserStore.setState({
                activeProgrammeId: '',
                activeProgrammeName: '',
                activeCourseId: '',
                courses: [],
                badges: [],
                tutorials: [],
                programmes: [],
            })

            set({
                token: data.access_token,
                isImpersonating: false,
            })
            return true
        } catch (error) {
            console.error('Failed to exit impersonation:', error)
            return false
        }
    }
}))