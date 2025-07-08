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
import json
from services.transcription import process_transcription
from services.authentication import authenticate
from services.cloud_storage import upload_file
from config import LOCAL_STORAGE_PATH

transcribe_bp = Blueprint('transcribe', __name__)
logger = logging.getLogger(__name__)


@transcribe_bp.route('/transcribe-media/progress/<job_id>', methods=['GET'])
@authenticate
def get_transcription_progress(job_id):
    """Get the progress of a transcription job."""
    try:
        jobs_dir = os.path.join(LOCAL_STORAGE_PATH, 'jobs')
        job_file = os.path.join(jobs_dir, f"{job_id}.json")
        
        if not os.path.exists(job_file):
            return jsonify({
                "error": "Job not found",
                "job_id": job_id
            }), 404
        
        with open(job_file, 'r') as f:
            job_data = json.load(f)
        
        # Extract progress information
        progress_info = {
            "job_id": job_id,
            "status": job_data.get('status', 'unknown'),
            "progress": job_data.get('progress', {}),
            "timestamp": job_data.get('timestamp'),
            "started_at": job_data.get('started_at'),
            "completed_at": job_data.get('completed_at'),
            "error": job_data.get('error')
        }
        
        return jsonify(progress_info), 200
        
    except Exception as e:
        logger.error(f"Error getting progress for job {job_id}: {str(e)}")
        return jsonify({
            "error": "Failed to get job progress",
            "job_id": job_id,
            "message": str(e)
        }), 500


@transcribe_bp.route('/transcribe-media/status', methods=['GET'])
@authenticate
def get_transcription_status():
    """Get status of all transcription jobs."""
    try:
        jobs_dir = os.path.join(LOCAL_STORAGE_PATH, 'jobs')
        
        if not os.path.exists(jobs_dir):
            return jsonify({
                "jobs": [],
                "message": "No jobs found"
            }), 200
        
        jobs = []
        for filename in os.listdir(jobs_dir):
            if filename.endswith('.json'):
                job_id = filename[:-5]  # Remove .json extension
                job_file = os.path.join(jobs_dir, filename)
                
                try:
                    with open(job_file, 'r') as f:
                        job_data = json.load(f)
                    
                    jobs.append({
                        "job_id": job_id,
                        "status": job_data.get('status', 'unknown'),
                        "progress": job_data.get('progress', {}),
                        "timestamp": job_data.get('timestamp'),
                        "started_at": job_data.get('started_at'),
                        "completed_at": job_data.get('completed_at')
                    })
                except Exception as e:
                    logger.warning(f"Error reading job file {filename}: {str(e)}")
                    continue
        
        # Sort by timestamp (most recent first)
        jobs.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return jsonify({
            "jobs": jobs,
            "total_jobs": len(jobs)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return jsonify({
            "error": "Failed to get job status",
            "message": str(e)
        }), 500

@transcribe_bp.route('/transcribe-media', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "output": {"type": "string", "enum": ["transcript", "srt", "vtt", "ass"]},
        "webhook_url": {"type": "string", "format": "uri"},
        "max_chars": {"type": "integer"},
        "language": {"type": "string"},
        "use_chunked": {"type": "boolean"},
        "id": {"type": "string"}
    },
    "required": ["media_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def transcribe(job_id, data):
    media_url = data['media_url']
    output = data.get('output', 'transcript')
    webhook_url = data.get('webhook_url')
    max_chars = data.get('max_chars', 56)
    language = data.get('language')
    use_chunked = data.get('use_chunked', True)
    id = data.get('id')

    logger.info(f"Job {job_id}: Received transcription request for {media_url}")
    logger.info(f"Job {job_id}: Parameters - output: {output}, language: {language}, use_chunked: {use_chunked}")

    try:
        result = process_transcription(
            media_url=media_url,
            output_type=output,
            max_chars=max_chars,
            language=language,
            job_id=job_id,
            use_chunked=use_chunked
        )
        logger.info(f"Job {job_id}: Transcription process completed successfully")

        # If the result is a file path, upload it using the unified upload_file() method
        if output in ['srt', 'vtt', 'ass']:
            cloud_url = upload_file(result)
            try:
                os.remove(result)  # Remove the temporary file after uploading
            except Exception as cleanup_error:
                logger.warning(f"Job {job_id}: Failed to cleanup temp file {result}: {cleanup_error}")
            return cloud_url, "/transcribe-media", 200
        else:
            return result, "/transcribe-media", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error during transcription process - {str(e)}")
        return str(e), "/transcribe-media", 500
