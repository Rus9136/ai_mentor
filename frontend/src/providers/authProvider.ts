import type { AuthProvider } from 'react-admin';
import type { User, LoginRequest, LoginResponse } from '../types';
import { UserRole } from '../types';

const API_URL = 'http://localhost:8000/api/v1';

export const authProvider: AuthProvider = {
  // Вызывается при попытке входа пользователя
  login: async ({ username, password }: { username: string; password: string }) => {
    const request: LoginRequest = {
      email: username,
      password: password,
    };

    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Invalid email or password');
    }

    const data: LoginResponse = await response.json();

    // Сохраняем токены в localStorage
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    return Promise.resolve();
  },

  // Вызывается при попытке выхода пользователя
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    return Promise.resolve();
  },

  // Вызывается при проверке аутентификации (при каждом переходе по маршруту)
  checkAuth: () => {
    const token = localStorage.getItem('access_token');
    return token ? Promise.resolve() : Promise.reject();
  },

  // Вызывается при возникновении ошибки API
  checkError: (error) => {
    const status = error.status;
    if (status === 401 || status === 403) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      return Promise.reject();
    }
    return Promise.resolve();
  },

  // Вызывается для получения данных о текущем пользователе
  getIdentity: async () => {
    let user: User;

    // Проверяем кеш
    const cachedUser = localStorage.getItem('user');
    if (cachedUser) {
      user = JSON.parse(cachedUser);
    } else {
      const token = localStorage.getItem('access_token');
      if (!token) {
        return Promise.reject();
      }

      const response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        return Promise.reject();
      }

      user = await response.json();

      // Кешируем пользователя
      localStorage.setItem('user', JSON.stringify(user));
    }

    // React Admin ожидает объект с id и fullName
    // Применяем трансформацию всегда (и для кэша, и для API)
    return Promise.resolve({
      ...user,
      fullName: user.first_name && user.last_name
        ? `${user.first_name} ${user.last_name}`
        : user.email,
      avatar: undefined,
    });
  },

  // Вызывается для получения прав доступа пользователя
  getPermissions: async () => {
    const cachedUser = localStorage.getItem('user');
    if (cachedUser) {
      const user: User = JSON.parse(cachedUser);
      return Promise.resolve(user.role);
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      return Promise.reject();
    }

    const response = await fetch(`${API_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      return Promise.reject();
    }

    const user: User = await response.json();
    localStorage.setItem('user', JSON.stringify(user));

    return Promise.resolve(user.role);
  },
};

// Вспомогательная функция для получения токена (используется в dataProvider)
export const getAuthToken = (): string | null => {
  return localStorage.getItem('access_token');
};

// Проверка, является ли пользователь SUPER_ADMIN
export const isSuperAdmin = async (): Promise<boolean> => {
  try {
    if (!authProvider.getPermissions) {
      return false;
    }
    const role = await authProvider.getPermissions({});
    return role === UserRole.SUPER_ADMIN;
  } catch {
    return false;
  }
};
