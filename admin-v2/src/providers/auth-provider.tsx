'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { authApi } from '@/lib/api/auth';
import type { User, UserRole } from '@/types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isSuperAdmin: boolean;
  isSchoolAdmin: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const PUBLIC_PATHS = ['/login'];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Get locale from pathname
  const locale = pathname.split('/')[1] || 'ru';

  // Check if current path is public
  const isPublicPath = PUBLIC_PATHS.some((path) =>
    pathname.endsWith(path) || pathname.includes(`${path}/`)
  );

  const initAuth = useCallback(async () => {
    const token = localStorage.getItem('access_token');

    if (!token) {
      setIsLoading(false);
      if (!isPublicPath) {
        router.push(`/${locale}/login`);
      }
      return;
    }

    try {
      const userData = await authApi.getMe();
      setUser(userData);
    } catch (error) {
      console.error('Auth init error:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      if (!isPublicPath) {
        router.push(`/${locale}/login`);
      }
    } finally {
      setIsLoading(false);
    }
  }, [locale, isPublicPath, router]);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  const login = async (email: string, password: string) => {
    const tokenResponse = await authApi.login({ email, password });

    localStorage.setItem('access_token', tokenResponse.access_token);
    localStorage.setItem('refresh_token', tokenResponse.refresh_token);

    const userData = await authApi.getMe();
    setUser(userData);

    router.push(`/${locale}`);
  };

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    router.push(`/${locale}/login`);
  }, [locale, router]);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    isSuperAdmin: user?.role === 'super_admin',
    isSchoolAdmin: user?.role === 'admin',
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Hook to check if user has specific role(s)
export function useHasRole(roles: UserRole | UserRole[]) {
  const { user } = useAuth();
  const roleArray = Array.isArray(roles) ? roles : [roles];
  return user ? roleArray.includes(user.role) : false;
}
