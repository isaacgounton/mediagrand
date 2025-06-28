from flask import Blueprint, jsonify
import os
import logging
import tempfile
import shutil
import uuid

from routes.v1.media.download import download_media
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
                "background_music": {"type": "boolean", "default": False}
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
    cookies_content = data.get('cookies_content')
    cookies_url = data.get('cookies_url')
    auth_method = data.get('auth_method', 'auto')

    # Advanced shorts configuration
    shorts_config = data.get('shorts_config', {})
    num_shorts = shorts_config.get('num_shorts', 1)
    short_duration = shorts_config.get('short_duration', 60)
    keep_original_voice = shorts_config.get('keep_original_voice', False)
    add_captions = shorts_config.get('add_captions', True)
    segment_method = shorts_config.get('segment_method', 'auto')
    transition_effects = shorts_config.get('transition_effects', False)
    background_music = shorts_config.get('background_music', False)

    # Generate a job_id if not provided by queue_task_wrapper
    if not job_id:
        job_id = str(uuid.uuid4())

    logger.info(f"Job {job_id}: Received request to create {num_shorts} short(s) from video: {video_url}")
    logger.info(f"Job {job_id}: Configuration - Duration: {short_duration}s, Keep original voice: {keep_original_voice}, Add captions: {add_captions}")

    # Note: Current implementation creates 1 short from the entire video
    # For multiple shorts or advanced segmentation, additional logic would be needed
    if num_shorts > 1:
        logger.warning(f"Job {job_id}: Multiple shorts requested ({num_shorts}), but current implementation creates 1 short. Feature enhancement needed.")

    temp_dir = None
    original_cwd = os.getcwd() # Initialize original_cwd here
    try:
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir) # Change to temporary directory for processing

        downloaded_video_path = None
        audio_file_path = None
        subtitle_file_path = None
        merged_video_path = None
        uploaded_short_url = None
        transcription_text = None  # Initialize transcription_text

        # Step 1: Download video using advanced media download service
        logger.info(f"Job {job_id}: Downloading video from {video_url}...")

        # Prepare download request data
        download_data = {
            "media_url": video_url,
            "cloud_upload": True,  # Upload to cloud storage
            "format": {"quality": "best"},  # Get best quality
            "audio": {"extract": False},  # We need video, not just audio
            "cookies_content": cookies_content,
            "cookies_url": cookies_url,
            "auth_method": auth_method
        }

        # Call the advanced download function
        download_result, _, status_code = download_media(f"{job_id}_download", download_data)

        if status_code != 200:
            raise Exception(f"Video download failed: {download_result.get('error', 'Unknown error')}")

        # Extract the downloaded video URL from cloud storage
        downloaded_video_url = download_result["media"]["media_url"]
        logger.info(f"Job {job_id}: Video downloaded and uploaded to cloud storage: {downloaded_video_url}")

        # Download the video locally for processing
        from services.file_management import download_file
        downloaded_video_path = download_file(downloaded_video_url, os.path.join(temp_dir, f"{job_id}_video.mp4"))
        logger.info(f"Job {job_id}: Video downloaded locally to {downloaded_video_path}")

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
            if not user_context and download_result.get("media"):
                video_metadata = download_result["media"]
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

            script_data = summarizer.generate_structured_script(context=metadata_context)

            # Combine hook and script for TTS
            script_text = f"{script_data['hook']} {script_data['script']}"
            logger.info(f"Job {job_id}: Structured script generated - Hook: {script_data['hook'][:50]}...")
            logger.info(f"Job {job_id}: Script: {script_data['script'][:100]}...")

            # Clean up temporary audio and transcription file
            os.remove(extracted_audio_path)
            os.remove(transcription_file_for_summarizer)

        # Step 3: Generate voiceover and subtitles (or keep original voice)
        if keep_original_voice:
            logger.info(f"Job {job_id}: Keeping original voice, extracting audio from video...")
            from services.ffmpeg_toolkit import extract_audio_from_video
            audio_file_path = os.path.join(temp_dir, f"{job_id}_original_audio.mp3")
            extract_audio_from_video(downloaded_video_path, audio_file_path)

            # For original voice, we still need subtitles if captions are enabled
            if add_captions:
                # We need transcription for subtitles, so extract and transcribe if we haven't already
                if 'transcription_text' not in locals():
                    logger.info(f"Job {job_id}: Need transcription for subtitles, extracting and transcribing audio...")
                    from services.ffmpeg_toolkit import extract_audio_from_video
                    from services.v1.media.media_transcribe import process_transcribe_media

                    extracted_audio_path = os.path.join(temp_dir, f"{job_id}_extracted_audio_for_subs.mp3")
                    extract_audio_from_video(downloaded_video_path, extracted_audio_path)

                    transcription_result = process_transcribe_media(
                        media_source=extracted_audio_path,
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
                    os.remove(extracted_audio_path)

                # Use the transcription to create subtitles
                subtitle_file_path = os.path.join(temp_dir, f"{job_id}_subtitles.srt")
                # Convert transcription to SRT format (simplified)
                with open(subtitle_file_path, "w", encoding="utf-8") as f:
                    f.write("1\n00:00:00,000 --> 00:01:00,000\n")
                    subtitle_text = transcription_text.replace('\n', ' ')[:100] + "..." if transcription_text else "Original audio content..."
                    f.write(subtitle_text + "\n\n")
                logger.info(f"Job {job_id}: Original audio extracted and basic subtitles created")
            else:
                subtitle_file_path = None
                logger.info(f"Job {job_id}: Original audio extracted, no subtitles requested")
        else:
            logger.info(f"Job {job_id}: Generating voiceover and subtitles...")
            audio_file_path, subtitle_file_path = generate_tts(
                tts="edge-tts", # Always use edge-tts
                text=script_text,
                voice=tts_voice,
                job_id=job_id,
                output_format="mp3",
                subtitle_format="srt" if add_captions else "srt"
            )
            logger.info(f"Job {job_id}: Voiceover audio at {audio_file_path}, subtitles at {subtitle_file_path}")

        # Step 4: Merge video with voiceover
        logger.info(f"Job {job_id}: Merging video with generated voiceover...")
        merged_video_path = os.path.join(temp_dir, f"{job_id}_merged_video.mp4")
        # process_video_merge_with_audio expects video_urls as a list and audio_url
        # Since it takes URL, we need to upload the downloaded video first or adapt the service
        # For now, let's assume process_video_merge_with_audio can take local paths.
        # If not, I'll need to upload downloaded_video_path and audio_file_path to cloud storage first.

        # Checking services/v1/video/merge_videos_with_audio.py: it expects URLs.
        # So, I need to upload downloaded_video_path and audio_file_path to cloud storage first.
        logger.info(f"Job {job_id}: Uploading downloaded video and audio for merging service...")
        temp_video_url = upload_file(downloaded_video_path)
        temp_audio_url = upload_file(audio_file_path)
        logger.info(f"Job {job_id}: Video temp URL: {temp_video_url}, Audio temp URL: {temp_audio_url}")

        merged_video_path_from_service = process_video_merge_with_audio(
            video_urls=[temp_video_url],
            audio_url=temp_audio_url,
            job_id=job_id
        )
        # The service returns a cloud URL. We need to download it to apply captions locally.
        merged_video_local_path = os.path.join(temp_dir, f"{job_id}_merged_video_local.mp4")
        # Assuming download_file from services.file_management can download from a URL.
        # Need to import services.file_management.
        from services.file_management import download_file
        download_file(merged_video_path_from_service, merged_video_local_path)
        merged_video_path = merged_video_local_path
        logger.info(f"Job {job_id}: Merged video downloaded locally to {merged_video_path}")


        # Step 5: Caption video (if captions are enabled)
        if add_captions and subtitle_file_path:
            logger.info(f"Job {job_id}: Applying captions to video...")
            # process_captioning_v1 expects video_url and captions as a string (SRT content)
            with open(subtitle_file_path, 'r', encoding="utf-8") as f:
                srt_content = f.read()
        else:
            logger.info(f"Job {job_id}: Skipping captions as requested...")
            srt_content = None

        if add_captions and srt_content:
            # process_captioning_v1 also expects a URL for video_url, so upload merged_video_path first.
            logger.info(f"Job {job_id}: Uploading merged video for captioning service...")
            temp_merged_video_url = upload_file(merged_video_path)
            logger.info(f"Job {job_id}: Merged video temp URL for captioning: {temp_merged_video_url}")

            final_captioned_video_path_from_service = process_captioning_v1(
                video_url=temp_merged_video_url,
                captions=srt_content,
                settings=caption_settings,
                replace=[], # No replace rules for now, can be added as optional parameter
                job_id=job_id,
                language="en" # Assuming English captions for now, can be optional parameter
            )
            # The captioning service also returns a cloud URL.
            uploaded_short_url = final_captioned_video_path_from_service
        else:
            # No captions requested, just upload the merged video
            logger.info(f"Job {job_id}: No captions requested, uploading final video...")
            uploaded_short_url = upload_file(merged_video_path)
        logger.info(f"Job {job_id}: Final captioned short uploaded to {uploaded_short_url}")

        return jsonify({"short_url": uploaded_short_url, "job_id": job_id}), 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error creating shorts: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        os.chdir(original_cwd) # Change back to original working directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir) # Clean up temporary directory
            logger.info(f"Job {job_id}: Cleaned up temporary directory {temp_dir}")
