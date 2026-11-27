import { useEffect, useState } from 'react'
import type { ThemedToken } from 'shiki/core'
import { Check, Copy } from 'lucide-react'
import { highlightTokens, resolveLanguage } from '@/lib/highlight'
import { cn } from '@/lib/utils'

const LANGUAGE_LABELS: Record<string, string> = {
    python: 'Python',
    bash: 'Terminal',
    csv: 'CSV',
    json: 'JSON',
    text: 'Text',
}

interface CodeBlockProps {
    code: string
    language: string | null
    className?: string
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ code, language, className }) => {
    const grammar = resolveLanguage(language)
    const [highlighted, setHighlighted] = useState<{ code: string; lines: ThemedToken[][] } | null>(null)
    const [copied, setCopied] = useState(false)
    const lines = highlighted?.code === code ? highlighted.lines : null

    useEffect(() => {
        if (!grammar) return
        let isCancelled = false
        highlightTokens(code, grammar)
            .then((result) => {
                if (!isCancelled) setHighlighted({ code, lines: result })
            })
            .catch(() => undefined)
        return () => {
            isCancelled = true
        }
    }, [code, grammar])

    const handleCopy = async (): Promise<void> => {
        try {
            await navigator.clipboard.writeText(code)
            setCopied(true)
            setTimeout(() => setCopied(false), 1500)
        } catch {
            setCopied(false)
        }
    }

    const label = LANGUAGE_LABELS[grammar ?? language?.toLowerCase() ?? ''] ?? 'Code'

    return (
        <figure className={cn('group/code my-5 overflow-hidden rounded-xl border border-terminal-border bg-terminal', className)}>
            <figcaption className="flex items-center justify-between gap-2 pl-4 pr-1 border-b border-terminal-border/70">
                <span className="font-terminal text-[11px] font-semibold uppercase tracking-wider text-terminal-muted">{label}</span>
                <button
                    type="button"
                    onClick={handleCopy}
                    aria-label={copied ? 'Copied' : `Copy ${label.toLowerCase()} code`}
                    className="inline-flex items-center gap-1.5 min-h-11 sm:min-h-9 px-3 rounded-md font-sans text-xs font-medium text-terminal-muted hover:text-terminal-fg hover:bg-terminal-border/60 transition duration-200 ease-in-out cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-terminal-prompt/60"
                >
                    {copied ? <Check className="size-3.5 text-terminal-prompt" /> : <Copy className="size-3.5" />}
                    {copied ? 'Copied' : 'Copy'}
                </button>
            </figcaption>
            <pre className="p-4 font-terminal text-[13px] leading-6 text-terminal-fg overflow-x-auto">
                <code>
                    {lines
                        ? lines.map((line, lineIndex) => (
                            <span key={lineIndex} className="block min-h-6">
                                {line.map((token, tokenIndex) => (
                                    <span key={tokenIndex} style={{ color: token.color }}>{token.content}</span>
                                ))}
                            </span>
                        ))
                        : code}
                </code>
            </pre>
        </figure>
    )
}
