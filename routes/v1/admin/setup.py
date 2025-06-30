# Copyright (c) 2025 Isaac Gounton

from flask import Blueprint, render_template_string
from models.api_keys import APIKeyManager

setup_bp = Blueprint('setup', __name__)

@setup_bp.route('/admin/setup')
def setup_page():
    """Setup page to help users get started with API key management"""
    
    api_manager = APIKeyManager()
    users = api_manager.get_all_users()
    
    setup_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DahoPevi API Setup</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-6">
            <h1 class="text-3xl font-bold text-gray-800 mb-6">🚀 DahoPevi API Setup</h1>
            
            <div class="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
                <h2 class="text-lg font-semibold text-green-800 mb-2">✅ System Status</h2>
                <p class="text-green-700">API Key Management System is initialized</p>
                <p class="text-green-700">{{ users|length }} user(s) in database</p>
            </div>
            
            <div class="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
                <h2 class="text-lg font-semibold text-blue-800 mb-2">🔑 Access Options</h2>
                <div class="space-y-2">
                    <p class="text-blue-700"><strong>Option 1:</strong> Use your existing legacy API key</p>
                    <p class="text-blue-700"><strong>Option 2:</strong> Use the admin key created during bootstrap</p>
                    <p class="text-blue-700"><strong>Option 3:</strong> Create a new API key via the management interface</p>
                </div>
            </div>
            
            <div class="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
                <h2 class="text-lg font-semibold text-yellow-800 mb-2">📋 Next Steps</h2>
                <ol class="list-decimal list-inside space-y-2 text-yellow-700">
                    <li>Get your API key (legacy or admin key from bootstrap)</li>
                    <li>Visit the <a href="/admin/api-keys" class="text-blue-600 underline">API Keys Dashboard</a></li>
                    <li>When prompted, enter your API key</li>
                    <li>Create users and manage their API keys</li>
                </ol>
            </div>
            
            <div class="bg-gray-50 border border-gray-200 rounded-md p-4">
                <h2 class="text-lg font-semibold text-gray-800 mb-2">🛠️ Commands</h2>
                <div class="space-y-2">
                    <p class="text-gray-700"><strong>Bootstrap again:</strong> <code class="bg-gray-200 px-2 py-1 rounded">python bootstrap_admin.py</code></p>
                    <p class="text-gray-700"><strong>Access dashboard:</strong> <a href="/admin/api-keys" class="text-blue-600 underline">/admin/api-keys</a></p>
                </div>
            </div>
            
            <div class="mt-6 text-center">
                <a href="/admin/api-keys" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg inline-block">
                    Go to API Keys Dashboard
                </a>
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(setup_html, users=users)