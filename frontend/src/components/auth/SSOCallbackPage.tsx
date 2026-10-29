import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useUserStore } from '@/store/userStore'
import { Loader2, AlertCircle, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'

export const SSOCallbackPage: React.FC = () => {
    const [searchParams] = useSearchParams()
    const ssoLogin = useAuthStore(state => state.ssoLogin)
    const fetchUser = useUserStore(state => state.fetchUser)
    const navigate = useNavigate()

    const [status, setStatus] = useState<'loading' | 'error'>('loading')
    const [errorMessage, setErrorMessage] = useState<string>('')

    useEffect(() => {
        let isMounted = true

        const performSSO = async () => {
            const token = searchParams.get('token') || searchParams.get('sso_token')

            if (!token) {
                if (isMounted) {
                    setStatus('error')
                    setErrorMessage('Missing SSO token. Please launch Spoken Social from the Spoken Tutorial website.')
                }
                return
            }

            const success = await ssoLogin(token)
            if (!isMounted) return

            if (success) {
                try {
                    await fetchUser()
                    toast.success('Successfully authenticated via SWAYAM Plus!', {
                        description: 'Welcome to your Spoken Social learning space.'
                    })
                    navigate('/', { replace: true })
                } catch (e) {
                    console.error('Failed to load user profile after SSO:', e)
                    navigate('/', { replace: true })
                }
            } else {
                const storeError = useAuthStore.getState().error
                setStatus('error')
                setErrorMessage(storeError || 'SSO authentication failed or token has expired.')
            }
        }

        performSSO()

        return () => {
            isMounted = false
        }
    }, [searchParams, ssoLogin, fetchUser, navigate])

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-[#020B24] flex flex-col justify-center items-center p-6 relative overflow-hidden font-sans">
            {/* Background Accents */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[450px] h-[450px] bg-indigo-500/10 dark:bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" />

            <div className="w-full max-w-md relative z-10">
                {/* Branding header */}
                <div className="flex flex-col items-center mb-8 text-center">
                    <div className="w-14 h-14 rounded-xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-2.5 flex items-center justify-center shadow-sm backdrop-blur-md mb-3">
                        <img src="/logo.png" alt="EduPyramids Logo" className="w-full h-full object-contain" />
                    </div>
                    <h1 className="font-mono text-2xl font-bold tracking-tight text-slate-900 dark:text-white leading-none">
                        <span className="text-[#1A237E] dark:text-white">Spoken</span> <span className="text-[#F26C25]">Social</span>
                    </h1>
                    <p className="text-[10px] font-bold tracking-widest mt-2">
                        by <span className="text-[#F26C25] font-extrabold">Edu</span><span className="text-[#1A237E] dark:text-slate-300 font-extrabold">Pyramids</span>
                    </p>
                </div>

                {/* Card */}
                <div className="bg-white/80 dark:bg-[#0b1329]/80 backdrop-blur-xl border border-slate-200/80 dark:border-white/10 shadow-xl dark:shadow-[0_25px_50px_-12px_rgba(0,0,0,0.5)] rounded-2xl p-8 relative text-center">
                    {status === 'loading' ? (
                        <div className="space-y-4 py-4">
                            <div className="flex justify-center">
                                <Loader2 className="w-10 h-10 animate-spin text-[#1A237E] dark:text-indigo-400" />
                            </div>
                            <h2 className="font-mono text-xl font-bold text-slate-900 dark:text-white">
                                Authenticating via SWAYAM Plus
                            </h2>
                            <p className="text-sm text-slate-500 dark:text-slate-400">
                                Verifying your credentials and preparing your course materials...
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-5 py-2">
                            <div className="flex justify-center text-rose-500">
                                <AlertCircle className="w-12 h-12" />
                            </div>
                            <div className="space-y-1.5">
                                <h2 className="font-mono text-xl font-bold text-slate-900 dark:text-white">
                                    Authentication Failed
                                </h2>
                                <p className="text-sm text-slate-600 dark:text-slate-300">
                                    {errorMessage}
                                </p>
                            </div>
                            <Button
                                onClick={() => navigate('/')}
                                className="w-full bg-[#1A237E] hover:bg-[#151b66] text-white font-semibold py-3 px-4 rounded-xl flex items-center justify-center gap-2 cursor-pointer mt-4"
                            >
                                <span>Go to Login</span>
                                <ArrowRight className="w-4 h-4" />
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
