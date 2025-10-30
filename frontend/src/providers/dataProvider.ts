import simpleRestProvider from 'ra-data-simple-rest';
import type { DataProvider } from 'react-admin';
import { getAuthToken } from './authProvider';

const API_URL = 'http://localhost:8000/api/v1';

// Базовый data provider от ra-data-simple-rest
const baseDataProvider = simpleRestProvider(API_URL);

// Расширенный data provider с JWT аутентификацией
export const dataProvider: DataProvider = {
  ...baseDataProvider,

  // Переопределяем методы для добавления JWT токена в заголовки
  getList: async (resource, params) => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const url = `${API_URL}/admin/${resource}`;
    const page = params.pagination?.page || 1;
    const perPage = params.pagination?.perPage || 10;
    const field = params.sort?.field || 'id';
    const order = params.sort?.order || 'ASC';

    // Формируем query параметры
    const query = {
      _sort: field,
      _order: order,
      _start: (page - 1) * perPage,
      _end: page * perPage,
      ...params.filter,
    };

    const response = await fetch(
      `${url}?${new URLSearchParams(query as Record<string, string>)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    return {
      data: data.items || data,
      total: data.total || data.length,
    };
  },

  getOne: async (resource, params) => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const url = `${API_URL}/admin/${resource}/${params.id}`;

    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    return { data };
  },

  getMany: async (resource, params) => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Для простоты делаем множественные запросы
    // В production можно оптимизировать через batch endpoint
    const requests = params.ids.map((id) =>
      fetch(`${API_URL}/admin/${resource}/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
    );

    const responses = await Promise.all(requests);
    const data = await Promise.all(responses.map((r) => r.json()));

    return { data };
  },

  getManyReference: async (resource, params) => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const page = params.pagination?.page || 1;
    const perPage = params.pagination?.perPage || 10;
    const field = params.sort?.field || 'id';
    const order = params.sort?.order || 'ASC';

    const query = {
      _sort: field,
      _order: order,
      _start: (page - 1) * perPage,
      _end: page * perPage,
      [params.target]: params.id,
      ...params.filter,
    };

    const url = `${API_URL}/admin/${resource}`;
    const response = await fetch(
      `${url}?${new URLSearchParams(query as Record<string, string>)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    return {
      data: data.items || data,
      total: data.total || data.length,
    };
  },

  create: async (resource, params) => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const url = `${API_URL}/admin/${resource}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(params.data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    return { data };
  },

  update: async (resource, params) => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const url = `${API_URL}/admin/${resource}/${params.id}`;

    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(params.data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    return { data };
  },

  updateMany: async (resource, params) => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Для простоты делаем множественные запросы
    const requests = params.ids.map((id) =>
      fetch(`${API_URL}/admin/${resource}/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(params.data),
      })
    );

    await Promise.all(requests);

    return { data: params.ids };
  },

  delete: async (resource, params) => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const url = `${API_URL}/admin/${resource}/${params.id}`;

    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    // Backend возвращает удалённый объект или success message
    const data = await response.json().catch(() => ({ id: params.id }));

    return { data: data.id ? data : { id: params.id } };
  },

  deleteMany: async (resource, params) => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Для простоты делаем множественные запросы
    const requests = params.ids.map((id) =>
      fetch(`${API_URL}/admin/${resource}/${id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
    );

    await Promise.all(requests);

    return { data: params.ids };
  },
};

// Вспомогательная функция для custom API запросов
export const apiRequest = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error('No authentication token found');
  }

  const url = endpoint.startsWith('http')
    ? endpoint
    : `${API_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response;
};
