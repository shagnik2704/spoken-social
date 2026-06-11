import {create} from 'zustand'
import api from  '@/lib/axios'

interface AuthState {
    token: string | null
    isLoading: boolean
    isAuthenticated: boolean
    isImpersonating: boolean
    error: string | null

    login: (email: string, password: string, role?: string, collegeId?: string) => Promise<boolean>
    logout: () => void
    impersonate: (collegeId: string, targetRole: string) => Promise<boolean>
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
        set({
            token: null,
            isLoading: false,
            isAuthenticated: false,
            isImpersonating: false,
        })
    },

    impersonate: async (collegeId, targetRole) => {
        try {
            const { data } = await api.post('/api/auth/impersonate', { 
                college_id: collegeId, 
                target_role: targetRole 
            })
            localStorage.setItem('token', data.access_token)
            localStorage.setItem('isImpersonating', 'true')
            set({
                token: data.access_token,
                isImpersonating: true,
            })
            return true
        } catch (error) {
            console.error('Impersonation failed:', error)
            return false
        }
    },

    exitImpersonation: async () => {
        try {
            const { data } = await api.post('/api/auth/exit-impersonation')
            localStorage.setItem('token', data.access_token)
            localStorage.removeItem('isImpersonating')
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