import uuid
import re
import os
import subprocess
from services.file_management import download_file
from services.cloud_storage import upload_file # Import upload_file
from config import LOCAL_STORAGE_PATH

class TextOverlayService:
    def __init__(self):
        self.presets = {
            "title_overlay": {
                "description": "Large title text at the top, optimized for short phrases",
                "options": {
                    "duration": 5,
                    "font_size": 50, # Adjusted for better fit
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 1.0, # Fully opaque
                    "boxborderw": 20, # Added padding
                    "position": "top-center",
                    "y_offset": 50
                }
            },
            "subtitle": {
                "description": "Subtitle text at the bottom, with good readability",
                "options": {
                    "duration": 10,
                    "font_size": 36, # Standard subtitle size
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 0.8,
                    "boxborderw": 15, # Added padding
                    "position": "bottom-center",
                    "y_offset": 80 # Slightly higher from bottom
                }
            },
            "watermark": {
                "description": "Small, subtle watermark text",
                "options": {
                    "duration": 999999,  # Show for entire video
                    "font_size": 24,
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 0.5,
                    "boxborderw": 10, # Added padding
                    "position": "bottom-right",
                    "y_offset": 30
                }
            },
            "alert": {
                "description": "Alert/notification style overlay, prominent",
                "options": {
                    "duration": 3,
                    "font_size": 50,
                    "font_color": "red",
                    "box_color": "yellow",
                    "box_opacity": 1.0, # Fully opaque
                    "boxborderw": 25, # Added more padding
                    "position": "center",
                    "y_offset": 0
                }
            },
            "modern_caption": { # New preset inspired by the example
                "description": "Modern caption style with solid background and good padding",
                "options": {
                    "duration": 5,
                    "font_size": 36,
                    "font_color": "black",
                    "box_color": "white",
                    "box_opacity": 1.0,
                    "boxborderw": 20,
                    "position": "top-center",
                    "y_offset": 50
                }
            }
        }

    def wrap_text(self, text, max_width=60):
        """Improved text wrapping function with proper spacing"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            # Calculate space needed (word length + space if not first word)
            space_needed = len(word) + (1 if current_line else 0)
            
            if current_length + space_needed > max_width and current_line:
                # Finalize current line and start new one
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word) + (1 if current_line else 0)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\\n'.join(lines)

    def escape_text_for_ffmpeg(self, text):
        """Escape special characters for FFmpeg drawtext filter with proper UTF-8 support"""
        # Ensure text is properly encoded as UTF-8
        if isinstance(text, str):
            text = text.encode('utf-8').decode('utf-8')
        
        # Escape characters that have special meaning in FFmpeg
        # Order matters: escape backslash first
        text = text.replace('\\', '\\\\')
        text = text.replace(':', '\\:')
        text = text.replace("'", "\\'")
        text = text.replace('[', '\\[')
        text = text.replace(']', '\\]')
        text = text.replace(',', '\\,')
        text = text.replace(';', '\\;')
        text = text.replace('%', '\\%')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        return text

    def add_text_overlay_to_video(self, video_url, text, webhook_url, options, request_id=None):
        """
        Add text overlay to a video using the FFmpeg compose API
        """
        
        # If request_id is not provided, generate a new one
        if request_id is None:
            request_id = str(uuid.uuid4())

        duration = options.get('duration', 3)
        font_size = options.get('font_size', 36) # Default to 36 as per example
        font_color = options.get('font_color', 'black')
        box_color = options.get('box_color', 'white')
        box_opacity = options.get('box_opacity', 1.0) # Default to 1.0 (fully opaque)
        boxborderw = options.get('boxborderw', 20) # Default to 20 for padding
        position = options.get('position', 'top-center')
        y_offset = options.get('y_offset', 50) # Default y_offset
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
            position_coords = 'x=(w-text_w)/2:y=50' # Adjusted default y for unknown position
        
        # Adjust y_offset based on position
        # Only adjust if y_offset is different from the default for the given position
        if 'top' in position and y_offset != 50:
            position_coords = position_coords.replace('y=50', f'y={y_offset}')
        elif 'bottom' in position and y_offset != 50:
            position_coords = position_coords.replace('y=h-text_h-50', f'y=h-text_h-{y_offset}')
        elif 'center' in position and 'top' not in position and 'bottom' not in position and y_offset != 0: # Center default y_offset is 0
            position_coords = position_coords.replace('y=(h-text_h)/2', f'y=(h-text_h)/2+{y_offset}')


        # Use a font that supports Unicode/emojis
        font_files = [
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/System/Library/Fonts/Arial.ttf"
        ]
        
        font_file = None
        for font in font_files:
            if os.path.exists(font):
                font_file = font
                break
        
        if not font_file:
            font_file = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        
        drawtext_filter = (
            f"drawtext=fontfile={font_file}:"
            f"text='{text}':"
            f"fontcolor={font_color}:"
            f"fontsize={font_size}:"
            f"box=1:"
            f"boxcolor={box_color}@{box_opacity}:"
            f"boxborderw={boxborderw}:"
            f"line_spacing=8:"
            f"{position_coords}:"
            f"enable=lt(t,{duration})"
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
            subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True, encoding='utf-8')
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg command failed: {e.stderr}")
        finally:
            # Clean up input file
            if os.path.exists(input_path):
                os.remove(input_path)
        
        # In a real scenario, you would upload output_filename to cloud storage
            # Upload the processed video to cloud storage
            cloud_url = upload_file(output_filename)
            
            # Clean up the local output file after upload
            if os.path.exists(output_filename):
                os.remove(output_filename)

            response_data = {
                "output_url": cloud_url,
                "message": "FFmpeg process completed successfully and uploaded to cloud storage."
            }
            
            # Return response_data, endpoint, status_code as expected by queue_task_wrapper
            return response_data, "/v1/text/add-text-overlay", 200

    def get_available_presets(self):
        return self.presets
