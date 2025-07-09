from flask import Blueprint, jsonify
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
from services.v1.audio.musicgen import MusicGenService
import logging

musicgen_bp = Blueprint('musicgen', __name__)
logger = logging.getLogger(__name__)

@musicgen_bp.route('/v1/audio/music', methods=['POST'])
@queue_task_wrapper(bypass_queue=False)
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "duration": {"type": ["integer", "string"], "minimum": 1, "maximum": 30, "default": 8},
        "model_size": {"type": "string", "enum": ["small"], "default": "small"},
        "output_format": {"type": "string", "enum": ["wav", "mp3"], "default": "wav"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["description"],
    "additionalProperties": False
})
def generate_music(job_id, data):
    """Generate music from text description using MusicGen model"""
    try:
        logger.info(f"Job {job_id}: MusicGen request received")
        
        description = data.get('description')
        duration = int(data.get('duration', 8))
        model_size = data.get('model_size', 'small')
        output_format = data.get('output_format', 'wav')
        
        # Initialize service
        service = MusicGenService()
        
        # Generate music
        result = service.generate_music(
            description=description,
            duration=duration,
            model_size=model_size,
            output_format=output_format,
            job_id=job_id
        )
        
        logger.info(f"Job {job_id}: MusicGen completed successfully")
        
        # Return in the format expected by the API framework
        return {
            "message": "Music generated successfully",
            "output_url": result['output_url'],
            "duration": result['duration'],
            "model_used": result['model_used'],
            "description": description,
            "file_size": result['file_size'],
            "sampling_rate": result['sampling_rate']
        }, "/v1/audio/music", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: MusicGen error - {str(e)}", exc_info=True)
        return str(e), "/v1/audio/music", 500

@musicgen_bp.route('/v1/audio/music', methods=['GET'])
@queue_task_wrapper(bypass_queue=True)
@authenticate
def musicgen_info(job_id=None, data=None):
    """Get information about the MusicGen endpoint"""
    return {
        "endpoint": "/v1/audio/music",
        "method": "POST",
        "description": "Generate music from text descriptions using Meta's MusicGen model",
        "parameters": {
            "description": {
                "type": "string",
                "required": True,
                "description": "Text description of the music to generate"
            },
            "duration": {
                "type": "integer",
                "required": False,
                "default": 8,
                "max": 30,
                "description": "Duration in seconds (max 30)"
            },
            "model_size": {
                "type": "string",
                "required": False,
                "default": "small",
                "options": ["small"],
                "description": "Model size to use"
            },
            "output_format": {
                "type": "string",
                "required": False,
                "default": "wav",
                "options": ["wav", "mp3"],
                "description": "Output audio format"
            },
            "webhook_url": {
                "type": "string",
                "required": False,
                "description": "Webhook URL for async processing"
            }
        },
        "examples": [
            {
                "description": "lo-fi music with a soothing melody",
                "duration": 8,
                "model_size": "small"
            },
            {
                "description": "upbeat electronic dance music",
                "duration": 15,
                "model_size": "small"
            }
        ]
    }, "/v1/audio/music", 200

@musicgen_bp.route('/v1/audio/music', methods=['OPTIONS'])
@queue_task_wrapper(bypass_queue=True)
def musicgen_options(job_id=None, data=None):
    """Handle preflight CORS requests"""
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,x-api-key')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response