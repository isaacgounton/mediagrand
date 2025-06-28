from flask import Blueprint, request, jsonify
import requests
from services.v1.text.text_overlay_service import TextOverlayService

text_overlay_bp = Blueprint('text_overlay', __name__)
text_overlay_service = TextOverlayService()

@text_overlay_bp.route('/add-text-overlay', methods=['POST'])
def add_text_overlay_route():
    """
    Add text overlay to a video using the FFmpeg compose API.
    Expected JSON payload:
    {
        "video_url": "https://example.com/video.mp4",
        "text": "Your overlay text here",
        "webhook_url": "https://your-webhook.com/callback",
        "options": {
            "duration": 3,           // How long to show text (seconds)
            "font_size": 60,         // Font size
            "font_color": "black",   // Font color
            "box_color": "white",    // Background box color
            "box_opacity": 0.85,     // Background box opacity (0-1)
            "position": "top-center", // Position: top-center, bottom-center, center, top-left, etc.
            "y_offset": 100,         // Vertical offset from position
            "auto_wrap": true        // Auto wrap text
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        required_fields = ['video_url', 'text', 'webhook_url']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        video_url = data['video_url']
        text = data['text']
        webhook_url = data['webhook_url']
        options = data.get('options', {})
        
        response_data, request_id = text_overlay_service.add_text_overlay_to_video(
            video_url, text, webhook_url, options
        )
        
        return jsonify({
            "success": True,
            "message": "Video overlay processing started",
            "request_id": request_id,
            "webhook_url": webhook_url,
            "ffmpeg_api_response": response_data
        }), 200
            
    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response else 500
        return jsonify({
            "error": "Failed to communicate with FFmpeg API",
            "details": str(e),
            "status_code": status_code
        }), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@text_overlay_bp.route('/presets', methods=['GET'])
def get_presets_route():
    """
    Get available text overlay presets.
    """
    presets = text_overlay_service.get_available_presets()
    return jsonify(presets)

@text_overlay_bp.route('/add-text-overlay/preset/<preset_name>', methods=['POST'])
def add_text_overlay_preset_route(preset_name):
    """
    Add text overlay using a preset.
    Expected JSON payload:
    {
        "video_url": "https://example.com/video.mp4",
        "text": "Your overlay text here",
        "webhook_url": "https://your-webhook.com/callback"
    }
    """
    presets = text_overlay_service.get_available_presets()
    
    if preset_name not in presets:
        return jsonify({"error": f"Preset '{preset_name}' not found"}), 404
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Add preset options to the request data
        preset_options = presets[preset_name]['options']
        combined_options = {**preset_options, **data.get('options', {})} # Allow overriding preset options
        data['options'] = combined_options
        
        required_fields = ['video_url', 'text', 'webhook_url']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        video_url = data['video_url']
        text = data['text']
        webhook_url = data['webhook_url']
        options = data['options']

        response_data, request_id = text_overlay_service.add_text_overlay_to_video(
            video_url, text, webhook_url, options
        )
        
        return jsonify({
            "success": True,
            "message": "Video overlay processing started with preset",
            "request_id": request_id,
            "webhook_url": webhook_url,
            "ffmpeg_api_response": response_data
        }), 200
            
    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response else 500
        return jsonify({
            "error": "Failed to communicate with FFmpeg API",
            "details": str(e),
            "status_code": status_code
        }), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
