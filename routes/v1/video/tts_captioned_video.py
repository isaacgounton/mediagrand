# Copyright (c) 2025 Isaac Gounton
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

from flask import Blueprint
from utils.app_utils import validate_payload, queue_task_wrapper
import logging
import os
from services.v1.video.tts_captioned_video import process_tts_captioned_video
from services.authentication import authenticate
from services.cloud_storage import upload_file

v1_video_tts_captioned_bp = Blueprint('v1_video_tts_captioned', __name__)
logger = logging.getLogger(__name__)

def get_available_fonts():
    """Get list of available fonts from the fonts directory"""
    font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'fonts')
    fonts = []
    font_families = {}
    
    if os.path.exists(font_dir):
        for file in os.listdir(font_dir):
            if file.endswith(('.ttf', '.otf')):
                # Remove file extension
                font_name = os.path.splitext(file)[0]
                
                # Parse font family and style
                if '-' in font_name:
                    family, style = font_name.split('-', 1)
                else:
                    family = font_name
                    style = 'Regular'
                
                # Clean up family name
                family = family.replace('_', ' ')
                style = style.replace('_', ' ')
                
                # Group by family
                if family not in font_families:
                    font_families[family] = []
                
                font_families[family].append({
                    "style": style,
                    "file": file,
                    "path": os.path.join(font_dir, file)
                })
    
    # Convert to list format with family information
    for family_name, styles in sorted(font_families.items()):
        # Add main family entry
        main_style = None
        for style_info in styles:
            if style_info["style"].lower() in ['regular', 'normal', '']:
                main_style = style_info
                break
        
        if not main_style and styles:
            main_style = styles[0]  # Use first style as default
        
        if main_style:
            fonts.append({
                "name": family_name,
                "file": main_style["file"], 
                "path": main_style["path"],
                "family": family_name,
                "styles": [s["style"] for s in styles]
            })
        
        # Add individual style entries for families with multiple styles
        if len(styles) > 1:
            for style_info in styles:
                if style_info["style"].lower() not in ['regular', 'normal']:
                    fonts.append({
                        "name": f"{family_name} {style_info['style']}",
                        "file": style_info["file"],
                        "path": style_info["path"],
                        "family": family_name,
                        "style": style_info["style"]
                    })
    
    # Add system fonts as fallback
    system_fonts = [
        {
            "name": "DejaVu Sans", 
            "file": "DejaVuSans.ttf", 
            "path": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "family": "DejaVu Sans"
        },
        {
            "name": "DejaVu Sans Bold", 
            "file": "DejaVuSans-Bold.ttf", 
            "path": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "family": "DejaVu Sans",
            "style": "Bold"
        },
    ]
    
    # Only add system fonts if they exist and aren't already in the list
    for sys_font in system_fonts:
        if os.path.exists(sys_font["path"]) and not any(f["name"] == sys_font["name"] for f in fonts):
            fonts.append(sys_font)
    
    return fonts

@v1_video_tts_captioned_bp.route('/v1/video/fonts', methods=['GET'])
@authenticate
def list_fonts():
    """Get available fonts for video generation"""
    try:
        fonts = get_available_fonts()
        return {"fonts": fonts}, 200
    except Exception as e:
        logger.error(f"Error listing fonts: {str(e)}")
        return {"error": "Failed to list fonts"}, 500

@v1_video_tts_captioned_bp.route('/v1/video/tts-captioned', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "background_url": {
            "type": "string",
            "format": "uri",
            "description": "URL of the background image"
        },
        "text": {
            "type": "string",
            "description": "Text to generate speech from (required if audio_url not provided)"
        },
        "audio_url": {
            "type": "string",
            "format": "uri",
            "description": "URL of existing audio file (required if text not provided)"
        },
        "width": {
            "type": "number",
            "minimum": 1,
            "description": "Width of the video (default: 1080)"
        },
        "height": {
            "type": "number",
            "minimum": 1,
            "description": "Height of the video (default: 1920)"
        },
        "provider": {
            "type": "string",
            "enum": ["kokoro", "chatterbox", "openai-edge-tts"],
            "description": "TTS provider to use (default: openai-edge-tts)"
        },
        "voice": {
            "type": "string",
            "description": "Voice for text-to-speech (default: en-US-AriaNeural)"
        },
        "speed": {
            "type": "number",
            "minimum": 0.1,
            "maximum": 3.0,
            "description": "Speed of speech (default: 1.0)"
        },
        "speech_speed": {
            "type": "number",
            "minimum": 0.1,
            "maximum": 3.0,
            "description": "Alias for speed parameter"
        },
        "language": {
            "type": "string",
            "description": "Language code for TTS (optional, e.g. 'en', 'fr', 'de')"
        },
        "image_effect": {
            "type": "string",
            "enum": ["none", "ken_burns", "pan_left", "pan_right", "pan_up", "pan_down", "zoom_in", "zoom_out"],
            "description": "Effect to apply to the background image (default: 'ken_burns')"
        },
        # Caption styling options
        "caption_line_count": {
            "type": "integer",
            "minimum": 1,
            "maximum": 5,
            "description": "Number of lines per subtitle segment (default: 1)"
        },
        "caption_line_max_length": {
            "type": "integer",
            "minimum": 1,
            "maximum": 200,
            "description": "Maximum characters per line (default: 50)"
        },
        "caption_font_size": {
            "type": "integer",
            "minimum": 8,
            "maximum": 200,
            "description": "Font size for subtitles (default: 120)"
        },
        "caption_font_name": {
            "type": "string",
            "description": "Font family name (default: 'Arial')"
        },
        "caption_font_bold": {
            "type": "boolean",
            "description": "Whether to use bold font (default: true)"
        },
        "caption_font_italic": {
            "type": "boolean",
            "description": "Whether to use italic font (default: false)"
        },
        "caption_font_color": {
            "type": "string",
            "description": "Font color in hex format (default: '#fff')"
        },
        "caption_position": {
            "type": "string",
            "enum": ["top", "center", "bottom"],
            "description": "Vertical position of subtitles (default: 'top')"
        },
        "caption_shadow_color": {
            "type": "string",
            "description": "Shadow color in hex format (default: '#000')"
        },
        "caption_shadow_transparency": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Shadow transparency from 0.0 to 1.0 (default: 0.4)"
        },
        "caption_shadow_blur": {
            "type": "integer",
            "minimum": 0,
            "maximum": 20,
            "description": "Shadow blur radius (default: 10)"
        },
        "caption_stroke_color": {
            "type": "string",
            "description": "Stroke/outline color in hex format (default: '#000')"
        },
        "caption_stroke_size": {
            "type": "integer",
            "minimum": 0,
            "maximum": 10,
            "description": "Stroke/outline size (default: 5)"
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["background_url"],
    "additionalProperties": False,
    "anyOf": [
        {"required": ["text"]},
        {"required": ["audio_url"]}
    ]
})
@queue_task_wrapper(bypass_queue=False)
def generate_tts_captioned_video(job_id, data):
    background_url = data['background_url']
    text = data.get('text')
    audio_url = data.get('audio_url')
    width = int(data.get('width', 1080))
    height = int(data.get('height', 1920))
    provider = data.get('provider', 'openai-edge-tts')
    voice = data.get('voice', 'en-US-AriaNeural')
    # Support both 'speed' and 'speech_speed' parameters
    speed = data.get('speed') or data.get('speech_speed', 1.0)
    language = data.get('language')
    image_effect = data.get('image_effect', 'ken_burns')
    
    # Caption styling parameters
    caption_config = {
        'line_count': data.get('caption_line_count', 1),
        'line_max_length': data.get('caption_line_max_length', 50),
        'font_size': data.get('caption_font_size', 120),
        'font_name': data.get('caption_font_name', 'Arial'),
        'font_bold': data.get('caption_font_bold', True),
        'font_italic': data.get('caption_font_italic', False),
        'font_color': data.get('caption_font_color', '#fff'),
        'position': data.get('caption_position', 'top'),
        'shadow_color': data.get('caption_shadow_color', '#000'),
        'shadow_transparency': data.get('caption_shadow_transparency', 0.4),
        'shadow_blur': data.get('caption_shadow_blur', 10),
        'stroke_color': data.get('caption_stroke_color', '#000'),
        'stroke_size': data.get('caption_stroke_size', 5)
    }
    
    webhook_url = data.get('webhook_url')
    id = data.get('id')

    logger.info(f"Job {job_id}: Received TTS captioned video request")

    try:
        output_file = process_tts_captioned_video(
            background_url=background_url,
            text=text,
            audio_url=audio_url,
            width=width,
            height=height,
            provider=provider,
            voice=voice,
            speed=speed,
            language=language,
            image_effect=image_effect,
            caption_config=caption_config,
            job_id=job_id
        )
        logger.info(f"Job {job_id}: TTS captioned video generation completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: TTS captioned video uploaded to cloud storage: {cloud_url}")

        return cloud_url, "/v1/video/tts-captioned", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during TTS captioned video generation - {str(e)}")
        return str(e), "/v1/video/tts-captioned", 500

@v1_video_tts_captioned_bp.route('/v1/video/tts-captioned', methods=['OPTIONS'])
def generate_tts_captioned_video_options():
    """Return API documentation for TTS captioned video endpoint"""
    available_fonts = [font["name"] for font in get_available_fonts()]
    
    return {
        "description": "Creates a captioned text-to-speech video from background image and text or audio with advanced styling options",
        "methods": ["POST"],
        "endpoints": {
            "fonts": "/v1/video/fonts - Get available fonts for video generation"
        },
        "parameters": {
            "background_url": {
                "type": "string",
                "required": True,
                "description": "URL of the background image",
                "example": "https://example.com/background.jpg"
            },
            "text": {
                "type": "string",
                "required": "conditional",
                "description": "Text to generate speech from (required if audio_url not provided)",
                "example": "Hello, this is a sample text for speech generation."
            },
            "audio_url": {
                "type": "string",
                "required": "conditional",
                "description": "URL of existing audio file (required if text not provided)",
                "example": "https://example.com/audio.mp3"
            },
            "width": {
                "type": "number",
                "required": False,
                "default": 1080,
                "description": "Width of the video",
                "example": 1080
            },
            "height": {
                "type": "number",
                "required": False,
                "default": 1920,
                "description": "Height of the video",
                "example": 1920
            },
            "provider": {
                "type": "string",
                "required": False,
                "default": "openai-edge-tts",
                "enum": ["kokoro", "chatterbox", "openai-edge-tts"],
                "description": "TTS provider to use",
                "example": "openai-edge-tts"
            },
            "voice": {
                "type": "string",
                "required": False,
                "default": "en-US-AriaNeural",
                "description": "Voice for text-to-speech",
                "example": "en-US-AriaNeural"
            },
            "speed": {
                "type": "number",
                "required": False,
                "default": 1.0,
                "description": "Speed of speech (0.1 to 3.0)",
                "example": 1.2
            },
            "language": {
                "type": "string",
                "required": False,
                "description": "Language code for TTS (e.g. 'en', 'fr', 'de')",
                "example": "en"
            },
            "image_effect": {
                "type": "string",
                "required": False,
                "default": "ken_burns",
                "enum": ["none", "ken_burns", "pan_left", "pan_right", "pan_up", "pan_down", "zoom_in", "zoom_out"],
                "description": "Effect to apply to the background image",
                "example": "ken_burns"
            },
            "caption_line_count": {
                "type": "integer",
                "required": False,
                "default": 1,
                "description": "Number of lines per subtitle segment (1-5)",
                "example": 2
            },
            "caption_line_max_length": {
                "type": "integer",
                "required": False,
                "default": 50,
                "description": "Maximum characters per line (1-200)",
                "example": 50
            },
            "caption_font_size": {
                "type": "integer",
                "required": False,
                "default": 120,
                "description": "Font size for subtitles (8-200)",
                "example": 120
            },
            "caption_font_name": {
                "type": "string",
                "required": False,
                "default": "Arial",
                "description": "Font family name",
                "example": "Arial",
                "available_fonts": available_fonts
            },
            "caption_font_bold": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Whether to use bold font",
                "example": True
            },
            "caption_font_italic": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Whether to use italic font",
                "example": False
            },
            "caption_font_color": {
                "type": "string",
                "required": False,
                "default": "#fff",
                "description": "Font color in hex format",
                "example": "#ffffff"
            },
            "caption_position": {
                "type": "string",
                "required": False,
                "default": "top",
                "enum": ["top", "center", "bottom"],
                "description": "Vertical position of subtitles",
                "example": "top"
            },
            "caption_shadow_color": {
                "type": "string",
                "required": False,
                "default": "#000",
                "description": "Shadow color in hex format",
                "example": "#000000"
            },
            "caption_shadow_transparency": {
                "type": "number",
                "required": False,
                "default": 0.4,
                "description": "Shadow transparency (0.0 to 1.0)",
                "example": 0.4
            },
            "caption_shadow_blur": {
                "type": "integer",
                "required": False,
                "default": 10,
                "description": "Shadow blur radius (0-20)",
                "example": 10
            },
            "caption_stroke_color": {
                "type": "string",
                "required": False,
                "default": "#000",
                "description": "Stroke/outline color in hex format",
                "example": "#000000"
            },
            "caption_stroke_size": {
                "type": "integer",
                "required": False,
                "default": 5,
                "description": "Stroke/outline size (0-10)",
                "example": 5
            },
            "webhook_url": {
                "type": "string",
                "required": False,
                "description": "Optional webhook URL for job completion notification"
            }
        },
        "response": {
            "success": {
                "code": 200,
                "description": "Returns cloud storage URL of generated captioned video"
            },
            "error": {
                "code": 500,
                "description": "Error message if generation fails"
            }
        },
        "example_request": {
            "background_url": "https://example.com/background.jpg",
            "text": "Hello, this is a sample text for speech generation.",
            "width": 1080,
            "height": 1920,
            "provider": "openai-edge-tts",
            "voice": "en-US-AriaNeural",
            "speed": 1.0,
            "image_effect": "ken_burns",
            "caption_font_size": 120,
            "caption_font_name": "Arial",
            "caption_font_color": "#ffffff",
            "caption_position": "top"
        }
    }