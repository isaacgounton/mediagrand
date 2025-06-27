from flask import Blueprint, request, jsonify
from services.simone.processor import process_video_to_blog
from app import task_queue, queue_task
import os
import logging

simone_bp = Blueprint('simone_bp', __name__)

# Get Tesseract path from environment or a default
# This should ideally be configured via app config or passed securely
TESSERACT_CMD_PATH = os.environ.get("TESSERACT_CMD_PATH", "/usr/bin/tesseract")

@simone_bp.route('/v1/simone/process_video', methods=['POST'])
@queue_task()
def process_video_endpoint(job_id, data):
    try:
        video_url = data.get('video_url')
        cookies_content = data.get('cookies_content')
        cookies_url = data.get('cookies_url')
        gemma_api_key = os.environ.get('GEMMA_API_KEY')

        if not video_url:
            return "Missing 'video_url' in request data", 400, "/v1/simone/process_video"

        if not gemma_api_key:
            return "GEMMA_API_KEY not configured on server.", 500, "/v1/simone/process_video"

        logging.info(f"Processing video {video_url} for job {job_id}")

        result = process_video_to_blog(video_url, TESSERACT_CMD_PATH, gemma_api_key, cookies_content, cookies_url)

        return jsonify(result), 200, "/v1/simone/process_video"

    except Exception as e:
        logging.error(f"Error processing video for job {job_id}: {str(e)}", exc_info=True)
        return str(e), 500, "/v1/simone/process_video"
