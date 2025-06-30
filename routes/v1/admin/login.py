# Copyright (c) 2025 Isaac Gounton

from flask import Blueprint, request, jsonify, make_response
from models.api_keys import APIKeyManager
import hashlib
import os
import time
import hmac
import base64

try:
    import jwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False

admin_login_bp = Blueprint('admin_login', __name__)
api_manager = APIKeyManager()

@admin_login_bp.route('/admin')
def admin_login():
    """Admin login page"""
    
    login_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DahoPevi Admin Login</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
    <div class="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div class="max-w-md w-full space-y-8">
            <div class="text-center">
                <i class="fas fa-shield-alt text-6xl text-blue-600 mb-4"></i>
                <h2 class="text-3xl font-extrabold text-gray-900">
                    DahoPevi Admin
                </h2>
                <p class="mt-2 text-sm text-gray-600">
                    API Key Management Dashboard
                </p>
            </div>
            
            <div class="bg-white rounded-lg shadow-md p-8">
                <!-- Login Method Toggle -->
                <div class="mb-6">
                    <div class="flex border-b border-gray-200">
                        <button type="button" id="apiKeyTab" class="py-2 px-4 text-sm font-medium text-blue-600 border-b-2 border-blue-600">
                            API Key
                        </button>
                        <button type="button" id="passwordTab" class="py-2 px-4 text-sm font-medium text-gray-500 hover:text-gray-700 ml-4">
                            Username/Password
                        </button>
                    </div>
                </div>

                <!-- API Key Form -->
                <form id="apiKeyForm" class="space-y-6">
                    <div>
                        <label for="apiKey" class="sr-only">API Key</label>
                        <div class="relative">
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <i class="fas fa-key text-gray-400"></i>
                            </div>
                            <input 
                                id="apiKey" 
                                name="apiKey" 
                                type="password" 
                                required 
                                class="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-md placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                                placeholder="Enter your API key"
                            >
                        </div>
                    </div>
                    <div>
                        <button 
                            type="submit" 
                            class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 ease-in-out"
                        >
                            <span class="absolute left-0 inset-y-0 flex items-center pl-3">
                                <i class="fas fa-sign-in-alt text-blue-500 group-hover:text-blue-400"></i>
                            </span>
                            Access Dashboard
                        </button>
                    </div>
                </form>

                <!-- Username/Password Form -->
                <form id="passwordForm" class="space-y-6 hidden">
                    <div>
                        <label for="username" class="sr-only">Username</label>
                        <div class="relative">
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <i class="fas fa-user text-gray-400"></i>
                            </div>
                            <input 
                                id="username" 
                                name="username" 
                                type="text" 
                                required 
                                class="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-md placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                                placeholder="Username"
                            >
                        </div>
                    </div>
                    <div>
                        <label for="password" class="sr-only">Password</label>
                        <div class="relative">
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <i class="fas fa-lock text-gray-400"></i>
                            </div>
                            <input 
                                id="password" 
                                name="password" 
                                type="password" 
                                required 
                                class="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-md placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                                placeholder="Password"
                            >
                        </div>
                    </div>
                    <div>
                        <button 
                            type="submit" 
                            class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 ease-in-out"
                        >
                            <span class="absolute left-0 inset-y-0 flex items-center pl-3">
                                <i class="fas fa-sign-in-alt text-blue-500 group-hover:text-blue-400"></i>
                            </span>
                            Login
                        </button>
                    </div>
                </form>
                
                <div id="errorMessage" class="mt-4 hidden">
                    <div class="bg-red-50 border border-red-200 rounded-md p-4">
                        <div class="flex">
                            <div class="flex-shrink-0">
                                <i class="fas fa-exclamation-triangle text-red-400"></i>
                            </div>
                            <div class="ml-3">
                                <h3 class="text-sm font-medium text-red-800">
                                    Authentication Failed
                                </h3>
                                <div class="mt-2 text-sm text-red-700">
                                    <p>Invalid API key. Please check your key and try again.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-6 border-t border-gray-200 pt-6">
                    <div class="text-sm text-gray-600">
                        <h4 class="font-medium text-gray-900 mb-2">Access Options:</h4>
                        <ul class="space-y-1">
                            <li>• <strong>API Key:</strong> Use your legacy API key (from environment)</li>
                            <li>• <strong>Username/Password:</strong> Use admin credentials (from environment)</li>
                            <li>• Use any valid user API key with admin permissions</li>
                        </ul>
                        <div class="mt-3 p-3 bg-blue-50 rounded-md">
                            <p class="text-xs text-blue-800">
                                <i class="fas fa-info-circle mr-1"></i>
                                Default admin credentials are configured via <code>ADMIN_USERNAME</code> and <code>ADMIN_PASSWORD</code> environment variables.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="text-center">
                <p class="text-sm text-gray-500">
                    Need help? Check the 
                    <a href="/admin/setup" class="font-medium text-blue-600 hover:text-blue-500">setup guide</a>
                </p>
            </div>
        </div>
    </div>

    <script>
        // Tab switching functionality
        document.getElementById('apiKeyTab').addEventListener('click', function() {
            // Switch to API key tab
            document.getElementById('apiKeyTab').className = 'py-2 px-4 text-sm font-medium text-blue-600 border-b-2 border-blue-600';
            document.getElementById('passwordTab').className = 'py-2 px-4 text-sm font-medium text-gray-500 hover:text-gray-700 ml-4';
            document.getElementById('apiKeyForm').classList.remove('hidden');
            document.getElementById('passwordForm').classList.add('hidden');
        });

        document.getElementById('passwordTab').addEventListener('click', function() {
            // Switch to password tab
            document.getElementById('passwordTab').className = 'py-2 px-4 text-sm font-medium text-blue-600 border-b-2 border-blue-600 ml-4';
            document.getElementById('apiKeyTab').className = 'py-2 px-4 text-sm font-medium text-gray-500 hover:text-gray-700';
            document.getElementById('passwordForm').classList.remove('hidden');
            document.getElementById('apiKeyForm').classList.add('hidden');
        });

        // API Key Form Handler
        document.getElementById('apiKeyForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const apiKey = document.getElementById('apiKey').value.trim();
            const errorDiv = document.getElementById('errorMessage');
            const submitButton = document.querySelector('button[type="submit"]');
            
            // Hide previous errors
            errorDiv.classList.add('hidden');
            
            // Show loading state
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Authenticating...';
            
            try {
                console.log('Attempting authentication with API key:', apiKey.substring(0, 10) + '...');
                
                // Test authentication with the provided API key
                const response = await fetch('/v1/toolkit/authenticate', {
                    method: 'GET',
                    headers: {
                        'X-API-Key': apiKey,
                        'Content-Type': 'application/json'
                    }
                });
                
                console.log('Auth response status:', response.status);
                const responseData = await response.json();
                console.log('Auth response data:', responseData);
                
                if (response.ok) {
                    // Store the API key securely
                    sessionStorage.setItem('admin_api_key', apiKey);
                    console.log('API key stored in sessionStorage');
                    
                    // Verify storage worked
                    const storedKey = sessionStorage.getItem('admin_api_key');
                    console.log('Verified stored key:', storedKey ? storedKey.substring(0, 10) + '...' : 'null');
                    
                    // Small delay to ensure storage is complete
                    setTimeout(() => {
                        console.log('Redirecting to dashboard...');
                        window.location.href = '/admin/api-keys';
                    }, 100);
                } else {
                    console.error('Authentication failed:', response.status, responseData);
                    // Show error message
                    errorDiv.classList.remove('hidden');
                    errorDiv.querySelector('p').textContent = `Authentication failed: ${responseData.message || 'Invalid API key'}`;
                }
            } catch (error) {
                console.error('Authentication error:', error);
                errorDiv.classList.remove('hidden');
                errorDiv.querySelector('p').textContent = `Network error: ${error.message}`;
            } finally {
                // Reset button state
                submitButton.disabled = false;
                submitButton.innerHTML = '<span class="absolute left-0 inset-y-0 flex items-center pl-3"><i class="fas fa-sign-in-alt text-blue-500 group-hover:text-blue-400"></i></span>Access Dashboard';
            }
        });

        // Username/Password Form Handler
        document.getElementById('passwordForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('errorMessage');
            const submitButton = document.querySelector('#passwordForm button[type="submit"]');
            
            // Hide previous errors
            errorDiv.classList.add('hidden');
            
            // Show loading state
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Authenticating...';
            
            try {
                console.log('Attempting login with username:', username);
                
                const response = await fetch('/v1/admin/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                });
                
                console.log('Login response status:', response.status);
                const responseData = await response.json();
                console.log('Login response data:', responseData);
                
                if (response.ok) {
                    // Cookie is automatically set by the server
                    console.log('Login successful, cookie set by server');
                    
                    // Small delay to ensure cookie is set
                    setTimeout(() => {
                        console.log('Redirecting to dashboard...');
                        window.location.href = '/admin/api-keys';
                    }, 100);
                } else {
                    console.error('Login failed:', response.status, responseData);
                    errorDiv.classList.remove('hidden');
                    errorDiv.querySelector('p').textContent = `Login failed: ${responseData.message || 'Invalid credentials'}`;
                }
            } catch (error) {
                console.error('Login error:', error);
                errorDiv.classList.remove('hidden');
                errorDiv.querySelector('p').textContent = `Network error: ${error.message}`;
            } finally {
                // Reset button state
                submitButton.disabled = false;
                submitButton.innerHTML = '<span class="absolute left-0 inset-y-0 flex items-center pl-3"><i class="fas fa-sign-in-alt text-blue-500 group-hover:text-blue-400"></i></span>Login';
            }
        });
        
        // Auto-fill if there's a stored key
        const storedKey = sessionStorage.getItem('admin_api_key');
        if (storedKey) {
            document.getElementById('apiKey').value = storedKey;
        }
    </script>
</body>
</html>
    """
    
    return login_html

def generate_secure_token(username, api_key):
    """Generate a secure token (JWT if available, otherwise custom HMAC)"""
    if HAS_JWT:
        return generate_jwt_token(username, api_key)
    else:
        return generate_hmac_token(username, api_key)

def verify_secure_token(token):
    """Verify secure token (JWT if available, otherwise custom HMAC)"""
    if HAS_JWT:
        return verify_jwt_token(token)
    else:
        return verify_hmac_token(token)

def generate_jwt_token(username, api_key):
    """Generate a secure JWT token"""
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'username': username,
        'api_key': api_key,
        'exp': now + datetime.timedelta(hours=24),  # 24 hour expiry
        'iat': now,
        'iss': 'dahopevi-admin'
    }
    
    # Use JWT secret from environment
    secret = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
    return jwt.encode(payload, secret, algorithm='HS256')

def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        secret = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_hmac_token(username, api_key):
    """Generate a secure HMAC-based token (fallback when JWT not available)"""
    secret = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key').encode()
    expiry = int(time.time()) + (24 * 60 * 60)  # 24 hours
    
    # Create payload: username|api_key|expiry
    payload = f"{username}|{api_key}|{expiry}"
    
    # Create HMAC signature
    signature = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
    
    # Combine payload and signature
    token_data = f"{payload}|{signature}"
    
    # Base64 encode for safe transport
    return base64.b64encode(token_data.encode()).decode()

def verify_hmac_token(token):
    """Verify HMAC-based token"""
    try:
        # Decode from base64
        token_data = base64.b64decode(token.encode()).decode()
        
        # Split token parts
        parts = token_data.split('|')
        if len(parts) != 4:
            return None
            
        username, api_key, expiry_str, signature = parts
        
        # Check expiry
        if int(time.time()) > int(expiry_str):
            return None
        
        # Verify signature
        secret = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key').encode()
        payload = f"{username}|{api_key}|{expiry_str}"
        expected_signature = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return None
        
        # Return payload in JWT-like format
        return {
            'username': username,
            'api_key': api_key,
            'exp': int(expiry_str)
        }
        
    except Exception:
        return None

@admin_login_bp.route('/v1/admin/login', methods=['POST'])
def admin_login_api():
    """Username/password login endpoint with secure cookie authentication"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip().lower()
        password = data.get('password', '')
        
        # Get admin credentials from environment variables
        admin_username = os.getenv('ADMIN_USERNAME', 'admin').lower()
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if username == admin_username and password == admin_password:
            # Get legacy API key for admin access
            from config import API_KEY as LEGACY_KEY
            
            # Generate secure token (JWT if available, HMAC fallback)
            token = generate_secure_token(admin_username, LEGACY_KEY)
            
            # Create response
            response = make_response(jsonify({
                "status": "success",
                "message": "Login successful",
                "user": {
                    "username": admin_username,
                    "permissions": ["admin"]
                }
            }))
            
            # Set secure HTTP-only cookie
            # For production, use secure=True. For development, allow HTTP
            is_production = os.getenv('APP_DEBUG', 'false').lower() == 'false'
            response.set_cookie(
                'admin_token',
                token,
                max_age=24*60*60,  # 24 hours
                httponly=True,      # Cannot be accessed by JavaScript
                secure=is_production,  # Only HTTPS in production
                samesite='Strict'   # CSRF protection
            )
            
            return response
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid username or password"
            }), 401
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Login failed"
        }), 500

@admin_login_bp.route('/v1/admin/verify', methods=['GET'])
def verify_admin_session():
    """Verify admin session and return API key"""
    try:
        # Debug: log all cookies
        import logging
        logging.info(f"All cookies: {dict(request.cookies)}")
        
        # Get token from cookie
        token = request.cookies.get('admin_token')
        logging.info(f"Admin token from cookie: {token[:20] if token else 'None'}...")
        
        if not token:
            return jsonify({"status": "error", "message": "No session found", "debug": "No admin_token cookie"}), 401
        
        # Verify token
        payload = verify_secure_token(token)
        logging.info(f"Token verification result: {payload is not None}")
        
        if not payload:
            return jsonify({"status": "error", "message": "Invalid or expired session", "debug": "Token verification failed"}), 401
        
        # Return API key for frontend use
        return jsonify({
            "status": "success",
            "api_key": payload['api_key'],
            "user": {
                "username": payload['username'],
                "permissions": ["admin"]
            }
        })
        
    except Exception as e:
        import logging
        logging.error(f"Session verification error: {str(e)}")
        return jsonify({"status": "error", "message": "Session verification failed", "debug": str(e)}), 500

@admin_login_bp.route('/admin/logout')
def admin_logout():
    """Logout and clear session"""
    response = make_response("""
    <script>
        // Clear sessionStorage as fallback
        sessionStorage.removeItem('admin_api_key');
        window.location.href = '/admin';
    </script>
    """)
    
    # Clear the secure cookie
    is_production = os.getenv('APP_DEBUG', 'false').lower() == 'false'
    response.set_cookie('admin_token', '', expires=0, httponly=True, secure=is_production, samesite='Strict')
    return response