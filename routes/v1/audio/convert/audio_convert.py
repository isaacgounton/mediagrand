# Copyright (c) 2025 Isaac Gounton

from flask import Blueprint, request, jsonify
from utils.app_utils import validate_payload, queue_task_wrapper
import logging
from services.v1.audio.convert.audio_convert import process_audio_convert_from_url, process_audio_convert_from_file
from services.authentication import authenticate
from services.cloud_storage import upload_file
import os

v1_audio_convert_bp = Blueprint('v1_audio_convert', __name__)
logger = logging.getLogger(__name__)

@v1_audio_convert_bp.route('/v1/audio/convert', methods=['POST'])
@authenticate
@queue_task_wrapper(bypass_queue=False)
def convert_audio(job_id, data):
    """
    Convert audio from either URL or file upload to specified format.
    Supports both JSON payload (for URL) and multipart form data (for file upload).
    """
    
    # Check if this is a file upload (multipart/form-data)
    if request.content_type and 'multipart/form-data' in request.content_type:
        return handle_file_upload(job_id, data)
    else:
        return handle_url_conversion(job_id, data)

def handle_file_upload(job_id, data):
    """Handle audio conversion from file upload"""
    # Get the format from query parameter or form data
    output_format = request.args.get('format') or request.form.get('format')
    if not output_format:
        logger.error(f"Job {job_id}: No format specified")
        return {"error": "Format parameter is required"}, "/v1/audio/convert", 400
    
    # Validate format
    supported_formats = ['mp3', 'ogg', 'oga']
    if output_format.lower() not in supported_formats:
        logger.error(f"Job {job_id}: Unsupported format: {output_format}")
        return {"error": f"Unsupported format: {output_format}. Supported formats: {supported_formats}"}, "/v1/audio/convert", 400
    
    # Check if file was uploaded
    if 'audio' not in request.files:
        logger.error(f"Job {job_id}: No audio file uploaded")
        return {"error": "No audio file uploaded"}, "/v1/audio/convert", 400
    
    file = request.files['audio']
    if file.filename == '':
        logger.error(f"Job {job_id}: No file selected")
        return {"error": "No file selected"}, "/v1/audio/convert", 400

    logger.info(f"Job {job_id}: Received audio conversion request for file: {file.filename} to format: {output_format}")

    try:
        # Read file data
        file_data = file.read()
        if not file_data:
            logger.error(f"Job {job_id}: Empty file uploaded")
            return {"error": "Empty file uploaded"}, "/v1/audio/convert", 400
        
        output_file = process_audio_convert_from_file(
            file_data, 
            job_id, 
            output_format,
            file.filename
        )
        logger.info(f"Job {job_id}: Audio conversion completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: Converted audio uploaded to cloud storage: {cloud_url}")
        
        return cloud_url, "/v1/audio/convert", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during audio conversion process - {str(e)}")
        return {"error": str(e)}, "/v1/audio/convert", 500

@validate_payload({
    "type": "object",
    "properties": {
        "audio_url": {"type": "string", "format": "uri"},
        "format": {"type": "string", "enum": ["mp3", "ogg", "oga"]},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["audio_url", "format"],
    "additionalProperties": False
})
def handle_url_conversion(job_id, data):
    """Handle audio conversion from URL"""
    audio_url = data['audio_url']
    output_format = data['format']
    webhook_url = data.get('webhook_url')
    id = data.get('id')

    logger.info(f"Job {job_id}: Received audio conversion request for audio URL: {audio_url} to format: {output_format}")

    try:
        output_file = process_audio_convert_from_url(
            audio_url, 
            job_id, 
            output_format
        )
        logger.info(f"Job {job_id}: Audio conversion completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: Converted audio uploaded to cloud storage: {cloud_url}")
        
        return cloud_url, "/v1/audio/convert", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during audio conversion process - {str(e)}")
        return {"error": str(e)}, "/v1/audio/convert", 500