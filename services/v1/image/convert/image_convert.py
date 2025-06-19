# Copyright (c) 2025 Isaac Gounton
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
import requests
from PIL import Image
from services.file_management import download_file
from config import LOCAL_STORAGE_PATH
from urllib.parse import urlparse
import tempfile

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def process_image_convert_from_url(image_url, job_id, output_format='webp'):
    """
    Convert image from URL to specified format.
    
    Args:
        image_url (str): URL of the image to convert
        job_id (str): Unique job identifier
        output_format (str): Target format (jpg, webp, png)
        
    Returns:
        str: Path to the converted output file
    """
    # Validate format
    supported_formats = ['jpg', 'jpeg', 'webp', 'png']
    if output_format.lower() not in supported_formats:
        raise ValueError(f"Unsupported format: {output_format}. Supported formats: {supported_formats}")
    
    # Download the image
    try:
        response = requests.get(image_url, timeout=10, stream=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise ValueError(f"URL does not point to an image. Content-Type: {content_type}")
        
        # Create temporary file for input
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            input_filename = temp_file.name
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to download image from URL: {str(e)}")
    
    # Convert the image
    try:
        output_filename = f"{job_id}.{output_format}"
        output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)
        
        # Open and convert the image
        with Image.open(input_filename) as img:
            # Convert RGBA to RGB for JPEG format
            if output_format.lower() in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Save in the target format
            save_format = 'JPEG' if output_format.lower() in ['jpg', 'jpeg'] else output_format.upper()
            img.save(output_path, format=save_format, optimize=True, quality=95)
        
        # Clean up input file
        os.remove(input_filename)
        logger.info(f"Image conversion successful: {output_path} to format {output_format}")
        
        # Ensure the output file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} does not exist after conversion.")
        
        return output_path
        
    except Exception as e:
        # Clean up input file if it exists
        if os.path.exists(input_filename):
            try:
                os.remove(input_filename)
            except Exception:
                pass
        
        error_msg = f"Image conversion failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def process_image_convert_from_file(image_data, job_id, output_format='webp', original_filename='image'):
    """
    Convert image from file data to specified format.
    
    Args:
        image_data (bytes): Image file data
        job_id (str): Unique job identifier
        output_format (str): Target format (jpg, webp, png)
        original_filename (str): Original filename for reference
        
    Returns:
        str: Path to the converted output file
    """
    # Validate format
    supported_formats = ['jpg', 'jpeg', 'webp', 'png']
    if output_format.lower() not in supported_formats:
        raise ValueError(f"Unsupported format: {output_format}. Supported formats: {supported_formats}")
    
    # Create temporary file for input
    with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as temp_file:
        temp_file.write(image_data)
        input_filename = temp_file.name
    
    try:
        output_filename = f"{job_id}.{output_format}"
        output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)
        
        # Open and convert the image
        with Image.open(input_filename) as img:
            # Convert RGBA to RGB for JPEG format
            if output_format.lower() in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Save in the target format
            save_format = 'JPEG' if output_format.lower() in ['jpg', 'jpeg'] else output_format.upper()
            img.save(output_path, format=save_format, optimize=True, quality=95)
        
        # Clean up input file
        os.remove(input_filename)
        logger.info(f"Image conversion successful: {output_path} to format {output_format}")
        
        # Ensure the output file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} does not exist after conversion.")
        
        return output_path
        
    except Exception as e:
        # Clean up input file if it exists
        if os.path.exists(input_filename):
            try:
                os.remove(input_filename)
            except Exception:
                pass
        
        error_msg = f"Image conversion failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)