# Copyright (c) 2025 Stephen G. Pope
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import logging

# Retrieve the API key from environment variables
API_KEY = os.environ.get('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable is not set")

# TTS Server configuration
TTS_SERVER_URL = os.environ.get('TTS_SERVER_URL', 'https://tts.mediagrand.com/api')
if not TTS_SERVER_URL.endswith('/'):
    TTS_SERVER_URL += '/'

# AI Model configuration for Simone (OpenAI-compatible)
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'google/gemma-3-12b-it:free')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')

# Storage path settings
LOCAL_STORAGE_PATH = os.environ.get('LOCAL_STORAGE_PATH', '/app/data/tmp')

# Create storage directory if it doesn't exist
os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)

# GCP environment variables
GCP_SA_CREDENTIALS = os.environ.get('GCP_SA_CREDENTIALS', '')
GCP_BUCKET_NAME = os.environ.get('GCP_BUCKET_NAME', '')

# Default video placeholder path
DEFAULT_PLACEHOLDER_VIDEO = os.environ.get('DEFAULT_PLACEHOLDER_VIDEO', 
    os.path.join(LOCAL_STORAGE_PATH, "assets", "placeholder.mp4"))

# Ensure placeholder path exists
placeholder_dir = os.path.dirname(DEFAULT_PLACEHOLDER_VIDEO)
if not os.path.exists(placeholder_dir):
    os.makedirs(placeholder_dir, exist_ok=True)

def validate_env_vars(provider):
    """Validate the necessary environment variables for the selected storage provider"""
    required_vars = {
        'GCP': ['GCP_BUCKET_NAME', 'GCP_SA_CREDENTIALS'],
        'S3': ['S3_ENDPOINT_URL', 'S3_ACCESS_KEY', 'S3_SECRET_KEY', 'S3_BUCKET_NAME', 'S3_REGION'],
        'S3_DO': ['S3_ENDPOINT_URL', 'S3_ACCESS_KEY', 'S3_SECRET_KEY']
    }
    
    missing_vars = [var for var in required_vars[provider] if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing environment variables for {provider} storage: {', '.join(missing_vars)}")
