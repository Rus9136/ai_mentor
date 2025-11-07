# E2E Tests для AI Mentor Admin Panel

Этот каталог содержит end-to-end тесты для админ панели AI Mentor, написанные на Playwright.

## Структура тестов

```
e2e/
├── helpers/
│   ├── auth.ts          # Утилиты для аутентификации (login, logout, waitForAPI)
│   └── test-data.ts     # Генераторы тестовых данных
├── super-admin/
│   ├── 01-login.spec.ts     # Тесты логина для SUPER_ADMIN
│   ├── 02-schools.spec.ts   # Тесты управления школами
│   ├── 03-textbooks.spec.ts # Тесты управления глобальными учебниками
│   └── 04-tests.spec.ts     # Тесты управления глобальными тестами
└── school-admin/
    ├── 01-login.spec.ts        # Тесты логина для School ADMIN
    ├── 02-students.spec.ts     # Тесты управления учениками
    ├── 03-classes.spec.ts      # Тесты управления классами
    └── 04-fork-textbook.spec.ts # Тесты кастомизации (fork) учебников
```

## Запуск тестов

### Все тесты (headless mode)
```bash
npm run test:e2e
```

### Тесты с UI (интерактивный режим)
```bash
npm run test:e2e:ui
```

### Тесты с видимым браузером
```bash
npm run test:e2e:headed
```

### Только SUPER_ADMIN тесты
```bash
npm run test:e2e:super-admin
```

### Только School ADMIN тесты
```bash
npm run test:e2e:school-admin
```

### Debug режим (step-by-step)
```bash
npm run test:e2e:debug
```

### Просмотр HTML отчета
```bash
npm run test:e2e:report
```

## Тестовые пользователи

### SUPER_ADMIN
- **Email:** `admin@test.com`
- **Password:** `admin123`
- **Доступ:** Управление школами, глобальными учебниками и тестами

### School ADMIN
- **Email:** `school.admin@test.com`
- **Password:** `admin123`
- **Доступ:** Управление пользователями школы, классами, школьными учебниками/тестами, кастомизация глобального контента

## Покрытие тестов

### SUPER_ADMIN (4 файла, ~40 тестов)
✅ **Login Flow**
- Отображение формы логина
- Успешная аутентификация
- Ошибка при неверных credentials
- Logout
- Сохранение сессии после reload
- Проверка меню для SUPER_ADMIN

✅ **Schools Management**
- Навигация к списку школ
- Создание новой школы
- Валидация обязательных полей
- Редактирование школы
- Удаление школы (soft delete)
- Блокировка/разблокировка школы
- Фильтрация по региону

✅ **Textbooks Management**
- Навигация к списку учебников
- Создание нового учебника
- Валидация полей
- Редактирование структуры (добавление глав)
- Фильтрация по предмету
- Поиск по названию
- Удаление учебника
- Просмотр деталей

✅ **Tests Management**
- Навигация к списку тестов
- Создание нового теста
- Валидация полей
- Добавление вопросов (SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER)
- Добавление опций к вопросам
- Редактирование метаданных теста
- Удаление теста
- Фильтрация по сложности

### School ADMIN (4 файла, ~35+ тестов)
✅ **Login Flow**
- Успешная аутентификация
- Проверка меню для School ADMIN
- Доступ к библиотеке
- Logout
- Сохранение сессии

✅ **Students Management**
- Навигация к списку учеников
- Создание нового ученика (transactional User → Student)
- Auto-generation student_code (STU{grade}{year}{sequence})
- Валидация полей
- Редактирование информации ученика
- Деактивация ученика
- Удаление ученика
- Фильтрация по классу
- Поиск по имени
- Просмотр деталей
- Bulk deactivate

✅ **Classes Management**
- Навигация к списку классов
- Создание нового класса
- Валидация полей
- Назначение учеников через Transfer List
- Удаление ученика из класса
- Назначение учителей
- Фильтрация по классу
- Просмотр деталей
- Удаление класса

✅ **Fork Textbook (Критически важный флоу)**
- Просмотр глобальных учебников (read-only)
- Отображение кнопки "Кастомизировать"
- Открытие dialog кастомизации
- Успешный fork учебника
- Копирование глав и параграфов
- Отображение forked учебника во вкладке "Наши учебники"
- Badge "Адаптировано из: {original}"
- Возможность редактирования forked учебника
- Запрет на редактирование глобальных учебников

## Браузеры

Тесты запускаются на следующих браузерах:
- ✅ Chromium (Desktop Chrome)
- ✅ Firefox (Desktop Firefox)
- ✅ WebKit (Desktop Safari)
- ✅ Mobile Chrome (Pixel 5)
- ✅ Mobile Safari (iPhone 12)

## CI/CD интеграция

Для запуска в CI окружении (GitHub Actions, GitLab CI):
```bash
# CI автоматически установит Playwright browsers
npx playwright install --with-deps

# Запуск тестов в CI режиме (с retry)
CI=true npm run test:e2e
```

## Debug и troubleshooting

### Просмотр traces
Если тест провалился, откройте trace viewer:
```bash
npx playwright show-trace trace.zip
```

### Запись видео
Видео автоматически записываются при провале теста (сохраняются в `test-results/`).

### Screenshots
Screenshots автоматически создаются при провале теста.

### Slow motion
Запуск тестов в slow motion для визуального debug:
```bash
npx playwright test --headed --slow-mo=1000
```

## Требования

### Backend API должен быть запущен
Убедитесь, что backend API работает на `http://localhost:8000`:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Тестовые пользователи созданы в БД
Используйте скрипты для создания тестовых пользователей:
```bash
cd backend
python create_superadmin.py  # Создать SUPER_ADMIN
python create_school_admin.py  # Создать School ADMIN
```

### Dev server запущен
Frontend dev server должен быть запущен на `http://localhost:5174` (или будет запущен автоматически).

## Добавление новых тестов

### 1. Создать новый spec файл
```typescript
import { test, expect } from '@playwright/test';
import { login, SUPER_ADMIN_USER } from '../helpers/auth';

test.describe('My New Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await login(page, SUPER_ADMIN_USER);
  });

  test('should do something', async ({ page }) => {
    // ... тест
  });
});
```

### 2. Использовать helpers
- `login(page, credentials)` - автоматический логин
- `logout(page)` - logout
- `waitForAPIResponse(page, urlPattern, method)` - ожидание API ответа
- `generateXData()` - генерация тестовых данных

### 3. Запустить тест
```bash
npm run test:e2e:debug
```

## Best Practices

1. **Всегда очищайте cookies** в `beforeEach`:
   ```typescript
   await page.context().clearCookies();
   ```

2. **Используйте явные ожидания**:
   ```typescript
   await page.waitForSelector('[role="grid"]', { timeout: 10000 });
   ```

3. **Используйте role-based селекторы**:
   ```typescript
   await page.getByRole('button', { name: /создать/i });
   ```

4. **Проверяйте visibility перед действиями**:
   ```typescript
   if (await button.isVisible({ timeout: 3000 }).catch(() => false)) {
     await button.click();
   }
   ```

5. **Используйте генераторы данных** для уникальности:
   ```typescript
   const studentData = generateStudentData(); // Генерирует уникальный email с timestamp
   ```

## Метрики

- **Всего тестов:** ~75+
- **SUPER_ADMIN:** ~40 тестов (4 файла)
- **School ADMIN:** ~35+ тестов (4 файла)
- **Покрытие:** Login, CRUD, Filters, Bulk Actions, Fork
- **Браузеры:** 5 (Desktop: Chrome, Firefox, Safari + Mobile: Chrome, Safari)
- **Среднее время выполнения:** ~5-10 минут (в зависимости от браузеров)

## Следующие шаги

После Фазы 1 (E2E тесты) будут добавлены:
- [ ] Unit тесты (Vitest) для authProvider, dataProvider
- [ ] Responsive тесты
- [ ] Accessibility тесты
- [ ] Performance тесты
