import {create} from 'zustand'
import api from  '@/lib/axios'

interface AuthState {
    token: string | null
    isLoading: boolean
    isAuthenticated: boolean
    error: string | null

    login: (email:string,password:string)=>Promise<boolean>
    logout: ()=>void
}

export const useAuthStore = create<AuthState>((set)=>({
    token:localStorage.getItem('token'),
    isLoading:false,
    isAuthenticated: !!localStorage.getItem('token'),
    error: null,

    login: async (email,password) => {
        set({error:null,isLoading:true})
        try{
            const {data} = await api.post('/api/auth/login',{email,password})
            localStorage.setItem('token',data.access_token)
            set({
                token:data.access_token,
                isLoading:false,
                isAuthenticated:true,
            })
            return true
        }   
        catch(error){
            set({
                isLoading:false,
                error:'Login failed',
            })
            return false
        }
    },

    logout:()=>{
        localStorage.removeItem('token')
        set({
            token:null,
            isLoading:false,
            isAuthenticated:false
        })
    },
}))