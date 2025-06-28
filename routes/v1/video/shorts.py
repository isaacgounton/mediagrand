from flask import Blueprint, jsonify
import os
import logging
import tempfile
import shutil
import uuid

import yt_dlp
from services.simone.utils.downloader import Downloader
from services.simone.utils.summarizer import Summarizer # For script generation
from services.v1.audio.speech import generate_tts # For voiceover
from services.v1.video.merge_videos_with_audio import process_video_merge_with_audio # For merging video and audio
from services.v1.video.caption_video import process_captioning_v1 # For captioning
from services.cloud_storage import upload_file # For uploading final short
from app_utils import validate_payload, queue_task_wrapper # Correct import for validate_payload
from services.authentication import authenticate

shorts_bp = Blueprint('shorts_bp', __name__)
logger = logging.getLogger(__name__)

@shorts_bp.route('/v1/video/shorts', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "script_text": {"type": "string"}, # Optional: if not provided, AI will generate
        "context": {"type": "string"}, # Optional: additional context for AI script generation
        "tts_voice": {"type": "string"}, # Optional: voice for TTS
        "cookies_content": {"type": "string"}, # Optional: YouTube cookies for authentication
        "cookies_url": {"type": "string", "format": "uri"}, # Optional: URL to download cookies from
        "auth_method": {
            "type": "string",
            "enum": ["auto", "oauth2", "cookies_content", "cookies_url", "cookies_file"],
            "default": "auto"
        }, # Optional: YouTube authentication method
        "shorts_config": {
            "type": "object",
            "properties": {
                "num_shorts": {"type": "integer", "minimum": 1, "maximum": 10, "default": 1},
                "short_duration": {"type": "integer", "minimum": 15, "maximum": 180, "default": 60},
                "keep_original_voice": {"type": "boolean", "default": False},
                "add_captions": {"type": "boolean", "default": True},
                "segment_method": {
                    "type": "string",
                    "enum": ["auto", "equal_parts", "highlights", "chapters"],
                    "default": "auto"
                },
                "transition_effects": {"type": "boolean", "default": False},
                "background_music": {"type": "boolean", "default": False},
                "video_format": {
                    "type": "string",
                    "enum": ["portrait", "landscape", "square"],
                    "default": "portrait"
                },
                "resolution": {
                    "type": "object",
                    "properties": {
                        "width": {"type": "integer", "minimum": 480, "maximum": 4096},
                        "height": {"type": "integer", "minimum": 480, "maximum": 4096}
                    }
                }
            }
        }, # Optional: advanced shorts configuration
        "caption_settings": { # Optional: settings for video captioning
            "type": "object",
            "properties": {
                "line_color": {"type": "string"},
                "word_color": {"type": "string"},
                "outline_color": {"type": "string"},
                "all_caps": {"type": "boolean"},
                "max_words_per_line": {"type": "integer"},
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "position": {
                    "type": "string",
                    "enum": [
                        "bottom_left", "bottom_center", "bottom_right",
                        "middle_left", "middle_center", "middle_right",
                        "top_left", "top_center", "top_right"
                    ]
                },
                "alignment": {
                    "type": "string",
                    "enum": ["left", "center", "right"]
                },
                "font_family": {"type": "string"},
                "font_size": {"type": "integer"},
                "bold": {"type": "boolean"},
                "italic": {"type": "boolean"},
                "underline": {"type": "boolean"},
                "strikeout": {"type": "boolean"},
                "style": {
                    "type": "string",
                    "enum": ["classic", "karaoke", "highlight", "underline", "word_by_word"]
                },
                "outline_width": {"type": "integer"},
                "spacing": {"type": "integer"},
                "angle": {"type": "integer"},
                "shadow_offset": {"type": "integer"}
            },
            "additionalProperties": False
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def create_shorts(job_id, data):
    video_url = data.get('video_url')
    script_text = data.get('script_text')
    tts_voice = data.get('tts_voice', 'en-US-AvaNeural') # Default voice
    caption_settings = data.get('caption_settings', {})
    
    # Extract language from TTS voice (e.g., 'fr-CA-ThierryNeural' -> 'fr')
    def extract_language_from_voice(voice_name):
        if '-' in voice_name:
            return voice_name.split('-')[0]
        return 'en'
    
    voice_language = extract_language_from_voice(tts_voice)
    cookies_content = data.get('cookies_content')
    cookies_url = data.get('cookies_url')
    auth_method = data.get('auth_method', 'auto')

    # Add diagnostic logging for authentication
    logger.info(f"Job {job_id}: Using cookies_url: {cookies_url} with auth_method: {auth_method}")

    # Advanced shorts configuration
    shorts_config = data.get('shorts_config', {})
    num_shorts = shorts_config.get('num_shorts', 1)
    short_duration = shorts_config.get('short_duration', 60)
    keep_original_voice = shorts_config.get('keep_original_voice', False)
    add_captions = shorts_config.get('add_captions', True)
    segment_method = shorts_config.get('segment_method', 'auto')
    transition_effects = shorts_config.get('transition_effects', False)
    background_music = shorts_config.get('background_music', False)
    video_format = shorts_config.get('video_format', 'portrait')
    custom_resolution = shorts_config.get('resolution', {})
    
    # Set video dimensions based on format
    if custom_resolution:
        video_width = custom_resolution.get('width', 1080)
        video_height = custom_resolution.get('height', 1920)
    else:
        format_dimensions = {
            'portrait': (1080, 1920),   # 9:16
            'landscape': (1920, 1080),  # 16:9
            'square': (1080, 1080)      # 1:1
        }
        video_width, video_height = format_dimensions.get(video_format, (1080, 1920))

    # Generate a job_id if not provided by queue_task_wrapper
    if not job_id:
        job_id = str(uuid.uuid4())

    logger.info(f"Job {job_id}: Received request to create {num_shorts} short(s) from video: {video_url}")
    logger.info(f"Job {job_id}: Configuration - Duration: {short_duration}s, Keep original voice: {keep_original_voice}, Add captions: {add_captions}")

    # Import video analysis service for intelligent segmentation
    from services.v1.video.video_analysis import analyze_video_segments

    temp_dir = None
    original_cwd = os.getcwd() # Initialize original_cwd here
    try:
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir) # Change to temporary directory for processing

        downloaded_video_path = None
        transcription_text = None  # Initialize transcription_text

        # Step 1: Download video using Simone Downloader
        logger.info(f"Job {job_id}: Downloading video from {video_url} using Simone Downloader...")

        # Step 1a: Fetch metadata first without downloading
        logger.info(f"Job {job_id}: Fetching video metadata...")
        from services.youtube_auth import YouTubeAuthenticator
        auth = YouTubeAuthenticator()
        ydl_opts = auth.get_enhanced_ydl_opts(temp_dir, auth_method, cookies_content, cookies_url)
        ydl_opts['quiet'] = True
        ydl_opts['no_warnings'] = True
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(video_url, download=False)
                # Wrap it to resemble the old response structure for compatibility
                actual_response = {"media": info_dict}
                logger.info(f"Job {job_id}: Successfully fetched metadata for '{info_dict.get('title')}'")
            except Exception as e:
                logger.error(f"Job {job_id}: Failed to extract video metadata: {e}")
                raise Exception(f"Failed to extract video metadata: {e}")

        # Step 1b: Download the actual video file
        logger.info(f"Job {job_id}: Downloading video file...")
        try:
            downloader = Downloader(url=video_url, cookies_content=cookies_content, cookies_url=cookies_url)
            downloader.video() # This downloads the file as 'video.mp4' in the current dir
            downloaded_video_path = os.path.join(temp_dir, 'video.mp4')
            if not os.path.exists(downloaded_video_path):
                raise Exception("Simone Downloader finished but 'video.mp4' not found.")
            logger.info(f"Job {job_id}: Video downloaded locally to {downloaded_video_path}")
        except Exception as e:
            logger.error(f"Job {job_id}: Simone Downloader failed: {e}")
            raise Exception(f"Video download failed: {e}")

        # Step 2: Generate script if not provided
        if not script_text:
            logger.info(f"Job {job_id}: No script_text provided. Generating script using Simone AI...")

            # Import necessary services for transcription
            from services.ffmpeg_toolkit import extract_audio_from_video
            from services.v1.media.media_transcribe import process_transcribe_media

            # Extract audio from the downloaded video
            extracted_audio_path = os.path.join(temp_dir, f"{job_id}_extracted_audio.mp3")
            logger.info(f"Job {job_id}: Extracting audio from video to {extracted_audio_path}...")
            extract_audio_from_video(downloaded_video_path, extracted_audio_path)

            # Transcribe the extracted audio
            logger.info(f"Job {job_id}: Transcribing audio from {extracted_audio_path}...")
            # process_transcribe_media returns (text, srt, segments)
            transcription_result = process_transcribe_media(
                media_source=extracted_audio_path,
                task='transcribe',
                include_text=True,
                include_srt=False,
                include_segments=False,
                word_timestamps=False,
                response_type='direct',
                language=None,  # Auto-detect language
                job_id=job_id,
                words_per_line=None
            )
            transcription_text = transcription_result[0]
            logger.info(f"Job {job_id}: Audio transcribed. Length: {len(transcription_text)} chars.")

            # Create a transcription file for the summarizer
            transcription_file_for_summarizer = os.path.join(temp_dir, f"{job_id}_transcription_for_summarizer.txt")
            with open(transcription_file_for_summarizer, "w", encoding="utf-8") as f:
                f.write(transcription_text)

            # Generate structured script with hook and main content
            # The Summarizer will use OPENAI_API_KEY from config automatically
            summarizer = Summarizer(transcription_filename=transcription_file_for_summarizer)

            # Use video metadata as context if no context is provided
            user_context = data.get('context', '')
            if not user_context and actual_response.get("media"):
                video_metadata = actual_response["media"]
                metadata_context = f"""Video Information:
Title: {video_metadata.get('title', 'Unknown')}
Uploader: {video_metadata.get('uploader', 'Unknown')}
Duration: {video_metadata.get('duration', 'Unknown')} seconds
Description: {video_metadata.get('description', '')[:200]}...
View Count: {video_metadata.get('view_count', 'Unknown')}
Upload Date: {video_metadata.get('upload_date', 'Unknown')}"""
                logger.info(f"Job {job_id}: Using video metadata as context for script generation")
            else:
                metadata_context = user_context

            # Add language instruction to context
            language_names = {'en': 'English', 'fr': 'French', 'es': 'Spanish', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese'}
            language_name = language_names.get(voice_language, 'English')
            language_context = f"{metadata_context}\n\nIMPORTANT: Generate the script in {language_name} language only. Do not include any JSON formatting text or explanations."
            
            script_data = summarizer.generate_structured_script(context=language_context)

            # Combine hook and script for TTS
            script_text = f"{script_data['hook']} {script_data['script']}"
            
            # Clean script text for TTS - remove any unwanted formatting or explanatory text
            import re
            # Remove JSON formatting artifacts
            script_text = re.sub(r'[Hh]ere is.*?[Jj][Ss][Oo][Nn].*?:', '', script_text)
            script_text = re.sub(r'[Cc]ode snippet\s*:', '', script_text)
            script_text = re.sub(r'Title\s*[—-]\s*', '', script_text)
            # Remove any remaining curly braces or JSON-like formatting
            script_text = re.sub(r'[{}"]', '', script_text)
            # Clean up extra whitespace
            script_text = re.sub(r'\s+', ' ', script_text).strip()
            logger.info(f"Job {job_id}: Structured script generated - Hook: {script_data['hook'][:50]}...")
            logger.info(f"Job {job_id}: Script: {script_data['script'][:100]}...")

            # Clean up temporary audio and transcription file
            os.remove(extracted_audio_path)
            os.remove(transcription_file_for_summarizer)

        # Step 2.5: Analyze video segments for intelligent clipping
        logger.info(f"Job {job_id}: Analyzing video segments using method '{segment_method}'...")
        try:
            video_segments = analyze_video_segments(
                video_path=downloaded_video_path,
                transcription_text=transcription_text,
                segment_method=segment_method,
                num_segments=num_shorts,
                segment_duration=short_duration,
                job_id=job_id
            )
        except ImportError as e:
            logger.warning(f"Job {job_id}: Video analysis dependencies missing: {str(e)}")
            logger.info(f"Job {job_id}: Falling back to equal parts segmentation")
            # Fallback to simple equal parts segmentation
            try:
                from moviepy.editor import VideoFileClip
                with VideoFileClip(downloaded_video_path) as video_clip:
                    video_duration = video_clip.duration
                    if num_shorts == 1:
                        start_time = max(0, (video_duration - short_duration) / 2)
                        end_time = min(video_duration, start_time + short_duration)
                        video_segments = [{
                            "start_time": start_time,
                            "end_time": end_time,
                            "score": 1.0,
                            "reason": "Fallback: middle segment"
                        }]
                    else:
                        segment_size = video_duration / num_shorts
                        video_segments = []
                        for i in range(num_shorts):
                            start_time = i * segment_size
                            end_time = min(video_duration, start_time + short_duration)
                            if end_time - start_time < short_duration * 0.5:
                                start_time = max(0, end_time - short_duration)
                            video_segments.append({
                                "start_time": start_time,
                                "end_time": end_time,
                                "score": 1.0,
                                "reason": f"Fallback: equal part {i+1}/{num_shorts}"
                            })
            except ImportError:
                # Ultimate fallback if even MoviePy is not available
                logger.warning(f"Job {job_id}: MoviePy not available, using basic segmentation")
                video_segments = [{
                    "start_time": 0,
                    "end_time": short_duration,
                    "score": 1.0,
                    "reason": "Basic fallback: first segment"
                }]
        except Exception as e:
            logger.error(f"Job {job_id}: Video analysis failed: {str(e)}")
            raise Exception(f"Video analysis failed: {str(e)}")

        logger.info(f"Job {job_id}: Found {len(video_segments)} segments for processing")
        for i, segment in enumerate(video_segments):
            logger.info(f"Job {job_id}: Segment {i+1}: {segment['start_time']:.1f}s-{segment['end_time']:.1f}s, Score: {segment['score']:.2f}, Reason: {segment['reason']}")

        # Step 3: Process each video segment to create shorts
        generated_shorts = []

        for segment_idx, segment in enumerate(video_segments):
            logger.info(f"Job {job_id}: Processing segment {segment_idx + 1}/{len(video_segments)}")
            segment_job_id = f"{job_id}_segment_{segment_idx + 1}"

            # Create segment-specific video clip
            segment_video_path = os.path.join(temp_dir, f"{segment_job_id}_clipped.mp4")
            logger.info(f"Job {job_id}: Clipping segment from {segment['start_time']:.1f}s to {segment['end_time']:.1f}s")

            # Use ffmpeg to extract the segment
            from services.ffmpeg_toolkit import clip_video
            clip_video(
                input_path=downloaded_video_path,
                output_path=segment_video_path,
                start_time=segment['start_time'],
                end_time=segment['end_time']
            )

            # Generate voiceover and subtitles for this segment (or keep original voice)
            if keep_original_voice:
                logger.info(f"Job {job_id}: Keeping original voice, extracting audio from segment...")
                from services.ffmpeg_toolkit import extract_audio_from_video
                segment_audio_path = os.path.join(temp_dir, f"{segment_job_id}_original_audio.mp3")
                extract_audio_from_video(segment_video_path, segment_audio_path)

                # Create basic subtitles for the segment if captions are enabled
                if add_captions:
                    segment_subtitle_path = os.path.join(temp_dir, f"{segment_job_id}_subtitles.srt")
                    with open(segment_subtitle_path, "w", encoding="utf-8") as f:
                        f.write("1\n00:00:00,000 --> 00:01:00,000\n")
                        subtitle_text = "Original audio content..."
                        f.write(subtitle_text + "\n\n")
                    logger.info(f"Job {job_id}: Basic subtitles created for segment")
                else:
                    segment_subtitle_path = None
                    logger.info(f"Job {job_id}: No subtitles requested for segment")
            else:
                # Generate TTS for this segment
                logger.info(f"Job {job_id}: Generating voiceover and subtitles for segment...")
                segment_audio_path, segment_subtitle_path = generate_tts(
                    tts="edge-tts", # Always use edge-tts
                    text=script_text,
                    voice=tts_voice,
                job_id=segment_job_id,
                    output_format="mp3",
                    subtitle_format="srt" if add_captions else "srt"
                )
                logger.info(f"Job {job_id}: Voiceover audio at {segment_audio_path}, subtitles at {segment_subtitle_path}")

            # Step 4: Merge segment video with audio
            logger.info(f"Job {job_id}: Merging segment video with audio...")

            # Upload segment video and audio for merging service
            temp_segment_video_url = upload_file(segment_video_path)
            temp_segment_audio_url = upload_file(segment_audio_path)

            merged_segment_path_from_service = process_video_merge_with_audio(
                video_urls=[temp_segment_video_url],
                audio_url=temp_segment_audio_url,
                job_id=segment_job_id,
                target_width=video_width,
                target_height=video_height
            )

            # Copy merged video locally for captioning
            merged_segment_local_path = os.path.join(temp_dir, f"{segment_job_id}_merged.mp4")
            import shutil
            shutil.copy2(merged_segment_path_from_service, merged_segment_local_path)

            # Step 5: Add captions to segment (if enabled)
            if add_captions and segment_subtitle_path:
                logger.info(f"Job {job_id}: Adding captions to segment...")
                with open(segment_subtitle_path, 'r', encoding="utf-8") as f:
                    srt_content = f.read()

                temp_merged_segment_url = upload_file(merged_segment_local_path)
                captioned_local_path = process_captioning_v1(
                    video_url=temp_merged_segment_url,
                    captions=srt_content,
                    settings=caption_settings,
                    replace=[],
                    job_id=segment_job_id,
                    language=voice_language
                )
                
                # Upload the captioned video to cloud storage
                if isinstance(captioned_local_path, dict) and 'error' in captioned_local_path:
                    raise Exception(f"Captioning failed: {captioned_local_path['error']}")
                
                final_segment_url = upload_file(captioned_local_path)
                
                # Clean up local captioned file
                try:
                    os.remove(captioned_local_path)
                    logger.info(f"Job {job_id}: Cleaned up captioned file: {captioned_local_path}")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Failed to clean up captioned file {captioned_local_path}: {e}")
            else:
                # No captions, just upload the merged video
                final_segment_url = upload_file(merged_segment_local_path)

            # Add to generated shorts list
            generated_shorts.append({
                "short_url": final_segment_url,
                "segment_info": segment,
                "segment_index": segment_idx + 1
            })

            logger.info(f"Job {job_id}: Segment {segment_idx + 1} completed: {final_segment_url}")

        # Return results based on number of shorts generated
        if len(generated_shorts) == 1:
            # Single short - return the original format for backward compatibility
            return jsonify({
                "short_url": generated_shorts[0]["short_url"],
                "job_id": job_id
            }), 200
        else:
            # Multiple shorts - return array with segment information
            return jsonify({
                "shorts": generated_shorts,
                "job_id": job_id,
                "total_shorts": len(generated_shorts)
            }), 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error creating shorts: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        os.chdir(original_cwd) # Change back to original working directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir) # Clean up temporary directory
            logger.info(f"Job {job_id}: Cleaned up temporary directory {temp_dir}")
