#!/usr/bin/env python3

import sys
sys.path.append('/app')

def test_key_validation():
    print("=== API Key Validation Test ===")
    
    from models.api_keys import APIKeyManager
    import hashlib
    
    api_manager = APIKeyManager()
    
    # Test keys
    legacy_key = "g1f7dcb8499ea2c7cb8d8c99a7a153p3a0i2fb3dbd97c152a8567ecfa5b31872"
    generated_key = "dahopevi_PoxQDl4Lfi5R75BsGhgEmPdZvWoROZI02j4sGTlf7Rw"
    
    print(f"Testing legacy key: {legacy_key[:20]}...")
    result = api_manager.validate_api_key(legacy_key)
    print(f"Legacy key validation result: {result}")
    
    print(f"\nTesting generated key: {generated_key[:20]}...")
    result = api_manager.validate_api_key(generated_key)
    print(f"Generated key validation result: {result}")
    
    # Check what's actually in the database
    import sqlite3
    conn = sqlite3.connect('/tmp/api_keys.db')
    cursor = conn.cursor()
    cursor.execute("SELECT key_hash, key_prefix FROM api_keys")
    stored_keys = cursor.fetchall()
    
    print(f"\nStored key hashes in database:")
    for key_hash, prefix in stored_keys:
        print(f"  Hash: {key_hash[:20]}... Prefix: {prefix}")
    
    # Test if our generated key hash matches
    generated_hash = hashlib.sha256(generated_key.encode()).hexdigest()
    print(f"\nGenerated key hash: {generated_hash[:20]}...")
    
    # Check if it matches any stored hash
    for stored_hash, prefix in stored_keys:
        if stored_hash == generated_hash:
            print(f"✅ Generated key hash MATCHES stored hash with prefix: {prefix}")
            break
    else:
        print(f"❌ Generated key hash does NOT match any stored hash")
    
    conn.close()

if __name__ == "__main__":
    test_key_validation()