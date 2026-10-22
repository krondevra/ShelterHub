import { useCallback, useEffect, useRef, useState } from 'react';

// `fetcher` must be a stable function (defined with useCallback, or module-level).
// Pass `skip: true` to avoid firing the request (e.g. while waiting on auth state).
export function useQuery(fetcher, { skip = false } = {}) {
  const [state, setState] = useState({ data: null, loading: !skip, error: null });
  const lastRequest = useRef(0);

  const run = useCallback(async () => {
    const id = ++lastRequest.current;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await fetcher();
      if (id === lastRequest.current) setState({ data, loading: false, error: null });
    } catch (e) {
      if (id === lastRequest.current) {
        setState((s) => ({ ...s, loading: false, error: e.message }));
      }
    }
  }, [fetcher]);

  useEffect(() => {
    if (skip) return;
    run();
  }, [run, skip]);

  return { ...state, refetch: run };
}

// For POST/PATCH: `run()` resolves with the result and also rethrows on
// failure, so forms can await it in a try/catch; `loading`/`error` are
// available for inline rendering too.
export function useMutation(fn) {
  const [state, setState] = useState({ loading: false, error: null });

  const run = useCallback(
    async (...args) => {
      setState({ loading: true, error: null });
      try {
        const result = await fn(...args);
        setState({ loading: false, error: null });
        return result;
      } catch (e) {
        setState({ loading: false, error: e.message });
        throw e;
      }
    },
    [fn]
  );

  return { run, ...state };
}
