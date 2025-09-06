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

from flask import Blueprint, request, jsonify
from utils.app_utils import validate_payload, queue_task_wrapper
import logging
from services.v1.image.convert.image_convert import process_image_convert_from_url, process_image_convert_from_file
from services.authentication import authenticate
from services.cloud_storage import upload_file
import os

v1_image_convert_bp = Blueprint('v1_image_convert', __name__)
logger = logging.getLogger(__name__)

@v1_image_convert_bp.route('/v1/image/convert', methods=['POST'])
@authenticate
@queue_task_wrapper(bypass_queue=False)
def convert_image(job_id, data):
    """
    Convert image from either URL or file upload to specified format.
    Supports both JSON payload (for URL) and multipart form data (for file upload).
    """
    
    # Check if this is a file upload (multipart/form-data)
    if request.content_type and 'multipart/form-data' in request.content_type:
        return handle_file_upload(job_id, data)
    else:
        return handle_url_conversion(job_id, data)

def handle_file_upload(job_id, data):
    """Handle image conversion from file upload"""
    # Get the format from query parameter or form data
    output_format = request.args.get('format') or request.form.get('format')
    if not output_format:
        logger.error(f"Job {job_id}: No format specified")
        return {"error": "Format parameter is required"}, "/v1/image/convert", 400
    
    # Validate format
    supported_formats = ['jpg', 'jpeg', 'webp', 'png']
    if output_format.lower() not in supported_formats:
        logger.error(f"Job {job_id}: Unsupported format: {output_format}")
        return {"error": f"Unsupported format: {output_format}. Supported formats: {supported_formats}"}, "/v1/image/convert", 400
    
    # Check if file was uploaded
    if 'image' not in request.files:
        logger.error(f"Job {job_id}: No image file uploaded")
        return {"error": "No image file uploaded"}, "/v1/image/convert", 400
    
    file = request.files['image']
    if file.filename == '':
        logger.error(f"Job {job_id}: No file selected")
        return {"error": "No file selected"}, "/v1/image/convert", 400

    logger.info(f"Job {job_id}: Received image conversion request for file: {file.filename} to format: {output_format}")

    try:
        # Read file data
        file_data = file.read()
        if not file_data:
            logger.error(f"Job {job_id}: Empty file uploaded")
            return {"error": "Empty file uploaded"}, "/v1/image/convert", 400
        
        output_file = process_image_convert_from_file(
            file_data, 
            job_id, 
            output_format,
            file.filename
        )
        logger.info(f"Job {job_id}: Image conversion completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: Converted image uploaded to cloud storage: {cloud_url}")
        
        return cloud_url, "/v1/image/convert", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during image conversion process - {str(e)}")
        return {"error": str(e)}, "/v1/image/convert", 500

@validate_payload({
    "type": "object",
    "properties": {
        "image_url": {"type": "string", "format": "uri"},
        "format": {"type": "string", "enum": ["jpg", "jpeg", "webp", "png"]},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["image_url", "format"],
    "additionalProperties": False
})
def handle_url_conversion(job_id, data):
    """Handle image conversion from URL"""
    image_url = data['image_url']
    output_format = data['format']
    webhook_url = data.get('webhook_url')
    id = data.get('id')

    logger.info(f"Job {job_id}: Received image conversion request for image URL: {image_url} to format: {output_format}")

    try:
        output_file = process_image_convert_from_url(
            image_url, 
            job_id, 
            output_format
        )
        logger.info(f"Job {job_id}: Image conversion completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: Converted image uploaded to cloud storage: {cloud_url}")
        
        return cloud_url, "/v1/image/convert", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during image conversion process - {str(e)}")
        return {"error": str(e)}, "/v1/image/convert", 500