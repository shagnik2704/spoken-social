import { useEffect, useState } from 'react'

/**
 * Returns a debounced copy of `value` that only updates after `delay` ms of no changes.
 * Used to keep search inputs feeling instant while firing at most one request per pause,
 * instead of one request per keystroke.
 */
export function useDebouncedValue<T>(value: T, delay = 400): T {
    const [debounced, setDebounced] = useState(value)

    useEffect(() => {
        const t = setTimeout(() => setDebounced(value), delay)
        return () => clearTimeout(t) // typing again cancels the pending update
    }, [value, delay])

    return debounced
}
