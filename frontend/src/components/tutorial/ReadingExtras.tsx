import { BookMarked, ChevronDown, Library } from 'lucide-react'
import ReactMarkdown, { type Components } from 'react-markdown'
import { normalizeReadMore } from '@/lib/learnerPack'
import { READING_COMPONENTS } from './readingMarkdown'

interface ReadingExtrasProps {
    keyTerms?: { term: string; meaning: string }[] | null
    readMore?: unknown[] | null
    keyTermsTitle?: string
}

const INLINE_COMPONENTS: Components = { ...READING_COMPONENTS, p: ({ ...props }) => <span {...props} /> }

export const ReadingExtras: React.FC<ReadingExtrasProps> = ({ keyTerms, readMore, keyTermsTitle = 'Key terms' }) => {
    const terms = (keyTerms ?? []).filter(item => item.term && item.meaning)
    const suggestions = normalizeReadMore(readMore)
    if (terms.length === 0 && suggestions.length === 0) return null

    return (
        <div className="mt-10 space-y-8">
            {terms.length > 0 && (
                <details className="group rounded-xl border border-teal/25 bg-teal/[0.04] open:pb-4 transition-all duration-200 ease-in-out">
                    <summary className="flex items-center justify-between gap-3 min-h-11 px-4 sm:px-5 py-3 cursor-pointer list-none [&::-webkit-details-marker]:hidden rounded-xl hover:bg-teal/[0.06] transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                        <span className="flex items-center gap-2 text-sm font-bold text-teal">
                            <BookMarked className="size-4" />
                            {keyTermsTitle}
                            <span className="font-mono font-medium text-muted-foreground">({terms.length})</span>
                        </span>
                        <ChevronDown className="size-4 text-muted-foreground transition-transform duration-200 ease-in-out group-open:rotate-180" />
                    </summary>
                    <dl className="px-4 sm:px-5 pt-1 grid gap-3 sm:grid-cols-2">
                        {terms.map(item => (
                            <div key={item.term} className="rounded-lg bg-card border border-border/70 p-3">
                                <dt className="text-sm font-semibold text-foreground">{item.term}</dt>
                                <dd className="mt-1 text-sm leading-6 text-foreground/80">{item.meaning}</dd>
                            </div>
                        ))}
                    </dl>
                </details>
            )}
            {suggestions.length > 0 && (
                <section aria-labelledby="read-more-heading">
                    <h3 id="read-more-heading" className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-muted-foreground">
                        <Library className="size-4" />
                        Read more
                    </h3>
                    <ul className="mt-3 space-y-2.5">
                        {suggestions.map(text => (
                            <li key={text} className="pl-4 border-l-2 border-border text-sm leading-6 text-foreground/80">
                                <ReactMarkdown components={INLINE_COMPONENTS}>{text}</ReactMarkdown>
                            </li>
                        ))}
                    </ul>
                </section>
            )}
        </div>
    )
}
