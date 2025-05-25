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
import uuid
import requests
from urllib.parse import urlparse, parse_qs
import mimetypes

def get_extension_from_url(url, is_cookie=False):
    """Extract file extension from URL or content type.
    
    Args:
        url (str): The URL to extract the extension from
        is_cookie (bool): If True, treats the file as a cookie file
        
    Returns:
        str: The file extension including the dot (e.g., '.txt')
    """
    if is_cookie:
        return '.txt'  # Cookie files are always text

    # First try to get extension from URL
    parsed_url = urlparse(url)
    path = parsed_url.path
    if path:
        ext = os.path.splitext(path)[1].lower()
        if ext:
            return ext

    # If no extension in URL, try to determine from content type
    try:
        response = requests.head(url, allow_redirects=True)
        content_type = response.headers.get('content-type', '').split(';')[0]
        ext = mimetypes.guess_extension(content_type)
        if ext:
            return ext.lower()
    except:
        pass

    # If we can't determine the extension, default to .txt for unknown types
    return '.txt'

def validate_cookie_file(file_path):
    """Validate that a file has proper Netscape cookie format.
    
    Args:
        file_path (str): Path to the cookie file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # Check for cookie file header
            if not lines or not any(line.startswith('# Netscape HTTP Cookie File') for line in lines):
                return False
                
            # Check for valid cookie entries (domain<tab>flag<tab>path<tab>secure<tab>expiry<tab>name<tab>value)
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    fields = line.strip().split('\t')
                    if len(fields) != 7:
                        return False
                        
            return True
    except:
        return False

def download_file(url, storage_path="/tmp/", is_cookie=False):
    """Download a file from URL to local storage."""
    # Create storage directory if it doesn't exist
    os.makedirs(storage_path, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    extension = get_extension_from_url(url, is_cookie)
    local_filename = os.path.join(storage_path, f"{file_id}{extension}")

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Validate cookie file format if it's supposed to be a cookie file
        if is_cookie and not validate_cookie_file(local_filename):
            os.remove(local_filename)
            raise ValueError("Invalid cookie file format. Must be Netscape/Mozilla format.")

        return local_filename
    except Exception as e:
        if os.path.exists(local_filename):
            os.remove(local_filename)
        raise e


def delete_old_files():
    now = time.time()
    for filename in os.listdir(STORAGE_PATH):
        file_path = os.path.join(STORAGE_PATH, filename)
        if os.path.isfile(file_path) and os.stat(file_path).st_mtime < now - 3600:
            os.remove(file_path)
