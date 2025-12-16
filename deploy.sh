#!/bin/bash

# ==========================================
# AI Mentor - Smart Deploy Script
# ==========================================
# Умный скрипт автоматического деплоя
# Определяет изменения и деплоит только нужное
# ==========================================

set -e  # Exit on error

# ==========================================
# Configuration
# ==========================================

PROJECT_DIR="/home/rus/projects/ai_mentor"
COMPOSE_FILE="docker-compose.infra.yml"
FRONTEND_DIST_VOLUME="ai_mentor_frontend_dist"
FRONTEND_TARGET_DIR="/var/www/ai-mentor"
ADMIN_TARGET_DIR="/var/www/ai-mentor-admin"

# Load helper functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.deploy-helpers.sh"

# ==========================================
# Navigate to project directory
# ==========================================

cd "$PROJECT_DIR"

# ==========================================
# Parse command line arguments
# ==========================================

DEPLOY_MODE="${1:-auto}"  # auto, backend, frontend, migrations, full

# ==========================================
# Detect Changes Function
# ==========================================

detect_changes() {
    log_header "🔍 ANALYZING CHANGES"

    # Get list of changed files
    CHANGED_FILES=$(get_changed_files)

    if [ -z "$CHANGED_FILES" ]; then
        log_warning "No changes detected in git"
        echo ""
        log_info "Changed files will be detected from uncommitted changes or last commit"
        echo ""
    fi

    # Display changed files
    if [ -n "$CHANGED_FILES" ]; then
        echo -e "${GRAY}Changed files:${NC}"
        echo "$CHANGED_FILES" | while read -r file; do
            echo -e "   ${GRAY}•${NC} $file"
        done
        echo ""
    fi

    # Detect what needs to be deployed
    BACKEND_CHANGED=false
    FRONTEND_CHANGED=false
    MIGRATIONS_CHANGED=false
    NGINX_CHANGED=false

    if echo "$CHANGED_FILES" | grep -q "^backend/app/"; then
        BACKEND_CHANGED=true
    fi

    if echo "$CHANGED_FILES" | grep -q "^backend/alembic/versions/"; then
        MIGRATIONS_CHANGED=true
    fi

    if echo "$CHANGED_FILES" | grep -q "^frontend/src/"; then
        FRONTEND_CHANGED=true
    fi

    if echo "$CHANGED_FILES" | grep -q "^frontend/public/"; then
        FRONTEND_CHANGED=true
    fi

    if echo "$CHANGED_FILES" | grep -q "^nginx/infra/"; then
        NGINX_CHANGED=true
    fi

    if echo "$CHANGED_FILES" | grep -q "^backend/Dockerfile.prod"; then
        BACKEND_CHANGED=true
    fi

    if echo "$CHANGED_FILES" | grep -q "^frontend/Dockerfile.prod"; then
        FRONTEND_CHANGED=true
    fi

    if echo "$CHANGED_FILES" | grep -q "pyproject.toml"; then
        BACKEND_CHANGED=true
    fi

    if echo "$CHANGED_FILES" | grep -q "package.json"; then
        FRONTEND_CHANGED=true
    fi

    # Export variables
    export BACKEND_CHANGED
    export FRONTEND_CHANGED
    export MIGRATIONS_CHANGED
    export NGINX_CHANGED
}

# ==========================================
# Show Deploy Plan
# ==========================================

show_deploy_plan() {
    log_header "📋 DEPLOY PLAN"

    if [ "$DEPLOY_MODE" = "auto" ]; then
        echo -e "   ${EMOJI_BACKEND} Backend:    $([ "$BACKEND_CHANGED" = "true" ] && echo "${GREEN}DEPLOY${NC}" || echo "${GRAY}Skip${NC}")"
        echo -e "   ${EMOJI_FRONTEND} Frontend:   $([ "$FRONTEND_CHANGED" = "true" ] && echo "${GREEN}DEPLOY${NC}" || echo "${GRAY}Skip${NC}")"
        echo -e "   ${EMOJI_DATABASE} Migrations: $([ "$MIGRATIONS_CHANGED" = "true" ] && echo "${GREEN}DEPLOY${NC}" || echo "${GRAY}Skip${NC}")"

        if [ "$NGINX_CHANGED" = "true" ]; then
            echo -e "   🌐 Nginx:       ${YELLOW}UPDATE REQUIRED${NC}"
            echo ""
            log_warning "Nginx config changed! Run: ./deploy-infra.sh install-nginx"
        fi
    elif [ "$DEPLOY_MODE" = "backend" ]; then
        echo -e "   ${EMOJI_BACKEND} Backend:    ${GREEN}FORCE DEPLOY${NC}"
        BACKEND_CHANGED=true
    elif [ "$DEPLOY_MODE" = "frontend" ]; then
        echo -e "   ${EMOJI_FRONTEND} Frontend:   ${GREEN}FORCE DEPLOY${NC}"
        FRONTEND_CHANGED=true
    elif [ "$DEPLOY_MODE" = "migrations" ]; then
        echo -e "   ${EMOJI_DATABASE} Migrations: ${GREEN}FORCE APPLY${NC}"
        MIGRATIONS_CHANGED=true
    elif [ "$DEPLOY_MODE" = "full" ]; then
        echo -e "   ${EMOJI_BACKEND} Backend:    ${GREEN}DEPLOY${NC}"
        echo -e "   ${EMOJI_FRONTEND} Frontend:   ${GREEN}DEPLOY${NC}"
        echo -e "   ${EMOJI_DATABASE} Migrations: ${GREEN}APPLY${NC}"
        BACKEND_CHANGED=true
        FRONTEND_CHANGED=true
        MIGRATIONS_CHANGED=true
    else
        log_error "Unknown deploy mode: $DEPLOY_MODE"
        show_usage
        exit 1
    fi

    echo ""

    # Check if anything to deploy
    if [ "$BACKEND_CHANGED" = "false" ] && [ "$FRONTEND_CHANGED" = "false" ] && [ "$MIGRATIONS_CHANGED" = "false" ]; then
        log_warning "Nothing to deploy!"
        echo ""
        log_info "Use one of these modes:"
        echo "   ./deploy.sh backend      # Force deploy backend"
        echo "   ./deploy.sh frontend     # Force deploy frontend"
        echo "   ./deploy.sh full         # Deploy everything"
        echo ""
        exit 0
    fi
}

# ==========================================
# Apply Database Migrations
# ==========================================

apply_migrations() {
    log_database "Applying database migrations..."

    # Check if backend is running
    if [ "$(get_container_status ai_mentor_backend_prod)" != "running" ]; then
        log_error "Backend container is not running!"
        return 1
    fi

    # Apply migrations
    if docker compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head; then
        log_success "Migrations applied successfully"
        return 0
    else
        log_error "Failed to apply migrations"
        show_error_details "Migrations" "ai_mentor_backend_prod"
        return 1
    fi
}

# ==========================================
# Deploy Backend
# ==========================================

deploy_backend() {
    log_backend "Starting backend deployment..."

    # Build backend image
    log_step "Building backend Docker image..."
    if docker compose -f "$COMPOSE_FILE" build backend; then
        log_success "Backend image built"
    else
        log_error "Failed to build backend image"
        show_error_details "Backend Build" "ai_mentor_backend_prod"
        show_troubleshooting "backend"
        return 1
    fi

    # Restart backend
    log_step "Restarting backend container..."
    if docker compose -f "$COMPOSE_FILE" restart backend; then
        log_success "Backend restarted"
    else
        log_error "Failed to restart backend"
        return 1
    fi

    # Wait for backend to start
    log_step "Waiting for backend to start..."
    sleep 5

    # Check backend health
    log_step "Checking backend health..."
    local retries=0
    local max_retries=6  # 30 seconds total (6 * 5)

    while [ $retries -lt $max_retries ]; do
        if check_http_endpoint "http://127.0.0.1:8006/health" 5; then
            log_success "Backend is healthy"
            return 0
        fi

        retries=$((retries + 1))
        if [ $retries -lt $max_retries ]; then
            echo -e "   ${GRAY}Retry $retries/$max_retries...${NC}"
            sleep 5
        fi
    done

    log_error "Backend healthcheck failed!"
    show_error_details "Backend" "ai_mentor_backend_prod"
    show_troubleshooting "backend"
    return 1
}

# ==========================================
# Deploy Frontend
# ==========================================

deploy_frontend() {
    log_frontend "Starting frontend deployment..."

    # Build frontend image (--no-cache ensures fresh build with latest source files)
    log_step "Building frontend Docker image..."
    if docker compose -f "$COMPOSE_FILE" --profile build build --no-cache frontend; then
        log_success "Frontend image built"
    else
        log_error "Failed to build frontend image"
        show_troubleshooting "frontend"
        return 1
    fi

    # Verify API URL in built image
    log_step "Verifying API URL in built image..."
    API_URL_CHECK=$(docker run --rm ai_mentor-frontend sh -c "grep -o 'https://api.ai-mentor.kz[^\"]*' /usr/share/nginx/html/assets/*.js 2>/dev/null | head -1" || echo "")

    if [[ -z "$API_URL_CHECK" ]]; then
        log_error "❌ ERROR: Could not find API URL in built frontend!"
        show_troubleshooting "frontend"
        return 1
    elif [[ "$API_URL_CHECK" != *"/api/v1"* ]]; then
        log_error "❌ ERROR: API URL does not contain /api/v1!"
        echo -e "   ${RED}Found: $API_URL_CHECK${NC}"
        echo -e "   ${RED}Expected: https://api.ai-mentor.kz/api/v1${NC}"
        echo ""
        echo -e "${YELLOW}This usually means Docker cached an old build with wrong VITE_API_URL${NC}"
        echo -e "${YELLOW}Solution: Rebuild with --no-cache${NC}"
        echo -e "   ${GRAY}cd frontend && docker build --no-cache --build-arg VITE_API_URL=\"https://api.ai-mentor.kz/api/v1\" -f Dockerfile.prod -t ai_mentor-frontend .${NC}"
        return 1
    else
        log_success "✅ API URL is correct: $API_URL_CHECK"
    fi

    # Start frontend container temporarily (nginx with built files)
    log_step "Starting frontend build container..."
    docker compose -f "$COMPOSE_FILE" --profile build up -d frontend

    # Wait for container to be ready
    sleep 3

    # Copy files to /tmp first
    log_step "Extracting frontend build from container..."
    if ! docker cp ai_mentor_frontend_build:/usr/share/nginx/html/. /tmp/frontend-dist/; then
        log_error "Failed to extract frontend files from container"
        docker compose -f "$COMPOSE_FILE" stop frontend 2>/dev/null || true
        return 1
    fi

    # Deploy to Landing (ai-mentor.kz)
    log_step "Deploying landing to $FRONTEND_TARGET_DIR..."
    sudo mkdir -p "$FRONTEND_TARGET_DIR"
    if sudo rm -rf "$FRONTEND_TARGET_DIR"/* && \
       sudo cp -r /tmp/frontend-dist/* "$FRONTEND_TARGET_DIR/"; then
        sudo chown -R www-data:www-data "$FRONTEND_TARGET_DIR"
        log_success "Landing deployed to $FRONTEND_TARGET_DIR"
    else
        log_error "Failed to deploy landing"
        sudo rm -rf /tmp/frontend-dist
        docker compose -f "$COMPOSE_FILE" stop frontend 2>/dev/null || true
        return 1
    fi

    # Deploy to Admin (admin.ai-mentor.kz)
    log_step "Deploying admin to $ADMIN_TARGET_DIR..."
    sudo mkdir -p "$ADMIN_TARGET_DIR"
    if sudo rm -rf "$ADMIN_TARGET_DIR"/* && \
       sudo cp -r /tmp/frontend-dist/* "$ADMIN_TARGET_DIR/"; then
        sudo chown -R www-data:www-data "$ADMIN_TARGET_DIR"
        log_success "Admin deployed to $ADMIN_TARGET_DIR"
    else
        log_error "Failed to deploy admin"
        sudo rm -rf /tmp/frontend-dist
        docker compose -f "$COMPOSE_FILE" stop frontend 2>/dev/null || true
        return 1
    fi

    # Clean up temp directory
    sudo rm -rf /tmp/frontend-dist

    # Stop frontend container
    log_step "Stopping frontend build container..."
    docker compose -f "$COMPOSE_FILE" stop frontend 2>/dev/null || true

    log_success "Frontend deployed successfully"
    return 0
}

# ==========================================
# Check Services Status
# ==========================================

check_services() {
    log_header "🔍 SERVICES STATUS"

    # Check backend
    local backend_status=$(get_container_status "ai_mentor_backend_prod")
    local backend_health=$(get_container_health "ai_mentor_backend_prod")

    if [ "$backend_health" != "unknown" ]; then
        show_service_status "Backend" "$backend_health"
    else
        show_service_status "Backend" "$backend_status"
    fi

    # Check postgres
    local postgres_status=$(get_container_status "ai_mentor_postgres_prod")
    local postgres_health=$(get_container_health "ai_mentor_postgres_prod")

    if [ "$postgres_health" != "unknown" ]; then
        show_service_status "PostgreSQL" "$postgres_health"
    else
        show_service_status "PostgreSQL" "$postgres_status"
    fi

    # Check API endpoint
    if check_http_endpoint "http://127.0.0.1:8006/health" 5; then
        show_service_status "API Health" "healthy"
    else
        show_service_status "API Health" "unhealthy"
    fi

    # Check frontend files (landing)
    if [ -f "$FRONTEND_TARGET_DIR/index.html" ]; then
        show_service_status "Landing Files" "deployed"
    else
        show_service_status "Landing Files" "missing"
    fi

    # Check admin files
    if [ -f "$ADMIN_TARGET_DIR/index.html" ]; then
        show_service_status "Admin Files" "deployed"
    else
        show_service_status "Admin Files" "missing"
    fi

    echo ""
}

# ==========================================
# Show Usage
# ==========================================

show_usage() {
    cat << EOF

${EMOJI_ROCKET} AI Mentor - Smart Deploy Script

Usage: ./deploy.sh [mode]

Modes:
    auto         Automatically detect changes and deploy (default)
    backend      Force deploy backend only
    frontend     Force deploy frontend only
    migrations   Apply database migrations only
    full         Deploy everything (backend + frontend + migrations)

Examples:
    ./deploy.sh              # Auto-detect and deploy
    ./deploy.sh backend      # Deploy only backend
    ./deploy.sh frontend     # Deploy only frontend
    ./deploy.sh full         # Full deployment

EOF
}

# ==========================================
# Main Deployment Flow
# ==========================================

main() {
    # Show header
    clear
    log_header "🚀 AI MENTOR DEPLOYMENT"

    echo -e "${GRAY}Deploy Mode: ${CYAN}${DEPLOY_MODE}${NC}"
    echo -e "${GRAY}Git Branch:  ${CYAN}$(get_current_branch)${NC}"
    echo -e "${GRAY}Git Commit:  ${CYAN}$(get_current_commit)${NC}"
    echo ""

    # Start timer
    start_timer

    # Detect changes (only in auto mode)
    if [ "$DEPLOY_MODE" = "auto" ]; then
        detect_changes
    fi

    # Show deploy plan
    show_deploy_plan

    # Start deployment
    log_header "🚀 STARTING DEPLOYMENT"

    DEPLOYED_BACKEND=false
    DEPLOYED_FRONTEND=false
    APPLIED_MIGRATIONS=false
    DEPLOY_SUCCESS=true

    # Apply migrations first (if needed)
    if [ "$MIGRATIONS_CHANGED" = "true" ]; then
        if apply_migrations; then
            APPLIED_MIGRATIONS=true
        else
            DEPLOY_SUCCESS=false
            # Continue with deployment even if migrations fail
            # (migrations might fail if no new migrations exist)
        fi
        echo ""
    fi

    # Deploy backend
    if [ "$BACKEND_CHANGED" = "true" ]; then
        if deploy_backend; then
            DEPLOYED_BACKEND=true
        else
            DEPLOY_SUCCESS=false
            # Stop deployment on backend failure
            show_deploy_summary "$DEPLOYED_BACKEND" "$DEPLOYED_FRONTEND" "$APPLIED_MIGRATIONS" "false"
            exit 1
        fi
        echo ""
    fi

    # Deploy frontend
    if [ "$FRONTEND_CHANGED" = "true" ]; then
        if deploy_frontend; then
            DEPLOYED_FRONTEND=true
        else
            DEPLOY_SUCCESS=false
            # Frontend failure is not critical - backend still works
        fi
        echo ""
    fi

    # Check final status
    check_services

    # Show summary
    show_deploy_summary "$DEPLOYED_BACKEND" "$DEPLOYED_FRONTEND" "$APPLIED_MIGRATIONS" "$DEPLOY_SUCCESS"

    # Exit with appropriate code
    if [ "$DEPLOY_SUCCESS" = "true" ]; then
        exit 0
    else
        exit 1
    fi
}

# ==========================================
# Handle arguments
# ==========================================

case "${DEPLOY_MODE}" in
    auto|backend|frontend|migrations|full)
        main
        ;;
    help|--help|-h)
        show_usage
        exit 0
        ;;
    *)
        log_error "Unknown mode: ${DEPLOY_MODE}"
        show_usage
        exit 1
        ;;
esac
