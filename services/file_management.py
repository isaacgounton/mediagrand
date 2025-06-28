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
import time
import logging
from urllib.parse import urlparse, parse_qs
import mimetypes
from config import LOCAL_STORAGE_PATH

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
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
            # First check for the header - this is the most important part
            # All Netscape/Mozilla format cookie files should have this header
            if not lines:
                return False
                
            has_header = any(line.startswith('# Netscape HTTP Cookie File') or 
                            line.startswith('# HTTP Cookie File') for line in lines)
            if not has_header:
                return False
            
            # More lenient check - just make sure there are valid cookie lines
            # rather than enforcing exactly 7 fields per line
            valid_cookie_lines = 0
            for line in lines:
                # Skip empty lines and comments
                if not line.strip() or line.strip().startswith('#'):
                    continue
                    
                # Check if line has at least 6 tabs (7 fields)
                # But also allow for slight variations in format
                fields = line.strip().split('\t')
                if len(fields) >= 4:  # At minimum, we need domain, path, secure, and name+value
                    valid_cookie_lines += 1
            
            # Require at least one valid-looking cookie line
            return valid_cookie_lines > 0
    except Exception as e:
        # Log the specific error for debugging
        logging.warning(f"Cookie validation error: {str(e)}")
        return False

def download_file(url, storage_path="/tmp/", is_cookie=False):
    """Download a file from URL to local storage."""
    logger = logging.getLogger(__name__)
    logger.info(f"Downloading file from URL: {url}")

    # Create storage directory if it doesn't exist
    os.makedirs(storage_path, exist_ok=True)

    file_id = str(uuid.uuid4())
    extension = get_extension_from_url(url, is_cookie)
    local_filename = os.path.join(storage_path, f"{file_id}{extension}")
    logger.info(f"Target local filename: {local_filename}")

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Track file size for validation
        total_size = 0
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)

        # Validate file size - if it's very small, it might be an error response
        logger.info(f"Downloaded file size: {total_size} bytes")
        if total_size < 1024 and not is_cookie:  # Less than 1KB for non-cookie files
            logger.warning(f"Downloaded file is very small ({total_size} bytes), checking for error content")
            # Read the content to check if it's an error message
            try:
                with open(local_filename, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    logger.debug(f"Small file content: {content}")
                    if any(error_word in content.lower() for error_word in ['error', 'not found', 'forbidden', 'unauthorized']):
                        os.remove(local_filename)
                        raise Exception(f"Download failed - received error response ({total_size} bytes): {content}")
            except UnicodeDecodeError:
                logger.debug("Small file is binary, assuming it's valid")
                pass  # If it's not text, it might be a valid small binary file

        # Validate cookie file format if it's supposed to be a cookie file
        if is_cookie:
            logger = logging.getLogger(__name__)
            
            if not validate_cookie_file(local_filename):
                logger.warning(f"Invalid cookie file format detected. File: {local_filename}")
                
                # Try to log a sample of the file content for debugging
                try:
                    with open(local_filename, 'r', encoding='utf-8', errors='ignore') as f:
                        sample = f.read(500)  # Read first 500 chars for diagnosis
                        logger.debug(f"Cookie file content sample: {sample}")
                except Exception as e:
                    logger.debug(f"Could not read cookie file for diagnosis: {str(e)}")
                
                os.remove(local_filename)
                raise ValueError("Invalid cookie file format. Must be Netscape/Mozilla format with appropriate YouTube auth cookies.")
            else:
                logger.info(f"Valid cookie file format confirmed: {local_filename}")

        logger.info(f"File download completed successfully: {local_filename}")
        return local_filename
    except Exception as e:
        if os.path.exists(local_filename):
            os.remove(local_filename)
        raise e


def delete_old_files():
    now = time.time()
    storage_path = LOCAL_STORAGE_PATH
    for filename in os.listdir(storage_path):
        file_path = os.path.join(storage_path, filename)
        if os.path.isfile(file_path) and os.stat(file_path).st_mtime < now - 3600:
            os.remove(file_path)
