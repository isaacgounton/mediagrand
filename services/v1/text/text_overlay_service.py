import uuid
import re
import os
import subprocess
import logging
from services.file_management import download_file
from services.cloud_storage import upload_file
from config.config import LOCAL_STORAGE_PATH

class TextOverlayService:
    def __init__(self):
        self.presets = {
            "title_overlay": {
                "description": "Large title text at the top, optimized for short phrases",
                "options": {
                    "duration": 5,
                    "font_size": 60,
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 0.85,
                    "boxborderw": 80,
                    "position": "top-center",
                    "y_offset": 80,
                    "line_spacing": 18
                }
            },
            "subtitle": {
                "description": "Subtitle text at the bottom, with good readability",
                "options": {
                    "duration": 10,
                    "font_size": 42,
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 0.8,
                    "boxborderw": 60,
                    "position": "bottom-center",
                    "y_offset": 100,
                    "line_spacing": 15
                }
            },
            "watermark": {
                "description": "Small, subtle watermark text",
                "options": {
                    "duration": 999999,
                    "font_size": 28,
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 0.6,
                    "boxborderw": 45,
                    "position": "bottom-right",
                    "y_offset": 40,
                    "line_spacing": 10
                }
            },
            "alert": {
                "description": "Alert/notification style overlay, prominent and attention-grabbing",
                "options": {
                    "duration": 4,
                    "font_size": 56,
                    "font_color": "white",
                    "box_color": "red",
                    "box_opacity": 0.9,
                    "boxborderw": 75,
                    "position": "center",
                    "y_offset": 0,
                    "line_spacing": 16
                }
            },
            "modern_caption": {
                "description": "Modern caption style with solid background and good padding",
                "options": {
                    "duration": 5,
                    "font_size": 50,
                    "font_color": "black",
                    "box_color": "white",
                    "box_opacity": 0.85,
                    "boxborderw": 70,
                    "position": "top-center",
                    "y_offset": 100,
                    "line_spacing": 16
                }
            },
            "social_post": {
                "description": "Instagram/TikTok style caption, trendy and engaging",
                "options": {
                    "duration": 6,
                    "font_size": 48,
                    "font_color": "white",
                    "box_color": "black",
                    "box_opacity": 0.7,
                    "boxborderw": 65,
                    "position": "bottom-center",
                    "y_offset": 120,
                    "line_spacing": 15
                }
            },
            "quote": {
                "description": "Quote or testimonial style with elegant presentation",
                "options": {
                    "duration": 8,
                    "font_size": 44,
                    "font_color": "white",
                    "box_color": "navy",
                    "box_opacity": 0.8,
                    "boxborderw": 70,
                    "position": "center",
                    "y_offset": 0,
                    "line_spacing": 17
                }
            },
            "news_ticker": {
                "description": "News ticker style for breaking news or updates",
                "options": {
                    "duration": 15,
                    "font_size": 36,
                    "font_color": "white",
                    "box_color": "darkred",
                    "box_opacity": 0.95,
                    "boxborderw": 50,
                    "position": "bottom-center",
                    "y_offset": 50,
                    "line_spacing": 12
                }
            }
        }

    def wrap_text(self, text, max_width=25):
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
        text = text.replace('\\', '\\\\\\\\')  # More aggressive backslash escaping
        text = text.replace(':', '\\\\:')
        text = text.replace("'", "\\\\'")
        text = text.replace('"', '\\\\"')
        text = text.replace('[', '\\\\[')
        text = text.replace(']', '\\\\]')
        text = text.replace(',', '\\\\,')
        text = text.replace(';', '\\\\;')
        text = text.replace('=', '\\\\=')
        text = text.replace('%', '\\\\%')
        text = text.replace('{', '\\\\{')
        text = text.replace('}', '\\\\}')
        
        # Handle French accented characters and other special characters
        text = text.replace('à', 'a')
        text = text.replace('á', 'a')
        text = text.replace('â', 'a')
        text = text.replace('ã', 'a')
        text = text.replace('ä', 'a')
        text = text.replace('å', 'a')
        text = text.replace('é', 'e')
        text = text.replace('è', 'e')
        text = text.replace('ê', 'e')
        text = text.replace('ë', 'e')
        text = text.replace('í', 'i')
        text = text.replace('ì', 'i')
        text = text.replace('î', 'i')
        text = text.replace('ï', 'i')
        text = text.replace('ó', 'o')
        text = text.replace('ò', 'o')
        text = text.replace('ô', 'o')
        text = text.replace('õ', 'o')
        text = text.replace('ö', 'o')
        text = text.replace('ú', 'u')
        text = text.replace('ù', 'u')
        text = text.replace('û', 'u')
        text = text.replace('ü', 'u')
        text = text.replace('ç', 'c')
        text = text.replace('ñ', 'n')
        text = text.replace('ÿ', 'y')
        
        # Handle special punctuation and symbols that might cause issues
        text = text.replace('—', '-')  # em dash
        text = text.replace('–', '-')  # en dash
        text = text.replace('"', '"')  # smart quotes
        text = text.replace('"', '"')
        text = text.replace(''', "'")
        text = text.replace(''', "'")
        text = text.replace('…', '...')  # ellipsis
        
        # Handle newlines properly for FFmpeg
        text = text.replace('\n', '\\\\n')
        text = text.replace('\r', '\\\\r')
        
        # Handle special spaces that might get mangled
        text = text.replace('  ', ' ')  # Normalize double spaces
        
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
        boxborderw = options.get('boxborderw', 60)
        position = options.get('position', 'top-center')
        y_offset = options.get('y_offset', 50)
        line_spacing = options.get('line_spacing', 8)
        auto_wrap = options.get('auto_wrap', True)
        
        # Apply text wrapping before escaping
        if auto_wrap:
            text = self.wrap_text(text)
        
        # Now escape the text for FFmpeg
        escaped_text = self.escape_text_for_ffmpeg(text)
        
        position_map = {
            'top-left': 'x=30:y=30',
            'top-center': 'x=(w-text_w)/2:y=30',
            'top-right': 'x=w-text_w-30:y=30',
            'center-left': 'x=30:y=(h-text_h)/2',
            'center': 'x=(w-text_w)/2:y=(h-text_h)/2',
            'center-right': 'x=w-text_w-30:y=(h-text_h)/2',
            'bottom-left': 'x=30:y=h-text_h-30',
            'bottom-center': 'x=(w-text_w)/2:y=h-text_h-30',
            'bottom-right': 'x=w-text_w-30:y=h-text_h-30',
        }
        
        if position in position_map:
            position_coords = position_map[position]
        else:
            position_coords = 'x=(w-text_w)/2:y=50'
        
        # Adjust y_offset based on position
        if 'top' in position and y_offset != 30:
            position_coords = position_coords.replace('y=30', f'y={y_offset}')
        elif 'bottom' in position and y_offset != 30:
            position_coords = position_coords.replace('y=h-text_h-30', f'y=h-text_h-{y_offset}')
        elif 'center' in position and 'top' not in position and 'bottom' not in position and y_offset != 0:
            position_coords = position_coords.replace('y=(h-text_h)/2', f'y=(h-text_h)/2+{y_offset}')

        # Font selection - Use local fonts first, then fallback to system fonts
        local_font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fonts')
        
        # Check if text contains emojis
        has_emoji = bool(re.search(r'[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]|[\U00002600-\U000027BF]|[\U0001F900-\U0001F9FF]', text))
        
        # Font files with priority order - local fonts first
        if has_emoji:
            font_files = [
                os.path.join(local_font_dir, "OpenSansEmoji.ttf"),
                os.path.join(local_font_dir, "DejaVuSans.ttf"),
                os.path.join(local_font_dir, "Roboto-Regular.ttf"),
                os.path.join(local_font_dir, "Arial.ttf"),
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        else:
            font_files = [
                os.path.join(local_font_dir, "Roboto-Bold.ttf"),
                os.path.join(local_font_dir, "Arial.ttf"),
                os.path.join(local_font_dir, "DejaVuSans-Bold.ttf"),
                os.path.join(local_font_dir, "DejaVuSans.ttf"),
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        
        font_file = None
        for font in font_files:
            if os.path.exists(font):
                font_file = font
                break
        
        # Final fallback
        if not font_file:
            font_file = os.path.join(local_font_dir, "DejaVuSans.ttf")
            if not os.path.exists(font_file):
                font_file = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        
        # Create text file instead of passing text directly in command
        # This is more reliable for complex text with special characters
        text_file_path = os.path.join(LOCAL_STORAGE_PATH, f"{request_id}_text.txt")
        
        # Initialize variables that might be used in exception handling
        input_path = None
        output_filename = None
        ffmpeg_command = None
        env = None
        
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
                f"line_spacing={line_spacing}:"
                f"{position_coords}:"
                f"enable='between(t,0,{duration})'"
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
            
            # Try multiple fallback strategies
            fallback_attempted = False
            
            # Strategy 1: Try with text parameter instead of textfile
            if ffmpeg_command is not None and env is not None and ("textfile" in str(e.stderr) or "Could not set font size" in str(e.stderr)):
                try:
                    drawtext_filter = (
                        f"drawtext=fontfile={font_file}:"
                        f"text='{escaped_text}':"
                        f"fontcolor={font_color}:"
                        f"fontsize={font_size}:"
                        f"box=1:"
                        f"boxcolor={box_color}@{box_opacity}:"
                        f"boxborderw={boxborderw}:"
                        f"line_spacing={line_spacing}:"
                        f"{position_coords}:"
                        f"enable='between(t,0,{duration})'"
                    )
                    ffmpeg_command[ffmpeg_command.index("-vf") + 1] = drawtext_filter
                    result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True, encoding='utf-8', env=env)
                    fallback_attempted = True
                except subprocess.CalledProcessError:
                    pass
            
            # Strategy 2: Try with a different font if font-related error
            if ffmpeg_command is not None and env is not None and not fallback_attempted and ("invalid library handle" in str(e.stderr) or "Could not set font size" in str(e.stderr)):
                try:
                    # Use a simpler, more reliable font
                    local_font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fonts')
                    reliable_fonts = [
                        os.path.join(local_font_dir, "DejaVuSans.ttf"),
                        os.path.join(local_font_dir, "Arial.ttf"),
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                    ]
                    
                    for reliable_font in reliable_fonts:
                        if os.path.exists(reliable_font):
                            drawtext_filter = (
                                f"drawtext=fontfile={reliable_font}:"
                                f"text='{escaped_text}':"
                                f"fontcolor={font_color}:"
                                f"fontsize={font_size}:"
                                f"box=1:"
                                f"boxcolor={box_color}@{box_opacity}:"
                                f"boxborderw={boxborderw}:"
                                f"line_spacing={line_spacing}:"
                                f"{position_coords}:"
                                f"enable='between(t,0,{duration})'"
                            )
                            ffmpeg_command[ffmpeg_command.index("-vf") + 1] = drawtext_filter
                            try:
                                result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True, encoding='utf-8', env=env)
                                fallback_attempted = True
                                break
                            except subprocess.CalledProcessError:
                                continue
                except Exception:
                    pass
            
            # Strategy 3: Try without font specification (use FFmpeg default)
            if ffmpeg_command is not None and env is not None and not fallback_attempted:
                try:
                    drawtext_filter = (
                        f"drawtext=text='{escaped_text}':"
                        f"fontcolor={font_color}:"
                        f"fontsize={font_size}:"
                        f"box=1:"
                        f"boxcolor={box_color}@{box_opacity}:"
                        f"boxborderw={boxborderw}:"
                        f"line_spacing={line_spacing}:"
                        f"{position_coords}:"
                        f"enable='between(t,0,{duration})'"
                    )
                    ffmpeg_command[ffmpeg_command.index("-vf") + 1] = drawtext_filter
                    result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True, encoding='utf-8', env=env)
                    fallback_attempted = True
                except subprocess.CalledProcessError:
                    pass
            
            if not fallback_attempted:
                raise Exception(f"FFmpeg failed with all fallback strategies. Last error: {e.stderr}")
        finally:
            # Clean up temporary files
            if input_path is not None and os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(text_file_path):
                os.remove(text_file_path)
        
        # Upload the processed video to cloud storage (only if we have a valid output file)
        if output_filename is None:
            raise Exception("Video processing failed - no output file generated")
            
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
