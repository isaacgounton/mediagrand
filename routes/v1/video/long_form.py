from flask import Blueprint, jsonify
import os
import logging
import tempfile
import shutil
import uuid

from services.video_source_handler import VideoSourceHandler
from services.v1.ai.long_form_ai_service import LongFormAIService
from services.v1.audio.speech import generate_tts
from services.v1.audio.long_form_audio_mixer import LongFormAudioMixer
from services.cloud_storage import upload_file
from utils.app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate

long_form_bp = Blueprint('long_form_bp', __name__)
logger = logging.getLogger(__name__)

@long_form_bp.route('/v1/video/long-form', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_input": {"type": "string", "description": "YouTube URL or direct video file URL"},
        "target_duration": {"type": "integer", "minimum": 300, "maximum": 3600, "default": 600},  # 5-60 minutes
        "content_style": {
            "type": "string",
            "enum": ["educational", "commentary", "documentary", "analysis"],
            "default": "educational"
        },
        "script_tone": {
            "type": "string", 
            "enum": ["professional", "casual", "academic", "conversational"],
            "default": "professional"
        },
        "video_format": {
            "type": "string",
            "enum": ["landscape", "portrait", "square", "original"],
            "default": "landscape"
        },
        "resolution": {
            "type": "object",
            "properties": {
                "width": {"type": "integer", "minimum": 720, "maximum": 4096},
                "height": {"type": "integer", "minimum": 480, "maximum": 4096}
            }
        },
        "audio_strategy": {
            "type": "string",
            "enum": ["commentary_focused", "balanced", "original_focused", "background_only"],
            "default": "commentary_focused"
        },
        "add_background_music": {"type": "boolean", "default": False},
        "normalize_audio": {"type": "boolean", "default": True},
        "fade_transitions": {"type": "boolean", "default": True},
        "add_captions": {"type": "boolean", "default": True},
        "context": {"type": "string"},
        "tts_voice": {"type": "string"},
        "cookies_content": {"type": "string"},
        "cookies_url": {"type": "string", "format": "uri"},
        "auth_method": {
            "type": "string",
            "enum": ["auto", "oauth2", "cookies_content", "cookies_url", "cookies_file"],
            "default": "auto"
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_input"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def create_long_form_video(job_id, data):
    """
    Create a long-form educational/commentary video optimized for YouTube:
    1. Download source video
    2. Upload to Gemini AI for comprehensive analysis
    3. Generate structured long-form script (intro, sections, conclusion)
    4. Generate TTS commentary
    5. Apply long-form audio mixing strategies
    6. Optimize for target format and duration
    7. Return final long-form video
    """
    video_input = data.get('video_input')
    target_duration = data.get('target_duration', 600)  # 10 minutes default
    content_style = data.get('content_style', 'educational')
    script_tone = data.get('script_tone', 'professional')
    video_format = data.get('video_format', 'landscape')
    custom_resolution = data.get('resolution', {})
    audio_strategy = data.get('audio_strategy', 'commentary_focused')
    add_background_music = data.get('add_background_music', False)
    normalize_audio = data.get('normalize_audio', True)
    fade_transitions = data.get('fade_transitions', True)
    add_captions = data.get('add_captions', True)
    context = data.get('context', '')
    tts_voice = data.get('tts_voice', 'en-US-AvaNeural')
    
    # Extract language from TTS voice for script generation
    def extract_language_from_voice(voice_name):
        if '-' in voice_name:
            return voice_name.split('-')[0]
        return 'en'
    
    voice_language = extract_language_from_voice(tts_voice)
    cookies_content = data.get('cookies_content')
    cookies_url = data.get('cookies_url')
    auth_method = data.get('auth_method', 'auto')
    
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Creating long-form video from {video_input}")
    logger.info(f"Job {job_id}: Style: {content_style}, Duration: {target_duration}s, Format: {video_format}, Language: {voice_language}")
    
    # Set video dimensions based on format
    if custom_resolution:
        target_width = custom_resolution.get('width')
        target_height = custom_resolution.get('height')
    elif video_format != 'original':
        format_dimensions = {
            'landscape': (1920, 1080),  # 16:9 for YouTube
            'portrait': (1080, 1920),   # 9:16
            'square': (1080, 1080)      # 1:1
        }
        target_width, target_height = format_dimensions.get(video_format, (1920, 1080))
    else:
        target_width = target_height = None
    
    temp_dir = None
    original_cwd = os.getcwd()
    
    try:
        # Setup temporary directory
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)
        
        # Step 1: Process video source (YouTube or direct file)
        logger.info(f"Job {job_id}: Processing video source...")
        try:
            # Validate video input first
            validation_result = VideoSourceHandler.validate_video_input(video_input)
            if not validation_result['valid']:
                raise Exception(f"Invalid video input: {', '.join(validation_result['errors'])}")
            
            # Process the video source
            downloaded_video_path, source_metadata = VideoSourceHandler.process_video_source(
                video_input=video_input,
                job_id=job_id,
                temp_dir=temp_dir,
                cookies_content=cookies_content,
                cookies_url=cookies_url,
                auth_method=auth_method
            )
            
            logger.info(f"Job {job_id}: Video processed successfully - Source: {source_metadata['source_type']}")
            
        except Exception as e:
            logger.error(f"Job {job_id}: Video processing failed: {e}")
            raise Exception(f"Video processing failed: {e}")
        
        # Step 2: AI Analysis and Script Generation
        logger.info(f"Job {job_id}: Analyzing video with Long-Form AI...")
        long_form_ai = LongFormAIService()
        
        try:
            # Upload video for AI analysis
            uploaded_file = long_form_ai.upload_video_for_analysis(downloaded_video_path)
            
            # Add language context for script generation
            language_names = {'en': 'English', 'fr': 'French', 'es': 'Spanish', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese'}
            language_name = language_names.get(voice_language, 'English')
            language_context = f"{context}\n\nIMPORTANT: Generate the script in {language_name} language only. Create {content_style} content with {script_tone} tone."
            
            # Generate structured long-form script
            script_data = long_form_ai.generate_long_form_script(
                uploaded_file=uploaded_file,
                content_style=content_style,
                target_duration=target_duration,
                context=language_context,
                script_tone=script_tone
            )
            
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
            
            # Add language context for script generation
            language_names = {'en': 'English', 'fr': 'French', 'es': 'Spanish', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese'}
            language_name = language_names.get(voice_language, 'English')
            language_context = f"{context}\n\nIMPORTANT: Generate the script in {language_name} language only. Create {content_style} content with {script_tone} tone."
            
            # Generate script from transcript
            script_data = long_form_ai.generate_script_from_transcript(
                transcript=transcript_text,
                content_style=content_style,
                target_duration=target_duration,
                context=language_context,
                script_tone=script_tone
            )
            
            # Clean up audio file
            os.remove(audio_path)
        
        # Combine all script sections for TTS
        full_script = long_form_ai.combine_script_sections(script_data)
        
        logger.info(f"Job {job_id}: Generated long-form script - Title: {script_data['title']}")
        logger.info(f"Job {job_id}: Script sections: {len(script_data['main_sections'])}")
        logger.info(f"Job {job_id}: Estimated duration: {script_data['total_duration_estimate']}s")
        
        # Step 3: Generate TTS commentary
        logger.info(f"Job {job_id}: Generating TTS commentary for long-form content...")
        commentary_audio_path, _ = generate_tts(
            tts="edge-tts",
            text=full_script,
            voice=tts_voice,
            job_id=job_id,
            output_format="mp3",
            subtitle_format="srt"
        )
        
        logger.info(f"Job {job_id}: TTS commentary generated: {commentary_audio_path}")
        
        # Step 4: Resize video if needed
        processed_video_path = downloaded_video_path
        if target_width and target_height:
            logger.info(f"Job {job_id}: Resizing video to {target_width}x{target_height}")
            resized_video_path = os.path.join(temp_dir, f"{job_id}_resized.mp4")
            
            import subprocess
            resize_command = [
                "ffmpeg",
                "-i", downloaded_video_path,
                "-vf", f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black",
                "-c:a", "copy",
                "-y",
                resized_video_path
            ]
            
            subprocess.run(resize_command, check=True, capture_output=True)
            processed_video_path = resized_video_path
            logger.info(f"Job {job_id}: Video resized successfully")
        
        # Step 5: Long-form audio mixing
        logger.info(f"Job {job_id}: Applying long-form audio mixing strategy: {audio_strategy}")
        audio_mixer = LongFormAudioMixer()
        
        # Create output path for mixed video
        mixed_video_path = os.path.join(temp_dir, f"{job_id}_mixed.mp4")
        
        # Apply long-form audio mixing
        final_video_path = audio_mixer.mix_long_form_audio(
            video_path=processed_video_path,
            commentary_audio_path=commentary_audio_path,
            output_path=mixed_video_path,
            mixing_strategy=audio_strategy,
            fade_transitions=fade_transitions
        )
        
        logger.info(f"Job {job_id}: Long-form audio mixing completed")
        
        # Step 6: Optional audio enhancements
        if normalize_audio:
            logger.info(f"Job {job_id}: Normalizing audio levels...")
            normalized_path = os.path.join(temp_dir, f"{job_id}_normalized.mp4")
            final_video_path = audio_mixer.normalize_audio_levels(final_video_path, normalized_path)
            logger.info(f"Job {job_id}: Audio normalization completed")
        
        # TODO: Add background music if requested
        # if add_background_music:
        #     # This would require a background music file
        #     pass
        
        # Step 7: Add captions if requested
        if add_captions:
            logger.info(f"Job {job_id}: Adding captions to long-form video...")
            
            # Generate subtitle file for the full script
            _, subtitle_path = generate_tts(
                tts="edge-tts",
                text=full_script,
                voice=tts_voice,
                job_id=f"{job_id}_srt",
                output_format="mp3",
                subtitle_format="srt"
            )
            
            # Use caption service to add subtitles
            from services.v1.video.caption_video import process_captioning_v1
            
            # Upload current video for captioning
            temp_video_url = upload_file(final_video_path)
            
            # Read subtitle content
            with open(subtitle_path, 'r', encoding="utf-8") as f:
                srt_content = f.read()
            
            # Apply captions with long-form optimized settings
            caption_settings = {
                "font_size": 24,
                "line_color": "#FFFFFF",
                "outline_color": "#000000",
                "outline_width": 2,
                "position": "bottom_center",
                "bold": False,
                "all_caps": False,
                "style": "classic"  # Classic style for long-form content
            }
            
            captioned_local_path = process_captioning_v1(
                video_url=temp_video_url,
                captions=srt_content,
                settings=caption_settings,
                replace=[],
                job_id=job_id,
                language=voice_language
            )
            
            if isinstance(captioned_local_path, dict) and 'error' in captioned_local_path:
                logger.warning(f"Job {job_id}: Captioning failed, using video without captions")
                final_output_path = final_video_path
            else:
                final_output_path = captioned_local_path
                logger.info(f"Job {job_id}: Captions added successfully")
        else:
            final_output_path = final_video_path
        
        # Step 8: Upload final video to cloud storage
        logger.info(f"Job {job_id}: Uploading long-form video to cloud storage...")
        final_video_url = upload_file(final_output_path)
        
        logger.info(f"Job {job_id}: Long-form video completed: {final_video_url}")
        
        return {
            "video_url": final_video_url,
            "job_id": job_id,
            "script_data": script_data,
            "source_metadata": source_metadata,
            "content_style": content_style,
            "target_duration": target_duration,
            "actual_duration": script_data['total_duration_estimate'],
            "video_format": video_format,
            "audio_strategy": audio_strategy,
            "language": voice_language,
            "captions_added": add_captions,
            "message": "Long-form video created successfully"
        }, "/v1/video/long-form", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error creating long-form video: {str(e)}", exc_info=True)
        return {"error": str(e)}, "/v1/video/long-form", 500
    
    finally:
        # Cleanup
        os.chdir(original_cwd)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Job {job_id}: Cleaned up temporary directory")