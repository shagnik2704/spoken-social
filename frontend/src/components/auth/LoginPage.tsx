import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useTheme } from '@/hooks/useTheme'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Loader2, Eye, EyeOff, CheckCircle2, Terminal, Activity, Code2, FileText, ArrowRight, Sun, Moon } from 'lucide-react'
import { toast } from 'sonner'

interface CourseBadge {
    name: string
    icon: React.ComponentType<{ className?: string }>
    color: string
}

export const LoginPage: React.FC = (): React.JSX.Element => {
    const [email, setEmail] = useState<string>('')
    const [password, setPassword] = useState<string>('')
    const [showPassword, setShowPassword] = useState<boolean>(false)
    const [isLoading, setIsLoading] = useState<boolean>(false)

    const login = useAuthStore(state => state.login)
    const error = useAuthStore(state => state.error)
    const navigate = useNavigate()
    const { theme, toggleTheme } = useTheme()

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
        e.preventDefault()
        setIsLoading(true)
        const success = await login(email, password)
        setIsLoading(false)
        if (success) {
            toast.success('Successfully logged in!', {
                description: 'Welcome back to Spoken Social'
            })
            navigate('/')
        } else {
            toast.error('Login failed. Please check your credentials')
        }
    }

    const coursesList: CourseBadge[] = [
        { name: 'Linux', icon: Terminal, color: 'text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-500/20 bg-blue-50/50 dark:bg-blue-500/5 hover:border-blue-300 dark:hover:border-blue-500/40 hover:bg-blue-100/50 dark:hover:bg-blue-500/10' },
        { name: 'Scilab', icon: Activity, color: 'text-cyan-600 dark:text-cyan-400 border-cyan-100 dark:border-cyan-500/20 bg-cyan-50/50 dark:bg-cyan-500/5 hover:border-cyan-300 dark:hover:border-cyan-500/40 hover:bg-cyan-100/50 dark:hover:bg-cyan-500/10' },
        { name: 'Python', icon: Code2, color: 'text-yellow-600 dark:text-yellow-400 border-yellow-100 dark:border-yellow-500/20 bg-yellow-50/50 dark:bg-yellow-500/5 hover:border-yellow-300 dark:hover:border-yellow-500/40 hover:bg-yellow-100/50 dark:hover:bg-yellow-500/10' },
        { name: 'LaTeX', icon: FileText, color: 'text-purple-600 dark:text-purple-400 border-purple-100 dark:border-purple-500/20 bg-purple-50/50 dark:bg-purple-500/5 hover:border-purple-300 dark:hover:border-purple-500/40 hover:bg-purple-100/50 dark:hover:bg-purple-500/10' },
    ]

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-[#020B24] flex overflow-hidden font-sans select-none w-full relative transition-colors duration-300">
            
            {/* Floating Theme Switcher */}
            <Button
                variant="outline"
                size="icon"
                onClick={toggleTheme}
                className="absolute top-6 right-6 z-20 h-10 w-10 rounded-full border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-white/10 shadow-sm hover:shadow transition-all duration-200 ease-in-out cursor-pointer hover:scale-105"
                title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
                {theme === 'dark' ? (
                    <Sun className="w-5 h-5" />
                ) : (
                    <Moon className="w-5 h-5" />
                )}
            </Button>

            {/* Left Column - Branding (Desktop only) */}
            <div className="hidden lg:flex lg:w-[58%] relative flex-col justify-between p-16 overflow-hidden border-r border-slate-200 dark:border-white/5 bg-gradient-to-br from-[#F5F6FD] via-[#ECEEF8] to-[#DDDFF0] dark:from-[#020B24] dark:via-[#051133] dark:to-[#0a205a] transition-all duration-300">
                
                {/* Background Grid Accent */}
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#28359304_1px,transparent_1px),linear-gradient(to_bottom,#28359304_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,#ffffff02_1px,transparent_1px),linear-gradient(to_bottom,#ffffff02_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black_80%)] pointer-events-none" />
                
                {/* Glowing Orbs */}
                <div className="absolute top-1/4 -left-20 w-[450px] h-[450px] bg-indigo-500/5 dark:bg-indigo-500/10 rounded-full blur-3xl animate-pulse pointer-events-none" style={{ animationDuration: '8s' }} />
                <div className="absolute bottom-1/4 right-0 w-[350px] h-[350px] bg-cyan-500/5 rounded-full blur-3xl animate-pulse pointer-events-none" style={{ animationDuration: '6s', animationDelay: '2s' }} />

                {/* Constant Network Connections Vector */}
                <svg className="absolute inset-0 w-full h-full opacity-25 dark:opacity-20 pointer-events-none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <radialGradient id="grid-glow" cx="50%" cy="50%" r="50%">
                            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.1" />
                            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
                        </radialGradient>
                    </defs>
                    <circle cx="75%" cy="35%" r="300" fill="url(#grid-glow)" />
                    <circle cx="25%" cy="65%" r="200" fill="url(#grid-glow)" />
                    
                    {/* Visual constellation links */}
                    <path d="M 150 180 L 280 140 L 440 280 L 250 420 Z" className="stroke-indigo-950/10 dark:stroke-white/5" strokeWidth="1" fill="none" />
                    <path d="M 280 140 L 520 90 M 440 280 L 650 380" className="stroke-indigo-950/5 dark:stroke-white/5" strokeWidth="1" strokeDasharray="6,6" />
                    
                    {/* Constellation Nodes */}
                    <circle cx="150" cy="180" r="3" className="fill-indigo-950/10 dark:fill-white/15" />
                    <circle cx="280" cy="140" r="5" className="fill-indigo-500/25 dark:fill-indigo-500/30" />
                    <circle cx="440" cy="280" r="4.5" className="fill-cyan-500/25 dark:fill-cyan-500/30" />
                    <circle cx="250" cy="420" r="3.5" className="fill-indigo-950/10 dark:fill-white/15" />
                </svg>

                {/* Logo & Header */}
                <div className="relative z-10 flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 p-2 flex items-center justify-center shadow-sm backdrop-blur-md transition-all duration-300 hover:border-indigo-500/40 hover:bg-slate-50 dark:hover:bg-white/10">
                        <img src="/logo.png" alt="EduPyramids Logo" className="w-full h-full object-contain" />
                    </div>
                    <div>
                        <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white block leading-none">Spoken Social</span>
                        <span className="text-[10px] font-bold tracking-widest block mt-1.5">
                            by <span className="text-[#F26C25] font-extrabold">Edu</span><span className="text-[#1A237E] dark:text-slate-300 font-extrabold">Pyramids</span>
                        </span>
                    </div>
                </div>

                {/* Hero Title & Features Checklist */}
                <div className="relative z-10 my-auto space-y-10 max-w-xl">
                    <div className="space-y-6">
                        {/* Course Badges */}
                        <div className="flex flex-wrap gap-2.5">
                            {coursesList.map((c) => {
                                const Icon = c.icon
                                return (
                                    <div
                                        key={c.name}
                                        className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border text-xs font-semibold tracking-wide transition-all duration-300 hover:scale-105 shadow-sm shadow-indigo-500/5 cursor-default ${c.color}`}
                                    >
                                        <Icon className="w-3.5 h-3.5" />
                                        <span>{c.name}</span>
                                    </div>
                                )
                            })}
                        </div>
                        
                        <h2 className="font-mono text-4xl xl:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-[1.1] animate-in fade-in slide-in-from-left-4 duration-500">
                            Welcome to <span className="text-[#1A237E] dark:text-white">Spoken</span> <span className="text-[#F26C25]">Social</span>
                        </h2>
                        
                        <p className="text-slate-600 dark:text-slate-300 text-base xl:text-lg leading-relaxed font-light">
                            Empowering Faculty Development Programme learners through practical, industry-focused training.
                        </p>
                    </div>

                    {/* Feature Highlights Checklist */}
                    <div className="space-y-4 border-t border-slate-200 dark:border-white/5 pt-8">
                        {[
                            'Hands-on Learning',
                            'Structured Course Progress',
                            'Interactive Learning Resources',
                            'Certification-Oriented Training'
                        ].map((feature, idx) => (
                            <div key={idx} className="flex items-center gap-3.5 group cursor-default">
                                <div className="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-all duration-200 ease-in-out">
                                    <CheckCircle2 className="w-3.5 h-3.5" />
                                </div>
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-white transition-colors duration-200 ease-in-out">
                                    {feature}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Left Side Footer */}
                <div className="relative z-10 pt-8 border-t border-slate-200 dark:border-white/5 flex items-center justify-between text-xs text-slate-500">
                    <p>© {new Date().getFullYear()} EduPyramids. All rights reserved.</p>
                    <a href="https://spoken-tutorial.org" target="_blank" rel="noreferrer" className="text-slate-500 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-300 transition-colors duration-200 ease-in-out">
                        Visit Spoken Tutorial Website
                    </a>
                </div>
            </div>

            {/* Right Column - Auth */}
            <div className="flex-1 lg:w-[42%] flex flex-col justify-center items-center p-6 sm:p-12 relative overflow-hidden bg-slate-50 dark:bg-[#020B24] transition-colors duration-300">
                
                {/* Visual Glow behind card for mobile/desktop depth */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

                {/* Mobile/Tablet Branding Header */}
                <div className="lg:hidden flex flex-col items-center mb-8 relative z-10 text-center">
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

                {/* Glassmorphism Auth Container */}
                <div className="w-full max-w-md relative z-10">
                    <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-indigo-500/5 to-cyan-500/5 dark:from-indigo-500/10 dark:to-cyan-500/10 blur-xl opacity-50 pointer-events-none" />
                    
                    <div className="bg-white/75 dark:bg-[#0b1329]/65 backdrop-blur-xl border border-slate-200/80 dark:border-white/10 hover:border-indigo-500/20 shadow-xl dark:shadow-[0_25px_50px_-12px_rgba(0,0,0,0.5)] shadow-slate-200/50 rounded-2xl p-8 relative hover:scale-[1.01] transition-all duration-300 ease-in-out">
                        <div className="mb-6">
                            <h2 className="font-mono text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">Welcome Back</h2>
                            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Sign in to continue your learning journey.</p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-5">
                            {error && (
                                <div className="bg-red-500/10 border border-red-500/25 text-red-700 dark:text-red-200 text-xs rounded-lg p-3 animate-pulse">
                                    {error}
                                </div>
                            )}

                            {/* Email input field */}
                            <div className="space-y-1.5">
                                <Label htmlFor="email" className="text-xs font-semibold text-slate-500 dark:text-slate-300 tracking-wide uppercase">Email Address</Label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    placeholder="user@example.com"
                                    required
                                    className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-white/10 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 dark:focus:ring-indigo-500/50 focus:border-indigo-600 dark:focus:border-indigo-500 transition-all duration-200 ease-in-out"
                                />
                            </div>

                            {/* Password input field */}
                            <div className="space-y-1.5">
                                <div className="flex items-center justify-between">
                                    <Label htmlFor="password" className="text-xs font-semibold text-slate-500 dark:text-slate-300 tracking-wide uppercase">Password</Label>
                                    <a
                                        href="https://spoken-tutorial.org/accounts/forgot-password/"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 hover:underline transition-colors duration-200 ease-in-out"
                                    >
                                        Forgot Password?
                                    </a>
                                </div>
                                <div className="relative">
                                    <input
                                        id="password"
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={e => setPassword(e.target.value)}
                                        placeholder="••••••••"
                                        required
                                        className="w-full px-4 py-3 pr-10 rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-white/10 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 dark:focus:ring-indigo-500/50 focus:border-indigo-600 dark:focus:border-indigo-500 transition-all duration-200 ease-in-out"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 focus:outline-none transition-colors duration-200 ease-in-out"
                                    >
                                        {showPassword ? (
                                            <EyeOff className="w-4 h-4" />
                                        ) : (
                                            <Eye className="w-4 h-4" />
                                        )}
                                    </button>
                                </div>
                            </div>


                            {/* Large primary Sign In button */}
                            <Button
                                type="submit"
                                disabled={isLoading}
                                className="w-full bg-[#1A237E] hover:bg-[#151b66] text-white font-semibold py-3 px-4 rounded-xl shadow-lg shadow-indigo-500/10 dark:shadow-indigo-950/20 focus:outline-none focus:ring-2 focus:ring-[#1A237E] focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-[#020B24] transition-all duration-200 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer mt-2"
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        <span>Signing in...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Sign In</span>
                                        <ArrowRight className="w-4 h-4" />
                                    </>
                                )}
                            </Button>
                            
                        </form>
                    </div>
                </div>

                {/* Platform Support Footer */}
                <div className="text-center mt-8 text-xs text-slate-500 dark:text-slate-400 relative z-10 max-w-sm">
                    <p className="text-slate-400 dark:text-slate-500">Registered Faculty Development Programme platform.</p>
                    <p className="mt-1.5 flex items-center justify-center gap-1">
                        <span>Need assistance?</span>
                        <a href="mailto:support@edupyramids.org" className="text-[#F26C25] hover:text-[#d95616] hover:underline font-semibold transition-colors duration-200 ease-in-out">
                            Contact us
                        </a>
                    </p>
                </div>
            </div>
        </div>
    )
}