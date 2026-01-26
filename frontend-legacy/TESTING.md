# Frontend Testing Instructions - Фаза 2 завершена ✅

## Серверы запущены

### Backend
- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Status:** ✅ Running

### Frontend
- **URL:** http://localhost:5174
- **Status:** ✅ Running

## Тестовый пользователь

Для тестирования аутентификации используйте:

```
Email: admin@test.com
Password: admin123
Role: SUPER_ADMIN
```

## Как протестировать

### 1. Открыть приложение в браузере

Откройте браузер и перейдите на:
```
http://localhost:5174
```

Вы увидите **login форму React Admin**.

### 2. Войти в систему

Введите:
- **Username:** `admin@test.com`
- **Password:** `admin123`

Нажмите **Sign in**

### 3. Что должно произойти

После успешного входа вы должны увидеть:
- ✅ Dashboard React Admin
- ✅ В левом меню появится "Schools" ресурс
- ✅ В правом верхнем углу - имя пользователя "Test Admin"

### 4. Проверить Schools список

Кликните на "Schools" в меню. Вы должны увидеть:
- ✅ Список школ из базы данных
- ✅ 3 школы: "Valid School", "Duplicate School", "Test School"
- ✅ Таблицу с колонками: id, name, code, is_active, email

### 5. Проверить Logout

Нажмите на имя пользователя в правом верхнем углу и выберите "Logout".
- ✅ Вы должны вернуться на login форму

## API Endpoints (для ручного тестирования)

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "admin123"}'
```

### Get Current User
```bash
# Сначала получите токен из login, затем:
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Get Schools List
```bash
curl http://localhost:8000/api/v1/admin/schools \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Структура проекта

```
frontend/
├── src/
│   ├── App.tsx              # Главный компонент React Admin
│   ├── main.tsx             # Entry point
│   ├── providers/
│   │   ├── authProvider.ts  # JWT аутентификация
│   │   ├── dataProvider.ts  # REST API integration
│   │   └── index.ts         # Exports
│   └── types/
│       └── index.ts         # TypeScript типы
├── package.json
└── vite.config.ts
```

## Технологии

- ✅ React 19.1.1
- ✅ TypeScript 5.9.3
- ✅ Vite 7.1.12
- ✅ React Admin 5.12.2
- ✅ Material UI 7.3.4
- ✅ JWT Authentication

## Следующие шаги (Фаза 3)

После того как вы протестируете Фазу 2, мы реализуем:

1. **SchoolList** - полноценная таблица с пагинацией, сортировкой, фильтрами
2. **SchoolCreate** - форма создания новой школы
3. **SchoolEdit** - форма редактирования школы
4. **SchoolShow** - детальный просмотр школы
5. **Block/Unblock действия** - кнопки для блокировки/разблокировки

## Проблемы?

Если что-то не работает:

1. Проверьте, что оба сервера запущены:
   ```bash
   # Backend
   lsof -i :8000

   # Frontend
   lsof -i :5174
   ```

2. Проверьте логи в консоли браузера (F12)

3. Проверьте логи backend сервера

4. Убедитесь, что PostgreSQL запущен:
   ```bash
   docker ps | grep postgres
   ```
