#!/usr/bin/env python3
"""
Debug script to check and create users for device registration testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from src.models import User, db
from werkzeug.security import generate_password_hash

def check_and_create_user():
    with app.app_context():
        try:
            # Check existing users
            print("=== Existing Users ===")
            users = User.query.all()
            for user in users:
                print(f"  - Username: {user.username}, Email: {user.email}, Active: {user.is_active}, User_ID: {user.user_id}")
            print(f"Total users: {len(users)}\n")
            
            # Check if 'newuser' exists
            newuser = User.query.filter_by(username='newuser').first()
            if newuser:
                print("✓ User 'newuser' already exists")
                print(f"  - Email: {newuser.email}")
                print(f"  - Active: {newuser.is_active}")
                print(f"  - Admin: {newuser.is_admin}")
                print(f"  - User_ID: {newuser.user_id}")
                return newuser.user_id
            else:
                print("✗ User 'newuser' does not exist. Creating...")
                
                # Create newuser
                new_user = User(
                    username="newuser",
                    email="newuser@example.com",
                    password_hash=generate_password_hash("test123"),
                    is_active=True,
                    is_admin=False
                )
                
                db.session.add(new_user)
                db.session.commit()
                print("✓ User 'newuser' created successfully!")
                print(f"  - Email: {new_user.email}")
                print(f"  - Password: test123 (for testing)")
                
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    user_id = check_and_create_user()
    print(f"\nUser ID for testing: {user_id}")
