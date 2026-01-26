/**
 * Утилита для перевода ошибок API на русский язык
 */

/**
 * Словарь переводов стандартных HTTP статусов
 */
const HTTP_STATUS_TRANSLATIONS: Record<number, string> = {
  400: 'Неверный запрос',
  401: 'Требуется авторизация',
  403: 'Доступ запрещен',
  404: 'Запись не найдена',
  409: 'Конфликт данных (запись уже существует)',
  422: 'Ошибка валидации данных',
  500: 'Внутренняя ошибка сервера',
  502: 'Сервер недоступен',
  503: 'Сервис временно недоступен',
};

/**
 * Словарь переводов типичных ошибок валидации
 */
const VALIDATION_ERROR_PATTERNS: Array<{ pattern: RegExp; translation: string }> = [
  {
    pattern: /email.*already exists/i,
    translation: 'Пользователь с таким email уже существует',
  },
  {
    pattern: /code.*already exists/i,
    translation: 'Запись с таким кодом уже существует',
  },
  {
    pattern: /not found/i,
    translation: 'Запись не найдена',
  },
  {
    pattern: /invalid.*credentials/i,
    translation: 'Неверный email или пароль',
  },
  {
    pattern: /access denied/i,
    translation: 'Доступ запрещен',
  },
  {
    pattern: /required field/i,
    translation: 'Не заполнены обязательные поля',
  },
  {
    pattern: /Code must contain only uppercase letters/i,
    translation: 'Код может содержать только заглавные буквы, цифры, дефис и подчеркивание',
  },
];

/**
 * Переводит ошибку API на русский язык
 *
 * @param error - Объект ошибки или строка
 * @param status - HTTP статус код (опционально)
 * @returns Переведенное сообщение об ошибке
 */
export function translateError(error: any, status?: number): string {
  // Если это объект ошибки с detail
  let errorMessage = '';

  if (error && typeof error === 'object') {
    if (error.detail) {
      errorMessage = error.detail;
    } else if (error.message) {
      errorMessage = error.message;
    } else if (error.error) {
      errorMessage = error.error;
    }
  } else if (typeof error === 'string') {
    errorMessage = error;
  }

  // Пытаемся найти совпадение с известными паттернами ошибок
  for (const { pattern, translation } of VALIDATION_ERROR_PATTERNS) {
    if (pattern.test(errorMessage)) {
      return translation;
    }
  }

  // Если есть HTTP статус, используем его перевод
  if (status && HTTP_STATUS_TRANSLATIONS[status]) {
    // Если есть детальное сообщение, добавляем его
    if (errorMessage) {
      return `${HTTP_STATUS_TRANSLATIONS[status]}: ${errorMessage}`;
    }
    return HTTP_STATUS_TRANSLATIONS[status];
  }

  // Если не нашли перевод, возвращаем оригинальное сообщение
  return errorMessage || 'Произошла неизвестная ошибка';
}

/**
 * Обрабатывает ошибку fetch запроса
 *
 * @param response - Response объект от fetch
 * @returns Promise с переведенной ошибкой
 */
export async function handleFetchError(response: Response): Promise<never> {
  let errorData: any;

  try {
    errorData = await response.json();
  } catch {
    // Если не удалось распарсить JSON, используем текст ответа
    errorData = await response.text();
  }

  const translatedMessage = translateError(errorData, response.status);

  throw new Error(translatedMessage);
}
