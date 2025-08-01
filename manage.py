#!/usr/bin/env python3
"""
Management script for IoT Connectivity Layer

Usage:
    poetry run python manage.py <command>
    
Commands:
    init-db               - Initialize SQLite database with tables
    create-device <name>  - Create a new device and generate API key
    run                   - Start the Flask development server
    test                  - Run tests using pytest
    shell                 - Start interactive Python shell with app context
"""
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app, db
from src.models import Device
import secrets
import string

def generate_api_key(length=32):
    """Generate a secure API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def init_db():
    """Initialize the database"""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

def create_device(name):
    """Create a new device"""
    app = create_app()
    with app.app_context():
        api_key = generate_api_key()
        device = Device(name=name, api_key=api_key, status='active')
        db.session.add(device)
        db.session.commit()
        print(f"Device created successfully!")
        print(f"Device Name: {name}")
        print(f"API Key: {api_key}")
        print(f"Device ID: {device.id}")



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'init-db':
        init_db()
    elif command == 'create-device':
        if len(sys.argv) < 3:
            print("Usage: poetry run python manage.py create-device <name>")
            sys.exit(1)
        create_device(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
