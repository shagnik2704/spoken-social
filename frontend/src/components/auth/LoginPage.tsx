import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useTheme } from '@/hooks/useTheme'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip'
import { Loader2, Eye, EyeOff, Terminal, ArrowRight, Sun, Moon } from 'lucide-react'
import { toast } from 'sonner'

const FULL_HEADLINE = 'Welcome to Spoken Social'

export const LoginPage: React.FC = (): React.JSX.Element => {
    const [searchParams] = useSearchParams()
    const [email, setEmail] = useState<string>('')
    const [password, setPassword] = useState<string>('')
    const [showPassword, setShowPassword] = useState<boolean>(false)
    const [isLoading, setIsLoading] = useState<boolean>(false)

    // Typewriter effect state
    const [displayText, setDisplayText] = useState<string>('')
    const [isDeleting, setIsDeleting] = useState<boolean>(false)

    const login = useAuthStore(state => state.login)
    const error = useAuthStore(state => state.error)
    const navigate = useNavigate()
    const { theme, toggleTheme } = useTheme()

    // Typewriter animation loop
    useEffect(() => {
        let timeout: ReturnType<typeof setTimeout>

        if (!isDeleting && displayText.length < FULL_HEADLINE.length) {
            // Typing forward (speed ~65ms per character)
            timeout = setTimeout(() => {
                setDisplayText(FULL_HEADLINE.slice(0, displayText.length + 1))
            }, 65)
        } else if (!isDeleting && displayText.length === FULL_HEADLINE.length) {
            // Hold the completed text for 4.5 seconds with blinking cursor
            timeout = setTimeout(() => {
                setIsDeleting(true)
            }, 4500)
        } else if (isDeleting && displayText.length > 0) {
            // Backspace delete smoothly (~30ms per character)
            timeout = setTimeout(() => {
                setDisplayText(FULL_HEADLINE.slice(0, displayText.length - 1))
            }, 30)
        } else if (isDeleting && displayText.length === 0) {
            // Brief pause before retyping
            timeout = setTimeout(() => {
                setIsDeleting(false)
            }, 500)
        }

        return () => clearTimeout(timeout)
    }, [displayText, isDeleting])

    useEffect(() => {
        const token = searchParams.get('token') || searchParams.get('sso_token')
        if (token) {
            navigate(`/sso?${searchParams.toString()}`, { replace: true })
        }
    }, [searchParams, navigate])

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
        e.preventDefault()
        setIsLoading(true)
        const success = await login(email, password)
        setIsLoading(false)
        if (success) {
            toast.success('Successfully logged in', {
                description: 'Welcome back to Spoken Social'
            })
            navigate('/')
        } else {
            toast.error('Login failed. Please check your credentials')
        }
    }

    return (
        <div className="min-h-screen w-full bg-background text-foreground font-sans selection:bg-primary/10 transition-colors duration-200 flex flex-col lg:flex-row overflow-x-hidden">
            
            {/* =========================================================================
                MOBILE TOP BAR (< lg): Brand + Theme Toggle in header
               ========================================================================= */}
            <header className="lg:hidden flex items-center justify-between px-4 py-2.5 sm:px-6 border-b border-[#D8E4F8] dark:border-white/5 bg-[#EEF4FC] dark:bg-[#071126] transition-colors">
                <div className="flex items-center gap-2 select-none">
                    <img 
                        src="/logo.png" 
                        alt="EduPyramids Logo" 
                        className="h-7 w-auto object-contain"
                    />
                    <div className="h-3.5 w-px bg-slate-300/80 dark:bg-white/10" />
                    <span className="font-semibold text-xs sm:text-sm tracking-tight text-slate-800 dark:text-slate-200">
                        Spoken Social
                    </span>
                </div>
                <TooltipProvider delayDuration={100}>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                variant="outline"
                                size="icon"
                                onClick={toggleTheme}
                                className="h-9 w-9 rounded-lg bg-card/90 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700/80 hover:bg-accent text-foreground shadow-xs transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer"
                                aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                            >
                                {theme === 'dark' ? (
                                    <Sun className="w-4 h-4 text-amber-400 transition-transform duration-300 hover:rotate-45" />
                                ) : (
                                    <Moon className="w-4 h-4 text-slate-800 dark:text-slate-200 transition-transform duration-300 hover:-rotate-12" />
                                )}
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent side="bottom" align="end" className="font-medium text-xs">
                            Switch to {theme === 'dark' ? 'Light' : 'Dark'} mode
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            </header>

            {/* =========================================================================
                LEFT PANEL: Soft Blue Canvas with Immersive Absorbed Scene
               ========================================================================= */}
            <div className="w-full lg:w-[55%] xl:w-[56%] bg-[#EEF4FC] dark:bg-[#071126] border-b lg:border-b-0 lg:border-r border-[#D8E4F8] dark:border-white/5 flex flex-col justify-between relative overflow-hidden transition-colors duration-200 lg:min-h-screen">
                
                {/* Upper Content Section */}
                <div className="p-6 sm:p-8 lg:p-12 xl:p-14 relative z-10 space-y-3 sm:space-y-6">
                    {/* Desktop Brand Header — Shown only on desktop */}
                    <div className="hidden lg:flex items-center gap-3 select-none">
                        <img 
                            src="/logo.png" 
                            alt="EduPyramids Logo" 
                            className="h-9 sm:h-10 w-auto object-contain"
                        />
                        <div className="h-5 w-px bg-slate-300/80 dark:bg-white/10" />
                        <span className="font-semibold text-sm tracking-tight text-slate-800 dark:text-slate-200">
                            Spoken Social
                        </span>
                    </div>

                    {/* Animated Bold Headline & Hook in Pure Solid Black Text with Typewriter Effect */}
                    <div className="pt-2 lg:pt-2 max-w-xl space-y-2 sm:space-y-2.5">
                        <h1 className="text-2xl sm:text-3xl lg:text-[40px] font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.18] min-h-[1.25em]">
                            <span>{displayText}</span>
                            <span className="inline-block w-[3px] h-[0.8em] bg-slate-900 dark:bg-white ml-1.5 translate-y-[2px] animate-pulse" />
                        </h1>
                        <p className="text-sm sm:text-base text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
                            Master Linux, Python & open source tech — step by step, with practical tasks and peer collaboration.
                        </p>
                    </div>
                </div>

                {/* Bottom Absorbed Illustration — Seamlessly dissolved into the background with Light/Dark dynamic switch */}
                <div className="relative w-full mt-auto select-none overflow-hidden">
                    <div 
                        className="w-full relative"
                        style={{
                            maskImage: 'linear-gradient(to top, black 80%, transparent 100%)',
                            WebkitMaskImage: 'linear-gradient(to top, black 80%, transparent 100%)',
                        }}
                    >
                        {/* Light Mode: Daytime studying scene — Full aspect ratio, uncropped */}
                        <img
                            src="/indian-student-study.jpg"
                            alt="Indian student studying open source tech during the day"
                            className={`w-full h-auto aspect-[1200/896] object-cover object-bottom transition-opacity duration-500 ease-in-out ${
                                theme === 'dark' ? 'opacity-0' : 'opacity-100'
                            }`}
                            loading="eager"
                        />
                        {/* Dark Mode: Cozy night studying scene with desk lamp — Full aspect ratio, uncropped */}
                        <img
                            src="/indian-student-study-dark.jpg"
                            alt="Indian student studying open source tech at night with desk lamp"
                            className={`w-full h-auto aspect-[1200/896] object-cover object-bottom absolute inset-0 transition-opacity duration-500 ease-in-out ${
                                theme === 'dark' ? 'opacity-100' : 'opacity-0 pointer-events-none'
                            }`}
                            loading="eager"
                        />
                    </div>
                </div>

            </div>

            {/* =========================================================================
                RIGHT PANEL: Clean Minimalist Sign In Form
               ========================================================================= */}
            <div className="w-full lg:w-[45%] xl:w-[44%] bg-background flex flex-col justify-between p-5 sm:p-8 lg:p-12 xl:p-14 lg:min-h-screen">
                
                {/* Theme Toggle Top Right (Desktop only) */}
                <div className="hidden lg:flex justify-end w-full">
                    <TooltipProvider delayDuration={100}>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="outline"
                                    size="icon"
                                    onClick={toggleTheme}
                                    className="h-10 w-10 rounded-xl bg-card/90 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700/80 hover:bg-accent text-foreground shadow-xs hover:shadow-md hover:border-primary/40 transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer"
                                    aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                                >
                                    {theme === 'dark' ? (
                                        <Sun className="w-5 h-5 text-amber-400 transition-transform duration-300 hover:rotate-45" />
                                    ) : (
                                        <Moon className="w-5 h-5 text-slate-800 dark:text-slate-200 transition-transform duration-300 hover:-rotate-12" />
                                    )}
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" align="end" className="font-medium text-xs">
                                Switch to {theme === 'dark' ? 'Light' : 'Dark'} mode
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                </div>

                {/* Centered Sign In Card */}
                <div className="w-full max-w-sm mx-auto my-auto py-6 sm:py-8 space-y-4 sm:space-y-6">
                    <div className="space-y-1.5">
                        <h2 className="text-2xl font-bold tracking-tight text-foreground">
                            Sign in
                        </h2>
                        <p className="text-xs text-muted-foreground">
                            Enter your credentials to access your courses & dashboard.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {error && (
                            <div 
                                className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs font-medium"
                                role="alert"
                            >
                                {error}
                            </div>
                        )}

                        {/* Email Field */}
                        <div className="space-y-1.5">
                            <Label htmlFor="email" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                Email
                            </Label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                placeholder="learner@example.com"
                                required
                                autoComplete="email"
                                className="w-full h-11 px-3.5 rounded-xl bg-card border border-input text-foreground placeholder:text-muted-foreground/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                            />
                        </div>

                        {/* Password Field */}
                        <div className="space-y-1.5">
                            <div className="flex items-center justify-between">
                                <Label htmlFor="password" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                    Password
                                </Label>
                                <a
                                    href="https://spoken-tutorial.org/accounts/forgot-password/"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-primary hover:underline transition-colors font-medium"
                                >
                                    Forgot?
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
                                    autoComplete="current-password"
                                    className="w-full h-11 px-3.5 pr-10 rounded-xl bg-card border border-input text-foreground placeholder:text-muted-foreground/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
                                    aria-label={showPassword ? "Hide password" : "Show password"}
                                >
                                    {showPassword ? (
                                        <EyeOff className="w-4 h-4" />
                                    ) : (
                                        <Eye className="w-4 h-4" />
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* Submit Button */}
                        <Button
                            type="submit"
                            disabled={isLoading}
                            className="w-full h-11 rounded-xl bg-primary hover:bg-primary-hover text-primary-foreground font-semibold text-sm transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer mt-2"
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

                        {/* Dev Auto-fill */}
                        {import.meta.env.DEV && (
                            <div className="pt-2">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setEmail('swayam_tester@test.com')
                                        setPassword('password123')
                                        toast.info('Filled SWAYAM Test credentials')
                                    }}
                                    className="w-full text-xs text-muted-foreground hover:text-foreground py-2 px-3 rounded-xl border border-dashed border-border/80 hover:border-primary/50 bg-muted/20 hover:bg-muted/40 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                                >
                                    <Terminal className="w-3.5 h-3.5 text-primary" />
                                    <span>Auto-fill Demo Student (Local Dev)</span>
                                </button>
                            </div>
                        )}
                    </form>
                </div>

                {/* Platform Support & Info Footer */}
                <footer className="w-full pt-6 pb-2 flex flex-col items-center justify-center gap-2 text-xs text-muted-foreground border-t border-border/40 text-center">
                    <p className="text-muted-foreground/80 text-[11px] sm:text-xs">
                        Official Spoken Tutorial learning and community platform.
                    </p>
                    <div className="flex flex-wrap items-center justify-center gap-x-2.5 gap-y-1 text-xs">
                        <span className="text-muted-foreground">Need assistance?</span>
                        <a
                            href="mailto:support@edupyramids.org"
                            className="font-medium text-primary hover:underline transition-colors"
                        >
                            Contact Support
                        </a>
                        <span className="text-border select-none">•</span>
                        <a
                            href="https://spoken-tutorial.org"
                            target="_blank"
                            rel="noreferrer"
                            className="hover:text-foreground hover:underline transition-colors"
                        >
                            Spoken Tutorial
                        </a>
                        <span className="text-border select-none">•</span>
                        <span>© {new Date().getFullYear()} EduPyramids</span>
                    </div>
                </footer>
            </div>

        </div>
    )
}
