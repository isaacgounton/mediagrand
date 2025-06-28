from flask import Blueprint, request, jsonify
from services.simone.processor import process_video_to_blog
from services.authentication import authenticate
from app_utils import queue_task_wrapper
import os
import logging

simone_bp = Blueprint('simone_bp', __name__)

# Get Tesseract path from environment or a default
# This should ideally be configured via app config or passed securely
TESSERACT_CMD_PATH = os.environ.get("TESSERACT_CMD_PATH", "/usr/bin/tesseract")

@simone_bp.route('/v1/simone/process_video', methods=['POST'])
@authenticate
@queue_task_wrapper(bypass_queue=False)
def process_video_endpoint(job_id, data):
    try:
        video_url = data.get('video_url')
        cookies_content = data.get('cookies_content')
        cookies_url = data.get('cookies_url')
        platform = data.get('platform') # Get the new platform parameter
        if not video_url:
            return {"error": "Missing 'video_url' in request data"}, "/v1/simone/process_video", 400

        logging.info(f"Processing video {video_url} for job {job_id}")

        result = process_video_to_blog(video_url, TESSERACT_CMD_PATH, platform, cookies_content, cookies_url)

        return result, "/v1/simone/process_video", 200

    except Exception as e:
        logging.error(f"Error processing video for job {job_id}: {str(e)}", exc_info=True)
        return {"error": str(e)}, "/v1/simone/process_video", 500
