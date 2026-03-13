# Промт для Claude Code — Фаза 1: Нативная геймификация

Скопируй всё ниже и вставь в новую сессию Claude Code:

---

## Задача

Реализуй Фазу 1 геймификации — нативный UI в student-app. Backend полностью готов (6 endpoints), нужен только фронтенд.

## Перед началом — изучи

1. **План реализации** — прочитай `docs/GAMIFICATION_FRONTEND_PLAN.md` (секция "Фаза 1")
2. **Backend API** — прочитай `backend/app/api/v1/students/gamification.py` (6 endpoints) и `backend/app/schemas/gamification.py` (response schemas)
3. **Существующие паттерны student-app:**
   - API клиент: прочитай `student-app/src/lib/api/chat.ts` или `student-app/src/lib/api/tests.ts` — следуй этому формату
   - React Query хуки: прочитай `student-app/src/lib/hooks/use-chat.ts` — следуй паттерну queryKeys + useQuery/useMutation
   - Страница-пример: прочитай `student-app/src/app/[locale]/(app)/home/page.tsx` — структура, layout, компоненты
   - UI компоненты: посмотри `student-app/src/components/ui/` — используй существующие (Button, Card, Progress, Badge, Tabs)
   - Навигация: прочитай `student-app/src/components/layout/MobileBottomNav.tsx` и `student-app/src/components/layout/AppSidebar.tsx` — чтобы понять куда добавить ссылку на /gamification
   - Локализация: прочитай `student-app/messages/ru.json` (структуру ключей) и `student-app/src/i18n/routing.ts`
4. **Tailwind конфиг**: прочитай `student-app/tailwind.config.ts` — цвета, шрифты
5. **Teacher leaderboard endpoint**: прочитай `backend/app/api/v1/teachers_gamification.py`

## Что реализовать (по порядку)

### Шаг 1 — API клиент и хуки

Создай `student-app/src/lib/api/gamification.ts`:
- `getGamificationProfile()` → GET `/students/gamification/profile`
- `getAchievements()` → GET `/students/gamification/achievements`
- `getRecentAchievements()` → GET `/students/gamification/achievements/recent`
- `getLeaderboard(scope: 'school' | 'class', classId?: number)` → GET `/students/gamification/leaderboard`
- `getDailyQuests()` → GET `/students/gamification/daily-quests`
- `getXpHistory(days?: number)` → GET `/students/gamification/xp-history`

Создай `student-app/src/lib/hooks/use-gamification.ts`:
- `useGamificationProfile()` — staleTime: 30 сек
- `useAchievements()`
- `useRecentAchievements()` — refetchInterval: 30 сек (polling для новых ачивок)
- `useLeaderboard(scope, classId?)`
- `useDailyQuests()`
- `useXpHistory(days?)`

Типы — создай `student-app/src/types/gamification.ts` на основе backend schemas из `backend/app/schemas/gamification.py`.

### Шаг 2 — Базовые компоненты

Создай в `student-app/src/components/gamification/`:

**XpProgressBar.tsx** — прогресс-бар XP до следующего уровня:
- Props: `currentXp`, `xpToNext`, `level`
- Цветной градиент (зелёный → синий → фиолетовый по уровню)
- Текст: "{currentXp} / {totalNeeded} XP"
- Анимация заполнения (CSS transition)

**StreakBadge.tsx** — бейдж стрика:
- Props: `days`, `isActive` (есть ли активность сегодня)
- Иконка огня + число дней
- Подсветка если активен

### Шаг 3 — Виджет на главной

Создай **XpLevelWidget.tsx** и вставь в `student-app/src/app/[locale]/(app)/home/page.tsx` в верхнюю часть:
- Используй `useGamificationProfile()`
- Показывай: уровень (крупно), XP прогресс-бар, стрик
- Кликабельный → переход на `/gamification`
- Компактный дизайн, одна строка на десктопе, две на мобильном

### Шаг 4 — Страница /gamification

Создай `student-app/src/app/[locale]/(app)/gamification/page.tsx` с табами (используй компонент Tabs из ui/):

**Tab "Профиль":**
- Уровень (большой номер) + XP прогресс-бар
- Стрик: текущий + рекорд
- Статистика: earned_achievements_count, total из profile endpoint

**Tab "Достижения":**
- Компонент `AchievementGrid.tsx` — сетка карточек
- Компонент `AchievementCard.tsx`:
  - Earned: цветная иконка, название (name_ru или name_kk по локали), дата
  - Locked: серая, прогресс-бар (progress 0-1)
  - Обводка по rarity: common=#9CA3AF, rare=#3B82F6, epic=#8B5CF6, legendary=#F59E0B
- Используй `useAchievements()`

**Tab "Рейтинг":**
- Компонент `Leaderboard.tsx`
- Переключатель Школа/Класс (SegmentedControl или два Button)
- Компонент `LeaderboardTopThree.tsx` — топ-3 с медалями 🥇🥈🥉
- Таблица остальных: ранг, имя, уровень, XP
- Текущий ученик подсвечен (выделенный ряд)
- Позиция ученика: `user_rank` из response
- Используй `useLeaderboard(scope, classId)`

**Tab "Задания":**
- Компонент `DailyQuests.tsx` — список карточек
- Компонент `DailyQuestCard.tsx`:
  - Название, описание, прогресс (current_value / target_value)
  - Прогресс-бар
  - Completed: галочка + "+{xp_reward} XP"
- Используй `useDailyQuests()`

### Шаг 5 — XP Toast

Создай `student-app/src/components/gamification/XpToast.tsx`:
- Плавающий toast "+{amount} XP" в правом верхнем углу
- Анимация: fade-in + slide-up → hold 2 сек → fade-out
- При level-up: расширенный toast "Уровень {N}!" с другим цветом

Создай `student-app/src/stores/gamification-store.ts` (zustand):
- `prevXp: number` — предыдущее значение XP
- `showXpToast(amount, levelUp?)` — триггер показа
- `hideXpToast()` — скрыть

Интегрируй: в `XpLevelWidget` после refetch сравнивай prevXp с новым — если выросло, показывай toast.

### Шаг 6 — Achievement Popup

Создай `student-app/src/components/gamification/AchievementPopup.tsx`:
- Модалка при получении новой ачивки
- Иконка + название + описание + XP reward
- Кнопка "Круто!" для закрытия
- Данные из `useRecentAchievements()` (polling каждые 30 сек)
- Показывать только если есть unnotified achievements

Добавь этот компонент в layout `student-app/src/app/[locale]/(app)/layout.tsx` чтобы он был доступен на всех страницах.

### Шаг 7 — Навигация

Добавь ссылку на `/gamification` в:
- `MobileBottomNav.tsx` — иконка Trophy или Star
- `AppSidebar.tsx` — пункт меню "Достижения" или "Геймификация"

### Шаг 8 — Локализация

Добавь ключи `gamification.*` в:
- `student-app/messages/ru.json`
- `student-app/messages/kk.json`

Ключи (минимум):
```
gamification.title, gamification.level, gamification.xpProgress,
gamification.streak, gamification.streakRecord,
gamification.achievements, gamification.leaderboard,
gamification.dailyQuests, gamification.school, gamification.class,
gamification.earned, gamification.locked, gamification.xpAwarded,
gamification.levelUp, gamification.questComplete, gamification.yourRank,
gamification.profile, gamification.noAchievements, gamification.keepLearning
```

## Правила

- Используй СУЩЕСТВУЮЩИЕ UI-компоненты из `student-app/src/components/ui/` (Card, Button, Progress, Tabs, Badge и т.д.) — НЕ создавай дублирующие
- Следуй паттернам кода из существующих файлов (API клиент, хуки, страницы)
- Стиль: Tailwind CSS, mobile-first, тёмная тема через `dark:` классы если она уже поддерживается в проекте
- Все тексты через `useTranslations('gamification')` — не хардкодь строки
- Каждый файл < 400 строк (правило проекта из CLAUDE.md)
- TypeScript strict mode — все типы должны быть определены
- После реализации проверь: `cd student-app && npm run build` — билд должен пройти без ошибок
