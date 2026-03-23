'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from 'react';
import { useRouter, usePathname } from '@/i18n/routing';
import {
  login as loginApi,
  getCurrentUser,
  logout as logoutApi,
  UserResponse,
} from '@/lib/api/auth';
import { getAccessToken, setTokens } from '@/lib/api/client';

interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (loginStr: string, password: string) => Promise<void>;
  loginWithToken: (token: string) => Promise<boolean>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const isAuthenticated = !!user;

  // Check auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = getAccessToken();
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const userData = await getCurrentUser();

        // Only allow teachers
        if (userData.role !== 'teacher') {
          logoutApi();
          setIsLoading(false);
          return;
        }

        setUser(userData);
      } catch {
        logoutApi();
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Handle WebView token from URL
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (token) {
      setTokens(token, '');
      // Remove token from URL for security
      const url = new URL(window.location.href);
      url.searchParams.delete('token');
      window.history.replaceState({}, '', url.toString());
      // Re-check auth with new token
      getCurrentUser().then((userData) => {
        if (userData.role === 'teacher') {
          setUser(userData);
        }
      }).catch(() => {});
    }
  }, []);

  // Redirect logic
  useEffect(() => {
    if (isLoading) return;

    const isAuthPage = pathname === '/login';
    const isWebViewPage = pathname.startsWith('/webview');

    if (!user && !isAuthPage && !isWebViewPage) {
      router.replace('/login');
    } else if (user && isAuthPage) {
      router.replace('/');
    }
  }, [user, isLoading, pathname, router]);

  const login = useCallback(async (loginStr: string, password: string) => {
    await loginApi({ login: loginStr, password });

    const userData = await getCurrentUser();

    // Only allow teachers
    if (userData.role !== 'teacher') {
      logoutApi();
      throw new Error('ACCESS_DENIED');
    }

    setUser(userData);
    router.replace('/');
  }, [router]);

  const loginWithToken = useCallback(async (token: string): Promise<boolean> => {
    try {
      setTokens(token, '');
      const userData = await getCurrentUser();
      if (userData.role !== 'teacher') {
        logoutApi();
        return false;
      }
      setUser(userData);
      return true;
    } catch {
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    logoutApi();
    setUser(null);
    router.replace('/login');
  }, [router]);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch {
      logout();
    }
  }, [logout]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        login,
        loginWithToken,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
