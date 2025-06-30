#!/usr/bin/env python3
# Copyright (c) 2025 Isaac Gounton
#
# Bootstrap script to initialize the API key management system

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.api_keys import APIKeyManager
from config import LOCAL_STORAGE_PATH

def bootstrap_admin():
    """Initialize the API key management system with an admin user"""
    
    print("🚀 Bootstrapping DahoPevi API Key Management System...")
    
    try:
        # Initialize the API key manager
        api_manager = APIKeyManager()
        print("✅ Database initialized successfully")
        
        # Check if admin user already exists
        users = api_manager.get_all_users()
        admin_user = next((user for user in users if user['username'] == 'admin'), None)
        
        if admin_user:
            print(f"✅ Admin user already exists (ID: {admin_user['id']})")
            user_id = admin_user['id']
        else:
            # Create admin user
            user_id = api_manager.create_user(
                username='admin',
                email='admin@dahopevi.local'
            )
            print(f"✅ Created admin user (ID: {user_id})")
        
        # Check if admin API key exists
        admin_keys = api_manager.get_user_api_keys(user_id)
        admin_key = next((key for key in admin_keys if key['key_name'] == 'Admin Dashboard Key'), None)
        
        if admin_key and admin_key['is_active']:
            print("✅ Admin API key already exists and is active")
            print("🔑 Admin key is ready for use in the dashboard")
        else:
            # Create admin API key
            api_key = api_manager.create_api_key(
                user_id=user_id,
                key_name='Admin Dashboard Key',
                permissions='admin',
                rate_limit=10000,  # High rate limit for admin
                expires_days=None  # Never expires
            )
            print("✅ Created admin API key")
            print(f"🔑 Admin API Key: {api_key}")
            print("⚠️  IMPORTANT: Save this key securely - it won't be shown again!")
            
            # Also save to a secure location for Docker startup
            import os
            key_file = os.path.join(LOCAL_STORAGE_PATH, '.admin_key')
            try:
                with open(key_file, 'w') as f:
                    f.write(api_key)
                print(f"📁 Admin key also saved to: {key_file}")
            except Exception as e:
                print(f"⚠️  Could not save admin key to file: {e}")
        
        print("\n🎉 Bootstrap completed successfully!")
        print(f"📁 Database location: {os.path.join(LOCAL_STORAGE_PATH, 'api_keys.db')}")
        print("🌐 Access the dashboard at: /admin/api-keys")
        print("🔑 Use your legacy API key or the admin key created above")
        
    except Exception as e:
        print(f"❌ Bootstrap failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    bootstrap_admin()