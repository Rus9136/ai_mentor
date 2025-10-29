FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock* /app/

# Настройка Poetry для установки зависимостей в системное окружение
RUN poetry config virtualenvs.create false

# Установка зависимостей
RUN poetry install --no-interaction --no-ansi --no-root

# Копируем код приложения
COPY backend /app/backend

# Установка пакета в режиме разработки
RUN poetry install --no-interaction --no-ansi

# Создание пользователя без прав root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Открываем порт
EXPOSE 8000

# Команда запуска (может быть переопределена в docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
