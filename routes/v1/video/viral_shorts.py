from flask import Blueprint, jsonify
import os
import logging
import tempfile
import shutil
import uuid
import yt_dlp

from services.video_source_handler import VideoSourceHandler
from services.v1.ai.gemini_service import GeminiService
from services.v1.audio.speech import generate_tts
from services.v1.audio.intelligent_audio_mixer import IntelligentAudioMixer
from services.v1.ffmpeg.ffmpeg_compose import process_ffmpeg_compose
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
        "video_input": {"type": "string", "description": "YouTube URL or direct video file path/URL"},
        "context": {"type": "string"},  # Optional context for AI script generation
        "tts_voice": {"type": "string"},  # Optional voice for TTS
        "short_duration": {"type": "integer", "minimum": 15, "maximum": 180, "default": 60},  # Duration of the short
        "video_format": {
            "type": "string",
            "enum": ["portrait", "landscape", "square"],
            "default": "portrait"
        },
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
    "required": ["video_input"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def create_viral_short(job_id, data):
    """
    Create a viral-style short using the viral-shorts-creator approach:
    1. Download video
    2. Find best segment for short duration
    3. Upload to Gemini AI for visual analysis
    4. Generate viral script with hook + main content (in correct language)
    5. Generate TTS commentary
    6. Intelligently mix original audio with commentary
    7. Convert to portrait format
    8. Return final viral short (without captions)
    """
    video_input = data.get('video_input')
    context = data.get('context', '')
    tts_voice = data.get('tts_voice', 'en-US-AvaNeural')
    short_duration = data.get('short_duration', 60)
    video_format = data.get('video_format', 'portrait')
    cookies_content = data.get('cookies_content')
    cookies_url = data.get('cookies_url')
    auth_method = data.get('auth_method', 'auto')
    
    # Extract language from TTS voice for script generation
    def extract_language_from_voice(voice_name):
        if '-' in voice_name:
            return voice_name.split('-')[0]
        return 'en'
    
    voice_language = extract_language_from_voice(tts_voice)
    
    if not job_id:
        job_id = str(uuid.uuid4())
    
    # Set video dimensions based on format
    format_dimensions = {
        'portrait': (1080, 1920),   # 9:16
        'landscape': (1920, 1080),  # 16:9
        'square': (1080, 1080)      # 1:1
    }
    target_width, target_height = format_dimensions.get(video_format, (1080, 1920))
    
    logger.info(f"Job {job_id}: Creating viral short from {video_input}")
    logger.info(f"Job {job_id}: Duration: {short_duration}s, Format: {video_format} ({target_width}x{target_height}), Language: {voice_language}")
    
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
        
        # Step 2: Find best segment for viral short + Cache transcription
        logger.info(f"Job {job_id}: Finding best segment for {short_duration}s viral short...")
        
        # Initialize cached transcription for reuse
        cached_transcription_text = None
        
        try:
            from services.v1.video.video_analysis import analyze_video_segments
            
            # Get video transcript for intelligent segmentation (and cache for later use)
            try:
                from services.ffmpeg_toolkit import extract_audio_from_video
                from services.v1.media.media_transcribe import process_transcribe_media
                
                # Extract audio for transcription (single time)
                temp_audio_path = os.path.join(temp_dir, f"{job_id}_temp_audio.mp3")
                extract_audio_from_video(downloaded_video_path, temp_audio_path)
                
                # Transcribe audio once and cache result
                transcription_result = process_transcribe_media(
                    media_source=temp_audio_path,
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
                
                cached_transcription_text = transcription_result[0]
                logger.info(f"Job {job_id}: ✅ Transcription completed ONCE and cached ({len(cached_transcription_text)} chars)")
                
                # Clean up temp audio
                os.remove(temp_audio_path)
                
            except Exception as e:
                logger.warning(f"Job {job_id}: Transcription for segmentation failed: {e}")
            
            # Find best segment using highlights method with cached transcription
            video_segments = analyze_video_segments(
                video_path=downloaded_video_path,
                transcription_text=cached_transcription_text,  # Use cached transcription
                segment_method="highlights",  # Use highlights for viral content
                num_segments=1,  # Just one segment for viral short
                segment_duration=short_duration,
                job_id=job_id
            )
            
            if video_segments:
                best_segment = video_segments[0]
                logger.info(f"Job {job_id}: Best segment found: {best_segment['start_time']:.1f}s-{best_segment['end_time']:.1f}s, Score: {best_segment['score']:.2f}")
            else:
                # Fallback: use first segment of video
                best_segment = {
                    "start_time": 0,
                    "end_time": short_duration,
                    "score": 0.5,
                    "reason": "Fallback: first segment"
                }
                logger.warning(f"Job {job_id}: No segments found, using first {short_duration}s")
                
        except Exception as e:
            logger.warning(f"Job {job_id}: Video segmentation failed: {e}")
            # Ultimate fallback
            best_segment = {
                "start_time": 0,
                "end_time": short_duration,
                "score": 0.5,
                "reason": "Fallback: segmentation failed"
            }
        
        # Step 3: Segment extraction will be done in the ultra-optimized FFmpeg operation
        logger.info(f"Job {job_id}: Preparing to extract viral segment from {best_segment['start_time']:.1f}s to {best_segment['end_time']:.1f}s")
        
        # Step 4: Generate viral script with optimized AI analysis
        logger.info(f"Job {job_id}: Analyzing video with optimized Gemini AI...")
        gemini_service = GeminiService()
        
        # Add language context for script generation
        language_names = {'en': 'English', 'fr': 'French', 'es': 'Spanish', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese'}
        language_name = language_names.get(voice_language, 'English')
        language_context = f"{context}\n\nIMPORTANT: Generate the script in {language_name} language only. Create engaging viral content suitable for short-form platforms."
        
        # Check if input is YouTube URL for direct analysis
        is_youtube = ('youtube.com' in video_input.lower() or 'youtu.be' in video_input.lower())
        
        if is_youtube:
            try:
                logger.info(f"Job {job_id}: Using YouTube URL direct analysis (no upload needed)")
                script_data = gemini_service.generate_viral_script_from_youtube(video_input, language_context)
            except Exception as e:
                logger.warning(f"Job {job_id}: YouTube URL analysis failed: {e}")
                logger.info(f"Job {job_id}: Falling back to cached transcript-based analysis...")
                # Use cached transcription from segmentation (NO double transcription!)
                if cached_transcription_text:
                    logger.info(f"Job {job_id}: ♻️ Using cached transcription (avoiding redundant transcription)")
                    script_data = gemini_service.generate_script_from_transcript(cached_transcription_text, language_context)
                else:
                    logger.warning(f"Job {job_id}: No cached transcription available, performing emergency transcription...")
                    # Emergency fallback only if cached transcription failed
                    from services.ffmpeg_toolkit import extract_audio_from_video
                    from services.v1.media.media_transcribe import process_transcribe_media
                    
                    audio_path = os.path.join(temp_dir, f"{job_id}_emergency_audio.mp3")
                    extract_audio_from_video(downloaded_video_path, audio_path)
                    
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
                    
                    script_data = gemini_service.generate_script_from_transcript(transcription_result[0], language_context)
                    os.remove(audio_path)
        else:
            # For non-YouTube videos, use cached transcript-based analysis (faster)
            logger.info(f"Job {job_id}: Using cached transcript-based analysis for faster processing")
            # Use cached transcription from segmentation (NO double transcription!)
            if cached_transcription_text:
                logger.info(f"Job {job_id}: ♻️ Using cached transcription (avoiding redundant transcription)")
                script_data = gemini_service.generate_script_from_transcript(cached_transcription_text, language_context)
            else:
                logger.warning(f"Job {job_id}: No cached transcription available, performing emergency transcription...")
                # Emergency fallback only if cached transcription failed
                from services.ffmpeg_toolkit import extract_audio_from_video
                from services.v1.media.media_transcribe import process_transcribe_media
                
                audio_path = os.path.join(temp_dir, f"{job_id}_emergency_audio.mp3")
                extract_audio_from_video(downloaded_video_path, audio_path)
                
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
                
                script_data = gemini_service.generate_script_from_transcript(transcription_result[0], language_context)
                os.remove(audio_path)
        
        # Combine hook and script for TTS
        full_script = f"{script_data['hook']} {script_data['script']}"
        
        logger.info(f"Job {job_id}: Generated viral script - Hook: {script_data['hook'][:50]}...")
        logger.info(f"Job {job_id}: Script: {script_data['script'][:100]}...")
        
        # Step 5: Generate TTS commentary
        logger.info(f"Job {job_id}: Generating TTS commentary...")
        commentary_audio_path, _ = generate_tts(
            tts="edge-tts",
            text=full_script,
            voice=tts_voice,
            job_id=job_id,
            output_format="mp3"
        )
        logger.info(f"Job {job_id}: TTS commentary generated: {commentary_audio_path}")
        
        # Step 6: Ultra-optimized processing with ffmpeg-compose stream mappings
        logger.info(f"Job {job_id}: Performing ultra-optimized processing with stream mappings...")
        
        # Upload TTS audio to get URL for ffmpeg-compose
        from services.cloud_storage import upload_file
        commentary_audio_url = upload_file(commentary_audio_path)
        
        # Get original video URL for direct processing
        original_video_url = None
        if hasattr(source_metadata, 'original_url'):
            original_video_url = source_metadata['original_url']
        else:
            # Upload downloaded video to get URL
            original_video_url = upload_file(downloaded_video_path)
        
        # Use proven optimal audio mixing parameters from IntelligentAudioMixer
        mix_settings = {
            'original_volume': '0.3',      # 30% original audio volume
            'commentary_volume': '1.5',    # 150% commentary volume
            'original_weight': '0.3',      # Weight for original audio in mix
            'commentary_weight': '1.5'     # Weight for commentary audio in mix
        }
        
        # Design single FFmpeg command with stream mappings for:
        # 1. Extract segment from original video
        # 2. Mix original audio with commentary (intelligent levels)
        # 3. Scale and format to target dimensions
        # 4. All in ONE operation!
        
        ffmpeg_compose_data = {
            "inputs": [
                {
                    "file_url": original_video_url,
                    "options": [
                        {"option": "-ss", "argument": str(best_segment['start_time'])},
                        {"option": "-t", "argument": str(best_segment['end_time'] - best_segment['start_time'])}
                    ]
                },
                {
                    "file_url": commentary_audio_url
                }
            ],
            "filters": [
                {
                    "filter": f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black[scaled_video]",
                    "type": "video"
                },
                {
                    "filter": f"[0:a]volume={mix_settings['original_volume']}[original_audio];[1:a]volume={mix_settings['commentary_volume']}[commentary_audio];[original_audio][commentary_audio]amix=inputs=2:duration=shortest:weights={mix_settings['original_weight']} {mix_settings['commentary_weight']}[mixed_audio]",
                    "type": "audio"
                }
            ],
            "stream_mappings": ["[scaled_video]", "[mixed_audio]"],
            "outputs": [
                {
                    "options": [
                        {"option": "-c:v", "argument": "libx264"},
                        {"option": "-preset", "argument": "faster"},
                        {"option": "-crf", "argument": "25"},
                        {"option": "-c:a", "argument": "aac"},
                        {"option": "-b:a", "argument": "128k"},
                        {"option": "-f", "argument": "mp4"}
                    ]
                }
            ],
            "metadata": {
                "duration": True,
                "filesize": True
            }
        }
        
        # Execute ultra-optimized single FFmpeg operation
        logger.info(f"Job {job_id}: Executing single FFmpeg operation (segment + mix + scale + encode)")
        output_files, metadata = process_ffmpeg_compose(ffmpeg_compose_data, job_id)
        final_output_path = output_files[0]
        
        logger.info(f"Job {job_id}: Ultra-optimized processing completed in single operation!")
        logger.info(f"Job {job_id}: Final video: {final_output_path}, Duration: {metadata[0].get('duration', 'unknown')}s")
        
        # Step 8: Video ready for upload (no captions)
        logger.info(f"Job {job_id}: Final video ready (no captions added)")
        
        # Step 9: Upload final video to cloud storage
        logger.info(f"Job {job_id}: Uploading viral short to cloud storage...")
        final_short_url = upload_file(final_output_path)
        
        logger.info(f"Job {job_id}: Viral short completed: {final_short_url}")
        
        return {
            "short_url": final_short_url,
            "job_id": job_id,
            "script_data": script_data,
            "segment_info": best_segment,
            "source_metadata": source_metadata,
            "video_format": video_format,
            "duration": short_duration,
            "language": voice_language,
            "message": "Viral short created successfully"
        }, "/v1/video/viral-shorts", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error creating viral short: {str(e)}", exc_info=True)
        return {"error": str(e)}, "/v1/video/viral-shorts", 500
    
    finally:
        # Cleanup
        os.chdir(original_cwd)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Job {job_id}: Cleaned up temporary directory")