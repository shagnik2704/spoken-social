import { useState } from 'react'
import { Check, Copy } from 'lucide-react'

interface CommandChipProps {
    command: string
}

export const CommandChip: React.FC<CommandChipProps> = ({ command }) => {
    const [copied, setCopied] = useState(false)

    const handleCopy = async (): Promise<void> => {
        try {
            await navigator.clipboard.writeText(command)
            setCopied(true)
            setTimeout(() => setCopied(false), 1500)
        } catch {
            setCopied(false)
        }
    }

    return (
        <div className="flex items-center gap-2 min-h-11 pl-3 pr-1 rounded-lg bg-terminal border border-terminal-border">
            <span className="font-terminal text-[13px] font-semibold text-terminal-prompt select-none" aria-hidden="true">$</span>
            <code className="flex-1 min-w-0 py-2 font-terminal text-[13px] text-terminal-fg break-all">{command}</code>
            <button
                type="button"
                onClick={handleCopy}
                aria-label={`Copy command: ${command}`}
                title="Copy"
                className="size-11 sm:size-9 shrink-0 inline-flex items-center justify-center rounded-md text-terminal-muted hover:text-terminal-fg hover:bg-terminal-border/60 transition duration-200 ease-in-out cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-terminal-prompt/60"
            >
                {copied ? <Check className="size-4 text-terminal-prompt" /> : <Copy className="size-4" />}
            </button>
        </div>
    )
}
