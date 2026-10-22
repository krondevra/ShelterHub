import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api, tokenStorage, setUnauthorizedHandler } from '../api/client';
import { decodeJwt } from '../api/jwt';
import { useMutation } from './useQuery';

const AuthContext = createContext(null);

// `exp` is in seconds (standard JWT claim); Date.now() is in milliseconds.
function userFromToken(token) {
  if (!token) return null;
  const payload = decodeJwt(token);
  if (!payload?.sub || !payload?.role) return null;
  if (typeof payload.exp === 'number' && payload.exp * 1000 <= Date.now()) return null;
  return { id: payload.sub, role: payload.role };
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const token = tokenStorage.get();
    const initialUser = userFromToken(token);
    // Token present but rejected (expired or malformed): stop carrying it around.
    if (token && !initialUser) tokenStorage.clear();
    return initialUser;
  });

  const logout = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
  }, []);

  // Backend rejected/expired our token on some request; drop client-side state too.
  useEffect(() => {
    setUnauthorizedHandler(logout);
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  const login = useMutation(async ({ email, password }) => {
    const { access_token } = await api.post('/auth/login', { email, password }, { auth: false });
    tokenStorage.set(access_token);
    const nextUser = userFromToken(access_token);
    setUser(nextUser);
    return nextUser;
  });

  const register = useMutation(async ({ email, password, role }) => {
    return api.post('/auth/register', { email, password, role }, { auth: false });
  });

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      login: login.run,
      loginLoading: login.loading,
      loginError: login.error,
      register: register.run,
      registerLoading: register.loading,
      registerError: register.error,
      logout,
    }),
    [user, login.run, login.loading, login.error, register.run, register.loading, register.error, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
