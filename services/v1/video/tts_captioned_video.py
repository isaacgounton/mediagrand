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
from services.file_management import download_file
from services.v1.audio.speech import generate_tts
from services.transcription import process_transcription
from config.config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)

def create_subtitle_file(captions, output_path, width=1080, height=1920, font_size=120):
    """
    Creates an ASS subtitle file from captions.
    
    Args:
        captions: List of caption dictionaries with text, start_ts, end_ts
        output_path: Path to save the subtitle file
        width: Video width
        height: Video height
        font_size: Font size for subtitles
    """
    try:
        # Create the .ass subtitle file with headers
        ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,0,8,20,20,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        pos_x = int(width / 2)
        pos_y = int(height * 0.8)  # Position at 80% down the screen

        # Process each caption and add to the subtitle file
        for caption in captions:
            start_time = format_time(caption["start_ts"])
            end_time = format_time(caption["end_ts"])
            text = caption["text"].strip()
            
            if text:  # Only add non-empty captions
                formatted_text = f"{{\\pos({pos_x},{pos_y})}}" + text
                ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{formatted_text}\n"

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
                               provider="openai-edge-tts", voice="en-US-AriaNeural", speed=1.0, job_id=None):
    """
    Creates a captioned text-to-speech video.
    
    Args:
        background_url: URL or path to background image
        text: Text to generate speech from (if audio_url not provided)
        audio_url: URL or path to existing audio file (if text not provided)
        width: Video width (default: 1080)
        height: Video height (default: 1920)
        provider: TTS provider (default: openai-edge-tts)
        voice: Voice for TTS (default: en-US-AriaNeural)
        speed: Speed of speech (default: 1.0)
        job_id: Job identifier for tracking
    
    Returns:
        str: Path to the generated captioned video
    """
    background_file = None
    audio_file = None
    cleanup_files = []
    
    try:
        logger.info(f"Job {job_id}: Starting TTS captioned video generation")

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
            
            audio_file, _ = generate_tts(
                tts=provider,
                text=text,
                voice=voice,
                job_id=job_id or "unknown",
                output_format="wav",
                rate=rate
            )
            cleanup_files.append(audio_file)
        else:
            raise ValueError("Either text or audio_url must be provided")

        # Create simple captions from the text or transcription
        audio_duration = get_audio_duration(audio_file)
        
        if text:
            # Use the original text for captions
            captions = [{
                "text": text,
                "start_ts": 0,
                "end_ts": audio_duration
            }]
        else:
            # For uploaded audio, we could transcribe it, but for now use a placeholder
            captions = [{
                "text": "Audio content",
                "start_ts": 0,
                "end_ts": audio_duration
            }]

        # Create subtitle file
        subtitle_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_subtitles.ass")
        create_subtitle_file(captions, subtitle_path, width, height)
        cleanup_files.append(subtitle_path)
        
        # Prepare output path
        output_filename = f"{job_id}_captioned_video.mp4"
        output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)

        # Build FFmpeg command to create video with background, audio, and subtitles
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-loop", "1",  # Loop the image
            "-i", background_file,  # Background image
            "-i", audio_file,  # Audio file
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,subtitles={subtitle_path}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(audio_duration),  # Match video length to audio duration
            "-shortest",  # Stop when shortest input ends
            output_path
        ]

        logger.info(f"Job {job_id}: Executing video generation: {' '.join(cmd)}")

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