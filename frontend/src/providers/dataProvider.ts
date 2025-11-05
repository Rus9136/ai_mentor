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

    // Специальная обработка для schools - backend не поддерживает query параметры
    // Выполняем client-side pagination, sorting и filtering
    if (resource === 'schools') {
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      let data = await response.json();

      // Client-side filtering
      if (params.filter) {
        // Фильтр по статусу (is_active)
        if (params.filter.is_active !== undefined) {
          data = data.filter(
            (item: any) => item.is_active === params.filter.is_active
          );
        }

        // Фильтр по поиску (q) - поиск по названию и коду
        if (params.filter.q) {
          const searchTerm = params.filter.q.toLowerCase();
          data = data.filter(
            (item: any) =>
              item.name.toLowerCase().includes(searchTerm) ||
              item.code.toLowerCase().includes(searchTerm)
          );
        }
      }

      // Client-side sorting
      data.sort((a: any, b: any) => {
        const aValue = a[field];
        const bValue = b[field];

        if (aValue === bValue) return 0;

        let comparison = 0;
        if (aValue === null || aValue === undefined) {
          comparison = 1;
        } else if (bValue === null || bValue === undefined) {
          comparison = -1;
        } else if (typeof aValue === 'string' && typeof bValue === 'string') {
          comparison = aValue.localeCompare(bValue);
        } else {
          comparison = aValue < bValue ? -1 : 1;
        }

        return order === 'ASC' ? comparison : -comparison;
      });

      // Client-side pagination
      const start = (page - 1) * perPage;
      const end = page * perPage;
      const paginatedData = data.slice(start, end);

      return {
        data: paginatedData,
        total: data.length,
      };
    }

    // Специальная обработка для chapters - используем nested endpoint
    if (resource === 'chapters') {
      // Для chapters требуется textbook_id в filter
      // Если filter undefined или textbook_id отсутствует, возвращаем пустой список
      if (!params.filter || !params.filter.textbook_id) {
        return { data: [], total: 0 };
      }

      const textbookId = params.filter.textbook_id;
      const chaptersUrl = `${API_URL}/admin/global/textbooks/${textbookId}/chapters`;
      const response = await fetch(chaptersUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      let data = await response.json();

      // Client-side filtering по поиску
      if (params.filter.q) {
        const searchTerm = params.filter.q.toLowerCase();
        data = data.filter((item: any) =>
          item.title.toLowerCase().includes(searchTerm)
        );
      }

      // Client-side sorting
      data.sort((a: any, b: any) => {
        const aValue = a[field];
        const bValue = b[field];
        if (aValue === bValue) return 0;
        let comparison = 0;
        if (aValue === null || aValue === undefined) {
          comparison = 1;
        } else if (bValue === null || bValue === undefined) {
          comparison = -1;
        } else if (typeof aValue === 'string' && typeof bValue === 'string') {
          comparison = aValue.localeCompare(bValue);
        } else {
          comparison = aValue < bValue ? -1 : 1;
        }
        return order === 'ASC' ? comparison : -comparison;
      });

      // Client-side pagination
      const start = (page - 1) * perPage;
      const end = page * perPage;
      const paginatedData = data.slice(start, end);

      return {
        data: paginatedData,
        total: data.length,
      };
    }

    // Специальная обработка для paragraphs - используем nested endpoint
    if (resource === 'paragraphs') {
      // Для paragraphs требуется chapter_id в filter
      // Если filter undefined или chapter_id отсутствует, возвращаем пустой список
      if (!params.filter || !params.filter.chapter_id) {
        return { data: [], total: 0 };
      }

      const chapterId = params.filter.chapter_id;
      const paragraphsUrl = `${API_URL}/admin/global/chapters/${chapterId}/paragraphs`;
      const response = await fetch(paragraphsUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      let data = await response.json();

      // Client-side filtering по поиску
      if (params.filter.q) {
        const searchTerm = params.filter.q.toLowerCase();
        data = data.filter((item: any) =>
          item.title.toLowerCase().includes(searchTerm)
        );
      }

      // Client-side sorting
      data.sort((a: any, b: any) => {
        const aValue = a[field];
        const bValue = b[field];
        if (aValue === bValue) return 0;
        let comparison = 0;
        if (aValue === null || aValue === undefined) {
          comparison = 1;
        } else if (bValue === null || bValue === undefined) {
          comparison = -1;
        } else if (typeof aValue === 'string' && typeof bValue === 'string') {
          comparison = aValue.localeCompare(bValue);
        } else {
          comparison = aValue < bValue ? -1 : 1;
        }
        return order === 'ASC' ? comparison : -comparison;
      });

      // Client-side pagination
      const start = (page - 1) * perPage;
      const end = page * perPage;
      const paginatedData = data.slice(start, end);

      return {
        data: paginatedData,
        total: data.length,
      };
    }

    // Специальная обработка для textbooks и tests - backend не поддерживает query параметры
    // Выполняем client-side pagination, sorting и filtering
    if (resource === 'textbooks' || resource === 'tests') {
      const globalUrl = `${API_URL}/admin/global/${resource}`;
      const response = await fetch(globalUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      let data = await response.json();

      // Client-side filtering
      if (params.filter) {
        if (resource === 'textbooks') {
          // Фильтр по предмету
          if (params.filter.subject) {
            data = data.filter(
              (item: any) => item.subject === params.filter.subject
            );
          }

          // Фильтр по классу
          if (params.filter.grade_level) {
            data = data.filter(
              (item: any) => item.grade_level === parseInt(params.filter.grade_level)
            );
          }

          // Фильтр по поиску (q) - поиск по названию
          if (params.filter.q) {
            const searchTerm = params.filter.q.toLowerCase();
            data = data.filter((item: any) =>
              item.title.toLowerCase().includes(searchTerm)
            );
          }
        }

        if (resource === 'tests') {
          // Фильтр по поиску (q) - поиск по названию
          if (params.filter.q) {
            const searchTerm = params.filter.q.toLowerCase();
            data = data.filter((item: any) =>
              item.title.toLowerCase().includes(searchTerm)
            );
          }

          // Фильтр по сложности
          if (params.filter.difficulty) {
            data = data.filter(
              (item: any) => item.difficulty === params.filter.difficulty
            );
          }
        }
      }

      // Client-side sorting
      data.sort((a: any, b: any) => {
        const aValue = a[field];
        const bValue = b[field];

        if (aValue === bValue) return 0;

        let comparison = 0;
        if (aValue === null || aValue === undefined) {
          comparison = 1;
        } else if (bValue === null || bValue === undefined) {
          comparison = -1;
        } else if (typeof aValue === 'string' && typeof bValue === 'string') {
          comparison = aValue.localeCompare(bValue);
        } else {
          comparison = aValue < bValue ? -1 : 1;
        }

        return order === 'ASC' ? comparison : -comparison;
      });

      // Client-side pagination
      const start = (page - 1) * perPage;
      const end = page * perPage;
      const paginatedData = data.slice(start, end);

      return {
        data: paginatedData,
        total: data.length,
      };
    }

    // Стандартная обработка для других resources
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

    // Специальная обработка для textbooks, tests, chapters, paragraphs - используем global endpoint
    let url = `${API_URL}/admin/${resource}/${params.id}`;
    if (resource === 'textbooks' || resource === 'tests' || resource === 'chapters' || resource === 'paragraphs') {
      url = `${API_URL}/admin/global/${resource}/${params.id}`;
    }

    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Для tests: автоматически вычисляем textbook_id из chapter_id
    if (resource === 'tests' && data.chapter_id) {
      try {
        const chapterResponse = await fetch(
          `${API_URL}/admin/global/chapters/${data.chapter_id}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        if (chapterResponse.ok) {
          const chapter = await chapterResponse.json();
          data.textbook_id = chapter.textbook_id;
        }
      } catch (error) {
        console.warn('Failed to fetch chapter for textbook_id:', error);
        // Не критично - просто не будет textbook_id
      }
    }

    return { data };
  },

  getMany: async (resource, params) => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Определяем базовый URL в зависимости от ресурса
    // Для textbooks, tests, chapters, paragraphs используем global endpoint
    const useGlobalEndpoint = ['textbooks', 'tests', 'chapters', 'paragraphs'].includes(resource);
    const baseUrl = useGlobalEndpoint ? `${API_URL}/admin/global` : `${API_URL}/admin`;

    // Для простоты делаем множественные запросы
    // В production можно оптимизировать через batch endpoint
    const requests = params.ids.map((id) =>
      fetch(`${baseUrl}/${resource}/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }).then(async (response) => {
        // Проверяем статус ответа
        if (!response.ok) {
          console.warn(`Failed to fetch ${resource} with id ${id}: ${response.status}`);
          return null; // Возвращаем null для ненайденных ресурсов
        }
        return response.json();
      }).catch((error) => {
        console.error(`Error fetching ${resource} with id ${id}:`, error);
        return null; // Возвращаем null при ошибке
      })
    );

    const responses = await Promise.all(requests);

    // Фильтруем null значения (ресурсы, которые не удалось загрузить)
    const data = responses.filter((item) => item !== null);

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

    // Специальная обработка для textbooks и tests - используем global endpoint
    let url = `${API_URL}/admin/${resource}`;
    if (resource === 'textbooks' || resource === 'tests') {
      url = `${API_URL}/admin/global/${resource}`;
    }

    // Для tests: удаляем textbook_id из данных (backend его не знает)
    let dataToSend = params.data;
    if (resource === 'tests') {
      const { textbook_id, ...restData } = params.data;
      dataToSend = restData;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(dataToSend),
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

    // Специальная обработка для textbooks и tests - используем global endpoint
    let url = `${API_URL}/admin/${resource}/${params.id}`;
    if (resource === 'textbooks' || resource === 'tests') {
      url = `${API_URL}/admin/global/${resource}/${params.id}`;
    }

    // Для tests: удаляем textbook_id из данных (backend его не знает)
    let dataToSend = params.data;
    if (resource === 'tests') {
      const { textbook_id, ...restData } = params.data;
      dataToSend = restData;
    }

    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(dataToSend),
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

    // Специальная обработка для textbooks и tests - используем global endpoint
    let url = `${API_URL}/admin/${resource}/${params.id}`;
    if (resource === 'textbooks' || resource === 'tests') {
      url = `${API_URL}/admin/global/${resource}/${params.id}`;
    }

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
