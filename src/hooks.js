import { useEffect } from 'react'

// Run `fn` immediately and then every `ms` milliseconds, cleaning up on unmount.
// `fn` should be a stable callback (wrap it in useCallback). Used to keep lists fresh
// without a manual reload (enrollment approval, join requests, announcements, dashboard).
export function usePoll(fn, ms) {
  useEffect(() => {
    fn()
    const timer = setInterval(fn, ms)
    return () => clearInterval(timer)
  }, [fn, ms])
}
