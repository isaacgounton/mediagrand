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

import os
import subprocess
import logging
import tempfile
import textwrap
from services.file_management import download_file
from services.v1.audio.speech import generate_tts
from services.transcription import process_transcription
from config.config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)

def get_font_path(font_name, font_bold=False, font_italic=False):
    """
    Get the full path to a font file based on font name and style.
    
    Args:
        font_name: Name of the font
        font_bold: Whether bold style is requested
        font_italic: Whether italic style is requested
    
    Returns:
        str: Path to the font file
    """
    font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'fonts')
    
    # Normalize font name (remove spaces, handle case variations)
    clean_name = font_name.replace(' ', '').replace('-', '').lower()
    
    # Build potential font file names based on style
    font_variations = []
    
    # For the new standardized naming scheme
    base_name = font_name.replace(' ', '-')  # Convert spaces to hyphens
    
    if font_bold and font_italic:
        font_variations.extend([
            f"{base_name}-BoldItalic.ttf",
            f"{base_name}-BoldItalic.otf"
        ])
    elif font_bold:
        font_variations.extend([
            f"{base_name}-Bold.ttf",
            f"{base_name}-Bold.otf"
        ])
    elif font_italic:
        font_variations.extend([
            f"{base_name}-Italic.ttf", 
            f"{base_name}-Italic.otf"
        ])
    else:
        font_variations.extend([
            f"{base_name}-Regular.ttf",
            f"{base_name}.ttf",
            f"{base_name}-Regular.otf",
            f"{base_name}.otf"
        ])
    
    # Also try with original name format
    original_name = font_name.replace('-', ' ')
    if font_bold and font_italic:
        font_variations.append(f"{original_name} BoldItalic.ttf")
    elif font_bold:
        font_variations.append(f"{original_name} Bold.ttf")
    elif font_italic:
        font_variations.append(f"{original_name} Italic.ttf")
    else:
        font_variations.extend([
            f"{original_name}.ttf",
            f"{original_name} Regular.ttf"
        ])
    
    # Check local fonts directory first
    for font_file in font_variations:
        font_path = os.path.join(font_dir, font_file)
        if os.path.exists(font_path):
            return font_path
    
    # Try to find any font that starts with the family name
    if os.path.exists(font_dir):
        for filename in os.listdir(font_dir):
            if filename.endswith(('.ttf', '.otf')):
                file_family = filename.split('-')[0].lower()
                if file_family == clean_name or file_family in clean_name or clean_name in file_family:
                    # Found a font in the same family
                    font_path = os.path.join(font_dir, filename)
                    return font_path
    
    # Fallback to system fonts
    system_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ]
    
    for font_path in system_fonts:
        if os.path.exists(font_path):
            return font_path
    
    # Final fallback - try Arial-Regular from our renamed fonts
    arial_fallback = os.path.join(font_dir, "Arial-Regular.ttf")
    if os.path.exists(arial_fallback):
        return arial_fallback
    
    # Ultimate fallback
    return os.path.join(font_dir, "DejaVuSans.ttf")

def wrap_text(text, max_length, max_lines):
    """
    Wrap text to specified length and number of lines.
    
    Args:
        text: Text to wrap
        max_length: Maximum characters per line
        max_lines: Maximum number of lines
    
    Returns:
        str: Wrapped text
    """
    if not text:
        return ""
    
    # Split into words
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        # Check if adding this word would exceed line length
        if len(current_line + " " + word) <= max_length:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            # Start new line if we haven't reached max lines
            if current_line:
                lines.append(current_line)
            if len(lines) < max_lines:
                current_line = word
            else:
                # Truncate if we've reached max lines
                break
    
    # Add the last line
    if current_line and len(lines) < max_lines:
        lines.append(current_line)
    
    return "\\n".join(lines)

def apply_image_effect(effect, width, height, duration):
    """
    Generate FFmpeg filter for image effects.
    
    Args:
        effect: Type of effect to apply
        width: Video width
        height: Video height
        duration: Duration of the video
    
    Returns:
        str: FFmpeg filter string
    """
    if effect == "none":
        return f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
    
    elif effect == "ken_burns":
        # Ken Burns effect - slow zoom and pan
        zoom_start = 1.0
        zoom_end = 1.1
        return f"scale={int(width*1.2)}:{int(height*1.2)}:force_original_aspect_ratio=decrease,pad={int(width*1.2)}:{int(height*1.2)}:(ow-iw)/2:(oh-ih)/2:black,zoompan=z='min(zoom+0.0015,{zoom_end})':d={int(duration*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}"
    
    elif effect == "zoom_in":
        return f"scale={int(width*1.2)}:{int(height*1.2)}:force_original_aspect_ratio=decrease,pad={int(width*1.2)}:{int(height*1.2)}:(ow-iw)/2:(oh-ih)/2:black,zoompan=z='min(zoom+0.002,1.2)':d={int(duration*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}"
    
    elif effect == "zoom_out":
        return f"scale={int(width*1.2)}:{int(height*1.2)}:force_original_aspect_ratio=decrease,pad={int(width*1.2)}:{int(height*1.2)}:(ow-iw)/2:(oh-ih)/2:black,zoompan=z='max(zoom-0.002,1.0)':d={int(duration*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}"
    
    elif effect == "pan_left":
        return f"scale={int(width*1.2)}:{int(height*1.2)}:force_original_aspect_ratio=decrease,pad={int(width*1.2)}:{int(height*1.2)}:(ow-iw)/2:(oh-ih)/2:black,crop={width}:{height}:'max(0,min(iw-{width},(iw-{width})*t/{duration}))':0"
    
    elif effect == "pan_right":
        return f"scale={int(width*1.2)}:{int(height*1.2)}:force_original_aspect_ratio=decrease,pad={int(width*1.2)}:{int(height*1.2)}:(ow-iw)/2:(oh-ih)/2:black,crop={width}:{height}:'max(0,min(iw-{width},(iw-{width})*(1-t/{duration})))':0"
    
    elif effect == "pan_up":
        return f"scale={width}:{int(height*1.2)}:force_original_aspect_ratio=decrease,pad={width}:{int(height*1.2)}:(ow-iw)/2:(oh-ih)/2:black,crop={width}:{height}:0:'max(0,min(ih-{height},(ih-{height})*t/{duration}))'"
    
    elif effect == "pan_down":
        return f"scale={width}:{int(height*1.2)}:force_original_aspect_ratio=decrease,pad={width}:{int(height*1.2)}:(ow-iw)/2:(oh-ih)/2:black,crop={width}:{height}:0:'max(0,min(ih-{height},(ih-{height})*(1-t/{duration})))'"
    
    else:
        # Default to basic scaling
        return f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"

def create_subtitle_file(captions, output_path, width=1080, height=1920, caption_config=None):
    """
    Creates an ASS subtitle file from captions with advanced styling.
    
    Args:
        captions: List of caption dictionaries with text, start_ts, end_ts
        output_path: Path to save the subtitle file
        width: Video width
        height: Video height
        caption_config: Dictionary with styling configuration
    """
    try:
        # Default configuration
        config = {
            'font_size': 120,
            'font_name': 'Arial',
            'font_bold': True,
            'font_italic': False,
            'font_color': '#fff',
            'position': 'top',
            'shadow_color': '#000',
            'shadow_transparency': 0.4,
            'shadow_blur': 10,
            'stroke_color': '#000',
            'stroke_size': 5,
            'line_count': 1,
            'line_max_length': 50
        }
        
        # Update with provided config
        if caption_config:
            config.update(caption_config)
        
        # Get font path
        font_path = get_font_path(config['font_name'], config['font_bold'], config['font_italic'])
        
        # Convert colors from hex to ASS format (BGR with alpha)
        def hex_to_ass_color(hex_color, alpha=1.0):
            """Convert hex color to ASS color format"""
            if hex_color.startswith('#'):
                hex_color = hex_color[1:]
            
            # Handle 3-digit hex
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            
            # Parse RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Convert to BGR and add alpha
            alpha_val = int((1.0 - alpha) * 255)
            return f"&H{alpha_val:02X}{b:02X}{g:02X}{r:02X}"
        
        primary_color = hex_to_ass_color(config['font_color'])
        outline_color = hex_to_ass_color(config['stroke_color'])
        shadow_color = hex_to_ass_color(config['shadow_color'], 1.0 - config['shadow_transparency'])
        
        # Determine alignment and positioning
        if config['position'] == 'top':
            alignment = 8  # Top center
            margin_v = 50
        elif config['position'] == 'center':
            alignment = 5  # Middle center
            margin_v = 0
        else:  # bottom
            alignment = 2  # Bottom center
            margin_v = 50
        
        # Create the .ass subtitle file with headers
        ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{os.path.basename(font_path).split('.')[0]},{config['font_size']},{primary_color},&H000000FF,{outline_color},{shadow_color},{-1 if config['font_bold'] else 0},{-1 if config['font_italic'] else 0},0,0,100,100,0,0,1,{config['stroke_size']},{config['shadow_blur']},{alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        # Process each caption and add to the subtitle file
        for caption in captions:
            start_time = format_time(caption["start_ts"])
            end_time = format_time(caption["end_ts"])
            text = caption["text"].strip()
            
            if text:  # Only add non-empty captions
                # Wrap text according to configuration
                wrapped_text = wrap_text(text, config['line_max_length'], config['line_count'])
                ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{wrapped_text}\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        logger.info(f"Subtitle file created: {output_path}")

    except Exception as e:
        logger.error(f"Failed to create subtitle file: {str(e)}")
        raise

def format_time(seconds):
    """
    Convert seconds to ASS time format (H:MM:SS.cc)
    """
    # Handle None or invalid values
    if seconds is None or not isinstance(seconds, (int, float)) or seconds < 0:
        seconds = 0.0
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

def process_tts_captioned_video(background_url, text=None, audio_url=None, width=1080, height=1920, 
                               provider="openai-edge-tts", voice="en-US-AriaNeural", speed=1.0, 
                               language=None, image_effect="ken_burns", caption_config=None, job_id=None):
    """
    Creates a captioned text-to-speech video with advanced styling and effects.
    
    Args:
        background_url: URL or path to background image
        text: Text to generate speech from (if audio_url not provided)
        audio_url: URL or path to existing audio file (if text not provided)
        width: Video width (default: 1080)
        height: Video height (default: 1920)
        provider: TTS provider (default: openai-edge-tts)
        voice: Voice for TTS (default: en-US-AriaNeural)
        speed: Speed of speech (default: 1.0)
        language: Language code for TTS (optional)
        image_effect: Effect to apply to background image (default: ken_burns)
        caption_config: Dictionary with caption styling configuration
        job_id: Job identifier for tracking
    
    Returns:
        str: Path to the generated captioned video
    """
    background_file = None
    audio_file = None
    cleanup_files = []
    
    try:
        logger.info(f"Job {job_id}: Starting TTS captioned video generation with effect: {image_effect}")

        # Download background image if it's a URL
        if os.path.isfile(background_url):
            background_file = background_url
        else:
            background_file = download_file(background_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_background"))
            cleanup_files.append(background_file)

        # Handle audio - either use provided audio or generate from text
        if audio_url:
            # Use provided audio
            if os.path.isfile(audio_url):
                audio_file = audio_url
            else:
                audio_file = download_file(audio_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_audio"))
                cleanup_files.append(audio_file)
        elif text:
            # Generate TTS audio from text
            logger.info(f"Job {job_id}: Generating TTS audio from text using {provider}")
            
            # Convert speed to rate string if needed
            rate = None
            if speed != 1.0:
                rate_percent = int((speed - 1.0) * 100)
                rate = f"{rate_percent:+d}%"
            
            # Use language-aware voice selection if language is provided
            if language and language != "en":
                # Try to find a voice for the specified language
                try:
                    from services.v1.audio.speech import list_voices_with_filter
                    available_voices = list_voices_with_filter(language)
                    if available_voices:
                        # Use the first available voice for the language
                        voice = available_voices[0].get('id', voice)
                        logger.info(f"Job {job_id}: Using language-specific voice: {voice}")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Could not get language-specific voice, using default: {str(e)}")
            
            audio_file, subtitle_file = generate_tts(
                tts=provider,
                text=text,
                voice=voice,
                job_id=job_id or "unknown",
                output_format="wav",
                rate=rate
            )
            cleanup_files.append(audio_file)
            if subtitle_file and os.path.exists(subtitle_file):
                cleanup_files.append(subtitle_file)
        else:
            raise ValueError("Either text or audio_url must be provided")

        # Get audio duration
        audio_duration = get_audio_duration(audio_file)
        
        # Create captions
        if text:
            # Use the original text for captions, split into segments if too long
            captions = create_text_segments(text, audio_duration, caption_config)
        else:
            # For uploaded audio, try to transcribe it or use a placeholder
            try:
                # Try to transcribe the audio
                logger.info(f"Job {job_id}: Transcribing uploaded audio for captions")
                transcription = process_transcription(audio_file, language=language)
                if transcription and 'captions' in transcription:
                    captions = transcription['captions']
                else:
                    # Fallback to placeholder
                    captions = [{
                        "text": "Audio content",
                        "start_ts": 0,
                        "end_ts": audio_duration
                    }]
            except Exception as e:
                logger.warning(f"Job {job_id}: Could not transcribe audio, using placeholder: {str(e)}")
                captions = [{
                    "text": "Audio content",
                    "start_ts": 0,
                    "end_ts": audio_duration
                }]

        # Create subtitle file with advanced styling
        subtitle_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_subtitles.ass")
        create_subtitle_file(captions, subtitle_path, width, height, caption_config)
        cleanup_files.append(subtitle_path)
        
        # Prepare output path
        output_filename = f"{job_id}_captioned_video.mp4"
        output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)

        # Generate image effect filter
        image_filter = apply_image_effect(image_effect, width, height, audio_duration)
        
        # Build FFmpeg command with advanced effects and subtitles
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-loop", "1",  # Loop the image
            "-i", background_file,  # Background image
            "-i", audio_file,  # Audio file
            "-vf", f"{image_filter},subtitles={subtitle_path}:force_style='FontName={caption_config.get('font_name', 'Arial') if caption_config else 'Arial'}'",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(audio_duration),  # Match video length to audio duration
            "-shortest",  # Stop when shortest input ends
            "-preset", "medium",  # Balance between speed and quality
            output_path
        ]

        logger.info(f"Job {job_id}: Executing video generation with effect '{image_effect}': {' '.join(cmd)}")

        # Execute the command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Clean up temporary files
        for file_path in cleanup_files:
            if os.path.exists(file_path):
                os.remove(file_path)

        logger.info(f"Job {job_id}: TTS captioned video generation completed successfully: {output_path}")

        # Check if the output file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output video {output_path} does not exist after generation.")

        return output_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Job {job_id}: FFmpeg failed: {e.stderr}")
        # Clean up on error
        for file_path in cleanup_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        raise Exception(f"Video generation failed: {e.stderr}")
    
    except Exception as e:
        logger.error(f"Job {job_id}: TTS captioned video generation failed: {str(e)}")
        # Clean up on error
        for file_path in cleanup_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        raise

def create_text_segments(text, duration, caption_config=None):
    """
    Split text into timed segments for captions.
    
    Args:
        text: Text to split
        duration: Total duration in seconds
        caption_config: Caption configuration
    
    Returns:
        List of caption dictionaries
    """
    if not text:
        return []
    
    # Default configuration
    config = caption_config or {}
    max_length = config.get('line_max_length', 50)
    max_lines = config.get('line_count', 1)
    
    # Estimate words per second (typical speech is 2-3 words per second)
    words_per_second = 2.5
    
    # Split text into words
    words = text.split()
    total_words = len(words)
    
    if total_words == 0:
        return [{
            "text": text,
            "start_ts": 0,
            "end_ts": duration
        }]
    
    # Calculate words per segment based on max characters and lines
    max_chars_per_segment = max_length * max_lines
    words_per_segment = max(1, int(max_chars_per_segment / 6))  # Estimate 6 chars per word
    
    captions = []
    current_word_index = 0
    
    while current_word_index < total_words:
        # Get words for this segment
        segment_words = words[current_word_index:current_word_index + words_per_segment]
        segment_text = " ".join(segment_words)
        
        # Calculate timing for this segment
        start_time = (current_word_index / total_words) * duration
        end_time = min(((current_word_index + len(segment_words)) / total_words) * duration, duration)
        
        captions.append({
            "text": segment_text,
            "start_ts": start_time,
            "end_ts": end_time
        })
        
        current_word_index += len(segment_words)
    
    return captions

def get_audio_duration(audio_file):
    """
    Get the duration of an audio file using ffprobe.
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            audio_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration_str = result.stdout.strip()
        
        # Check if we got a valid duration
        if not duration_str:
            logger.warning(f"Empty duration result for {audio_file}, using fallback")
            return 60.0
            
        duration = float(duration_str)
        
        # Ensure duration is positive and reasonable
        if duration <= 0 or duration > 86400:  # Max 24 hours
            logger.warning(f"Invalid duration {duration} for {audio_file}, using fallback")
            return 60.0
            
        return duration
        
    except (ValueError, subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"Failed to get audio duration for {audio_file}: {str(e)}")
        return 60.0  # Default fallback duration
    except Exception as e:
        logger.error(f"Unexpected error getting audio duration for {audio_file}: {str(e)}")
        return 60.0  # Default fallback duration