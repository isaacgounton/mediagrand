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
        import logging
        logging.warning(f"Cookie validation error: {str(e)}")
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
        if is_cookie:
            import logging
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

def get_presigned_url(file_path, expiration=3600):
    """
    Generate a presigned URL for a file in S3 storage.
    
    Args:
        file_path (str): Path or key of the file in S3
        expiration (int): Expiration time in seconds
        
    Returns:
        str: Presigned URL for downloading the file
    """
    from services.cloud_storage import get_storage_provider
    import boto3
    import os
    
    # Only works with S3 providers
    if not os.getenv('S3_ENDPOINT_URL'):
        raise ValueError("S3 storage not configured, presigned URLs not available")
    
    try:
        provider = get_storage_provider()
        
        # Create S3 client
        session = boto3.Session(
            aws_access_key_id=provider.access_key,
            aws_secret_access_key=provider.secret_key,
            region_name=provider.region
        )
        
        s3_client = session.client('s3', endpoint_url=provider.endpoint_url)
        
        # If file_path is a full path, extract just the filename
        file_name = os.path.basename(file_path)
        
        # Generate presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': provider.bucket_name,
                'Key': file_name
            },
            ExpiresIn=expiration
        )
        
        return presigned_url
    except Exception as e:
        logging.error(f"Error generating presigned URL: {str(e)}")
        raise

def upload_file_to_s3(file_path, content_type=None):
    """
    Upload a file to S3 storage and return the URL.
    
    Args:
        file_path (str): Path to the file to upload
        content_type (str, optional): Content type of the file
        
    Returns:
        str: URL of the uploaded file
    """
    from services.cloud_storage import upload_file
    
    try:
        return upload_file(file_path)
    except Exception as e:
        logging.error(f"Error uploading file to S3: {str(e)}")
        raise
