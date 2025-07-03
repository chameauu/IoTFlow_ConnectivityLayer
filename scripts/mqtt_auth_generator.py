#!/usr/bin/env python3
"""
MQTT Password File Generator for Mosquitto
Generates mosquitto password file from registered devices in SQLite database
"""

import os
import sys
import hashlib
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models import Device, db
from src.config.config import Config
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_mosquitto_password_hash(password):
    """
    Create a mosquitto-compatible password hash
    Uses PBKDF2 which is what mosquitto_passwd uses
    """
    import base64
    import secrets
    import hashlib
    
    # Generate random salt (12 bytes)
    salt = secrets.token_bytes(12)
    
    # Use PBKDF2 with SHA256 (mosquitto default)
    iterations = 101  # mosquitto default
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    
    # Encode salt and hash in base64
    salt_b64 = base64.b64encode(salt).decode('ascii')
    hash_b64 = base64.b64encode(dk).decode('ascii')
    
    # Format: $6$salt$hash (mosquitto PBKDF2 format)
    return f"$6${salt_b64}${hash_b64}"

def generate_mosquitto_passwd_file(output_path):
    """
    Generate mosquitto password file from registered devices
    """
    try:
        # Initialize Flask app and database
        app = Flask(__name__)
        app.config.from_object(Config)
        
        with app.app_context():
            db.init_app(app)
            
            # Get all active devices
            devices = Device.query.filter_by(status='active').all()
            
            # Generate password file content
            passwd_lines = []
            passwd_lines.append("# Mosquitto password file - Generated automatically")
            passwd_lines.append("# Format: username:password (will be hashed by mosquitto)")
            passwd_lines.append("")
            
            if not devices:
                logger.warning("No active devices found in database")
                # Create empty but valid password file
                passwd_lines.append("# No devices registered yet")
                
                # Write to file
                with open(output_path, 'w') as f:
                    f.write('\n'.join(passwd_lines) + '\n')
                
                logger.info(f"Generated empty password file: {output_path}")
                return True
            
            for device in devices:
                username = str(device.id)  # Device ID as username
                password = device.api_key   # API key as password
                
                # Create simple username:password entry (mosquitto will hash it)
                passwd_lines.append(f"{username}:{password}")
                
                logger.info(f"Added device: {device.name} (ID: {device.id})")
            
            # Write to file
            with open(output_path, 'w') as f:
                f.write('\n'.join(passwd_lines) + '\n')
            
            logger.info(f"Generated password file with {len(devices)} devices: {output_path}")
            return True
            
    except Exception as e:
        logger.error(f"Error generating password file: {e}")
        return False

def generate_mosquitto_acl_file(output_path):
    """
    Generate mosquitto ACL file for device authorization
    """
    try:
        # Initialize Flask app and database
        app = Flask(__name__)
        app.config.from_object(Config)
        
        with app.app_context():
            db.init_app(app)
            
            # Get all active devices
            devices = Device.query.filter_by(status='active').all()
            
            acl_lines = []
            acl_lines.append("# Mosquitto ACL file - Generated automatically")
            acl_lines.append("# Device-specific topic access control")
            acl_lines.append("")
            
            if not devices:
                acl_lines.append("# No devices registered yet")
            else:
                for device in devices:
                    device_id = str(device.id)
                    
                    acl_lines.append(f"# Device: {device.name} (ID: {device.id})")
                    acl_lines.append(f"user {device_id}")
                    
                    # Allow publishing to device's own telemetry and status topics
                    acl_lines.append(f"topic write iotflow/devices/{device_id}/telemetry")
                    acl_lines.append(f"topic write iotflow/devices/{device_id}/status")
                    acl_lines.append(f"topic write iotflow/devices/{device_id}/heartbeat")
                    
                    # Allow subscribing to device's own command and config topics
                    acl_lines.append(f"topic read iotflow/devices/{device_id}/commands")
                    acl_lines.append(f"topic read iotflow/devices/{device_id}/config")
                    
                    acl_lines.append("")
            
            # Write to file
            with open(output_path, 'w') as f:
                f.write('\n'.join(acl_lines) + '\n')
            
            logger.info(f"Generated ACL file with {len(devices)} devices: {output_path}")
            return True
            
    except Exception as e:
        logger.error(f"Error generating ACL file: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python mqtt_auth_generator.py <command>")
        print("Commands:")
        print("  passwd - Generate password file")
        print("  acl    - Generate ACL file")
        print("  both   - Generate both files")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Default paths
    mqtt_config_dir = project_root / "mqtt" / "config"
    passwd_file = mqtt_config_dir / "passwd"
    acl_file = mqtt_config_dir / "acl.conf"
    
    # Ensure config directory exists
    mqtt_config_dir.mkdir(parents=True, exist_ok=True)
    
    success = True
    
    if command in ['passwd', 'both']:
        logger.info("Generating mosquitto password file...")
        success &= generate_mosquitto_passwd_file(passwd_file)
    
    if command in ['acl', 'both']:
        logger.info("Generating mosquitto ACL file...")
        success &= generate_mosquitto_acl_file(acl_file)
    
    if command not in ['passwd', 'acl', 'both']:
        logger.error(f"Unknown command: {command}")
        sys.exit(1)
    
    if success:
        logger.info("MQTT authentication files generated successfully")
        print("\nNext steps:")
        print("1. Restart mosquitto broker to reload authentication files")
        print("2. Test device connections with generated credentials")
    else:
        logger.error("Failed to generate MQTT authentication files")
        sys.exit(1)

if __name__ == "__main__":
    main()
