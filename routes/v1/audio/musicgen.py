from flask import Blueprint, request, jsonify
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
from services.v1.audio.musicgen import MusicGenService
import logging

musicgen_bp = Blueprint('musicgen', __name__)

@musicgen_bp.route('/v1/audio/music', methods=['POST'])
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
@queue_task_wrapper(bypass_queue=False)
def generate_music(job_id, data):
    """Generate music from text description using MusicGen model"""
    try:
        logging.info(f"MusicGen request received for job {job_id}")
        
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
        
        logging.info(f"MusicGen completed successfully for job {job_id}")
        
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
        logging.error(f"MusicGen error for job {job_id}: {str(e)}", exc_info=True)
        return f"Music generation failed: {str(e)}", "/v1/audio/music", 500

@musicgen_bp.route('/v1/audio/music', methods=['GET'])
def musicgen_info():
    """Get information about the MusicGen endpoint"""
    return jsonify({
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
                "model_size": "medium"
            }
        ]
    })

@musicgen_bp.route('/v1/audio/music', methods=['OPTIONS'])
def musicgen_options():
    """Handle preflight CORS requests"""
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,x-api-key')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response