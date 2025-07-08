from flask import Blueprint, request, jsonify
from services.enhanced_authentication import enhanced_authenticate
from services.v1.audio.musicgen import MusicGenService
import logging

musicgen_bp = Blueprint('musicgen', __name__)

@musicgen_bp.route('/v1/audio/music', methods=['POST'])
@enhanced_authenticate
def generate_music(job_id=None, data=None):
    """
    Generate music from text description using MusicGen model
    
    Expected JSON payload:
    {
        "description": "lo-fi music with a soothing melody",
        "duration": 8,
        "model_size": "small",
        "output_format": "wav",
        "webhook_url": "https://your-webhook.com/callback"
    }
    """
    try:
        logging.info(f"MusicGen request received for job {job_id}")
        
        # Validate required parameters
        if not data or not data.get('description'):
            return jsonify({
                "error": "Missing required parameter: description"
            }), 400
        
        description = data.get('description')
        duration = data.get('duration', 8)
        model_size = data.get('model_size', 'small')
        output_format = data.get('output_format', 'wav')
        
        # Validate parameters
        if duration > 30:
            return jsonify({
                "error": "Duration cannot exceed 30 seconds"
            }), 400
        
        if model_size not in ['small', 'medium', 'large']:
            return jsonify({
                "error": "Invalid model_size. Must be 'small', 'medium', or 'large'"
            }), 400
        
        if output_format not in ['wav', 'mp3']:
            return jsonify({
                "error": "Invalid output_format. Must be 'wav' or 'mp3'"
            }), 400
        
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
        
        return jsonify({
            "message": "Music generated successfully",
            "output_url": result['output_url'],
            "duration": result['duration'],
            "model_used": result['model_used'],
            "description": description,
            "file_size": result['file_size']
        }), 200
        
    except Exception as e:
        logging.error(f"MusicGen error for job {job_id}: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Music generation failed",
            "message": str(e)
        }), 500

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
                "options": ["small", "medium", "large"],
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