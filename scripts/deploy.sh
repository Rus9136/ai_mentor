#!/bin/bash

# ==========================================
# AI Mentor Production Deployment Script
# ==========================================
# Использование:
#   ./scripts/deploy.sh [initial|update|restart]
#
# initial - первый деплой (с настройкой)
# update  - обновление существующего деплоя
# restart - перезапуск сервисов
# ==========================================

set -e  # Остановиться при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функции для красивого вывода
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка, что скрипт запущен от root или с sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Пожалуйста, запустите скрипт с sudo"
    exit 1
fi

# Определяем режим работы
DEPLOY_MODE=${1:-update}

print_info "Режим деплоя: $DEPLOY_MODE"
print_info "Текущая директория: $(pwd)"

# ==========================================
# 1. Проверка зависимостей
# ==========================================
check_dependencies() {
    print_info "Проверка зависимостей..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен. Установите Docker:"
        echo "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose не установлен"
        exit 1
    fi

    if ! command -v git &> /dev/null; then
        print_error "Git не установлен"
        exit 1
    fi

    print_info "✓ Все зависимости установлены"
}

# ==========================================
# 2. Проверка .env файла
# ==========================================
check_env_file() {
    print_info "Проверка .env файла..."

    if [ ! -f "backend/.env" ]; then
        print_warning "backend/.env не найден"

        if [ -f ".env.production" ]; then
            print_info "Копируем .env.production -> backend/.env"
            cp .env.production backend/.env
            print_warning "⚠️  ВАЖНО: Отредактируйте backend/.env и установите:"
            print_warning "  - SECRET_KEY (openssl rand -hex 32)"
            print_warning "  - POSTGRES_PASSWORD"
            print_warning "  - OPENAI_API_KEY"
            read -p "Нажмите Enter после редактирования backend/.env..."
        else
            print_error "Файл .env.production не найден. Создайте его сначала."
            exit 1
        fi
    fi

    # Проверяем критические переменные
    if grep -q "CHANGE_ME" backend/.env; then
        print_error "В backend/.env найдены незаполненные переменные (CHANGE_ME)"
        print_error "Пожалуйста, заполните все обязательные переменные"
        exit 1
    fi

    print_info "✓ .env файл корректен"
}

# ==========================================
# 3. Создание необходимых директорий
# ==========================================
create_directories() {
    print_info "Создание директорий..."

    mkdir -p uploads
    mkdir -p nginx/logs
    mkdir -p nginx/ssl
    mkdir -p postgres_data

    # Права доступа
    chmod 755 uploads
    chmod 755 nginx/logs

    print_info "✓ Директории созданы"
}

# ==========================================
# 4. Initial deployment (первый раз)
# ==========================================
initial_deploy() {
    print_info "=== INITIAL DEPLOYMENT ==="

    check_dependencies
    check_env_file
    create_directories

    print_info "Собираем Docker образы..."
    docker compose -f docker-compose.prod.yml build --no-cache

    print_info "Запускаем контейнеры..."
    docker compose -f docker-compose.prod.yml up -d postgres

    # Ждем запуска PostgreSQL
    print_info "Ожидание запуска PostgreSQL..."
    sleep 10

    # Применяем миграции
    print_info "Применяем миграции базы данных..."
    docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

    # Запускаем остальные сервисы
    print_info "Запускаем backend и frontend..."
    docker compose -f docker-compose.prod.yml up -d

    print_info "=== DEPLOYMENT ЗАВЕРШЕН ==="
    print_warning ""
    print_warning "⚠️  СЛЕДУЮЩИЙ ШАГ: Настройте SSL сертификаты"
    print_warning "Запустите: ./scripts/ssl-setup.sh"
}

# ==========================================
# 5. Update deployment (обновление)
# ==========================================
update_deploy() {
    print_info "=== UPDATE DEPLOYMENT ==="

    # Git pull (если используется Git)
    if [ -d ".git" ]; then
        print_info "Обновляем код из Git..."
        git pull origin main || print_warning "Не удалось обновить из Git"
    fi

    # Останавливаем сервисы (кроме БД)
    print_info "Останавливаем сервисы..."
    docker compose -f docker-compose.prod.yml stop backend frontend nginx

    # Пересобираем образы
    print_info "Пересобираем образы..."
    docker compose -f docker-compose.prod.yml build backend frontend

    # Применяем миграции
    print_info "Применяем новые миграции..."
    docker compose -f docker-compose.prod.yml up -d postgres
    sleep 5
    docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

    # Запускаем обновленные сервисы
    print_info "Запускаем обновленные сервисы..."
    docker compose -f docker-compose.prod.yml up -d

    # Очистка неиспользуемых образов
    print_info "Очистка старых образов..."
    docker image prune -f

    print_info "=== UPDATE ЗАВЕРШЕН ==="
}

# ==========================================
# 6. Restart services
# ==========================================
restart_services() {
    print_info "=== RESTART SERVICES ==="

    docker compose -f docker-compose.prod.yml restart

    print_info "✓ Сервисы перезапущены"
}

# ==========================================
# 7. Вывод статуса
# ==========================================
show_status() {
    print_info ""
    print_info "=== СТАТУС СЕРВИСОВ ==="
    docker compose -f docker-compose.prod.yml ps

    print_info ""
    print_info "=== ЛОГИ (последние 20 строк) ==="
    docker compose -f docker-compose.prod.yml logs --tail=20

    print_info ""
    print_info "=== ДОСТУПНЫЕ ЭНДПОИНТЫ ==="
    echo "  Frontend (Student/Parent): https://ai-mentor.kz"
    echo "  Admin Panel: https://admin.ai-mentor.kz"
    echo "  Backend API: https://api.ai-mentor.kz"
    echo "  API Docs: https://api.ai-mentor.kz/docs"
}

# ==========================================
# MAIN SCRIPT
# ==========================================

case "$DEPLOY_MODE" in
    initial)
        initial_deploy
        show_status
        ;;
    update)
        update_deploy
        show_status
        ;;
    restart)
        restart_services
        show_status
        ;;
    *)
        print_error "Неизвестный режим: $DEPLOY_MODE"
        echo "Использование: $0 [initial|update|restart]"
        exit 1
        ;;
esac

print_info ""
print_info "=== Полезные команды ==="
echo "  Логи всех сервисов:       docker compose -f docker-compose.prod.yml logs -f"
echo "  Логи backend:             docker compose -f docker-compose.prod.yml logs -f backend"
echo "  Статус контейнеров:       docker compose -f docker-compose.prod.yml ps"
echo "  Остановить все:           docker compose -f docker-compose.prod.yml down"
echo "  Подключиться к БД:        docker compose -f docker-compose.prod.yml exec postgres psql -U ai_mentor_user -d ai_mentor_db"
echo "  Создать backup БД:        docker compose -f docker-compose.prod.yml exec postgres pg_dump -U ai_mentor_user ai_mentor_db > backup.sql"
