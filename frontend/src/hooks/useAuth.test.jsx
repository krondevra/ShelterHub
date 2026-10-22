import { renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { tokenStorage } from '../api/client';
import { AuthProvider, useAuth } from './useAuth';

function makeToken(payload) {
  const base64 = btoa(JSON.stringify(payload));
  const base64url = base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  return `header.${base64url}.signature`;
}

const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;

describe('useAuth / userFromToken expiry handling', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('treats a token with a future exp as logged in', () => {
    const token = makeToken({ sub: '1', role: 'adopter', exp: Math.floor(Date.now() / 1000) + 3600 });
    tokenStorage.set(token);

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual({ id: '1', role: 'adopter' });
  });

  it('treats a token with a past exp as logged out and clears it', () => {
    const token = makeToken({ sub: '1', role: 'adopter', exp: Math.floor(Date.now() / 1000) - 3600 });
    tokenStorage.set(token);

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(tokenStorage.get()).toBeNull();
  });

  it('treats a token with no exp claim as logged in (backend always sets one, but the field is optional here)', () => {
    const token = makeToken({ sub: '1', role: 'staff' });
    tokenStorage.set(token);

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(true);
  });

  it('treats a malformed token as logged out and clears it', () => {
    tokenStorage.set('not-a-real-jwt');

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(tokenStorage.get()).toBeNull();
  });

  it('stays logged out with no stored token', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(tokenStorage.get()).toBeNull();
  });
});
