from flask import Blueprint, jsonify
import os
import logging
import tempfile
import shutil
import uuid
import yt_dlp

from services.simone.utils.downloader import Downloader
from services.v1.ai.gemini_service import GeminiService
from services.v1.audio.speech import generate_tts
from services.v1.audio.intelligent_audio_mixer import IntelligentAudioMixer
from services.cloud_storage import upload_file
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate

viral_shorts_bp = Blueprint('viral_shorts_bp', __name__)
logger = logging.getLogger(__name__)

@viral_shorts_bp.route('/v1/video/viral-shorts', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "context": {"type": "string"},  # Optional context for AI script generation
        "tts_voice": {"type": "string"},  # Optional voice for TTS
        "cookies_content": {"type": "string"},  # Optional YouTube cookies
        "cookies_url": {"type": "string", "format": "uri"},  # Optional cookies URL
        "auth_method": {
            "type": "string",
            "enum": ["auto", "oauth2", "cookies_content", "cookies_url", "cookies_file"],
            "default": "auto"
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def create_viral_short(job_id, data):
    """
    Create a viral-style short using the viral-shorts-creator approach:
    1. Download video
    2. Upload to Gemini AI for visual analysis
    3. Generate viral script with hook + main content
    4. Generate TTS commentary
    5. Intelligently mix original audio with commentary
    6. Return final viral short
    """
    video_url = data.get('video_url')
    context = data.get('context', '')
    tts_voice = data.get('tts_voice', 'en-US-AvaNeural')
    cookies_content = data.get('cookies_content')
    cookies_url = data.get('cookies_url')
    auth_method = data.get('auth_method', 'auto')
    
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Creating viral short from {video_url}")
    
    temp_dir = None
    original_cwd = os.getcwd()
    
    try:
        # Setup temporary directory
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)
        
        # Step 1: Download video using Simone Downloader (same as viral-shorts-creator)
        logger.info(f"Job {job_id}: Downloading video...")
        try:
            downloader = Downloader(url=video_url, cookies_content=cookies_content, cookies_url=cookies_url)
            downloader.video()  # Downloads as 'video.mp4'
            downloaded_video_path = os.path.join(temp_dir, 'video.mp4')
            
            if not os.path.exists(downloaded_video_path):
                raise Exception("Video download failed - file not found")
            
            logger.info(f"Job {job_id}: Video downloaded successfully")
            
        except Exception as e:
            logger.error(f"Job {job_id}: Video download failed: {e}")
            raise Exception(f"Video download failed: {e}")
        
        # Step 2: Upload video to Gemini AI for visual analysis
        logger.info(f"Job {job_id}: Analyzing video with Gemini AI...")
        gemini_service = GeminiService()
        
        try:
            # Upload video for AI analysis
            uploaded_file = gemini_service.upload_video_for_analysis(downloaded_video_path)
            
            # Generate viral script using visual analysis
            script_data = gemini_service.generate_viral_script(uploaded_file, context)
            
        except Exception as e:
            logger.warning(f"Job {job_id}: Video upload to Gemini failed: {e}")
            logger.info(f"Job {job_id}: Falling back to transcript-based analysis...")
            
            # Fallback: Extract audio and transcribe for script generation
            from services.ffmpeg_toolkit import extract_audio_from_video
            from services.v1.media.media_transcribe import process_transcribe_media
            
            # Extract audio
            audio_path = os.path.join(temp_dir, f"{job_id}_audio.mp3")
            extract_audio_from_video(downloaded_video_path, audio_path)
            
            # Transcribe audio
            transcription_result = process_transcribe_media(
                media_source=audio_path,
                task='transcribe',
                include_text=True,
                include_srt=False,
                include_segments=False,
                word_timestamps=False,
                response_type='direct',
                language=None,
                job_id=job_id,
                words_per_line=None
            )
            
            transcript_text = transcription_result[0]
            
            # Generate script from transcript
            script_data = gemini_service.generate_script_from_transcript(transcript_text, context)
            
            # Clean up audio file
            os.remove(audio_path)
        
        # Combine hook and script for TTS
        full_script = f"{script_data['hook']} {script_data['script']}"
        
        logger.info(f"Job {job_id}: Generated viral script - Hook: {script_data['hook'][:50]}...")
        logger.info(f"Job {job_id}: Script: {script_data['script'][:100]}...")
        
        # Step 3: Generate TTS commentary
        logger.info(f"Job {job_id}: Generating TTS commentary...")
        commentary_audio_path, _ = generate_tts(
            tts="edge-tts",
            text=full_script,
            voice=tts_voice,
            job_id=job_id,
            output_format="mp3",
            subtitle_format="srt"
        )
        
        logger.info(f"Job {job_id}: TTS commentary generated: {commentary_audio_path}")
        
        # Step 4: Intelligent audio mixing (viral-shorts-creator style)
        logger.info(f"Job {job_id}: Mixing audio with viral-style intelligence...")
        audio_mixer = IntelligentAudioMixer()
        
        # Create output path for mixed video
        mixed_video_path = os.path.join(temp_dir, f"{job_id}_viral_short.mp4")
        
        # Create viral-style short with intelligent audio mixing
        final_video_path = audio_mixer.create_viral_style_short(
            video_path=downloaded_video_path,
            commentary_audio_path=commentary_audio_path,
            output_path=mixed_video_path
        )
        
        logger.info(f"Job {job_id}: Viral short created with intelligent audio mixing")
        
        # Step 5: Upload final video to cloud storage
        logger.info(f"Job {job_id}: Uploading viral short to cloud storage...")
        final_short_url = upload_file(final_video_path)
        
        logger.info(f"Job {job_id}: Viral short completed: {final_short_url}")
        
        return jsonify({
            "short_url": final_short_url,
            "job_id": job_id,
            "script_data": script_data,
            "message": "Viral short created successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error creating viral short: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Cleanup
        os.chdir(original_cwd)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Job {job_id}: Cleaned up temporary directory")