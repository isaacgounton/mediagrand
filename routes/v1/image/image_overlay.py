from flask import Blueprint
from app_utils import *
import logging
from services.v1.image.image_overlay import image_overlay
from services.authentication import authenticate
from services.cloud_storage import upload_file

image_overlay_bp = Blueprint('image_overlay', __name__)
logger = logging.getLogger(__name__)

@image_overlay_bp.route('/add-overlay-image', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "base_image_url": {"type": "string", "format": "uri"},
        "overlay_images": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "format": "uri"},
                    "x": {"type": "number", "minimum": 0, "maximum": 1},
                    "y": {"type": "number", "minimum": 0, "maximum": 1},
                    "width": {"type": "number", "minimum": 0, "maximum": 1},
                    "height": {"type": "number", "minimum": 0, "maximum": 1},
                    "rotation": {"type": "number", "minimum": 0, "maximum": 360},
                    "opacity": {"type": "number", "minimum": 0, "maximum": 1},
                    "z_index": {"type": "integer"}
                },
                "required": ["url", "x", "y"]
            }
        },
        "output_format": {"type": "string", "enum": ["png", "jpg", "webp"]},
        "output_quality": {"type": "integer", "minimum": 1, "maximum": 100},
        "output_width": {"type": "integer"},
        "output_height": {"type": "integer"},
        "maintain_aspect_ratio": {"type": "boolean"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["base_image_url", "overlay_images"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def add_overlay_image(job_id, data):
    logger.info(f"Job {job_id}: Received image overlay request")

    try:
        # Process image overlay
        output_filename = image_overlay(data)

        # Upload the resulting file using the unified upload_file() method
        cloud_url = upload_file(output_filename)

        # Log the successful upload
        logger.info(f"Job {job_id}: Converted video uploaded to cloud storage: {cloud_url}")

        # Return the cloud URL for the uploaded file
        return cloud_url, "/add-overlay-image", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error processing image overlay: {str(e)}", exc_info=True)
        return str(e), "/add-overlay-image", 500
