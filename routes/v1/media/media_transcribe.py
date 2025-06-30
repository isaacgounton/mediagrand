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



from flask import Blueprint, request, jsonify
from app_utils import *
import logging
import os
import tempfile
import jsonschema
from functools import wraps
from werkzeug.utils import secure_filename
from services.v1.media.media_transcribe import process_transcribe_media
from services.enhanced_authentication import enhanced_authenticate, require_permission
from services.cloud_storage import upload_file
from config import LOCAL_STORAGE_PATH

v1_media_transcribe_bp = Blueprint('v1_media_transcribe', __name__)
logger = logging.getLogger(__name__)

def validate_transcribe_request():
    """Custom validation for transcribe endpoint that handles both JSON and multipart requests"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if we have a file upload or JSON data
            has_file = 'file' in request.files and request.files['file'].filename != ''
            has_json = request.is_json and request.json and request.json.get('media_url')
            
            if not has_file and not has_json:
                return jsonify({"message": "Either upload a file or provide media_url in JSON"}), 400
            
            if has_file and has_json:
                return jsonify({"message": "Provide either a file upload or media_url, not both"}), 400
            
            # If it's JSON, validate with the original schema
            if has_json:
                schema = {
                    "type": "object",
                    "properties": {
                        "media_url": {"type": "string", "format": "uri"},
                        "task": {"type": "string", "enum": ["transcribe", "translate"]},
                        "include_text": {"type": "boolean"},
                        "include_srt": {"type": "boolean"},
                        "include_segments": {"type": "boolean"},
                        "word_timestamps": {"type": "boolean"},
                        "response_type": {"type": "string", "enum": ["direct", "cloud"]},
                        "language": {"type": "string"},
                        "webhook_url": {"type": "string", "format": "uri"},
                        "id": {"type": "string"},
                        "words_per_line": {"type": "integer", "minimum": 1}
                    },
                    "required": ["media_url"],
                    "additionalProperties": False
                }
                
                try:
                    # Pre-process boolean strings to actual booleans for validation
                    def convert_bools(obj):
                        if isinstance(obj, dict):
                            return {k: convert_bools(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_bools(item) for item in obj]
                        elif isinstance(obj, str) and obj.lower() in ['true', 'false']:
                            return obj.lower() == 'true'
                        return obj

                    data = convert_bools(request.json)
                    jsonschema.validate(instance=data, schema=schema)
                    setattr(request, '_validated_json', data)
                except jsonschema.ValidationError as validation_error:
                    return jsonify({"message": f"Invalid payload: {validation_error.message}"}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@v1_media_transcribe_bp.route('/v1/media/transcribe', methods=['POST'])
@enhanced_authenticate
@require_permission('read')
@validate_transcribe_request()
@queue_task_wrapper(bypass_queue=False)
def transcribe(job_id, data):
    media_file_path = None
    
    try:
        # Handle file upload
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            
            # Save uploaded file temporarily
            file_extension = os.path.splitext(secure_filename(file.filename))[1]
            if not file_extension:
                file_extension = '.tmp'
            
            media_file_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_upload{file_extension}")
            os.makedirs(os.path.dirname(media_file_path), exist_ok=True)
            file.save(media_file_path)
            
            # Get parameters from form data
            task = request.form.get('task', 'transcribe')
            include_text = request.form.get('include_text', 'true').lower() == 'true'
            include_srt = request.form.get('include_srt', 'false').lower() == 'true'
            include_segments = request.form.get('include_segments', 'false').lower() == 'true'
            word_timestamps = request.form.get('word_timestamps', 'false').lower() == 'true'
            response_type = request.form.get('response_type', 'direct')
            language = request.form.get('language', None)
            webhook_url = request.form.get('webhook_url', None)
            id = request.form.get('id', None)
            words_per_line_str = request.form.get('words_per_line', None)
            words_per_line = int(words_per_line_str) if words_per_line_str else None
            
            logger.info(f"Job {job_id}: Received transcription request for uploaded file {file.filename}")
            
        # Handle JSON with media_url
        else:
            validated_data = getattr(request, '_validated_json', request.json)
            media_file_path = validated_data['media_url']
            task = validated_data.get('task', 'transcribe')
            include_text = validated_data.get('include_text', True)
            include_srt = validated_data.get('include_srt', False)
            include_segments = validated_data.get('include_segments', False)
            word_timestamps = validated_data.get('word_timestamps', False)
            response_type = validated_data.get('response_type', 'direct')
            language = validated_data.get('language', None)
            webhook_url = validated_data.get('webhook_url')
            id = validated_data.get('id')
            words_per_line = validated_data.get('words_per_line', None)
            
            logger.info(f"Job {job_id}: Received transcription request for URL {media_file_path}")
        
        # Validate form parameters for file uploads
        if 'file' in request.files:
            if task not in ['transcribe', 'translate']:
                return "Invalid task value. Must be 'transcribe' or 'translate'", "/v1/transcribe/media", 400
            if response_type not in ['direct', 'cloud']:
                return "Invalid response_type value. Must be 'direct' or 'cloud'", "/v1/transcribe/media", 400

        try:
            result = process_transcribe_media(media_file_path, task, include_text, include_srt, include_segments, word_timestamps, response_type, language, job_id, words_per_line)
            logger.info(f"Job {job_id}: Transcription process completed successfully")

            # If the result is a file path, upload it using the unified upload_file() method
            if response_type == "direct":
               
                result_json = {
                    "text": result[0],
                    "srt": result[1],
                    "segments": result[2],
                    "text_url": None,
                    "srt_url": None,
                    "segments_url": None,
                }

                return result_json, "/v1/transcribe/media", 200

            else:

                cloud_urls = {
                    "text": None,
                    "srt": None,
                    "segments": None,
                    "text_url": upload_file(result[0]) if include_text is True else None,
                    "srt_url": upload_file(result[1]) if include_srt is True else None,
                    "segments_url": upload_file(result[2]) if include_segments is True else None,
                }

                if include_text is True:
                    os.remove(result[0])  # Remove the temporary file after uploading
                
                if include_srt is True:
                    os.remove(result[1])

                if include_segments is True:
                    os.remove(result[2])
                
                return cloud_urls, "/v1/transcribe/media", 200

        except Exception as e:
            logger.error(f"Job {job_id}: Error during transcription process - {str(e)}")
            return str(e), "/v1/transcribe/media", 500
    
    finally:
        # Clean up uploaded file if it exists and was uploaded (not a URL)
        if media_file_path and 'file' in request.files and os.path.exists(media_file_path):
            try:
                os.remove(media_file_path)
                logger.info(f"Job {job_id}: Cleaned up uploaded file {media_file_path}")
            except Exception as e:
                logger.warning(f"Job {job_id}: Failed to clean up uploaded file {media_file_path}: {str(e)}")

    try:
        result = process_transcribe_media(media_url, task, include_text, include_srt, include_segments, word_timestamps, response_type, language, job_id, words_per_line)
        logger.info(f"Job {job_id}: Transcription process completed successfully")

        # If the result is a file path, upload it using the unified upload_file() method
        if response_type == "direct":
           
            result_json = {
                "text": result[0],
                "srt": result[1],
                "segments": result[2],
                "text_url": None,
                "srt_url": None,
                "segments_url": None,
            }

            return result_json, "/v1/transcribe/media", 200

        else:

            cloud_urls = {
                "text": None,
                "srt": None,
                "segments": None,
                "text_url": upload_file(result[0]) if include_text is True else None,
                "srt_url": upload_file(result[1]) if include_srt is True else None,
                "segments_url": upload_file(result[2]) if include_segments is True else None,
            }

            if include_text is True:
                os.remove(result[0])  # Remove the temporary file after uploading
            
            if include_srt is True:
                os.remove(result[1])

            if include_segments is True:
                os.remove(result[2])
            
            return cloud_urls, "/v1/transcribe/media", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during transcription process - {str(e)}")
        return str(e), "/v1/transcribe/media", 500
