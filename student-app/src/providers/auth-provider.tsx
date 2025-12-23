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
  loginWithPassword as loginWithPasswordApi,
  UserResponse,
} from '@/lib/api/auth';
import { getAccessToken } from '@/lib/api/client';

interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  requiresOnboarding: boolean;
  login: (idToken: string) => Promise<boolean>;
  loginWithPassword: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  setRequiresOnboarding: (value: boolean) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [requiresOnboarding, setRequiresOnboarding] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const isAuthenticated = !!user && !requiresOnboarding;

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

        // If user has no school_id, check if they skipped onboarding
        if (!userData.school_id && userData.role === 'student') {
          const skippedOnboarding = typeof window !== 'undefined'
            ? localStorage.getItem('ai_mentor_skipped_onboarding') === 'true'
            : false;

          if (!skippedOnboarding) {
            setRequiresOnboarding(true);
          }
        }
      } catch {
        // Token invalid, clear and redirect
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
    const isOnboardingPage = pathname.startsWith('/onboarding');

    if (!user && !isAuthPage && !isOnboardingPage) {
      router.replace('/login');
    } else if (user && requiresOnboarding && !isOnboardingPage) {
      router.replace('/onboarding');
    } else if (user && !requiresOnboarding && (isAuthPage || isOnboardingPage)) {
      router.replace('/');
    }
  }, [user, isLoading, requiresOnboarding, pathname, router]);

  const login = async (idToken: string): Promise<boolean> => {
    try {
      const response = await googleAuth(idToken);
      setUser(response.user as unknown as UserResponse);

      if (response.requires_onboarding) {
        setRequiresOnboarding(true);
        return true;
      }

      return true;
    } catch {
      return false;
    }
  };

  const loginWithPassword = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      await loginWithPasswordApi({ email, password });
      const userData = await getCurrentUser();

      // Only allow students
      if (userData.role !== 'student') {
        logoutApi();
        return { success: false, error: 'ACCESS_DENIED' };
      }

      setUser(userData);

      // Check if onboarding is required
      if (!userData.school_id) {
        const skippedOnboarding = typeof window !== 'undefined'
          ? localStorage.getItem('ai_mentor_skipped_onboarding') === 'true'
          : false;

        if (!skippedOnboarding) {
          setRequiresOnboarding(true);
        }
      }

      return { success: true };
    } catch (error) {
      // Extract error message from API response
      const axiosError = error as { response?: { data?: { detail?: string } } };
      const errorMessage = axiosError.response?.data?.detail || 'INVALID_CREDENTIALS';
      return { success: false, error: errorMessage };
    }
  };

  const logout = () => {
    logoutApi();
    // Clear skipped onboarding flag
    if (typeof window !== 'undefined') {
      localStorage.removeItem('ai_mentor_skipped_onboarding');
    }
    setUser(null);
    setRequiresOnboarding(false);
    router.replace('/login');
  };

  const refreshUser = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);

      if (userData.school_id) {
        setRequiresOnboarding(false);
      }
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
        requiresOnboarding,
        login,
        loginWithPassword,
        logout,
        refreshUser,
        setRequiresOnboarding,
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
