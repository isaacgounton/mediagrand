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

# Storage path settings
LOCAL_STORAGE_PATH = os.environ.get('LOCAL_STORAGE_PATH', '/app/data/tmp') # Changed default
VOICE_FILES_PATH = os.environ.get('VOICE_FILES_PATH', '/app/data/voices')

# Create voice files directory if it doesn't exist
if not os.path.exists(VOICE_FILES_PATH):
    os.makedirs(VOICE_FILES_PATH, exist_ok=True)

# Ensure voice files are available in the expected location
def ensure_voice_files():
    """Verify voice files exist and copy them if needed (for non-Docker environments)"""
    
    # Voice files that should exist
    voice_files = [
        'edge_tts_voices.json',
        'kokoro_voices.json', 
        'openai_edge_tts_voices.json',
        'streamlabs_voices.json'
    ]
    
    # Check if we're in a Docker environment (where files should already be in place)
    is_docker = os.path.exists('/app') and VOICE_FILES_PATH == '/app/data/voices'
    
    for voice_file in voice_files:
        target_path = os.path.join(VOICE_FILES_PATH, voice_file)
        
        if not os.path.exists(target_path):
            if is_docker:
                # In Docker, files should have been copied during build
                logging.error(f"Voice file {voice_file} missing in Docker container at {target_path}")
            else:
                # For local development, try to copy from source locations
                import shutil
                possible_sources = [
                    os.path.join('data', 'voices', voice_file),  # Current working directory
                    os.path.join(os.path.dirname(__file__), 'data', 'voices', voice_file),  # Relative to config.py
                ]
                
                source_found = False
                for source_path in possible_sources:
                    if os.path.exists(source_path):
                        try:
                            shutil.copy2(source_path, target_path)
                            logging.info(f"Copied {voice_file} to {target_path}")
                            source_found = True
                            break
                        except Exception as e:
                            logging.warning(f"Could not copy {voice_file}: {e}")
                
                if not source_found:
                    logging.warning(f"Could not find source file for {voice_file}")
        else:
            logging.debug(f"Voice file {voice_file} found at {target_path}")

# Initialize voice files on import
ensure_voice_files()

# GCP environment variables
GCP_SA_CREDENTIALS = os.environ.get('GCP_SA_CREDENTIALS', '')
GCP_BUCKET_NAME = os.environ.get('GCP_BUCKET_NAME', '')

# Video service API keys (optional - used for background video search)
PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY', '')
if not PEXELS_API_KEY:
    logging.warning("PEXELS_API_KEY not set - Pexels video search will be unavailable")

PIXABAY_API_KEY = os.environ.get('PIXABAY_API_KEY', '')
if not PIXABAY_API_KEY:
    logging.warning("PIXABAY_API_KEY not set - Pixabay video search will be unavailable")

# Default video placeholder path
DEFAULT_PLACEHOLDER_VIDEO = os.environ.get('DEFAULT_PLACEHOLDER_VIDEO', 
    os.path.join(LOCAL_STORAGE_PATH, "assets", "placeholder.mp4"))

# Ensure placeholder path exists
placeholder_dir = os.path.dirname(DEFAULT_PLACEHOLDER_VIDEO)
if not os.path.exists(placeholder_dir):
    os.makedirs(placeholder_dir, exist_ok=True)

def validate_env_vars(provider):

    """ Validate the necessary environment variables for the selected storage provider """
    required_vars = {
        'GCP': ['GCP_BUCKET_NAME', 'GCP_SA_CREDENTIALS'],
        'S3': ['S3_ENDPOINT_URL', 'S3_ACCESS_KEY', 'S3_SECRET_KEY', 'S3_BUCKET_NAME', 'S3_REGION'],
        'S3_DO': ['S3_ENDPOINT_URL', 'S3_ACCESS_KEY', 'S3_SECRET_KEY']
    }
    
    missing_vars = [var for var in required_vars[provider] if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing environment variables for {provider} storage: {', '.join(missing_vars)}")
