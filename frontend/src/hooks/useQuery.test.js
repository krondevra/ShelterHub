import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useQuery } from './useQuery';

// Returns a fetcher plus a `resolve`/`reject` pair so a test can control
// exactly when a given call settles.
function deferredFetcher() {
  const calls = [];
  const fetcher = vi.fn(() => {
    let resolve, reject;
    const promise = new Promise((res, rej) => {
      resolve = res;
      reject = rej;
    });
    calls.push({ promise, resolve, reject });
    return promise;
  });
  return { fetcher, calls };
}

describe('useQuery', () => {
  it('is loading with no data before the first fetch resolves', () => {
    const { fetcher } = deferredFetcher();
    const { result } = renderHook(() => useQuery(fetcher));

    expect(result.current.loading).toBe(true);
    expect(result.current.refreshing).toBe(false);
    expect(result.current.data).toBeNull();
  });

  it('is not loading once the first fetch resolves', async () => {
    const { fetcher, calls } = deferredFetcher();
    const { result } = renderHook(() => useQuery(fetcher));

    await act(async () => calls[0].resolve(['a']));

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toEqual(['a']);
  });

  it('keeps showing old data during a refetch instead of clearing it', async () => {
    const { fetcher, calls } = deferredFetcher();
    const { result } = renderHook(() => useQuery(fetcher));
    await act(async () => calls[0].resolve(['a']));

    act(() => {
      result.current.refetch();
    });

    // A second (pending) call now exists; data from the first call is retained.
    expect(result.current.loading).toBe(false);
    expect(result.current.refreshing).toBe(true);
    expect(result.current.data).toEqual(['a']);

    await act(async () => calls[1].resolve(['a', 'b']));

    expect(result.current.refreshing).toBe(false);
    expect(result.current.data).toEqual(['a', 'b']);
  });

  it('keeps the old data and surfaces an error if a refetch fails', async () => {
    const { fetcher, calls } = deferredFetcher();
    const { result } = renderHook(() => useQuery(fetcher));
    await act(async () => calls[0].resolve(['a']));

    act(() => {
      result.current.refetch();
    });
    await act(async () => calls[1].reject(new Error('boom')));

    expect(result.current.data).toEqual(['a']);
    expect(result.current.error).toBe('boom');
    expect(result.current.refreshing).toBe(false);
    expect(result.current.loading).toBe(false);
  });

  it('does not fetch when skip is true', () => {
    const { fetcher } = deferredFetcher();
    const { result } = renderHook(() => useQuery(fetcher, { skip: true }));

    expect(fetcher).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });

  it('only keeps the latest in-flight request (stale responses are ignored)', async () => {
    const { fetcher, calls } = deferredFetcher();
    const { result } = renderHook(() => useQuery(fetcher));
    await act(async () => calls[0].resolve(['a']));

    act(() => {
      result.current.refetch();
      result.current.refetch();
    });

    // The first of the two overlapping refetches resolves late...
    await act(async () => calls[1].resolve(['stale']));
    expect(result.current.data).toEqual(['a']); // ...and is ignored.

    await act(async () => calls[2].resolve(['fresh']));
    await waitFor(() => expect(result.current.data).toEqual(['fresh']));
  });
});
