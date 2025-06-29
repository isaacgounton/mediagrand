from flask import Blueprint, jsonify
import os
import logging
import tempfile
import shutil
import uuid

from services.simone.utils.downloader import Downloader
from services.v1.video.video_analysis import analyze_video_segments
from services.ffmpeg_toolkit import clip_video
from services.cloud_storage import upload_file
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate

clips_generator_bp = Blueprint('clips_generator_bp', __name__)
logger = logging.getLogger(__name__)

@clips_generator_bp.route('/v1/video/generate-clips', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "num_clips": {"type": "integer", "minimum": 1, "maximum": 20, "default": 3},
        "clip_duration": {"type": "integer", "minimum": 15, "maximum": 180, "default": 60},
        "segment_method": {
            "type": "string",
            "enum": ["auto", "equal_parts", "highlights", "chapters"],
            "default": "auto"
        },
        "video_format": {
            "type": "string", 
            "enum": ["portrait", "landscape", "square", "original"],
            "default": "portrait"
        },
        "resolution": {
            "type": "object",
            "properties": {
                "width": {"type": "integer", "minimum": 480, "maximum": 4096},
                "height": {"type": "integer", "minimum": 480, "maximum": 4096}
            }
        },
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
    "required": ["video_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def generate_clips(job_id, data):
    """
    Generate multiple clips from a single video using intelligent segmentation
    """
    video_url = data.get('video_url')
    num_clips = data.get('num_clips', 3)
    clip_duration = data.get('clip_duration', 60)
    segment_method = data.get('segment_method', 'auto')
    video_format = data.get('video_format', 'portrait')
    custom_resolution = data.get('resolution', {})
    cookies_content = data.get('cookies_content')
    cookies_url = data.get('cookies_url')
    auth_method = data.get('auth_method', 'auto')
    
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Generating {num_clips} clips from {video_url}")
    logger.info(f"Job {job_id}: Clip duration: {clip_duration}s, Method: {segment_method}")
    
    # Set video dimensions based on format
    if custom_resolution:
        target_width = custom_resolution.get('width')
        target_height = custom_resolution.get('height')
    elif video_format != 'original':
        format_dimensions = {
            'portrait': (1080, 1920),   # 9:16
            'landscape': (1920, 1080),  # 16:9
            'square': (1080, 1080)      # 1:1
        }
        target_width, target_height = format_dimensions.get(video_format, (1080, 1920))
    else:
        target_width = target_height = None  # Keep original dimensions
    
    temp_dir = None
    original_cwd = os.getcwd()
    
    try:
        # Setup temporary directory
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)
        
        # Step 1: Download video
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
        
        # Step 2: Get video transcript for intelligent segmentation
        transcription_text = None
        try:
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
            
            transcription_text = transcription_result[0]
            logger.info(f"Job {job_id}: Transcription completed ({len(transcription_text)} chars)")
            
            # Clean up audio file
            os.remove(audio_path)
            
        except Exception as e:
            logger.warning(f"Job {job_id}: Transcription failed: {e}")
            logger.info(f"Job {job_id}: Proceeding without transcript")
        
        # Step 3: Analyze video segments for intelligent clipping
        logger.info(f"Job {job_id}: Analyzing video segments...")
        try:
            video_segments = analyze_video_segments(
                video_path=downloaded_video_path,
                transcription_text=transcription_text,
                segment_method=segment_method,
                num_segments=num_clips,
                segment_duration=clip_duration,
                job_id=job_id
            )
        except Exception as e:
            logger.warning(f"Job {job_id}: Intelligent segmentation failed: {e}")
            logger.info(f"Job {job_id}: Falling back to equal parts segmentation")
            
            # Fallback to simple equal parts segmentation using FFmpeg
            try:
                # Get video duration using FFprobe
                import subprocess
                ffprobe_command = [
                    "ffprobe",
                    "-v", "quiet",
                    "-show_entries", "format=duration",
                    "-of", "csv=p=0",
                    downloaded_video_path
                ]
                
                result = subprocess.run(
                    ffprobe_command,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                video_duration = float(result.stdout.strip())
                logger.info(f"Job {job_id}: Video duration: {video_duration}s")
                
                if num_clips == 1:
                    # Single clip from middle of video
                    start_time = max(0, (video_duration - clip_duration) / 2)
                    end_time = min(video_duration, start_time + clip_duration)
                    video_segments = [{
                        "start_time": start_time,
                        "end_time": end_time,
                        "score": 1.0,
                        "reason": "Middle segment"
                    }]
                else:
                    # Multiple clips spread across video
                    segment_size = video_duration / num_clips
                    video_segments = []
                    for i in range(num_clips):
                        start_time = i * segment_size
                        end_time = min(video_duration, start_time + clip_duration)
                        
                        # Ensure minimum clip duration
                        if end_time - start_time < clip_duration * 0.5:
                            start_time = max(0, end_time - clip_duration)
                        
                        video_segments.append({
                            "start_time": start_time,
                            "end_time": end_time,
                            "score": 1.0,
                            "reason": f"Equal part {i+1}/{num_clips}"
                        })
            except Exception as fallback_error:
                logger.error(f"Job {job_id}: Even fallback segmentation failed: {fallback_error}")
                raise Exception(f"Video segmentation failed: {fallback_error}")
        
        logger.info(f"Job {job_id}: Found {len(video_segments)} segments for clipping")
        for i, segment in enumerate(video_segments):
            logger.info(f"Job {job_id}: Segment {i+1}: {segment['start_time']:.1f}s-{segment['end_time']:.1f}s, Score: {segment['score']:.2f}")
        
        # Step 4: Generate clips from segments
        generated_clips = []
        
        for segment_idx, segment in enumerate(video_segments):
            logger.info(f"Job {job_id}: Processing clip {segment_idx + 1}/{len(video_segments)}")
            clip_job_id = f"{job_id}_clip_{segment_idx + 1}"
            
            # Create clip from segment
            clip_video_path = os.path.join(temp_dir, f"{clip_job_id}.mp4")
            
            try:
                # Extract segment using ffmpeg
                clip_video(
                    input_path=downloaded_video_path,
                    output_path=clip_video_path,
                    start_time=segment['start_time'],
                    end_time=segment['end_time']
                )
                
                # Resize video if needed
                if target_width and target_height:
                    resized_clip_path = os.path.join(temp_dir, f"{clip_job_id}_resized.mp4")
                    
                    # Use ffmpeg to resize
                    import subprocess
                    resize_command = [
                        "ffmpeg",
                        "-i", clip_video_path,
                        "-vf", f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black",
                        "-c:a", "copy",
                        "-y",
                        resized_clip_path
                    ]
                    
                    subprocess.run(resize_command, check=True, capture_output=True)
                    
                    # Replace original clip with resized version
                    os.remove(clip_video_path)
                    os.rename(resized_clip_path, clip_video_path)
                    
                    logger.info(f"Job {job_id}: Clip {segment_idx + 1} resized to {target_width}x{target_height}")
                
                # Upload clip to cloud storage
                clip_url = upload_file(clip_video_path)
                
                # Add to generated clips list
                generated_clips.append({
                    "clip_url": clip_url,
                    "clip_index": segment_idx + 1,
                    "start_time": segment['start_time'],
                    "end_time": segment['end_time'],
                    "duration": segment['end_time'] - segment['start_time'],
                    "score": segment['score'],
                    "reason": segment['reason']
                })
                
                logger.info(f"Job {job_id}: Clip {segment_idx + 1} completed: {clip_url}")
                
            except Exception as e:
                logger.error(f"Job {job_id}: Failed to process clip {segment_idx + 1}: {e}")
                # Continue with other clips even if one fails
                continue
        
        if not generated_clips:
            raise Exception("No clips were successfully generated")
        
        logger.info(f"Job {job_id}: Successfully generated {len(generated_clips)}/{num_clips} clips")
        
        return {
            "clips": generated_clips,
            "job_id": job_id,
            "total_clips": len(generated_clips),
            "requested_clips": num_clips,
            "clip_duration": clip_duration,
            "segment_method": segment_method,
            "video_format": video_format,
            "message": f"Successfully generated {len(generated_clips)} clips"
        }, "/v1/video/generate-clips", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error generating clips: {str(e)}", exc_info=True)
        return {"error": str(e)}, "/v1/video/generate-clips", 500
    
    finally:
        # Cleanup
        os.chdir(original_cwd)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Job {job_id}: Cleaned up temporary directory")