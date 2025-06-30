import uuid
import re
import os
import subprocess
from services.file_management import download_file
from services.cloud_storage import upload_file
from config import LOCAL_STORAGE_PATH

class TextOverlayService:
    def __init__(self):
        self.presets = {
            "title_overlay": {
                "description": "Large title text at the top, optimized for short phrases",
                "options": {
                    "duration": 5,
                    "font_size": 50,
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 1.0,
                    "boxborderw": 20,
                    "position": "top-center",
                    "y_offset": 50
                }
            },
            "subtitle": {
                "description": "Subtitle text at the bottom, with good readability",
                "options": {
                    "duration": 10,
                    "font_size": 36,
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 0.8,
                    "boxborderw": 15,
                    "position": "bottom-center",
                    "y_offset": 80
                }
            },
            "watermark": {
                "description": "Small, subtle watermark text",
                "options": {
                    "duration": 999999,
                    "font_size": 24,
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 0.5,
                    "boxborderw": 10,
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
                    "box_opacity": 1.0,
                    "boxborderw": 25,
                    "position": "center",
                    "y_offset": 0
                }
            },
            "modern_caption": {
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

    def wrap_text(self, text, max_width=40):
        """Improved text wrapping function with proper spacing for video overlays"""
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
                current_length += space_needed
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)  # Use actual newline, not escaped

    def escape_text_for_ffmpeg(self, text):
        """Escape special characters for FFmpeg drawtext filter"""
        # First, handle the text encoding
        if isinstance(text, str):
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        # FFmpeg drawtext filter requires these escapes:
        # Order is important - escape backslash first
        text = text.replace('\\', '\\\\')
        text = text.replace(':', '\\:')
        text = text.replace("'", "\\'")
        text = text.replace('"', '\\"')
        text = text.replace('[', '\\[')
        text = text.replace(']', '\\]')
        text = text.replace(',', '\\,')
        text = text.replace(';', '\\;')
        text = text.replace('=', '\\=')
        text = text.replace('%', '\\%')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        
        # Handle newlines properly for FFmpeg
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        
        return text

    def add_text_overlay_to_video(self, video_url, text, webhook_url, options, request_id=None):
        """Add text overlay to a video using FFmpeg"""
        
        if request_id is None:
            request_id = str(uuid.uuid4())

        duration = options.get('duration', 3)
        font_size = options.get('font_size', 48)
        font_color = options.get('font_color', 'black')
        box_color = options.get('box_color', 'white')
        box_opacity = options.get('box_opacity', 1.0)
        boxborderw = options.get('boxborderw', 20)
        position = options.get('position', 'top-center')
        y_offset = options.get('y_offset', 50)
        auto_wrap = options.get('auto_wrap', True)
        
        # Apply text wrapping before escaping
        if auto_wrap:
            text = self.wrap_text(text)
        
        # Now escape the text for FFmpeg
        escaped_text = self.escape_text_for_ffmpeg(text)
        
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
            position_coords = 'x=(w-text_w)/2:y=50'
        
        # Adjust y_offset based on position
        if 'top' in position and y_offset != 50:
            position_coords = position_coords.replace('y=50', f'y={y_offset}')
        elif 'bottom' in position and y_offset != 50:
            position_coords = position_coords.replace('y=h-text_h-50', f'y=h-text_h-{y_offset}')
        elif 'center' in position and 'top' not in position and 'bottom' not in position and y_offset != 0:
            position_coords = position_coords.replace('y=(h-text_h)/2', f'y=(h-text_h)/2+{y_offset}')

        # Font selection
        font_files = [
            "/usr/share/fonts/truetype/custom/OpenSansEmoji.ttf",
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",  # Better emoji support
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        
        font_file = None
        for font in font_files:
            if os.path.exists(font):
                font_file = font
                break
        
        if not font_file:
            font_file = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        
        # Create text file instead of passing text directly in command
        # This is more reliable for complex text with special characters
        text_file_path = os.path.join(LOCAL_STORAGE_PATH, f"{request_id}_text.txt")
        try:
            with open(text_file_path, 'w', encoding='utf-8') as f:
                f.write(text)  # Write the unescaped text
            
            # Build drawtext filter using textfile instead of text parameter
            drawtext_filter = (
                f"drawtext=fontfile={font_file}:"
                f"textfile={text_file_path}:"
                f"fontcolor={font_color}:"
                f"fontsize={font_size}:"
                f"box=1:"
                f"boxcolor={box_color}@{box_opacity}:"
                f"boxborderw={boxborderw}:"
                f"line_spacing=8:"
                f"{position_coords}:"
                f"enable='lt(t,{duration})'"
            )
            
            output_id = request_id
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
                "-c:a", "copy",  # Copy audio without re-encoding
                "-y",
                output_filename
            ]

            # Ensure UTF-8 environment for subprocess
            env = os.environ.copy()
            env['LC_ALL'] = 'C.UTF-8'
            env['LANG'] = 'C.UTF-8'
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True, encoding='utf-8', env=env)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg command failed: {e.stderr}"
            # Try alternative approach with direct text if textfile fails
            if "textfile" in str(e.stderr):
                # Fall back to using text parameter with escaped text
                drawtext_filter = (
                    f"drawtext=fontfile={font_file}:"
                    f"text='{escaped_text}':"
                    f"fontcolor={font_color}:"
                    f"fontsize={font_size}:"
                    f"box=1:"
                    f"boxcolor={box_color}@{box_opacity}:"
                    f"boxborderw={boxborderw}:"
                    f"line_spacing=8:"
                    f"{position_coords}:"
                    f"enable='lt(t,{duration})'"
                )
                ffmpeg_command[ffmpeg_command.index("-vf") + 1] = drawtext_filter
                try:
                    result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True, encoding='utf-8', env=env)
                except subprocess.CalledProcessError as e2:
                    raise Exception(f"FFmpeg failed with both textfile and text parameter: {e2.stderr}")
            else:
                raise Exception(error_msg)
        finally:
            # Clean up temporary files
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(text_file_path):
                os.remove(text_file_path)
        
        # Upload the processed video to cloud storage
        cloud_url = upload_file(output_filename)
        
        # Clean up the local output file after upload
        if os.path.exists(output_filename):
            os.remove(output_filename)

        response_data = {
            "output_url": cloud_url,
            "message": "FFmpeg process completed successfully and uploaded to cloud storage."
        }
        
        return response_data, "/v1/text/add-text-overlay", 200

    def get_available_presets(self):
        return self.presets