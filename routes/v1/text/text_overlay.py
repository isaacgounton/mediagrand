from flask import Blueprint, request, jsonify
import requests
import logging
from services.v1.text.text_overlay_service import TextOverlayService
from utils.app_utils import queue_task_wrapper
import uuid

text_overlay_bp = Blueprint('text_overlay', __name__)
text_overlay_service = TextOverlayService()

@text_overlay_bp.route('/add-text-overlay', methods=['POST'])
@queue_task_wrapper(bypass_queue=False)
def add_text_overlay_route(job_id, data):
    """
    Add text overlay to a video using the FFmpeg compose API.
    Expected JSON payload:
    {
        "video_url": "https://example.com/video.mp4",
        "text": "Your overlay text here",
        "webhook_url": "https://your-webhook.com/callback", (optional)
        "id": "your-custom-id", (optional)
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
        logging.info(f"Starting text overlay operation - Job ID: {job_id}")
        # data is already parsed by queue_task_wrapper
        
        required_fields = ['video_url', 'text'] # webhook_url is now optional, handled by queue_task_wrapper
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400, {} # Return empty dict for headers
        
        video_url = data['video_url']
        text = data['text']
        webhook_url = data.get('webhook_url') # Now optional
        custom_id = data.get('id') # Optional custom ID from user
        options = data.get('options', {})
        
        # Use custom_id if provided, otherwise use the internally generated job_id
        request_id_to_use = custom_id if custom_id else job_id
        
        response_data, endpoint, status_code = text_overlay_service.add_text_overlay_to_video(
            video_url, text, webhook_url, options, request_id=request_id_to_use # Pass request_id
        )
        
        # queue_task_wrapper expects a tuple (response_data, endpoint, status_code)
        return {
            "success": True,
            "message": "Video overlay processing started",
            "request_id": request_id_to_use,
            "webhook_url": webhook_url,
            "ffmpeg_api_response": response_data
        }, endpoint, status_code
            
    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response else 500
        return {
            "error": "Failed to communicate with FFmpeg API",
            "details": str(e),
            "status_code": status_code
        }, "/v1/text/add-text-overlay", status_code # Include endpoint
    except Exception as e:
        return {"error": str(e)}, "/v1/text/add-text-overlay", 500 # Include endpoint

@text_overlay_bp.route('/presets', methods=['GET'])
def get_presets_route():
    """
    Get available text overlay presets.
    """
    presets = text_overlay_service.get_available_presets()
    return jsonify(presets)

@text_overlay_bp.route('/add-text-overlay/preset/<preset_name>', methods=['POST'])
@queue_task_wrapper(bypass_queue=False)
def add_text_overlay_preset_route(job_id, data, preset_name=None):
    """
    Add text overlay using a preset.
    Expected JSON payload:
    {
        "video_url": "https://example.com/video.mp4",
        "text": "Your overlay text here",
        "webhook_url": "https://your-webhook.com/callback", (optional)
        "id": "your-custom-id" (optional)
    }
    """
    # Extract preset_name from the URL if not passed as parameter
    if preset_name is None:
        preset_name = request.view_args.get('preset_name')
    
    presets = text_overlay_service.get_available_presets()
    
    if preset_name not in presets:
        return {"error": f"Preset '{preset_name}' not found"}, "/v1/text/add-text-overlay/preset", 404
    
    try:
        logging.info(f"Starting text overlay preset '{preset_name}' operation - Job ID: {job_id}")
        required_fields = ['video_url', 'text']
        for field in required_fields:
            if field not in data:
                return {"error": f"Missing required field: {field}"}, "/v1/text/add-text-overlay/preset", 400
        
        # Add preset options to the request data
        preset_options = presets[preset_name]['options']
        combined_options = {**preset_options, **data.get('options', {})} # Allow overriding preset options
        
        video_url = data['video_url']
        text = data['text']
        webhook_url = data.get('webhook_url')
        custom_id = data.get('id')
        
        # Use custom_id if provided, otherwise use the internally generated job_id
        request_id_to_use = custom_id if custom_id else job_id
        
        response_data, endpoint, status_code = text_overlay_service.add_text_overlay_to_video(
            video_url, text, webhook_url, combined_options, request_id=request_id_to_use
        )
        
        return {
            "success": True,
            "message": f"Video overlay processing started with preset '{preset_name}'",
            "request_id": request_id_to_use,
            "webhook_url": webhook_url,
            "preset_used": preset_name,
            "ffmpeg_api_response": response_data
        }, endpoint, status_code
            
    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response else 500
        return {
            "error": "Failed to communicate with FFmpeg API",
            "details": str(e),
            "status_code": status_code
        }, "/v1/text/add-text-overlay/preset", status_code
    except Exception as e:
        return {"error": str(e)}, "/v1/text/add-text-overlay/preset", 500
