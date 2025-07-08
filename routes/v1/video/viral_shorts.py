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
        
        # Step 2: Enhanced viral compilation analysis with multiple segments
        logger.info(f"Job {job_id}: Finding viral compilation segments for {short_duration}s viral short...")
        
        # Initialize cached transcription for reuse
        cached_transcription_text = None
        cached_transcription_srt = None
        
        try:
            from services.v1.video.video_analysis import analyze_viral_compilation_segments
            
            # Get video transcript for intelligent segmentation (and cache for later use)
            try:
                from services.ffmpeg_toolkit import extract_audio_from_video
                from services.v1.media.media_transcribe import process_transcribe_media
                
                # Extract audio for transcription (single time)
                temp_audio_path = os.path.join(temp_dir, f"{job_id}_temp_audio.mp3")
                extract_audio_from_video(downloaded_video_path, temp_audio_path)
                
                # Transcribe audio once and cache both text and SRT
                transcription_result = process_transcribe_media(
                    media_source=temp_audio_path,
                    task='transcribe',
                    include_text=True,
                    include_srt=True,  # Get SRT for precision timing
                    include_segments=False,
                    word_timestamps=False,
                    response_type='direct',
                    language=None,
                    job_id=job_id,
                    words_per_line=None
                )
                
                cached_transcription_text = transcription_result[0]
                cached_transcription_srt = transcription_result[1] if len(transcription_result) > 1 else None
                logger.info(f"Job {job_id}: ✅ Transcription completed ONCE and cached ({len(cached_transcription_text)} chars)")
                if cached_transcription_srt:
                    logger.info(f"Job {job_id}: ✅ SRT transcription cached for precision timing")
                
                # Clean up temp audio
                os.remove(temp_audio_path)
                
            except Exception as e:
                logger.warning(f"Job {job_id}: Transcription for segmentation failed: {e}")
            
            # Use enhanced viral compilation analysis
            compilation_result = analyze_viral_compilation_segments(
                video_path=downloaded_video_path,
                transcription_text=cached_transcription_text,
                transcription_srt=cached_transcription_srt,
                target_duration=short_duration,
                min_segment_duration=5,  # Minimum 5s segments
                max_segment_duration=15,  # Maximum 15s segments  
                job_id=job_id
            )
            
            if compilation_result and compilation_result.get('segments'):
                logger.info(f"Job {job_id}: ✅ Viral compilation analysis complete:")
                logger.info(f"Job {job_id}: - {compilation_result['segment_count']} viral segments found")
                logger.info(f"Job {job_id}: - Total duration: {compilation_result['total_duration']:.1f}s")
                logger.info(f"Job {job_id}: - Viral score: {compilation_result['viral_score']:.2f}")
                logger.info(f"Job {job_id}: - Diversity score: {compilation_result['diversity_score']:.2f}")
                logger.info(f"Job {job_id}: - Strategy: {compilation_result['compilation_strategy']}")
                
                # Use compilation result
                compilation_segments = compilation_result['segments']
                viral_compilation_metadata = {
                    'viral_score': compilation_result['viral_score'],
                    'diversity_score': compilation_result['diversity_score'],
                    'engagement_score': compilation_result['engagement_score'],
                    'segment_count': compilation_result['segment_count'],
                    'compilation_strategy': compilation_result['compilation_strategy'],
                    'precision_timing_applied': compilation_result.get('precision_timing_applied', False)
                }
            else:
                # Fallback to single segment
                from services.v1.video.video_analysis import analyze_video_segments
                logger.warning(f"Job {job_id}: Viral compilation failed, falling back to single segment")
                
                video_segments = analyze_video_segments(
                    video_path=downloaded_video_path,
                    transcription_text=cached_transcription_text,
                    segment_method="highlights",
                    num_segments=1,
                    segment_duration=short_duration,
                    job_id=job_id
                )
                
                if video_segments:
                    compilation_segments = video_segments
                    viral_compilation_metadata = {
                        'viral_score': video_segments[0].get('score', 0.5),
                        'diversity_score': 0.5,
                        'engagement_score': video_segments[0].get('score', 0.5),
                        'segment_count': 1,
                        'compilation_strategy': 'single_segment_fallback',
                        'precision_timing_applied': False
                    }
                    logger.info(f"Job {job_id}: Fallback segment: {video_segments[0]['start_time']:.1f}s-{video_segments[0]['end_time']:.1f}s")
                else:
                    # Ultimate fallback
                    compilation_segments = [{
                        "start_time": 0,
                        "end_time": short_duration,
                        "score": 0.5,
                        "reason": "Ultimate fallback: first segment"
                    }]
                    viral_compilation_metadata = {
                        'viral_score': 0.5,
                        'diversity_score': 0.5,
                        'engagement_score': 0.5,
                        'segment_count': 1,
                        'compilation_strategy': 'ultimate_fallback',
                        'precision_timing_applied': False
                    }
                    logger.warning(f"Job {job_id}: No segments found, using first {short_duration}s")
                
        except Exception as e:
            logger.warning(f"Job {job_id}: Enhanced viral segmentation failed: {e}")
            # Ultimate fallback
            compilation_segments = [{
                "start_time": 0,
                "end_time": short_duration,
                "score": 0.5,
                "reason": "Fallback: segmentation failed"
            }]
            viral_compilation_metadata = {
                'viral_score': 0.5,
                'diversity_score': 0.5,
                'engagement_score': 0.5,
                'segment_count': 1,
                'compilation_strategy': 'error_fallback',
                'precision_timing_applied': False
            }
        
        # Step 3: Multi-segment extraction with smart transitions
        if len(compilation_segments) > 1:
            segment_info_str = ", ".join([f"{seg['start_time']:.1f}-{seg['end_time']:.1f}s" for seg in compilation_segments])
            logger.info(f"Job {job_id}: Preparing to extract and combine {len(compilation_segments)} viral segments: {segment_info_str}")
        else:
            logger.info(f"Job {job_id}: Preparing to extract single segment from {compilation_segments[0]['start_time']:.1f}s to {compilation_segments[0]['end_time']:.1f}s")
        
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
        
        # Step 6: Enhanced multi-segment processing with smart transitions
        logger.info(f"Job {job_id}: Performing enhanced multi-segment processing...")
        
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
        
        # Use proven optimal audio mixing parameters
        mix_settings = {
            'original_volume': '0.3',      # 30% original audio volume
            'commentary_volume': '1.5',    # 150% commentary volume
            'original_weight': '0.3',      # Weight for original audio in mix
            'commentary_weight': '1.5'     # Weight for commentary audio in mix
        }
        
        if len(compilation_segments) > 1:
            # Multi-segment viral compilation with transitions
            logger.info(f"Job {job_id}: Creating multi-segment compilation with {len(compilation_segments)} segments")
            ffmpeg_compose_data = _create_multi_segment_ffmpeg_config(
                segments=compilation_segments,
                original_video_url=original_video_url,
                commentary_audio_url=commentary_audio_url,
                target_width=target_width,
                target_height=target_height,
                mix_settings=mix_settings,
                job_id=job_id
            )
        else:
            # Single segment processing (existing logic)
            logger.info(f"Job {job_id}: Creating single-segment viral short")
            segment = compilation_segments[0]
            ffmpeg_compose_data = {
                "inputs": [
                    {
                        "file_url": original_video_url,
                        "options": [
                            {"option": "-ss", "argument": str(segment['start_time'])},
                            {"option": "-t", "argument": str(segment['end_time'] - segment['start_time'])}
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
        
        # Execute optimized FFmpeg operation
        logger.info(f"Job {job_id}: Executing FFmpeg operation ({len(compilation_segments)} segments)")
        output_files, metadata = process_ffmpeg_compose(ffmpeg_compose_data, job_id)
        final_output_path = output_files[0]
        
        logger.info(f"Job {job_id}: Enhanced processing completed!")
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
            "segment_info": compilation_segments[0] if len(compilation_segments) == 1 else None,  # Legacy compatibility
            "compilation_info": {
                "segments": compilation_segments,
                "metadata": viral_compilation_metadata
            },
            "source_metadata": source_metadata,
            "video_format": video_format,
            "duration": short_duration,
            "language": voice_language,
            "enhanced_features": {
                "multi_segment_compilation": len(compilation_segments) > 1,
                "viral_score": viral_compilation_metadata['viral_score'],
                "diversity_score": viral_compilation_metadata['diversity_score'],
                "engagement_score": viral_compilation_metadata['engagement_score'],
                "compilation_strategy": viral_compilation_metadata['compilation_strategy'],
                "precision_timing_applied": viral_compilation_metadata['precision_timing_applied']
            },
            "message": f"Enhanced viral short created successfully with {len(compilation_segments)} segment(s)"
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


def _create_multi_segment_ffmpeg_config(segments, original_video_url, commentary_audio_url, 
                                       target_width, target_height, mix_settings, job_id):
    """
    Create FFmpeg configuration for multi-segment viral compilation with smart transitions.
    
    This function creates a complex FFmpeg filter graph that:
    1. Extracts multiple segments from the original video
    2. Applies cross-fade transitions between segments  
    3. Scales and formats to target dimensions
    4. Mixes original audio with commentary
    """
    logger.info(f"Job {job_id}: Creating multi-segment FFmpeg config for {len(segments)} segments")
    
    # Build inputs - original video and commentary audio
    inputs = [
        {
            "file_url": original_video_url
        },
        {
            "file_url": commentary_audio_url  
        }
    ]
    
    # Build complex filter graph for multi-segment compilation
    filters = []
    video_segments = []
    audio_segments = []
    
    # Extract each segment and scale it
    for i, segment in enumerate(segments):
        duration = segment['end_time'] - segment['start_time']
        
        # Extract and scale video segment
        video_filter = f"[0:v]trim=start={segment['start_time']}:duration={duration},setpts=PTS-STARTPTS,scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black[v{i}]"
        filters.append({
            "filter": video_filter,
            "type": "video"
        })
        video_segments.append(f"[v{i}]")
        
        # Extract audio segment
        audio_filter = f"[0:a]atrim=start={segment['start_time']}:duration={duration},asetpts=PTS-STARTPTS,volume={mix_settings['original_volume']}[a{i}]"
        filters.append({
            "filter": audio_filter,
            "type": "audio"
        })
        audio_segments.append(f"[a{i}]")
    
    # Create transitions between video segments
    if len(segments) > 1:
        # Concatenate video segments with crossfade transitions
        transition_duration = 0.5  # 0.5 second crossfade
        
        # Build xfade chain for video
        video_concat_filter = video_segments[0]
        for i in range(1, len(video_segments)):
            if i == 1:
                video_concat_filter = f"{video_concat_filter}{video_segments[i]}xfade=transition=fade:duration={transition_duration}:offset={sum(seg['end_time'] - seg['start_time'] for seg in segments[:i]) + (i-1)*transition_duration - transition_duration}[vx{i}]"
            else:
                video_concat_filter = f"[vx{i-1}]{video_segments[i]}xfade=transition=fade:duration={transition_duration}:offset={sum(seg['end_time'] - seg['start_time'] for seg in segments[:i]) + (i-1)*transition_duration - transition_duration}[vx{i}]"
        
        final_video_label = f"[vx{len(video_segments)-1}]" if len(video_segments) > 1 else video_segments[0]
        
        filters.append({
            "filter": video_concat_filter,
            "type": "video"
        })
        
        # Concatenate audio segments
        audio_concat_input = "".join(audio_segments)
        audio_concat_filter = f"{audio_concat_input}concat=n={len(audio_segments)}:v=0:a=1[original_audio_concat]"
        filters.append({
            "filter": audio_concat_filter,
            "type": "audio"
        })
        
        audio_input_label = "[original_audio_concat]"
    else:
        # Single segment - no transitions needed
        final_video_label = video_segments[0]
        audio_input_label = audio_segments[0]
    
    # Mix concatenated original audio with commentary
    commentary_filter = f"[1:a]volume={mix_settings['commentary_volume']}[commentary_audio]"
    filters.append({
        "filter": commentary_filter,
        "type": "audio"
    })
    
    mix_filter = f"{audio_input_label}[commentary_audio]amix=inputs=2:duration=shortest:weights={mix_settings['original_weight']} {mix_settings['commentary_weight']}[mixed_audio]"
    filters.append({
        "filter": mix_filter,
        "type": "audio"
    })
    
    # Return complete FFmpeg configuration
    return {
        "inputs": inputs,
        "filters": filters,
        "stream_mappings": [final_video_label, "[mixed_audio]"],
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