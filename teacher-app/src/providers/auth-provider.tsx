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
  googleAuth,
  getCurrentUser,
  logout as logoutApi,
  UserResponse,
} from '@/lib/api/auth';
import { getAccessToken } from '@/lib/api/client';

interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (idToken: string) => Promise<{ success: boolean; error?: string }>;
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

  // Redirect logic
  useEffect(() => {
    if (isLoading) return;

    const isAuthPage = pathname === '/login';

    if (!user && !isAuthPage) {
      router.replace('/login');
    } else if (user && isAuthPage) {
      router.replace('/');
    }
  }, [user, isLoading, pathname, router]);

  const login = async (idToken: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await googleAuth(idToken);
      setUser(response.user as unknown as UserResponse);
      return { success: true };
    } catch (error: unknown) {
      if (error instanceof Error && error.message === 'ACCESS_DENIED') {
        return { success: false, error: 'ACCESS_DENIED' };
      }
      return { success: false, error: 'LOGIN_ERROR' };
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
        login,
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
