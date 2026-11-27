import type { HighlighterCore, ThemedToken } from 'shiki/core'

const LANG_ALIASES: Record<string, string> = {
    py: 'python',
    python: 'python',
    sh: 'bash',
    shell: 'bash',
    bash: 'bash',
    console: 'bash',
    csv: 'csv',
    json: 'json',
}

const THEME = 'github-dark-default'

let highlighterPromise: Promise<HighlighterCore> | null = null

const loadHighlighter = (): Promise<HighlighterCore> => {
    highlighterPromise ??= (async () => {
        const [{ createHighlighterCore }, { createJavaScriptRegexEngine }] = await Promise.all([
            import('shiki/core'),
            import('shiki/engine/javascript'),
        ])
        return createHighlighterCore({
            themes: [import('@shikijs/themes/github-dark-default')],
            langs: [
                import('@shikijs/langs/python'),
                import('@shikijs/langs/bash'),
                import('@shikijs/langs/csv'),
                import('@shikijs/langs/json'),
            ],
            engine: createJavaScriptRegexEngine(),
        })
    })()
    return highlighterPromise
}

export const resolveLanguage = (language: string | null): string | null =>
    language ? LANG_ALIASES[language.toLowerCase()] ?? null : null

export const highlightTokens = async (code: string, language: string): Promise<ThemedToken[][]> => {
    const highlighter = await loadHighlighter()
    return highlighter.codeToTokensBase(code, { lang: language, theme: THEME })
}
