# Краткая инструкция по работе с миграциями

## Быстрый старт

### Текущее состояние БД

```bash
# Проверить версию миграции
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "SELECT version_num FROM alembic_version;"

# Текущая версия: 003
```

---

## Шаблон: Добавление новой колонки

### 1. Создать файл миграции

**Файл:** `backend/alembic/versions/00X_short_description.py`

```python
"""Short description

Revision ID: 00X
Revises: 00Y
Create Date: YYYY-MM-DD
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '00X'
down_revision: Union[str, None] = '00Y'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('table_name', sa.Column('column_name', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('table_name', 'column_name')
```

### 2. Создать SQL версию (опционально)

**Файл:** `backend/alembic/versions/00X_short_description.sql`

```sql
-- Short description
ALTER TABLE table_name ADD COLUMN column_name TEXT;
```

### 3. Обновить модель

**Файл:** `backend/app/models/model_name.py`

```python
class ModelName(SoftDeleteModel):
    __tablename__ = "table_name"

    # Добавить новую колонку
    column_name = Column(Text, nullable=True)  # Описание
```

### 4. Применить миграцию

```bash
# Применить SQL
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "
ALTER TABLE table_name ADD COLUMN column_name TEXT;
"

# Обновить версию
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "
UPDATE alembic_version SET version_num = '00X';
"
```

### 5. Проверить

```bash
# Проверить структуру таблицы
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\d table_name"

# Проверить версию
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "
SELECT version_num FROM alembic_version;
"
```

---

## Частые операции

### Добавить колонку

```python
# Миграция
def upgrade() -> None:
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))

# SQL
ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);
```

### Удалить колонку

```python
# Миграция
def upgrade() -> None:
    op.drop_column('users', 'old_field')

# SQL
ALTER TABLE users DROP COLUMN old_field;
```

### Изменить тип колонки

```python
# Миграция
def upgrade() -> None:
    op.alter_column('users', 'phone',
                    existing_type=sa.VARCHAR(50),
                    type_=sa.VARCHAR(100))

# SQL
ALTER TABLE users ALTER COLUMN phone TYPE VARCHAR(100);
```

### Добавить индекс

```python
# Миграция
def upgrade() -> None:
    op.create_index('ix_users_phone', 'users', ['phone'])

# SQL
CREATE INDEX ix_users_phone ON users(phone);
```

### Сделать колонку обязательной

```python
# Миграция (в два шага)
def upgrade() -> None:
    # Сначала заполнить NULL значения
    op.execute("UPDATE users SET email = 'default@example.com' WHERE email IS NULL")
    # Потом сделать NOT NULL
    op.alter_column('users', 'email', nullable=False)

# SQL
UPDATE users SET email = 'default@example.com' WHERE email IS NULL;
ALTER TABLE users ALTER COLUMN email SET NOT NULL;
```

### Добавить внешний ключ

```python
# Миграция
def upgrade() -> None:
    op.create_foreign_key(
        'fk_posts_user_id',
        'posts', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

# SQL
ALTER TABLE posts ADD CONSTRAINT fk_posts_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

### Создать новую таблицу

```python
# Миграция
def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])

# SQL
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_notifications_user_id ON notifications(user_id);
```

---

## Типы данных SQLAlchemy → PostgreSQL

| SQLAlchemy | PostgreSQL | Пример |
|------------|------------|--------|
| `sa.Integer()` | `INTEGER` | `sa.Column('age', sa.Integer())` |
| `sa.String(N)` | `VARCHAR(N)` | `sa.Column('name', sa.String(255))` |
| `sa.Text()` | `TEXT` | `sa.Column('content', sa.Text())` |
| `sa.Boolean()` | `BOOLEAN` | `sa.Column('is_active', sa.Boolean())` |
| `sa.Float()` | `FLOAT` | `sa.Column('score', sa.Float())` |
| `sa.Date()` | `DATE` | `sa.Column('birth_date', sa.Date())` |
| `sa.DateTime(timezone=True)` | `TIMESTAMP WITH TIME ZONE` | `sa.Column('created_at', sa.DateTime(timezone=True))` |
| `sa.JSON()` | `JSON` | `sa.Column('metadata', sa.JSON())` |
| `postgresql.VECTOR(N)` | `VECTOR(N)` | `sa.Column('embedding', postgresql.VECTOR(1536))` |
| `sa.Enum(...)` | `ENUM` | `sa.Column('role', sa.Enum('admin', 'user', name='userrole'))` |

---

## Чеклист для новой миграции

- [ ] Создан файл миграции `.py` с правильной нумерацией
- [ ] Указан правильный `down_revision`
- [ ] Реализована функция `upgrade()`
- [ ] Реализована функция `downgrade()`
- [ ] Обновлена модель SQLAlchemy
- [ ] Создан SQL файл (опционально)
- [ ] Миграция применена к БД
- [ ] Обновлена версия в `alembic_version`
- [ ] Проверена структура таблицы
- [ ] Протестирована работа приложения

---

## Полезные команды

```bash
# ===== Проверка состояния =====
# Текущая версия миграции
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "SELECT version_num FROM alembic_version;"

# Список всех таблиц
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\dt"

# Структура конкретной таблицы
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\d table_name"

# ===== Применение миграции =====
# Добавить колонку
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "ALTER TABLE table_name ADD COLUMN column_name TYPE;"

# Удалить колонку
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "ALTER TABLE table_name DROP COLUMN column_name;"

# Обновить версию миграции
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "UPDATE alembic_version SET version_num = '00X';"

# ===== Откат =====
# Удалить последнюю добавленную колонку
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "ALTER TABLE table_name DROP COLUMN column_name;"

# Откатить версию миграции
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "UPDATE alembic_version SET version_num = '00Y';"

# ===== Резервное копирование =====
# Создать дамп БД перед миграцией
docker exec ai_mentor_postgres pg_dump -U ai_mentor_user ai_mentor_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить из дампа
docker exec -i ai_mentor_postgres psql -U ai_mentor_user ai_mentor_db < backup_file.sql
```

---

## Примеры реальных миграций

### Миграция 002: Добавление целей обучения

```python
"""Add learning and lesson objectives

Revision ID: 002
Revises: 001
"""
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'

def upgrade() -> None:
    op.add_column('chapters', sa.Column('learning_objective', sa.Text(), nullable=True))
    op.add_column('paragraphs', sa.Column('lesson_objective', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('paragraphs', 'lesson_objective')
    op.drop_column('chapters', 'learning_objective')
```

### Миграция 003: Добавление learning_objective для параграфов

```python
"""Add learning_objective to paragraphs

Revision ID: 003
Revises: 002
"""
from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'

def upgrade() -> None:
    op.add_column('paragraphs', sa.Column('learning_objective', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('paragraphs', 'learning_objective')
```

---

## Troubleshooting

### Ошибка: "column already exists"

```bash
# Проверить существующие колонки
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\d table_name"

# Удалить дублирующуюся колонку
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "ALTER TABLE table_name DROP COLUMN column_name;"
```

### Ошибка: "relation does not exist"

```bash
# Проверить список таблиц
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\dt"

# Создать таблицу вручную или применить предыдущие миграции
```

### Несоответствие версии миграции

```bash
# Проверить текущую версию
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "SELECT version_num FROM alembic_version;"

# Установить правильную версию
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "UPDATE alembic_version SET version_num = '00X';"
```

---

## Безопасность

### Перед применением миграции на production:

1. **Создать резервную копию БД**
   ```bash
   docker exec ai_mentor_postgres pg_dump -U ai_mentor_user ai_mentor_db > backup_before_migration_00X.sql
   ```

2. **Протестировать на тестовой БД**
   ```bash
   # Применить миграцию на тестовой БД
   docker exec ai_mentor_postgres_test psql -U ai_mentor_user -d ai_mentor_test_db -c "ALTER TABLE ..."
   ```

3. **Проверить время выполнения**
   ```bash
   # Измерить время выполнения миграции
   time docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "ALTER TABLE ..."
   ```

4. **Спланировать downtime** (если требуется)
   - Для больших таблиц операции могут занять время
   - Уведомить пользователей заранее

5. **Подготовить план отката**
   - Убедиться, что функция `downgrade()` работает
   - Подготовить SQL команды для отката

---

## Контакты

Для вопросов по базе данных и миграциям см. полную документацию:
- [database_schema.md](./database_schema.md) - Полная документация по БД
- [README.md](../README.md) - Общая информация о проекте
