import { useAuthStore } from '@/store/authStore'
import { useUserStore } from '@/store/userStore'
import { Button } from '@/components/ui/button'
import { Eye } from 'lucide-react'
import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'

export function ImpersonationBanner() {
    const isImpersonating = useAuthStore(state => state.isImpersonating)
    const exitImpersonation = useAuthStore(state => state.exitImpersonation)
    const fetchUser = useUserStore(state => state.fetchUser)
    const user = useUserStore(state => state.user)
    const navigate = useNavigate()

    if (!isImpersonating) return null

    const handleExit = async () => {
        const success = await exitImpersonation()
        if (success) {
            toast.success(`Exited ${roleDisplayName.toLowerCase()} view`, {
                description: 'You are now back to your original account.'
            })
            await fetchUser()
            // Redirect based on restored role
            const restoredRole = useUserStore.getState().user?.role
            if (restoredRole === 'coordinator') {
                navigate('/coordinator')
            } else if (restoredRole === 'admin') {
                navigate('/admin')
            } else {
                navigate('/dashboard')
            }
        }
    }

    const roleDisplayName = user?.role === 'student' ? 'Learner' : 'Coordinator'

    return (
        <div className="bg-sky-500/10 border-b border-sky-500/20 text-sky-400 px-4 py-2 flex items-center justify-between z-[100] backdrop-blur-sm">
            <div className="flex items-center gap-2 text-xs font-semibold tracking-wide">
                <Eye className="h-4 w-4 text-sky-400" />
                <span>Viewing as a {roleDisplayName}: <span className="font-bold text-sky-300">{user?.displayName}</span></span>
            </div>
            <Button 
                variant="outline" 
                size="sm" 
                className="h-6 text-[10px] font-bold px-3 border-sky-500/30 text-sky-400 hover:bg-sky-500/20 hover:text-sky-300 transition-colors uppercase tracking-wider"
                onClick={handleExit}
            >
                Exit {roleDisplayName} View
            </Button>
        </div>
    )
}
