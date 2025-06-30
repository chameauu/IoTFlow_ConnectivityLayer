#!/bin/bash
# Docker management script for IoT Connectivity Layer

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log_info "Docker is running"
}

# Check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker > /dev/null 2>&1 || ! docker compose version > /dev/null 2>&1; then
        log_error "Docker Compose is not available. Please install Docker with Compose plugin."
        exit 1
    fi
    log_info "Docker Compose is available"
}

# Start services
start_services() {
    log_step "Starting PostgreSQL and Redis services..."
    docker compose up -d postgres redis
    
    log_step "Waiting for services to be ready..."
    
    # Wait for PostgreSQL
    log_info "Waiting for PostgreSQL to be ready..."
    timeout=60
    counter=0
    while ! docker compose exec postgres pg_isready -U iotflow_user -d iotflow_db > /dev/null 2>&1; do
        if [ $counter -eq $timeout ]; then
            log_error "PostgreSQL failed to start within $timeout seconds"
            exit 1
        fi
        sleep 1
        counter=$((counter + 1))
    done
    log_info "PostgreSQL is ready"
    
    # Wait for Redis
    log_info "Waiting for Redis to be ready..."
    counter=0
    while ! docker compose exec redis redis-cli ping > /dev/null 2>&1; do
        if [ $counter -eq $timeout ]; then
            log_error "Redis failed to start within $timeout seconds"
            exit 1
        fi
        sleep 1
        counter=$((counter + 1))
    done
    log_info "Redis is ready"
    
    log_info "All services are ready!"
}

# Start all services including pgAdmin
start_all() {
    log_step "Starting all services (PostgreSQL, Redis, pgAdmin)..."
    docker compose up -d
    
    log_step "Waiting for services to be ready..."
    start_services
    
    log_info "pgAdmin is available at: http://localhost:8080"
    log_info "  Email: admin@iotflow.com"
    log_info "  Password: admin123"
}

# Stop services
stop_services() {
    log_step "Stopping services..."
    docker compose down
    log_info "Services stopped"
}

# Show service status
status() {
    log_step "Service status:"
    docker compose ps
}

# Show logs
logs() {
    if [ -n "$2" ]; then
        log_step "Showing logs for $2..."
        docker compose logs -f "$2"
    else
        log_step "Showing logs for all services..."
        docker compose logs -f
    fi
}

# Reset data (dangerous!)
reset_data() {
    log_warn "This will delete ALL data in the database and Redis!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_step "Stopping services..."
        docker compose down
        
        log_step "Removing volumes..."
        docker compose down -v
        docker volume rm connectivity_layer_postgres_data connectivity_layer_redis_data connectivity_layer_pgadmin_data 2>/dev/null || true
        
        log_step "Starting services with fresh data..."
        start_services
        log_info "Data reset completed"
    else
        log_info "Reset cancelled"
    fi
}

# Connect to PostgreSQL
psql() {
    log_step "Connecting to PostgreSQL..."
    docker compose exec postgres psql -U iotflow_user -d iotflow_db
}

# Connect to Redis
redis_cli() {
    log_step "Connecting to Redis..."
    docker compose exec redis redis-cli
}

# Backup database
backup() {
    backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    log_step "Creating database backup: $backup_file"
    docker compose exec postgres pg_dump -U iotflow_user -d iotflow_db > "$backup_file"
    log_info "Backup created: $backup_file"
}

# Restore database
restore() {
    if [ -z "$2" ]; then
        log_error "Please provide backup file: $0 restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$2" ]; then
        log_error "Backup file not found: $2"
        exit 1
    fi
    
    log_warn "This will replace all data in the database!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_step "Restoring database from: $2"
        docker compose exec -T postgres psql -U iotflow_user -d iotflow_db < "$2"
        log_info "Database restored successfully"
    else
        log_info "Restore cancelled"
    fi
}

# Main script
case "$1" in
    "start")
        check_docker
        check_docker_compose
        start_services
        ;;
    "start-all")
        check_docker
        check_docker_compose
        start_all
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        start_services
        ;;
    "status")
        status
        ;;
    "logs")
        logs "$@"
        ;;
    "reset")
        check_docker
        check_docker_compose
        reset_data
        ;;
    "psql")
        psql
        ;;
    "redis")
        redis_cli
        ;;
    "backup")
        backup
        ;;
    "restore")
        restore "$@"
        ;;
    *)
        echo "IoT Connectivity Layer - Docker Management"
        echo "Usage: $0 {start|start-all|stop|restart|status|logs|reset|psql|redis|backup|restore}"
        echo ""
        echo "Commands:"
        echo "  start      - Start PostgreSQL and Redis"
        echo "  start-all  - Start all services including pgAdmin"
        echo "  stop       - Stop all services"
        echo "  restart    - Restart services"
        echo "  status     - Show service status"
        echo "  logs       - Show logs (optionally for specific service)"
        echo "  reset      - Reset all data (DANGEROUS!)"
        echo "  psql       - Connect to PostgreSQL"
        echo "  redis      - Connect to Redis CLI"
        echo "  backup     - Create database backup"
        echo "  restore    - Restore database from backup"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 logs postgres"
        echo "  $0 backup"
        echo "  $0 restore backup_20250630_120000.sql"
        exit 1
        ;;
esac
