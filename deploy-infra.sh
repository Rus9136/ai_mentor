#!/bin/bash

# ==========================================
# AI Mentor - Infrastructure Deployment Script
# ==========================================
# Скрипт управления для production деплоя
# Интеграция с централизованной инфраструктурой
# ==========================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/rus/projects/ai_mentor"
COMPOSE_FILE="docker-compose.infra.yml"
FRONTEND_DIST_VOLUME="ai_mentor_frontend_dist"
FRONTEND_TARGET_DIR="/var/www/ai-mentor"
NGINX_CONFIG_SOURCE="$PROJECT_DIR/nginx/infra"
NGINX_CONFIG_TARGET="/home/rus/infrastructure/nginx/sites-enabled"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Navigate to project directory
cd "$PROJECT_DIR"

# ==========================================
# Functions
# ==========================================

# Start services
start() {
    log_info "Starting AI Mentor services..."

    # Start postgres and backend
    docker compose -f $COMPOSE_FILE up -d postgres backend

    log_success "Services started successfully"
    log_info "Waiting for postgres to be ready..."
    sleep 5

    # Show status
    status
}

# Stop services
stop() {
    log_info "Stopping AI Mentor services..."
    docker compose -f $COMPOSE_FILE down
    log_success "Services stopped successfully"
}

# Restart services
restart() {
    log_info "Restarting AI Mentor services..."
    docker compose -f $COMPOSE_FILE restart
    log_success "Services restarted successfully"
}

# Show status
status() {
    log_info "AI Mentor services status:"
    docker compose -f $COMPOSE_FILE ps
}

# Show logs
logs() {
    SERVICE=${1:-backend}
    log_info "Showing logs for $SERVICE..."
    docker compose -f $COMPOSE_FILE logs -f $SERVICE
}

# Build services
build() {
    log_info "Building AI Mentor services..."
    docker compose -f $COMPOSE_FILE build
    log_success "Build completed successfully"
}

# Apply database migrations
migrate() {
    log_info "Applying database migrations..."
    docker compose -f $COMPOSE_FILE exec backend alembic upgrade head
    log_success "Migrations applied successfully"
}

# Seed database with initial data
seed() {
    log_info "Seeding database with initial data..."
    log_warning "This will create:"
    log_warning "  - SUPER_ADMIN and School ADMIN users"
    log_warning "  - Test school with teachers and students"
    log_warning "  - Global textbooks and tests"
    echo ""

    read -p "Continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Seed cancelled"
        exit 0
    fi

    log_info "Running seed script..."
    docker compose -f $COMPOSE_FILE exec backend python seed_database_prod.py

    log_success "Database seeded successfully"
    log_info "Login credentials:"
    log_info "  SUPER_ADMIN: superadmin@aimentor.com / admin123"
    log_info "  School ADMIN: school.admin@test.com / admin123"
    log_warning "⚠️  IMPORTANT: Change passwords after deployment!"
}

# Build frontend
build_frontend() {
    log_info "Building frontend..."

    # Build frontend image
    docker compose -f $COMPOSE_FILE --profile build build frontend

    # Run frontend build container
    log_info "Running frontend build container..."
    docker compose -f $COMPOSE_FILE --profile build up frontend

    # Stop frontend container
    docker compose -f $COMPOSE_FILE stop frontend

    log_success "Frontend build completed"
}

# Deploy frontend to /var/www/ai-mentor/
deploy_frontend() {
    log_info "Deploying frontend to $FRONTEND_TARGET_DIR..."

    # Create target directory
    sudo mkdir -p "$FRONTEND_TARGET_DIR"

    # Copy files from volume to target directory
    log_info "Copying files from Docker volume..."
    docker run --rm \
        -v ${FRONTEND_DIST_VOLUME}:/source:ro \
        -v ${FRONTEND_TARGET_DIR}:/dest \
        alpine sh -c "cp -r /source/* /dest/"

    # Set proper permissions
    sudo chown -R www-data:www-data "$FRONTEND_TARGET_DIR"

    log_success "Frontend deployed to $FRONTEND_TARGET_DIR"
}

# Install Nginx configs
install_nginx_configs() {
    log_info "Installing Nginx configurations..."

    # Check if nginx config directory exists
    if [ ! -d "$NGINX_CONFIG_TARGET" ]; then
        log_error "Nginx config directory not found: $NGINX_CONFIG_TARGET"
        exit 1
    fi

    # Copy configs
    sudo cp -v "$NGINX_CONFIG_SOURCE/ai-mentor-api.conf" "$NGINX_CONFIG_TARGET/"
    sudo cp -v "$NGINX_CONFIG_SOURCE/ai-mentor-frontend.conf" "$NGINX_CONFIG_TARGET/"
    sudo cp -v "$NGINX_CONFIG_SOURCE/ai-mentor-admin.conf" "$NGINX_CONFIG_TARGET/"

    # Test nginx config
    log_info "Testing Nginx configuration..."
    sudo nginx -t

    # Reload nginx
    log_info "Reloading Nginx..."
    sudo systemctl reload nginx

    log_success "Nginx configurations installed and reloaded"
}

# Full deployment
deploy() {
    log_info "Starting full deployment..."

    # Build services
    build

    # Start services
    start

    # Wait for postgres
    log_info "Waiting for PostgreSQL to be ready..."
    sleep 10

    # Apply migrations
    migrate

    # Build frontend
    build_frontend

    # Deploy frontend
    deploy_frontend

    log_success "Full deployment completed!"
    log_info "Next steps:"
    log_info "  1. Install Nginx configs: $0 install-nginx"
    log_info "  2. Setup SSL: sudo certbot certonly --webroot -w /var/www/certbot -d ai-mentor.kz -d www.ai-mentor.kz -d api.ai-mentor.kz -d admin.ai-mentor.kz"
    log_info "  3. Check services: $0 status"
}

# Backup database
backup() {
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    log_info "Creating database backup: $BACKUP_FILE..."

    docker compose -f $COMPOSE_FILE exec postgres pg_dump \
        -U ai_mentor_user ai_mentor_db > "$BACKUP_FILE"

    log_success "Backup created: $BACKUP_FILE"
}

# Restore database
restore() {
    BACKUP_FILE=$1

    if [ -z "$BACKUP_FILE" ]; then
        log_error "Usage: $0 restore <backup_file.sql>"
        exit 1
    fi

    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi

    log_warning "This will restore database from: $BACKUP_FILE"
    read -p "Are you sure? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled"
        exit 0
    fi

    log_info "Restoring database..."
    cat "$BACKUP_FILE" | docker compose -f $COMPOSE_FILE exec -T postgres \
        psql -U ai_mentor_user -d ai_mentor_db

    log_success "Database restored successfully"
}

# Show help
help() {
    cat << EOF
AI Mentor - Infrastructure Deployment Script

Usage: $0 <command> [options]

Commands:
    start                Start services (postgres + backend)
    stop                 Stop all services
    restart              Restart all services
    status               Show services status
    logs [service]       Show logs (default: backend)

    build                Build all Docker images
    migrate              Apply database migrations
    seed                 Seed database with initial data (users, textbooks, tests)

    build-frontend       Build frontend static files
    deploy-frontend      Deploy frontend to /var/www/ai-mentor/

    install-nginx        Install Nginx configurations

    deploy               Full deployment (build + start + migrate + frontend)

    backup               Backup database
    restore <file>       Restore database from backup

    help                 Show this help message

Examples:
    $0 start             # Start services
    $0 logs backend      # Show backend logs
    $0 deploy            # Full deployment
    $0 seed              # Seed database with test data
    $0 backup            # Backup database

EOF
}

# ==========================================
# Main
# ==========================================

case "${1}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "${2}"
        ;;
    build)
        build
        ;;
    migrate)
        migrate
        ;;
    seed)
        seed
        ;;
    build-frontend)
        build_frontend
        ;;
    deploy-frontend)
        deploy_frontend
        ;;
    install-nginx)
        install_nginx_configs
        ;;
    deploy)
        deploy
        ;;
    backup)
        backup
        ;;
    restore)
        restore "${2}"
        ;;
    help|--help|-h)
        help
        ;;
    *)
        log_error "Unknown command: ${1}"
        echo ""
        help
        exit 1
        ;;
esac
