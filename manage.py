#!/usr/bin/env python3
"""
Management script for IoT Connectivity Layer

Usage:
    poetry run python manage.py <command>
    
Commands:
    init-db    - Initialize database with tables
    create-device <name> - Create a new device
    run        - Start the Flask development server
    test       - Run tests
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

def run_app():
    """Run the Flask development server"""
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

def run_tests():
    """Run tests"""
    os.system('poetry run pytest')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'init-db':
        init_db()
    elif command == 'create-device':
        if len(sys.argv) < 3:
            print("Usage: python manage.py create-device <name>")
            sys.exit(1)
        create_device(sys.argv[2])
    elif command == 'run':
        run_app()
    elif command == 'test':
        run_tests()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
