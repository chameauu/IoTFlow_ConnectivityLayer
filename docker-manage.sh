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

# Check if Poetry is available
check_poetry() {
    if ! command -v poetry > /dev/null 2>&1; then
        log_error "Poetry is not available. Please install Poetry first."
        exit 1
    fi
    log_info "Poetry is available"
}

# Start services
start_services() {
    log_step "Starting Redis, IoTDB, and MQTT services..."
    docker compose up -d redis iotdb mosquitto
    
    log_step "Waiting for services to be ready..."
    
    # Wait for IoTDB
    log_info "Waiting for IoTDB to be ready..."
    timeout=60
    counter=0
    while ! nc -z localhost 6667 > /dev/null 2>&1; do
        if [ $counter -eq $timeout ]; then
            log_error "IoTDB failed to start within $timeout seconds"
            exit 1
        fi
        sleep 1
        counter=$((counter + 1))
    done
    log_info "IoTDB is ready"
    
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
    
    # Check MQTT broker
    log_info "Checking MQTT broker..."
    if docker compose ps mosquitto | grep -q "Up"; then
        log_info "MQTT broker is running"
    else
        log_warn "MQTT broker may not be running properly"
    fi
    
    log_info "All services are ready!"
}

# Start all services
start_all() {
    log_step "Starting all services (Redis, IoTDB, MQTT)..."
    docker compose up -d
    
    log_step "Waiting for services to be ready..."
    start_services
    
    log_info "IoTDB UI is available at: http://localhost:8181"
    log_info "MQTT broker is running on port 1883 (TLS: 8883, WebSocket: 9001)"
}

# Initialize Python environment and database
init_app() {
    log_step "Initializing application..."
    check_poetry
    
    log_info "Installing Python dependencies..."
    poetry install
    
    log_info "Initializing SQLite database..."
    poetry run python manage.py init-db
    
    log_info "Application initialized successfully!"
}

# Run the Flask application
run_app() {
    log_step "Starting Flask application..."
    check_poetry
    poetry run python manage.py run
}

# Run tests
test_app() {
    log_step "Running application tests..."
    check_poetry
    poetry run python manage.py test
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
    log_warn "This will delete ALL data including SQLite database and Docker volumes!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_step "Stopping services..."
        docker compose down
        
        log_step "Removing Docker volumes..."
        docker compose down -v
        
        log_step "Removing SQLite database..."
        rm -f iotflow.db
        
        log_step "Removing logs directory..."
        rm -rf logs
        
        log_info "Data reset completed. Run 'init-app' to reinitialize."
    else
        log_info "Reset cancelled"
    fi
}

# Connect to Redis
redis_cli() {
    log_step "Connecting to Redis..."
    docker compose exec redis redis-cli
}

# Connect to IoTDB CLI
iotdb_cli() {
    log_step "Connecting to IoTDB CLI..."
    docker compose exec iotdb /iotdb/sbin/start-cli.sh -h localhost -p 6667 -u root -pw root
}

# Backup SQLite database
backup() {
    backup_file="backup_$(date +%Y%m%d_%H%M%S).db"
    log_step "Creating SQLite database backup: $backup_file"
    if [ -f "iotflow.db" ]; then
        cp iotflow.db "$backup_file"
        log_info "SQLite backup created: $backup_file"
    else
        log_error "SQLite database file not found. Run 'init-app' first."
        exit 1
    fi
}

# Restore SQLite database
restore() {
    if [ -z "$2" ]; then
        log_error "Please provide backup file: $0 restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$2" ]; then
        log_error "Backup file not found: $2"
        exit 1
    fi
    
    log_warn "This will replace the current SQLite database!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_step "Restoring SQLite database from: $2"
        cp "$2" iotflow.db
        log_info "Database restored successfully"
    else
        log_info "Restore cancelled"
    fi
}

# Update MQTT authentication files and restart mosquitto
update_mqtt_auth() {
    log_step "Updating MQTT authentication files..."
    
    # Generate MQTT authentication files
    log_info "Generating MQTT password and ACL files..."
    if poetry run python scripts/mqtt_auth_generator.py both; then
        log_info "MQTT authentication files generated successfully"
    else
        log_error "Failed to generate MQTT authentication files"
        return 1
    fi
    
    # Restart mosquitto container to reload auth files
    log_info "Restarting mosquitto container to reload authentication..."
    if docker compose restart mosquitto; then
        log_info "Mosquitto restarted successfully"
        
        # Wait for mosquitto to be ready
        sleep 3
        if docker compose ps mosquitto | grep -q "Up"; then
            log_info "MQTT broker is ready with updated authentication"
        else
            log_warn "MQTT broker may not be running properly after restart"
        fi
    else
        log_error "Failed to restart mosquitto container"
        return 1
    fi
    
    log_info "MQTT authentication update completed"
}

# Initialize app with MQTT auth setup
init_app_with_auth() {
    log_step "Initializing application with MQTT authentication..."
    
    # First initialize the app
    init_app
    
    # Then update MQTT auth
    update_mqtt_auth
    
    log_info "Application initialization with MQTT authentication completed"
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
    "init-app")
        check_docker
        check_docker_compose
        init_app
        ;;
    "init-app-auth")
        check_docker
        check_docker_compose
        init_app_with_auth
        ;;
    "update-mqtt-auth")
        check_docker
        check_docker_compose
        update_mqtt_auth
        ;;
    "run")
        run_app
        ;;
    "test")
        test_app
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
    "redis")
        redis_cli
        ;;
    "iotdb")
        iotdb_cli
        ;;
    "backup")
        backup
        ;;
    "restore")
        restore "$@"
        ;;
    *)
        echo "IoT Connectivity Layer - Docker Management"
        echo "Usage: $0 {start|start-all|init-app|init-app-auth|update-mqtt-auth|run|test|stop|restart|status|logs|reset|redis|iotdb|backup|restore}"
        echo ""
        echo "Commands:"
        echo "  start           - Start Redis, IoTDB, and MQTT services"
        echo "  start-all       - Start all services"
        echo "  init-app        - Initialize Python environment and SQLite database"
        echo "  init-app-auth   - Initialize app and setup MQTT authentication"
        echo "  update-mqtt-auth - Update MQTT authentication files and restart mosquitto"
        echo "  run             - Run Flask application (uses Poetry)"
        echo "  test            - Run application tests (uses Poetry)"
        echo "  stop            - Stop all services"
        echo "  restart         - Restart services"
        echo "  status          - Show service status"
        echo "  logs            - Show logs (optionally for specific service)"
        echo "  reset           - Reset all data (DANGEROUS!)"
        echo "  redis           - Connect to Redis CLI"
        echo "  iotdb           - Connect to IoTDB CLI"
        echo "  backup          - Create SQLite database backup"
        echo "  restore         - Restore SQLite database from backup"
        echo ""
        echo "Examples:"
        echo "  $0 start-all              # Start all services"
        echo "  $0 init-app-auth          # Initialize app with MQTT auth"
        echo "  $0 update-mqtt-auth       # Update MQTT authentication"
        echo "  $0 run                    # Run Flask app"
        echo "  $0 logs mosquitto         # Show mosquitto logs"
        echo "  $0 restore backup_20250702_120000.db"
        exit 1
        ;;
esac
