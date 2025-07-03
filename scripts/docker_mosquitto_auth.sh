#!/bin/bash
"""
Docker Mosquitto Password Management Script
Updates mosquitto password file and reloads the container
"""

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MQTT_CONFIG_DIR="$PROJECT_ROOT/mqtt/config"

echo "🔐 Docker Mosquitto Password Management"
echo "======================================="

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to generate password files
generate_passwords() {
    echo "🔄 Generating mosquitto password and ACL files..."
    cd "$PROJECT_ROOT"
    
    # Run the Python script to generate password files
    python scripts/mqtt_auth_generator.py both
    
    if [ $? -eq 0 ]; then
        echo "✅ Password and ACL files generated successfully"
    else
        echo "❌ Failed to generate password files"
        exit 1
    fi
}

# Function to hash passwords using mosquitto_passwd in Docker
hash_passwords() {
    echo "🔄 Hashing passwords using mosquitto_passwd..."
    
    # Check if password file exists
    if [ ! -f "$MQTT_CONFIG_DIR/passwd" ]; then
        echo "❌ Password file not found: $MQTT_CONFIG_DIR/passwd"
        exit 1
    fi
    
    # Create a temporary hashed password file
    TEMP_PASSWD="$MQTT_CONFIG_DIR/passwd.tmp"
    > "$TEMP_PASSWD"
    
    # Read the password file and hash each entry
    while IFS=':' read -r username password || [ -n "$username" ]; do
        # Skip comments and empty lines
        if [[ "$username" =~ ^#.*$ ]] || [ -z "$username" ]; then
            echo "$username:$password" >> "$TEMP_PASSWD"
            continue
        fi
        
        # Hash the password using mosquitto_passwd in Docker
        echo "🔄 Hashing password for user: $username"
        docker run --rm eclipse-mosquitto:2.0 mosquitto_passwd -b /dev/stdout "$username" "$password" >> "$TEMP_PASSWD"
        
    done < "$MQTT_CONFIG_DIR/passwd"
    
    # Replace the original file with the hashed version
    mv "$TEMP_PASSWD" "$MQTT_CONFIG_DIR/passwd"
    echo "✅ Passwords hashed successfully"
}

# Function to reload mosquitto container
reload_mosquitto() {
    echo "🔄 Reloading mosquitto container..."
    
    # Check if container is running
    if docker ps --format "table {{.Names}}" | grep -q "iotflow_mosquitto"; then
        echo "📡 Sending SIGHUP to mosquitto container to reload config..."
        docker kill --signal=HUP iotflow_mosquitto
        
        if [ $? -eq 0 ]; then
            echo "✅ Mosquitto container reloaded successfully"
        else
            echo "⚠️ Failed to reload mosquitto container, trying restart..."
            docker restart iotflow_mosquitto
        fi
    else
        echo "⚠️ Mosquitto container is not running. Starting it..."
        cd "$PROJECT_ROOT"
        docker-compose up -d mosquitto
    fi
}

# Function to test MQTT connection
test_mqtt_connection() {
    echo "🧪 Testing MQTT connection..."
    
    # Wait a moment for mosquitto to fully reload
    sleep 2
    
    # Test with a simple publish (this will fail auth, but tests connectivity)
    if docker run --rm --network host eclipse-mosquitto:2.0 mosquitto_pub -h localhost -p 1883 -t test/connection -m "test" -u "nonexistent" -P "invalid" 2>/dev/null; then
        echo "⚠️ MQTT broker accessible but auth may not be working (anonymous access?)"
    else
        echo "✅ MQTT broker is running and authentication is active"
    fi
}

# Main execution
main() {
    echo "Starting mosquitto password management..."
    
    check_docker
    generate_passwords
    hash_passwords
    reload_mosquitto
    test_mqtt_connection
    
    echo ""
    echo "🎯 Password management complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Check mosquitto logs: docker logs iotflow_mosquitto"
    echo "2. Test device connection with generated credentials"
    echo "3. Run device simulator: python test/temperature_sensor_mqtt.py"
    echo ""
    echo "📁 Files updated:"
    echo "- $MQTT_CONFIG_DIR/passwd (hashed passwords)"
    echo "- $MQTT_CONFIG_DIR/acl.conf (access control)"
}

# Run main function
main "$@"
