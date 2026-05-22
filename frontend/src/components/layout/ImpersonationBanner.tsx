import { useAuthStore } from '@/store/authStore'
import { useUserStore } from '@/store/userStore'
import { Button } from '@/components/ui/button'
import { AlertCircle } from 'lucide-react'
import { toast } from 'sonner'

export function ImpersonationBanner() {
    const isImpersonating = useAuthStore(state => state.isImpersonating)
    const exitImpersonation = useAuthStore(state => state.exitImpersonation)
    const fetchUser = useUserStore(state => state.fetchUser)
    const user = useUserStore(state => state.user)

    if (!isImpersonating) return null

    const handleExit = async () => {
        const success = await exitImpersonation()
        if (success) {
            toast.success('Exited impersonation', {
                description: 'You are now back to your original account.'
            })
            await fetchUser()
        }
    }

    return (
        <div className="bg-yellow-500/20 border-b border-yellow-500/30 text-yellow-500 px-4 py-1.5 flex items-center justify-between z-[100]">
            <div className="flex items-center gap-2 text-xs font-bold">
                <AlertCircle className="h-4 w-4" />
                <span>IMPERSONATING: {user?.displayName} ({user?.role?.toUpperCase()})</span>
            </div>
            <Button 
                variant="destructive" 
                size="sm" 
                className="h-6 text-[10px] font-bold px-3 uppercase tracking-wider"
                onClick={handleExit}
            >
                Exit Session
            </Button>
        </div>
    )
}
