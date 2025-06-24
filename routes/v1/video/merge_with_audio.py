from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
import logging
from services.authentication import authenticate
from services.cloud_storage import upload_file

v1_video_merge_with_audio_bp = Blueprint('v1_video_merge_with_audio', __name__)
logger = logging.getLogger(__name__)

@v1_video_merge_with_audio_bp.route('/v1/video/merge_with_audio', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_urls": {
            "type": "array",
            "items": {
                "type": "string",
                "format": "uri"
            },
            "minItems": 1,
            "description": "List of video URLs to merge"
        },
        "audio_url": {
            "type": "string",
            "format": "uri",
            "description": "Required speech audio URL"
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_urls", "audio_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def merge_videos_with_audio(job_id, data):
    from services.v1.video.merge_videos_with_audio import process_video_merge_with_audio
    video_urls = data['video_urls']
    audio_url = data['audio_url']
    webhook_url = data.get('webhook_url')
    id = data.get('id')

    logger.info(f"Job {job_id}: Received video merge with audio request for {len(video_urls)} videos")

    try:
        output_file = process_video_merge_with_audio(
            video_urls=video_urls,
            audio_url=audio_url,
            job_id=job_id
        )
        logger.info(f"Job {job_id}: Video merge with audio process completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: Merged video with audio uploaded to cloud storage: {cloud_url}")

        return cloud_url, "/v1/video/merge_with_audio", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during video merge with audio process - {str(e)}")
        return str(e), "/v1/video/merge_with_audio", 500
