'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from 'react';
import { useRouter, usePathname } from '@/i18n/routing';
import {
  getCurrentUser,
  logout as logoutApi,
  loginWithPassword as loginWithPasswordApi,
  UserResponse,
} from '@/lib/api/auth';
import { getAccessToken, setTokens } from '@/lib/api/client';

interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  loginWithPassword: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
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
      // Remove token from URL
      const url = new URL(window.location.href);
      url.searchParams.delete('token');
      window.history.replaceState({}, '', url.toString());
      // Re-check auth
      getCurrentUser().then(setUser).catch(() => {});
    }
  }, []);

  // Redirect logic
  useEffect(() => {
    if (isLoading) return;

    const isAuthPage = pathname === '/login';
    const isPublicPage = pathname === '/' || pathname.startsWith('/webview');

    if (!user && !isAuthPage && !isPublicPage) {
      router.replace('/login');
    } else if (user && isAuthPage) {
      router.replace('/');
    }
  }, [user, isLoading, pathname, router]);

  const loginWithPassword = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      await loginWithPasswordApi({ email, password });
      const userData = await getCurrentUser();

      if (userData.role !== 'student') {
        logoutApi();
        return { success: false, error: 'ACCESS_DENIED' };
      }

      setUser(userData);
      return { success: true };
    } catch (error) {
      const axiosError = error as { response?: { data?: { detail?: string } } };
      return { success: false, error: axiosError.response?.data?.detail || 'INVALID_CREDENTIALS' };
    }
  };

  const loginWithToken = async (token: string): Promise<boolean> => {
    try {
      setTokens(token, '');
      const userData = await getCurrentUser();
      setUser(userData);
      return true;
    } catch {
      return false;
    }
  };

  const logout = () => {
    logoutApi();
    setUser(null);
    router.replace('/login');
  };

  const refreshUser = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch {
      logout();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        loginWithPassword,
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
