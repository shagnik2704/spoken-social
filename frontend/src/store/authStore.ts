import {create} from 'zustand'
import api from  '@/lib/axios'

interface AuthState {
    token: string | null
    isAuthenticated: boolean
    error: string | null

    login: (email:string,password:string)=>Promise<boolean>
    logout: ()=>void
}

export const useAuthStore = create<AuthState>((set)=>({
    token:localStorage.getItem('token'),
    isAuthenticated: !!localStorage.getItem('token'),
    error: null,

    login: async (email,password) => {
        set({error:null})
        try{
            const {data} = await api.post('/api/auth/login',{email,password})
            localStorage.setItem('token',data.access_token)
            set({
                token:data.access_token,
                isAuthenticated:true,
            })
            return true
        }   
        catch(error){
            set({
                error:'Login failed',
            })
            return false
        }
    },

    logout:()=>{
        localStorage.removeItem('token')
        set({
            token:null,
            isAuthenticated:false
        })
    },
}))