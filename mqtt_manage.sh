#!/bin/bash

# MQTT Management Script for IoTFlow
# Provides utilities for managing MQTT broker and user credentials

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MQTT_CONFIG_DIR="$PROJECT_DIR/mqtt/config"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to run docker compose (supports both v1 and v2)
docker_compose() {
    if command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    else
        docker compose "$@"
    fi
}

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Check if required tools are installed
check_dependencies() {
    info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check for docker compose (v2) or docker-compose (v1)
    if ! (command -v "docker-compose" &> /dev/null || docker compose version &> /dev/null); then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log "All dependencies are installed."
}

# Setup MQTT broker with Docker
setup_broker() {
    info "Setting up MQTT broker..."
    
    cd "$PROJECT_DIR"
    
    # Create necessary directories
    mkdir -p mqtt/data mqtt/logs mqtt/config
    
    # Set proper permissions
    chmod 755 mqtt/data mqtt/logs mqtt/config 2>/dev/null || true
    
    # Pull the Mosquitto image
    docker pull eclipse-mosquitto:2.0
    
    # Start the services
    docker_compose up -d mosquitto
    
    # Wait for broker to start
    sleep 5
    
    # Check if broker is running
    if docker ps | grep -q iotflow_mosquitto; then
        log "MQTT broker started successfully"
    else
        error "Failed to start MQTT broker"
        exit 1
    fi
}

# Create MQTT user credentials
create_user() {
    local username="$1"
    local password="$2"
    
    if [ -z "$username" ] || [ -z "$password" ]; then
        error "Usage: create_user <username> <password>"
        return 1
    fi
    
    info "Creating MQTT user: $username"
    
    # Use mosquitto_passwd command in container
    docker exec iotflow_mosquitto mosquitto_passwd -b /mosquitto/config/passwd "$username" "$password"
    
    if [ $? -eq 0 ]; then
        log "User '$username' created successfully"
        
        # Restart broker to reload password file
        docker restart iotflow_mosquitto
        log "MQTT broker restarted to reload credentials"
    else
        error "Failed to create user '$username'"
        return 1
    fi
}

# Delete MQTT user
delete_user() {
    local username="$1"
    
    if [ -z "$username" ]; then
        error "Usage: delete_user <username>"
        return 1
    fi
    
    info "Deleting MQTT user: $username"
    
    # Use mosquitto_passwd command in container
    docker exec iotflow_mosquitto mosquitto_passwd -D /mosquitto/config/passwd "$username"
    
    if [ $? -eq 0 ]; then
        log "User '$username' deleted successfully"
        
        # Restart broker to reload password file
        docker restart iotflow_mosquitto
        log "MQTT broker restarted to reload credentials"
    else
        error "Failed to delete user '$username'"
        return 1
    fi
}

# List MQTT users
list_users() {
    info "Listing MQTT users..."
    
    if [ -f "$MQTT_CONFIG_DIR/passwd" ]; then
        echo "Current MQTT users:"
        docker exec iotflow_mosquitto cat /mosquitto/config/passwd | cut -d: -f1
    else
        warn "No password file found"
    fi
}

# Setup initial admin user
setup_admin() {
    local admin_password="${1:-admin123}"
    
    info "Setting up admin user..."
    
    # Create admin user
    create_user "admin" "$admin_password"
    
    log "Admin user created with password: $admin_password"
    warn "Please change the default admin password in production!"
}

# Generate device credentials
generate_device_credentials() {
    local device_id="$1"
    
    if [ -z "$device_id" ]; then
        error "Usage: generate_device_credentials <device_id>"
        return 1
    fi
    
    # Generate random password
    local password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    info "Generating credentials for device: $device_id"
    
    # Create device user
    create_user "$device_id" "$password"
    
    log "Device credentials generated:"
    echo "  Device ID: $device_id"
    echo "  Username: $device_id"
    echo "  Password: $password"
    
    # Save credentials to file
    local creds_file="$PROJECT_DIR/device_credentials_$device_id.txt"
    echo "Device Credentials for $device_id" > "$creds_file"
    echo "=================================" >> "$creds_file"
    echo "Device ID: $device_id" >> "$creds_file"
    echo "Username: $device_id" >> "$creds_file"
    echo "Password: $password" >> "$creds_file"
    echo "MQTT Host: localhost" >> "$creds_file"
    echo "MQTT Port: 1883" >> "$creds_file"
    echo "Generated: $(date)" >> "$creds_file"
    
    log "Credentials saved to: $creds_file"
}

# Test MQTT connection
test_connection() {
    local username="${1:-admin}"
    local password="${2:-admin123}"
    
    info "Testing MQTT connection..."
    
    # Test publish
    docker exec iotflow_mosquitto mosquitto_pub -h localhost -p 1883 -u "$username" -P "$password" -t "iotflow/test" -m "Hello from IoTFlow"
    
    if [ $? -eq 0 ]; then
        log "MQTT connection test successful"
    else
        error "MQTT connection test failed"
        return 1
    fi
}

# Monitor MQTT broker logs
monitor_logs() {
    info "Monitoring MQTT broker logs (Press Ctrl+C to stop)..."
    docker logs -f iotflow_mosquitto
}

# Get broker status
broker_status() {
    info "MQTT Broker Status:"
    
    if docker ps | grep -q iotflow_mosquitto; then
        log "Broker is running"
        
        # Get container info
        echo ""
        info "Container Information:"
        docker ps --filter "name=iotflow_mosquitto" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        # Get broker statistics (if available)
        echo ""
        info "Broker Statistics:"
        docker exec iotflow_mosquitto mosquitto_sub -h localhost -t '$SYS/#' -C 10 2>/dev/null || echo "Statistics not available"
    else
        error "Broker is not running"
        return 1
    fi
}

# Stop MQTT broker
stop_broker() {
    info "Stopping MQTT broker..."
    docker_compose stop mosquitto
    log "MQTT broker stopped"
}

# Start MQTT broker
start_broker() {
    info "Starting MQTT broker..."
    docker_compose start mosquitto
    log "MQTT broker started"
}

# Restart MQTT broker
restart_broker() {
    info "Restarting MQTT broker..."
    docker_compose restart mosquitto
    log "MQTT broker restarted"
}

# Backup MQTT configuration
backup_config() {
    local backup_dir="$PROJECT_DIR/backups/mqtt_$(date +%Y%m%d_%H%M%S)"
    
    info "Creating backup of MQTT configuration..."
    
    mkdir -p "$backup_dir"
    
    # Backup configuration files
    cp -r "$MQTT_CONFIG_DIR" "$backup_dir/"
    
    # Backup data directory
    if [ -d "$PROJECT_DIR/mqtt/data" ]; then
        cp -r "$PROJECT_DIR/mqtt/data" "$backup_dir/"
    fi
    
    log "Backup created: $backup_dir"
}

# Show help
show_help() {
    echo "MQTT Management Script for IoTFlow"
    echo ""
    echo "Usage: $0 <command> [arguments]"
    echo ""
    echo "Commands:"
    echo "  setup              - Setup MQTT broker with Docker"
    echo "  setup-admin [pwd]  - Setup admin user (default password: admin123)"
    echo "  create-user <user> <password> - Create MQTT user"
    echo "  delete-user <user> - Delete MQTT user"
    echo "  list-users         - List all MQTT users"
    echo "  generate-device <device_id> - Generate device credentials"
    echo "  test [user] [pwd]  - Test MQTT connection"
    echo "  status             - Show broker status"
    echo "  logs               - Monitor broker logs"
    echo "  start              - Start MQTT broker"
    echo "  stop               - Stop MQTT broker"
    echo "  restart            - Restart MQTT broker"
    echo "  backup             - Backup MQTT configuration"
    echo "  help               - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 setup-admin mypassword"
    echo "  $0 create-user device001 secretpassword"
    echo "  $0 generate-device sensor_01"
    echo "  $0 test admin admin123"
}

# Main script logic
main() {
    case "$1" in
        setup)
            check_dependencies
            setup_broker
            ;;
        setup-admin)
            setup_admin "$2"
            ;;
        create-user)
            create_user "$2" "$3"
            ;;
        delete-user)
            delete_user "$2"
            ;;
        list-users)
            list_users
            ;;
        generate-device)
            generate_device_credentials "$2"
            ;;
        test)
            test_connection "$2" "$3"
            ;;
        status)
            broker_status
            ;;
        logs)
            monitor_logs
            ;;
        start)
            start_broker
            ;;
        stop)
            stop_broker
            ;;
        restart)
            restart_broker
            ;;
        backup)
            backup_config
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
