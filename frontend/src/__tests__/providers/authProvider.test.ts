import { describe, it, expect, beforeEach, vi } from 'vitest';
import { authProvider, getAuthToken, isSuperAdmin } from '../../providers/authProvider';
import { UserRole } from '../../types';

// Mock fetch globally
global.fetch = vi.fn();

describe('authProvider', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Reset fetch mock
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('should login successfully with valid credentials', async () => {
      const mockResponse = {
        access_token: 'test_access_token',
        refresh_token: 'test_refresh_token',
        token_type: 'bearer',
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await authProvider.login({ username: 'test@example.com', password: 'password123' });

      // Check that tokens are saved
      expect(localStorage.getItem('access_token')).toBe('test_access_token');
      expect(localStorage.getItem('refresh_token')).toBe('test_refresh_token');

      // Check that fetch was called correctly
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/auth/login',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: 'test@example.com', password: 'password123' }),
        }
      );
    });

    it('should throw error with invalid credentials', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      await expect(
        authProvider.login({ username: 'invalid@example.com', password: 'wrong' })
      ).rejects.toThrow('Invalid email or password');

      // Tokens should not be saved
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });

    it('should handle network errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      await expect(
        authProvider.login({ username: 'test@example.com', password: 'password123' })
      ).rejects.toThrow('Network error');
    });
  });

  describe('logout', () => {
    it('should remove tokens and user from localStorage', async () => {
      // Set tokens and user
      localStorage.setItem('access_token', 'test_token');
      localStorage.setItem('refresh_token', 'test_refresh');
      localStorage.setItem('user', JSON.stringify({ id: 1, email: 'test@example.com' }));

      await authProvider.logout({});

      // All should be removed
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });

    it('should resolve even if nothing to remove', async () => {
      // No tokens in localStorage
      await expect(authProvider.logout({})).resolves.toBeUndefined();
    });
  });

  describe('checkAuth', () => {
    it('should resolve if access_token exists', async () => {
      localStorage.setItem('access_token', 'test_token');

      await expect(authProvider.checkAuth({})).resolves.toBeUndefined();
    });

    it('should reject if access_token does not exist', async () => {
      await expect(authProvider.checkAuth({})).rejects.toBeUndefined();
    });
  });

  describe('checkError', () => {
    it('should reject and clear tokens on 401 error', async () => {
      localStorage.setItem('access_token', 'test_token');
      localStorage.setItem('refresh_token', 'test_refresh');
      localStorage.setItem('user', JSON.stringify({ id: 1 }));

      await expect(authProvider.checkError({ status: 401 })).rejects.toBeUndefined();

      // Tokens should be cleared
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });

    it('should reject and clear tokens on 403 error', async () => {
      localStorage.setItem('access_token', 'test_token');

      await expect(authProvider.checkError({ status: 403 })).rejects.toBeUndefined();

      expect(localStorage.getItem('access_token')).toBeNull();
    });

    it('should resolve on non-auth errors', async () => {
      localStorage.setItem('access_token', 'test_token');

      await expect(authProvider.checkError({ status: 500 })).resolves.toBeUndefined();

      // Token should still exist
      expect(localStorage.getItem('access_token')).toBe('test_token');
    });
  });

  describe('getIdentity', () => {
    it('should return cached user if available', async () => {
      const cachedUser = {
        id: 1,
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
        role: 'admin',
      };
      localStorage.setItem('user', JSON.stringify(cachedUser));

      const identity = await authProvider.getIdentity!({});

      expect(identity).toEqual({
        ...cachedUser,
        fullName: 'Test User',
        avatar: undefined,
      });

      // fetch should not be called
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should fetch user from API if not cached', async () => {
      localStorage.setItem('access_token', 'test_token');

      const mockUser = {
        id: 1,
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
        role: 'admin',
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      });

      const identity = await authProvider.getIdentity!({});

      expect(identity).toEqual({
        ...mockUser,
        fullName: 'Test User',
        avatar: undefined,
      });

      // User should be cached
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));

      // fetch should be called with correct params
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/auth/me', {
        headers: {
          Authorization: 'Bearer test_token',
        },
      });
    });

    it('should reject if no token available', async () => {
      await expect(authProvider.getIdentity!({})).rejects.toBeUndefined();
    });

    it('should reject if API returns error', async () => {
      localStorage.setItem('access_token', 'test_token');

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      await expect(authProvider.getIdentity!({})).rejects.toBeUndefined();
    });

    it('should use email as fullName if first_name or last_name missing', async () => {
      const cachedUser = {
        id: 1,
        email: 'test@example.com',
        role: 'admin',
      };
      localStorage.setItem('user', JSON.stringify(cachedUser));

      const identity = await authProvider.getIdentity!({});

      expect(identity.fullName).toBe('test@example.com');
    });
  });

  describe('getPermissions', () => {
    it('should return cached user role if available', async () => {
      const cachedUser = {
        id: 1,
        email: 'test@example.com',
        role: 'super_admin',
      };
      localStorage.setItem('user', JSON.stringify(cachedUser));

      const role = await authProvider.getPermissions!({});

      expect(role).toBe('super_admin');

      // fetch should not be called
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should fetch user from API if not cached', async () => {
      localStorage.setItem('access_token', 'test_token');

      const mockUser = {
        id: 1,
        email: 'test@example.com',
        role: 'admin',
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      });

      const role = await authProvider.getPermissions!({});

      expect(role).toBe('admin');

      // User should be cached
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
    });

    it('should reject if no token available', async () => {
      await expect(authProvider.getPermissions!({})).rejects.toBeUndefined();
    });
  });
});

describe('getAuthToken', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should return access_token if exists', () => {
    localStorage.setItem('access_token', 'test_token');
    expect(getAuthToken()).toBe('test_token');
  });

  it('should return null if no token exists', () => {
    expect(getAuthToken()).toBeNull();
  });
});

describe('isSuperAdmin', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should return true for SUPER_ADMIN role', async () => {
    const cachedUser = {
      id: 1,
      email: 'admin@test.com',
      role: UserRole.SUPER_ADMIN,
    };
    localStorage.setItem('user', JSON.stringify(cachedUser));

    const result = await isSuperAdmin();

    expect(result).toBe(true);
  });

  it('should return false for non-SUPER_ADMIN role', async () => {
    const cachedUser = {
      id: 1,
      email: 'admin@test.com',
      role: UserRole.ADMIN,
    };
    localStorage.setItem('user', JSON.stringify(cachedUser));

    const result = await isSuperAdmin();

    expect(result).toBe(false);
  });

  it('should return false if no user cached', async () => {
    const result = await isSuperAdmin();

    expect(result).toBe(false);
  });
});
