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
        "short_duration": {"type": "integer", "minimum": 15, "maximum": 180, "default": 60},  # Duration of the short
        "video_format": {
            "type": "string",
            "enum": ["portrait", "landscape", "square"],
            "default": "portrait"
        },
        "add_captions": {"type": "boolean", "default": True},  # Add captions automatically
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
    2. Find best segment for short duration
    3. Upload to Gemini AI for visual analysis
    4. Generate viral script with hook + main content (in correct language)
    5. Generate TTS commentary
    6. Intelligently mix original audio with commentary
    7. Convert to portrait format and add captions
    8. Return final viral short
    """
    video_url = data.get('video_url')
    context = data.get('context', '')
    tts_voice = data.get('tts_voice', 'en-US-AvaNeural')
    short_duration = data.get('short_duration', 60)
    video_format = data.get('video_format', 'portrait')
    add_captions = data.get('add_captions', True)
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
    
    logger.info(f"Job {job_id}: Creating viral short from {video_url}")
    logger.info(f"Job {job_id}: Duration: {short_duration}s, Format: {video_format} ({target_width}x{target_height}), Language: {voice_language}")
    
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
        
        # Step 2: Find best segment for viral short
        logger.info(f"Job {job_id}: Finding best segment for {short_duration}s viral short...")
        try:
            from services.v1.video.video_analysis import analyze_video_segments
            
            # Get video transcript for intelligent segmentation
            transcription_text = None
            try:
                from services.ffmpeg_toolkit import extract_audio_from_video
                from services.v1.media.media_transcribe import process_transcribe_media
                
                # Extract audio for transcription
                temp_audio_path = os.path.join(temp_dir, f"{job_id}_temp_audio.mp3")
                extract_audio_from_video(downloaded_video_path, temp_audio_path)
                
                # Transcribe audio
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
                
                transcription_text = transcription_result[0]
                logger.info(f"Job {job_id}: Transcription completed for segmentation ({len(transcription_text)} chars)")
                
                # Clean up temp audio
                os.remove(temp_audio_path)
                
            except Exception as e:
                logger.warning(f"Job {job_id}: Transcription for segmentation failed: {e}")
            
            # Find best segment using highlights method
            video_segments = analyze_video_segments(
                video_path=downloaded_video_path,
                transcription_text=transcription_text,
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
        
        # Step 3: Extract the best segment
        logger.info(f"Job {job_id}: Extracting viral segment from {best_segment['start_time']:.1f}s to {best_segment['end_time']:.1f}s")
        
        segment_video_path = os.path.join(temp_dir, f"{job_id}_segment.mp4")
        from services.ffmpeg_toolkit import clip_video
        clip_video(
            input_path=downloaded_video_path,
            output_path=segment_video_path,
            start_time=best_segment['start_time'],
            end_time=best_segment['end_time']
        )
        
        # Step 4: Upload segment to Gemini AI for visual analysis
        logger.info(f"Job {job_id}: Analyzing video with Gemini AI...")
        gemini_service = GeminiService()
        
        try:
            # Upload video segment for AI analysis
            uploaded_file = gemini_service.upload_video_for_analysis(segment_video_path)
            
            # Add language context for script generation
            language_names = {'en': 'English', 'fr': 'French', 'es': 'Spanish', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese'}
            language_name = language_names.get(voice_language, 'English')
            language_context = f"{context}\n\nIMPORTANT: Generate the script in {language_name} language only. Create engaging viral content suitable for short-form platforms."
            
            # Generate viral script using visual analysis
            script_data = gemini_service.generate_viral_script(uploaded_file, language_context)
            
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
            
            # Generate script from transcript with language context
            language_names = {'en': 'English', 'fr': 'French', 'es': 'Spanish', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese'}
            language_name = language_names.get(voice_language, 'English')
            language_context = f"{context}\n\nIMPORTANT: Generate the script in {language_name} language only. Create engaging viral content suitable for short-form platforms."
            
            script_data = gemini_service.generate_script_from_transcript(transcript_text, language_context)
            
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
        
        # Step 6: Intelligent audio mixing (viral-shorts-creator style)
        logger.info(f"Job {job_id}: Mixing audio with viral-style intelligence...")
        audio_mixer = IntelligentAudioMixer()
        
        # Create output path for mixed video
        mixed_video_path = os.path.join(temp_dir, f"{job_id}_viral_short.mp4")
        
        # Create viral-style short with intelligent audio mixing
        final_video_path = audio_mixer.create_viral_style_short(
            video_path=segment_video_path,  # Use segment, not full video
            commentary_audio_path=commentary_audio_path,
            output_path=mixed_video_path
        )
        
        logger.info(f"Job {job_id}: Viral short created with intelligent audio mixing")
        
        # Step 7: Convert to target format
        logger.info(f"Job {job_id}: Converting to {video_format} format ({target_width}x{target_height})")
        formatted_video_path = os.path.join(temp_dir, f"{job_id}_formatted.mp4")
        
        import subprocess
        format_command = [
            "ffmpeg",
            "-i", final_video_path,
            "-vf", f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:a", "copy",
            "-y",
            formatted_video_path
        ]
        
        subprocess.run(format_command, check=True, capture_output=True)
        logger.info(f"Job {job_id}: Video converted to {video_format} format")
        
        # Step 8: Add captions if requested
        if add_captions:
            logger.info(f"Job {job_id}: Adding captions to viral short...")
            
            # Generate subtitle file for the segment
            segment_subtitle_path = os.path.join(temp_dir, f"{job_id}_subtitles.srt")
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
            
            # Upload formatted video for captioning
            temp_formatted_url = upload_file(formatted_video_path)
            
            # Read subtitle content
            with open(subtitle_path, 'r', encoding="utf-8") as f:
                srt_content = f.read()
            
            # Apply captions with viral-optimized settings
            caption_settings = {
                "font_size": 28,
                "line_color": "#FFFFFF",
                "outline_color": "#000000",
                "outline_width": 3,
                "position": "bottom_center",
                "bold": True,
                "all_caps": True,
                "style": "word_by_word"
            }
            
            captioned_local_path = process_captioning_v1(
                video_url=temp_formatted_url,
                captions=srt_content,
                settings=caption_settings,
                replace=[],
                job_id=job_id,
                language=voice_language
            )
            
            if isinstance(captioned_local_path, dict) and 'error' in captioned_local_path:
                logger.warning(f"Job {job_id}: Captioning failed, using video without captions")
                final_output_path = formatted_video_path
            else:
                final_output_path = captioned_local_path
                logger.info(f"Job {job_id}: Captions added successfully")
        else:
            final_output_path = formatted_video_path
        
        # Step 9: Upload final video to cloud storage
        logger.info(f"Job {job_id}: Uploading viral short to cloud storage...")
        final_short_url = upload_file(final_output_path)
        
        logger.info(f"Job {job_id}: Viral short completed: {final_short_url}")
        
        return jsonify({
            "short_url": final_short_url,
            "job_id": job_id,
            "script_data": script_data,
            "segment_info": best_segment,
            "video_format": video_format,
            "duration": short_duration,
            "language": voice_language,
            "captions_added": add_captions,
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