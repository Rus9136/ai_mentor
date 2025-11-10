#!/bin/bash

# ==========================================
# Deploy Helper Functions
# ==========================================
# Вспомогательные функции для deploy.sh
# Цветной вывод, прогресс-бары, утилиты
# ==========================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Emojis
EMOJI_INFO="🔍"
EMOJI_SUCCESS="✅"
EMOJI_ERROR="❌"
EMOJI_WARNING="⚠️"
EMOJI_ROCKET="🚀"
EMOJI_BACKEND="🔨"
EMOJI_FRONTEND="⚛️"
EMOJI_DATABASE="🗄️"
EMOJI_TIMER="⏱️"
EMOJI_DOCKER="🐳"
EMOJI_CHECK="✓"
EMOJI_CROSS="✗"

# ==========================================
# Logging Functions
# ==========================================

log_info() {
    echo -e "${BLUE}${EMOJI_INFO} INFO:${NC} $1"
}

log_success() {
    echo -e "${GREEN}${EMOJI_SUCCESS} SUCCESS:${NC} $1"
}

log_error() {
    echo -e "${RED}${EMOJI_ERROR} ERROR:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}${EMOJI_WARNING} WARNING:${NC} $1"
}

log_step() {
    echo -e "${CYAN}${EMOJI_ROCKET} $1${NC}"
}

log_backend() {
    echo -e "${MAGENTA}${EMOJI_BACKEND} Backend:${NC} $1"
}

log_frontend() {
    echo -e "${CYAN}${EMOJI_FRONTEND} Frontend:${NC} $1"
}

log_database() {
    echo -e "${YELLOW}${EMOJI_DATABASE} Database:${NC} $1"
}

log_separator() {
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_header() {
    echo ""
    log_separator
    echo -e "${CYAN}${1}${NC}"
    log_separator
}

# ==========================================
# Progress Bar
# ==========================================

# Показать прогресс-бар
# Использование: show_progress "Операция" 30
show_progress() {
    local message="$1"
    local duration="${2:-5}"
    local steps=8
    local delay=$(echo "scale=2; $duration / $steps" | bc)

    echo -n -e "${BLUE}[${NC}"

    for i in $(seq 1 $steps); do
        echo -n -e "${GREEN}▓${NC}"
        sleep "$delay" 2>/dev/null || sleep 1
    done

    echo -e "${BLUE}]${NC} ${message} ${GREEN}OK${NC}"
}

# ==========================================
# Status Indicators
# ==========================================

# Показать статус (OK или FAIL)
show_status() {
    local status=$1
    local message=$2

    if [ "$status" -eq 0 ]; then
        echo -e "${GREEN}${EMOJI_CHECK} ${message}${NC}"
        return 0
    else
        echo -e "${RED}${EMOJI_CROSS} ${message}${NC}"
        return 1
    fi
}

# Показать статус сервиса
show_service_status() {
    local service=$1
    local status=$2

    if [ "$status" = "healthy" ] || [ "$status" = "running" ] || [ "$status" = "deployed" ]; then
        echo -e "   ${GREEN}${EMOJI_CHECK} ${service}: ${status}${NC}"
    else
        echo -e "   ${RED}${EMOJI_CROSS} ${service}: ${status}${NC}"
    fi
}

# ==========================================
# Timer Functions
# ==========================================

# Глобальная переменная для таймера
TIMER_START=0

# Начать отсчет времени
start_timer() {
    TIMER_START=$(date +%s)
}

# Показать прошедшее время
show_elapsed() {
    local end=$(date +%s)
    local elapsed=$((end - TIMER_START))

    if [ $elapsed -lt 60 ]; then
        echo -e "${GRAY}${EMOJI_TIMER} Время: ${elapsed} секунд${NC}"
    else
        local minutes=$((elapsed / 60))
        local seconds=$((elapsed % 60))
        echo -e "${GRAY}${EMOJI_TIMER} Время: ${minutes} минут ${seconds} секунд${NC}"
    fi
}

# ==========================================
# Docker Helper Functions
# ==========================================

# Проверить статус контейнера
get_container_status() {
    local container_name=$1
    docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null || echo "not found"
}

# Проверить health контейнера
get_container_health() {
    local container_name=$1
    docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown"
}

# Получить последние логи контейнера
get_container_logs() {
    local container_name=$1
    local lines="${2:-20}"
    docker logs --tail "$lines" "$container_name" 2>&1
}

# ==========================================
# Git Helper Functions
# ==========================================

# Получить список измененных файлов с последнего коммита
get_changed_files() {
    # Если есть uncommitted changes, показать их
    if ! git diff-index --quiet HEAD 2>/dev/null; then
        git diff --name-only HEAD
    else
        # Сравнить с предыдущим коммитом
        git diff --name-only HEAD~1 HEAD 2>/dev/null || git diff --name-only HEAD
    fi
}

# Проверить есть ли изменения в директории
has_changes_in_dir() {
    local directory=$1
    get_changed_files | grep -q "^${directory}/"
}

# Получить текущий git hash
get_current_commit() {
    git rev-parse --short HEAD 2>/dev/null || echo "unknown"
}

# Получить текущую git ветку
get_current_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"
}

# ==========================================
# Healthcheck Functions
# ==========================================

# Проверить HTTP endpoint
check_http_endpoint() {
    local url=$1
    local timeout=${2:-5}

    if curl -f -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" | grep -q "200"; then
        return 0
    else
        return 1
    fi
}

# Проверить PostgreSQL доступность
check_postgres() {
    local container_name=${1:-ai_mentor_postgres_prod}

    if docker exec "$container_name" pg_isready -U ai_mentor_user -d ai_mentor_db >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# ==========================================
# Error Handling
# ==========================================

# Показать детали ошибки с логами
show_error_details() {
    local service=$1
    local container_name=$2

    log_error "${service} deployment failed!"
    echo ""
    echo -e "${YELLOW}📋 Last 20 lines of ${service} logs:${NC}"
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    get_container_logs "$container_name" 20
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Показать подсказки по решению проблемы
show_troubleshooting() {
    local service=$1

    echo -e "${YELLOW}💡 Troubleshooting steps:${NC}"

    case "$service" in
        backend)
            echo "   1. Check Python syntax errors"
            echo "   2. Check pyproject.toml dependencies"
            echo "   3. Review logs: docker compose -f docker-compose.infra.yml logs backend"
            ;;
        frontend)
            echo "   1. Check JavaScript/TypeScript syntax"
            echo "   2. Check package.json dependencies"
            echo "   3. Review build output above"
            ;;
        postgres)
            echo "   1. Check database credentials in backend/.env"
            echo "   2. Review logs: docker compose -f docker-compose.infra.yml logs postgres"
            echo "   3. Check disk space: df -h"
            ;;
    esac

    echo ""
}

# ==========================================
# Confirmation Prompts
# ==========================================

# Спросить подтверждение у пользователя
ask_confirmation() {
    local message=$1
    local default=${2:-n}

    if [ "$default" = "y" ]; then
        read -p "$(echo -e ${YELLOW}${message} [Y/n]: ${NC})" response
        response=${response:-y}
    else
        read -p "$(echo -e ${YELLOW}${message} [y/N]: ${NC})" response
        response=${response:-n}
    fi

    if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# ==========================================
# Summary Functions
# ==========================================

# Показать итоговую статистику деплоя
show_deploy_summary() {
    local backend_deployed=$1
    local frontend_deployed=$2
    local migrations_applied=$3
    local success=$4

    echo ""
    log_header "📊 DEPLOY SUMMARY"

    echo -e "   ${EMOJI_BACKEND} Backend:   $([ "$backend_deployed" = "true" ] && echo "${GREEN}DEPLOYED${NC}" || echo "${GRAY}Skipped${NC}")"
    echo -e "   ${EMOJI_FRONTEND} Frontend:  $([ "$frontend_deployed" = "true" ] && echo "${GREEN}DEPLOYED${NC}" || echo "${GRAY}Skipped${NC}")"
    echo -e "   ${EMOJI_DATABASE} Migrations: $([ "$migrations_applied" = "true" ] && echo "${GREEN}APPLIED${NC}" || echo "${GRAY}Skipped${NC}")"

    echo ""

    if [ "$success" = "true" ]; then
        log_success "Deployment completed successfully!"
        show_elapsed
        echo ""
        echo -e "${CYAN}🌐 Services:${NC}"
        echo -e "   • Landing:  ${GREEN}https://ai-mentor.kz${NC}"
        echo -e "   • Admin:    ${GREEN}https://admin.ai-mentor.kz${NC}"
        echo -e "   • API:      ${GREEN}https://api.ai-mentor.kz${NC}"
        echo -e "   • API Docs: ${GREEN}https://api.ai-mentor.kz/docs${NC}"
    else
        log_error "Deployment failed!"
        show_elapsed
        echo ""
        echo -e "${YELLOW}⚠️  Previous version is still running${NC}"
    fi

    echo ""
    log_separator
}

# ==========================================
# Export Functions (для использования в deploy.sh)
# ==========================================

export -f log_info log_success log_error log_warning log_step
export -f log_backend log_frontend log_database
export -f log_separator log_header
export -f show_progress show_status show_service_status
export -f start_timer show_elapsed
export -f get_container_status get_container_health get_container_logs
export -f get_changed_files has_changes_in_dir get_current_commit get_current_branch
export -f check_http_endpoint check_postgres
export -f show_error_details show_troubleshooting
export -f ask_confirmation
export -f show_deploy_summary
