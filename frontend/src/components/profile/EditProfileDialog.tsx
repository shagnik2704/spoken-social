import { useState, useEffect } from 'react'
import { Loader2, User as UserIcon, MapPin, LinkIcon, GraduationCap, FileText } from 'lucide-react'
import {
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useUserStore } from '@/store/userStore'
import { toast } from 'sonner'
import api from '@/lib/axios'

interface EditProfileDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
}

export default function EditProfileDialog({ open, onOpenChange }: EditProfileDialogProps) {
    const user = useUserStore(state => state.user)
    const updateProfile = useUserStore(state => state.updateProfile)

    const [form, setForm] = useState({
        displayName: '',
        bio: '',
        departmentYear: '',
        location: '',
        website: '',
    })
    const [saving, setSaving] = useState(false)
    const [errors, setErrors] = useState<Record<string, string>>({})

    // Sync form state when dialog opens or user changes
    useEffect(() => {
        if (open && user) {
            setForm({
                displayName: user.displayName || '',
                bio: user.bio || '',
                departmentYear: user.departmentYear || '',
                location: user.location || '',
                website: user.website || '',
            })
            setErrors({})
        }
    }, [open, user])

    const handleChange = (field: keyof typeof form, value: string) => {
        setForm(prev => ({ ...prev, [field]: value }))
        // Clear error on change
        if (errors[field]) {
            setErrors(prev => {
                const next = { ...prev }
                delete next[field]
                return next
            })
        }
    }

    const validate = (): boolean => {
        const newErrors: Record<string, string> = {}
        if (!form.displayName.trim()) {
            newErrors.displayName = 'Display name is required'
        } else if (form.displayName.length > 100) {
            newErrors.displayName = 'Max 100 characters'
        }
        if (form.bio.length > 500) {
            newErrors.bio = 'Max 500 characters'
        }
        if (form.departmentYear.length > 128) {
            newErrors.departmentYear = 'Max 128 characters'
        }
        if (form.location.length > 100) {
            newErrors.location = 'Max 100 characters'
        }
        if (form.website.length > 255) {
            newErrors.website = 'Max 255 characters'
        }
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSave = async () => {
        if (!validate()) return

        setSaving(true)
        try {
            const { data } = await api.put('/api/me', form)

            // Update the Zustand store with the returned user data
            updateProfile(data.user)

            toast.success('Profile updated successfully!')
            onOpenChange(false)
        } catch (err: any) {
            const message = err?.response?.data?.detail || 'Failed to update profile'
            toast.error(message)
        } finally {
            setSaving(false)
        }
    }

    const fields = [
        {
            key: 'displayName' as const,
            label: 'Display Name',
            icon: UserIcon,
            placeholder: 'Your display name',
            type: 'input' as const,
            maxLength: 100,
        },
        {
            key: 'bio' as const,
            label: 'Bio',
            icon: FileText,
            placeholder: 'Tell people about yourself...',
            type: 'textarea' as const,
            maxLength: 500,
        },
        {
            key: 'departmentYear' as const,
            label: 'Department / Year',
            icon: GraduationCap,
            placeholder: 'e.g. Computer Science, 3rd Year',
            type: 'input' as const,
            maxLength: 128,
        },
        {
            key: 'location' as const,
            label: 'Location',
            icon: MapPin,
            placeholder: 'e.g. Mumbai, India',
            type: 'input' as const,
            maxLength: 100,
        },
        {
            key: 'website' as const,
            label: 'Website',
            icon: LinkIcon,
            placeholder: 'https://yoursite.com',
            type: 'input' as const,
            maxLength: 255,
        },
    ]

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                            <UserIcon className="h-4 w-4 text-primary" />
                        </div>
                        Edit Profile
                    </DialogTitle>
                    <DialogDescription>
                        Update your profile information. Changes are saved to your account.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-2">
                    {fields.map(field => {
                        const Icon = field.icon
                        const value = form[field.key]
                        const error = errors[field.key]

                        return (
                            <div key={field.key} className="space-y-1.5">
                                <Label
                                    htmlFor={`edit-${field.key}`}
                                    className="text-sm font-medium flex items-center gap-1.5"
                                >
                                    <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                                    {field.label}
                                </Label>

                                {field.type === 'textarea' ? (
                                    <div>
                                        <Textarea
                                            id={`edit-${field.key}`}
                                            value={value}
                                            onChange={e => handleChange(field.key, e.target.value)}
                                            placeholder={field.placeholder}
                                            rows={3}
                                            maxLength={field.maxLength}
                                            className={error ? 'border-destructive' : ''}
                                        />
                                        <p className="text-[10px] text-muted-foreground text-right mt-1">
                                            {value.length}/{field.maxLength}
                                        </p>
                                    </div>
                                ) : (
                                    <Input
                                        id={`edit-${field.key}`}
                                        value={value}
                                        onChange={e => handleChange(field.key, e.target.value)}
                                        placeholder={field.placeholder}
                                        maxLength={field.maxLength}
                                        className={error ? 'border-destructive' : ''}
                                    />
                                )}

                                {error && (
                                    <p className="text-xs text-destructive">{error}</p>
                                )}
                            </div>
                        )
                    })}
                </div>

                <DialogFooter className="gap-2 sm:gap-0">
                    <Button
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                        disabled={saving}
                        className="rounded-full"
                    >
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSave}
                        disabled={saving}
                        className="rounded-full bg-primary hover:bg-primary-hover text-white gap-1.5"
                    >
                        {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                        {saving ? 'Saving...' : 'Save Changes'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
