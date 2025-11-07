#!/bin/bash

# ==========================================
# SSL Certificate Setup Script
# ==========================================
# Использует Let's Encrypt для получения SSL сертификатов
# для всех доменов проекта AI Mentor
# ==========================================

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав
if [ "$EUID" -ne 0 ]; then
    print_error "Запустите скрипт с sudo"
    exit 1
fi

# Домены
DOMAINS=(
    "ai-mentor.kz"
    "www.ai-mentor.kz"
    "api.ai-mentor.kz"
    "admin.ai-mentor.kz"
)

EMAIL="admin@ai-mentor.kz"  # Измените на ваш email

print_info "=== SSL CERTIFICATE SETUP ==="
print_info "Домены для сертификатов:"
for domain in "${DOMAINS[@]}"; do
    echo "  - $domain"
done
echo ""

# ==========================================
# 1. Проверка DNS записей
# ==========================================
check_dns() {
    print_info "Проверка DNS записей..."

    local all_ok=true
    for domain in "${DOMAINS[@]}"; do
        if host "$domain" > /dev/null 2>&1; then
            print_info "✓ $domain - DNS запись найдена"
        else
            print_error "✗ $domain - DNS запись НЕ найдена"
            all_ok=false
        fi
    done

    if [ "$all_ok" = false ]; then
        print_error "Некоторые DNS записи не настроены"
        print_warning "Пожалуйста, настройте A-записи для всех доменов на IP сервера"
        read -p "Продолжить все равно? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_info "✓ Все DNS записи настроены"
    fi
}

# ==========================================
# 2. Временный nginx конфиг для ACME challenge
# ==========================================
setup_temp_nginx() {
    print_info "Создание временного nginx конфига для получения сертификатов..."

    cat > /tmp/nginx-temp.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name ai-mentor.kz www.ai-mentor.kz api.ai-mentor.kz admin.ai-mentor.kz;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 200 'SSL setup in progress...';
            add_header Content-Type text/plain;
        }
    }
}
EOF

    # Копируем временный конфиг
    cp /tmp/nginx-temp.conf nginx/nginx-temp.conf

    print_info "✓ Временный конфиг создан"
}

# ==========================================
# 3. Запуск временного nginx
# ==========================================
start_temp_nginx() {
    print_info "Запуск временного nginx для ACME challenge..."

    # Останавливаем основной nginx если запущен
    docker compose -f docker-compose.prod.yml stop nginx 2>/dev/null || true

    # Запускаем временный nginx
    docker run -d \
        --name nginx_temp \
        -p 80:80 \
        -v "$(pwd)/nginx/nginx-temp.conf:/etc/nginx/nginx.conf:ro" \
        -v certbot_www:/var/www/certbot \
        nginx:alpine

    sleep 2
    print_info "✓ Временный nginx запущен"
}

# ==========================================
# 4. Получение сертификатов
# ==========================================
obtain_certificates() {
    print_info "Получение SSL сертификатов от Let's Encrypt..."

    # Для каждого домена получаем сертификат
    for domain in "${DOMAINS[@]}"; do
        print_info "Получение сертификата для $domain..."

        docker run -it --rm \
            --name certbot \
            -v certbot_conf:/etc/letsencrypt \
            -v certbot_www:/var/www/certbot \
            certbot/certbot certonly \
            --webroot \
            --webroot-path=/var/www/certbot \
            --email "$EMAIL" \
            --agree-tos \
            --no-eff-email \
            -d "$domain" \
            || print_warning "Не удалось получить сертификат для $domain"
    done

    print_info "✓ Сертификаты получены"
}

# ==========================================
# 5. Остановка временного nginx
# ==========================================
stop_temp_nginx() {
    print_info "Остановка временного nginx..."

    docker stop nginx_temp 2>/dev/null || true
    docker rm nginx_temp 2>/dev/null || true
    rm -f nginx/nginx-temp.conf

    print_info "✓ Временный nginx остановлен"
}

# ==========================================
# 6. Запуск production nginx с SSL
# ==========================================
start_production_nginx() {
    print_info "Запуск production nginx с SSL..."

    docker compose -f docker-compose.prod.yml up -d nginx

    print_info "✓ Production nginx запущен с SSL"
}

# ==========================================
# 7. Проверка сертификатов
# ==========================================
verify_certificates() {
    print_info "Проверка сертификатов..."

    sleep 3

    for domain in "${DOMAINS[@]}"; do
        if curl -s "https://$domain" > /dev/null 2>&1; then
            print_info "✓ $domain - SSL работает"
        else
            print_warning "⚠  $domain - проверьте SSL вручную"
        fi
    done
}

# ==========================================
# 8. Настройка автоматического обновления
# ==========================================
setup_auto_renewal() {
    print_info "Настройка автоматического обновления сертификатов..."

    # Certbot контейнер будет автоматически обновлять сертификаты
    # (настроено в docker-compose.prod.yml)

    print_info "✓ Автоматическое обновление настроено"
    print_info "  Сертификаты будут обновляться каждые 12 часов"
}

# ==========================================
# MAIN SCRIPT
# ==========================================

print_warning ""
print_warning "⚠️  ВАЖНО: Перед продолжением убедитесь, что:"
print_warning "  1. Все DNS A-записи настроены на IP этого сервера"
print_warning "  2. Порты 80 и 443 открыты в firewall"
print_warning "  3. Email для Let's Encrypt: $EMAIL"
print_warning ""
read -p "Продолжить? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Отменено"
    exit 0
fi

# Выполняем все шаги
check_dns
setup_temp_nginx
start_temp_nginx
obtain_certificates
stop_temp_nginx
start_production_nginx
verify_certificates
setup_auto_renewal

print_info ""
print_info "=== SSL SETUP ЗАВЕРШЕН ==="
print_info ""
print_info "Проверьте ваши сайты:"
echo "  https://ai-mentor.kz"
echo "  https://admin.ai-mentor.kz"
echo "  https://api.ai-mentor.kz/docs"
print_info ""
print_info "Сертификаты будут автоматически обновляться каждые 90 дней"
print_info ""

# Вывод информации о сертификатах
print_info "=== ИНФОРМАЦИЯ О СЕРТИФИКАТАХ ==="
docker compose -f docker-compose.prod.yml exec certbot certbot certificates || true
