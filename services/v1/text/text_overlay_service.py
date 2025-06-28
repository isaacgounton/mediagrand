import uuid
import re
import os
import subprocess
from services.file_management import download_file
from config import LOCAL_STORAGE_PATH

class TextOverlayService:
    def __init__(self):
        self.presets = {
            "title_overlay": {
                "description": "Large title text at the top",
                "options": {
                    "duration": 5,
                    "font_size": 80,
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 0.7,
                    "position": "top-center",
                    "y_offset": 50
                }
            },
            "subtitle": {
                "description": "Subtitle text at the bottom",
                "options": {
                    "duration": 10,
                    "font_size": 40,
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 0.8,
                    "position": "bottom-center",
                    "y_offset": 100
                }
            },
            "watermark": {
                "description": "Small watermark text",
                "options": {
                    "duration": 999999,  # Show for entire video
                    "font_size": 24,
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 0.5,
                    "position": "bottom-right",
                    "y_offset": 30
                }
            },
            "alert": {
                "description": "Alert/notification style overlay",
                "options": {
                    "duration": 3,
                    "font_size": 50,
                    "font_color": "red",
                    "box_color": "yellow",
                    "box_opacity": 0.9,
                    "position": "center",
                    "y_offset": 0
                }
            }
        }

    def wrap_text(self, text, max_width=40):
        """Simple text wrapping function"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + len(current_line) <= max_width:
                current_line.append(word)
                current_length += len(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    lines.append(word)  # Word is longer than max_width
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\\n'.join(lines)

    def escape_text_for_ffmpeg(self, text):
        """Escape special characters for FFmpeg drawtext filter"""
        # Escape characters that have special meaning in FFmpeg
        text = text.replace('\\', '\\\\')
        text = text.replace(':', '\\:')
        text = text.replace("'", "\\'")
        text = text.replace('[', '\\[')
        text = text.replace(']', '\\]')
        text = text.replace(',', '\\,')
        text = text.replace(';', '\\;')
        return text

    def add_text_overlay_to_video(self, video_url, text, webhook_url, options, request_id=None):
        """
        Add text overlay to a video using the FFmpeg compose API
        """
        
        # If request_id is not provided, generate a new one
        if request_id is None:
            request_id = str(uuid.uuid4())

        duration = options.get('duration', 3)
        font_size = options.get('font_size', 60)
        font_color = options.get('font_color', 'black')
        box_color = options.get('box_color', 'white')
        box_opacity = options.get('box_opacity', 0.85)
        position = options.get('position', 'top-center')
        y_offset = options.get('y_offset', 100)
        auto_wrap = options.get('auto_wrap', True)
        
        if auto_wrap:
            text = self.wrap_text(text)
        text = self.escape_text_for_ffmpeg(text)
        
        position_map = {
            'top-left': 'x=50:y=50',
            'top-center': 'x=(w-text_w)/2:y=50',
            'top-right': 'x=w-text_w-50:y=50',
            'center-left': 'x=50:y=(h-text_h)/2',
            'center': 'x=(w-text_w)/2:y=(h-text_h)/2',
            'center-right': 'x=w-text_w-50:y=(h-text_h)/2',
            'bottom-left': 'x=50:y=h-text_h-50',
            'bottom-center': 'x=(w-text_w)/2:y=h-text_h-50',
            'bottom-right': 'x=w-text_w-50:y=h-text_h-50',
        }
        
        if position in position_map:
            position_coords = position_map[position]
        else:
            position_coords = 'x=(w-text_w)/2:y=100'
        
        if position in position_map and y_offset != 100:
            if 'top' in position:
                position_coords = position_coords.replace('y=50', f'y={y_offset}')
            elif 'bottom' in position:
                position_coords = position_coords.replace('y=h-text_h-50', f'y=h-text_h-{y_offset}')
            elif 'center' in position and 'top' not in position and 'bottom' not in position:
                position_coords = position_coords.replace('y=(h-text_h)/2', f'y=(h-text_h)/2+{y_offset-100}')
        
        drawtext_filter = (
            f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"text='{text}':"
            f"fontcolor={font_color}:"
            f"fontsize={font_size}:"
            f"box=1:"
            f"boxcolor={box_color}@{box_opacity}:"
            f"boxborderw=35:"
            f"line_spacing=14:"
            f"{position_coords}:"
            f"enable='lt(t,{duration})'"
        )
        
        # Generate unique ID for output file
        output_id = request_id # Use the provided/generated request_id as output_id
        output_filename = os.path.join(LOCAL_STORAGE_PATH, f"{output_id}_output.mp4")

        # Download video locally
        input_path = download_file(video_url, LOCAL_STORAGE_PATH)

        # Build FFmpeg command
        ffmpeg_command = [
            "ffmpeg",
            "-i", input_path,
            "-vf", drawtext_filter,
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "medium",
            "-y", # Overwrite output files without asking
            output_filename
        ]

        try:
            subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg command failed: {e.stderr}")
        finally:
            # Clean up input file
            if os.path.exists(input_path):
                os.remove(input_path)
        
        # In a real scenario, you would upload output_filename to cloud storage
        # and send its URL via webhook. For now, we'll just return the local path
        # and a dummy success response.
        response_data = {
            "output_file_path": output_filename,
            "message": "FFmpeg process completed successfully locally."
        }
        
        # Return response_data, endpoint, status_code as expected by queue_task_wrapper
        return response_data, "/v1/text/add-text-overlay", 200

    def get_available_presets(self):
        return self.presets
