# Copyright (c) 2025 Isaac Gounton

from flask import Blueprint

admin_login_bp = Blueprint('admin_login', __name__)

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
                <form id="loginForm" class="space-y-6">
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
                            <li>• Use your legacy API key (from environment)</li>
                            <li>• Use admin API key (generated during setup)</li>
                            <li>• Use any valid user API key with admin permissions</li>
                        </ul>
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
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const apiKey = document.getElementById('apiKey').value;
            const errorDiv = document.getElementById('errorMessage');
            
            // Hide previous errors
            errorDiv.classList.add('hidden');
            
            try {
                // Test authentication with the provided API key
                const response = await fetch('/v1/toolkit/authenticate', {
                    method: 'GET',
                    headers: {
                        'X-API-Key': apiKey
                    }
                });
                
                if (response.ok) {
                    // Store the API key securely (you might want to use a more secure method)
                    sessionStorage.setItem('admin_api_key', apiKey);
                    
                    // Redirect to API keys dashboard
                    window.location.href = '/admin/api-keys';
                } else {
                    // Show error message
                    errorDiv.classList.remove('hidden');
                }
            } catch (error) {
                console.error('Authentication error:', error);
                errorDiv.classList.remove('hidden');
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

@admin_login_bp.route('/admin/logout')
def admin_logout():
    """Logout and clear session"""
    return """
    <script>
        sessionStorage.removeItem('admin_api_key');
        window.location.href = '/admin';
    </script>
    """