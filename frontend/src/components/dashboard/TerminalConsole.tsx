import { useState } from 'react'
import { Check, Copy, Eraser } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TerminalConsoleProps {
    value: string
    onChange: (value: string) => void
    maxChars: number
    title?: string
    placeholder?: string
    isSubmitted?: boolean
    className?: string
}

const PROMPT_PATTERN = /^((?:[\w.-]+@[\w.-]+:[^$#]*)?[$#])(\s.*|)$/

const TEXT_LAYER = 'font-terminal text-[13px] leading-6 whitespace-pre-wrap break-words p-4 m-0'

const renderLine = (line: string, index: number, dimmed: boolean): React.ReactNode => {
    const match = PROMPT_PATTERN.exec(line)
    if (!match) {
        return (
            <span key={index} className={dimmed ? 'text-terminal-muted/60' : 'text-terminal-fg/80'}>
                {line}
                {'\n'}
            </span>
        )
    }
    return (
        <span key={index}>
            <span className={dimmed ? 'text-terminal-prompt/50' : 'text-terminal-prompt font-semibold'}>{match[1]}</span>
            <span className={dimmed ? 'text-terminal-muted/60' : 'text-terminal-fg font-medium'}>{match[2]}</span>
            {'\n'}
        </span>
    )
}

export const TerminalConsole: React.FC<TerminalConsoleProps> = ({
    value,
    onChange,
    maxChars,
    title = 'student@ubuntu: ~',
    placeholder = '',
    isSubmitted = false,
    className,
}) => {
    const [copied, setCopied] = useState(false)

    const isEmpty = value.length === 0
    const lines = (isEmpty ? placeholder : value).split('\n')
    const lineCount = isEmpty ? 0 : lines.length
    const charCount = value.length
    const isOverLimit = charCount > maxChars
    const isNearLimit = !isOverLimit && charCount > maxChars * 0.9

    const handleCopy = async (): Promise<void> => {
        if (isEmpty) return
        try {
            await navigator.clipboard.writeText(value)
            setCopied(true)
            setTimeout(() => setCopied(false), 1500)
        } catch {
            setCopied(false)
        }
    }

    const barButton =
        'size-9 inline-flex items-center justify-center rounded-md text-terminal-muted hover:text-terminal-fg hover:bg-terminal-border/60 transition duration-200 ease-in-out cursor-pointer disabled:opacity-40 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-terminal-prompt/60'

    return (
        <div
            className={cn(
                'rounded-xl border border-terminal-border bg-terminal overflow-hidden flex flex-col shadow-sm transition duration-200 ease-in-out focus-within:ring-2 focus-within:ring-ring/60',
                className
            )}
        >
            <div className="flex items-center gap-3 pl-4 pr-1.5 h-11 bg-terminal-bar border-b border-terminal-border select-none">
                <div className="flex items-center gap-1.5" aria-hidden="true">
                    <span className="size-2.5 rounded-full bg-terminal-border" />
                    <span className="size-2.5 rounded-full bg-terminal-border" />
                    <span className="size-2.5 rounded-full bg-terminal-border" />
                </div>
                <span className="flex-1 text-center font-terminal text-xs text-terminal-muted truncate">{title}</span>
                <div className="flex items-center">
                    <button type="button" onClick={handleCopy} disabled={isEmpty} className={barButton} aria-label="Copy terminal contents" title="Copy">
                        {copied ? <Check className="h-4 w-4 text-terminal-prompt" /> : <Copy className="h-4 w-4" />}
                    </button>
                    <button type="button" onClick={() => onChange('')} disabled={isEmpty} className={barButton} aria-label="Clear terminal" title="Clear">
                        <Eraser className="h-4 w-4" />
                    </button>
                </div>
            </div>

            <div className="relative min-h-[280px] max-h-[440px] overflow-y-auto flex-1">
                <pre aria-hidden="true" className={cn(TEXT_LAYER, 'min-h-[280px] pointer-events-none')}>
                    {lines.map((line, index) => renderLine(line, index, isEmpty))}
                </pre>
                <textarea
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    spellCheck={false}
                    autoCapitalize="off"
                    autoCorrect="off"
                    aria-label="Terminal commands and output"
                    className={cn(
                        TEXT_LAYER,
                        'absolute inset-0 w-full h-full resize-none overflow-hidden bg-transparent text-transparent caret-terminal-prompt outline-none selection:bg-terminal-fg/25'
                    )}
                />
            </div>

            <div className="flex items-center justify-between gap-3 px-4 h-9 bg-terminal-bar border-t border-terminal-border font-terminal text-[11px] text-terminal-muted">
                <div className="flex items-center gap-3 min-w-0">
                    <span>bash</span>
                    <span className="hidden sm:inline">
                        {lineCount} {lineCount === 1 ? 'line' : 'lines'}
                    </span>
                    <span className={cn(isOverLimit ? 'text-destructive font-semibold' : isNearLimit ? 'text-xp-gold font-semibold' : undefined)}>
                        {charCount.toLocaleString()} / {maxChars.toLocaleString()}
                    </span>
                </div>
                {isSubmitted && (
                    <span className="flex items-center gap-1 text-terminal-prompt font-semibold shrink-0">
                        <Check className="h-3 w-3" />
                        Submitted
                    </span>
                )}
            </div>
        </div>
    )
}
