import { createContext, useContext, useState, type ReactNode } from 'react'

interface ComposeModalContextType {
    isOpen: boolean
    open: () => void
    close: () => void
}

const ComposeModalContext = createContext<ComposeModalContextType | null>(null)

export function ComposeModalProvider({ children }: { children: ReactNode }) {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <ComposeModalContext.Provider value={{
            isOpen,
            open: () => setIsOpen(true),
            close: () => setIsOpen(false),
        }}>
            {children}
        </ComposeModalContext.Provider>
    )
}

export function useComposeModal() {
    const context = useContext(ComposeModalContext)
    if (!context) throw new Error('useComposeModal must be used within ComposeModalProvider')
    return context
}
