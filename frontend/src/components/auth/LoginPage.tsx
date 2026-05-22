import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'

export function LoginPage() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [role, setRole] = useState<'student' | 'coordinator' | 'admin'>('student')
    const [isLoading, setIsLoading] = useState(false)
    const [colleges, setColleges] = useState<{ id: string, name: string }[]>([])
    const [selectedCollegeId, setSelectedCollegeId] = useState('')

    const login = useAuthStore(state => state.login)
    const error = useAuthStore(state => state.error)
    const navigate = useNavigate()

    useEffect(() => {
        api.get('/api/coordinator/public/list').then(res => setColleges(res.data))
    }, [])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        const success = await login(email, password, role, selectedCollegeId)
        setIsLoading(false)
        if (success) {
            toast.success('Successfully logged in!',
                {
                    description: 'Welcome back to Spoken Social'
                }
            )
            navigate('/')
        }
        else {
            toast.error('Login failed. Please check your credentials')
        }
    }


    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <div className="w-full max-w-sm">

                {/* Logo + Branding */}
                <div className="text-center mb-8">
                    <img src="/logo.png" alt="EduPyramids" className="w-16 h-16 object-contain mx-auto mb-4" />
                    <h1 className="text-2xl font-bold tracking-tight text-foreground">
                        Spoken Social
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1">
                        Sign in to continue learning
                    </p>
                </div>

                {/* Login Card */}
                <Card>
                    <CardHeader>
                        <CardTitle>Sign In</CardTitle>
                        <CardDescription>
                            Enter your Spoken Tutorial credentials
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {/* Role selection tabs */}
                            <div className="flex p-1 bg-muted rounded-lg mb-2">
                                {(['student', 'coordinator', 'admin'] as const).map((r) => (
                                    <button
                                        key={r}
                                        type="button"
                                        onClick={() => setRole(r)}
                                        className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
                                            role === r 
                                            ? 'bg-background text-foreground shadow-sm' 
                                            : 'text-muted-foreground hover:text-foreground'
                                        }`}
                                    >
                                        {r.charAt(0).toUpperCase() + r.slice(1)}
                                    </button>
                                ))}
                            </div>

                            {/* Error message */}
                            {error && (
                                <div className="bg-destructive/10 text-destructive text-sm rounded-lg p-3">
                                    {error}
                                </div>
                            )}

                            {/* Email field */}
                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    placeholder="user@example.com"
                                    required
                                />
                            </div>

                            {/* Password field */}
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <Label htmlFor="password">Password</Label>
                                    <a
                                        href="https://spoken-tutorial.org/accounts/forgot-password/"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs text-muted-foreground hover:text-primary underline-offset-4 hover:underline transition-colors"
                                    >
                                        Forgot Password?
                                    </a>
                                </div>
                                <Input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                />
                            </div>

                            {/* College Selection (Conditional) */}
                            {role !== 'admin' && (
                                <div className="space-y-2 animate-in fade-in slide-in-from-top-1 duration-200">
                                    <Label htmlFor="college">College</Label>
                                    <select
                                        id="college"
                                        value={selectedCollegeId}
                                        onChange={e => setSelectedCollegeId(e.target.value)}
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                        required
                                    >
                                        <option value="">Select a college...</option>
                                        {colleges.map(c => (
                                            <option key={c.id} value={c.id}>
                                                {c.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            )}

                            {/* Submit button */}
                            <Button type="submit" className="w-full" disabled={isLoading}>
                                {isLoading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Signing in...
                                    </>
                                ) : (
                                    'Sign In'
                                )}
                            </Button>
                        </form>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
