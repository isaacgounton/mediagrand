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
# NOTE: This uses the ffmpeg-python package, which exposes ffmpeg.input, ffmpeg.output, etc.
# Pylance may show errors, but these are valid for ffmpeg-python.
import ffmpeg
import logging
from services.file_management import download_file
from config.config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)

def process_video_merge(
    video_urls,
    background_music_url=None,
    background_music_volume=0.3,  # Reduced default volume
    crossfade_duration=0.5,  # Add crossfade parameter
    job_id=None
):
    """
    Merges multiple videos into one, optionally with background music.
    Preserves original video audio and adds smooth transitions.
    
    Args:
        video_urls: List of video URLs to merge
        background_music_url: Optional background music URL
        background_music_volume: Volume level for background music (0.0 to 1.0)
        crossfade_duration: Duration of audio crossfade between videos (seconds)
        job_id: Job identifier for tracking
    
    Returns:
        str: Path to the merged output video
    """
    if not video_urls:
        raise ValueError("No video URLs provided for merging")

    input_files = []
    downloaded_files = []
    output_filename = f"{job_id}_merged.mp4"
    output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)
    concat_file_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_concat_list.txt")

    try:
        logger.info(f"Job {job_id}: Starting video merge for {len(video_urls)} videos")

        # Download all video files
        for i, video_url in enumerate(video_urls):
            if os.path.isfile(video_url):
                input_files.append(video_url)
            else:
                input_filename = download_file(video_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_video_{i}"))
                input_files.append(input_filename)
                downloaded_files.append(input_filename)

        # Verify all video files exist and get their durations
        video_info = []
        total_video_duration = 0
        
        for i, input_file in enumerate(input_files):
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Input video file {i} does not exist: {input_file}")
            
            try:
                probe = ffmpeg.probe(input_file)
                duration = float(probe['format']['duration'])
                has_audio = any(stream['codec_type'] == 'audio' for stream in probe['streams'])
                
                video_info.append({
                    'file': input_file,
                    'duration': duration,
                    'has_audio': has_audio
                })
                total_video_duration += duration
                logger.info(f"Job {job_id}: Video {i} - Duration: {duration:.2f}s, Has audio: {has_audio}, File: {input_file}")
            except Exception as e:
                logger.warning(f"Job {job_id}: Could not get info for video {i}: {e}")
                video_info.append({
                    'file': input_file,
                    'duration': 0,
                    'has_audio': False
                })

        logger.info(f"Job {job_id}: Total expected video duration: {total_video_duration:.2f}s")


        # Download background music if provided
        music_file = None
        if background_music_url:
            if os.path.isfile(background_music_url):
                music_file = background_music_url
            else:
                music_file = download_file(background_music_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_music"))
                downloaded_files.append(music_file)
            
            if not os.path.exists(music_file):
                logger.error(f"Job {job_id}: Music file does not exist: {music_file}")
                music_file = None
            else:
                logger.info(f"Job {job_id}: Background music file: {music_file}")

        # Method 1: Create smooth concatenation with audio crossfades if multiple videos have audio
        videos_with_audio = [v for v in video_info if v['has_audio']]
        
        if len(videos_with_audio) > 1 and crossfade_duration > 0:
            logger.info(f"Job {job_id}: Creating smooth audio transitions with {crossfade_duration}s crossfade")
            temp_concat_path = create_smooth_concat(input_files, video_info, crossfade_duration, job_id)
        else:
            # Method 2: Standard concatenation
            logger.info(f"Job {job_id}: Using standard concatenation")
            temp_concat_path = create_standard_concat(input_files, concat_file_path, job_id)

        # Verify the concatenated video
        if not os.path.exists(temp_concat_path):
            raise FileNotFoundError(f"Concatenated video not created: {temp_concat_path}")

        # Get concatenated video info
        try:
            video_probe = ffmpeg.probe(temp_concat_path)
            video_duration = float(video_probe['format']['duration'])
            has_video_audio = any(stream['codec_type'] == 'audio' for stream in video_probe['streams'])
            logger.info(f"Job {job_id}: Concatenated video duration: {video_duration:.2f}s, has audio: {has_video_audio}")
        except Exception as e:
            logger.warning(f"Job {job_id}: Could not probe concatenated video: {e}")
            has_video_audio = False
            video_duration = total_video_duration if total_video_duration > 0 else 60

        # Now handle additional audio mixing (voice over and background music)
        video_input = ffmpeg.input(temp_concat_path)
        audio_inputs = []
        
        # IMPORTANT: Always preserve original video audio if it exists
        if has_video_audio:
            # Keep original video audio at full volume
            original_audio = video_input['a']
            audio_inputs.append(original_audio)
            logger.info(f"Job {job_id}: Preserved original video audio")


        # Add background music if provided
        if music_file:
            try:
                music_probe = ffmpeg.probe(music_file)
                music_duration = float(music_probe['format']['duration'])
                logger.info(f"Job {job_id}: Music duration: {music_duration:.2f}s")
                
                # Loop music to match video duration and apply volume
                music_input = ffmpeg.input(music_file, stream_loop=-1, t=video_duration)
                # Add fade in/out to background music for smoother experience
                # Use afade for fade in/out instead of complex volume eval
                music_audio = ffmpeg.filter(
                    music_input['a'],
                    'afade', t='in', ss=0, d=2
                )
                music_audio = ffmpeg.filter(
                    music_audio,
                    'afade', t='out', st=max(0, video_duration-2), d=2
                )
                music_audio = ffmpeg.filter(
                    music_audio,
                    'volume', background_music_volume
                )
                audio_inputs.append(music_audio)
                logger.info(f"Job {job_id}: Added background music with fade in/out (volume: {background_music_volume})")
            except Exception as e:
                logger.error(f"Job {job_id}: Error processing music file: {e}")

        # Create final output
        logger.info(f"Job {job_id}: Creating final output with {len(audio_inputs)} audio streams...")
        
        if len(audio_inputs) == 0:
            # No audio at all
            logger.info(f"Job {job_id}: No audio streams, copying video only")
            (
                ffmpeg.output(
                    video_input['v'],
                    output_path,
                    vcodec='copy',
                    an=None
                )
                .run(overwrite_output=True, quiet=False)
            )
        elif len(audio_inputs) == 1:
            # Single audio stream
            logger.info(f"Job {job_id}: Single audio stream")
            (
                ffmpeg.output(
                    video_input['v'],
                    audio_inputs[0],
                    output_path,
                    vcodec='copy',
                    acodec='aac',
                    **{'b:a': '192k'}
                )
                .run(overwrite_output=True, quiet=False)
            )
        else:
            # Multiple audio streams - mix them with proper weighting
            logger.info(f"Job {job_id}: Mixing {len(audio_inputs)} audio streams")
            
            # Use amix with custom weights to ensure original audio isn't drowned out
            mixed_audio = ffmpeg.filter(
                audio_inputs, 
                'amix', 
                inputs=len(audio_inputs), 
                duration='longest',
                weights='1.0 0.7 0.3'[:len(audio_inputs)*4-1],  # Give more weight to original audio
                normalize=0
            )
            
            (
                ffmpeg.output(
                    video_input['v'],
                    mixed_audio,
                    output_path,
                    vcodec='copy',
                    acodec='aac',
                    **{'b:a': '256k'}  # Higher bitrate for better quality
                )
                .run(overwrite_output=True, quiet=False)
            )

        # Clean up temp file
        if os.path.exists(temp_concat_path):
            os.remove(temp_concat_path)

        # Verify final output
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} does not exist after merge.")
            
        # Log final video info
        try:
            final_probe = ffmpeg.probe(output_path)
            final_duration = float(final_probe['format']['duration'])
            final_has_audio = any(stream['codec_type'] == 'audio' for stream in final_probe['streams'])
            final_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            logger.info(f"Job {job_id}: Final video - Duration: {final_duration:.2f}s, Has audio: {final_has_audio}, Size: {final_size:.1f}MB")
        except Exception as e:
            logger.warning(f"Job {job_id}: Could not probe final video: {e}")

        # Clean up downloaded files and concat list
        cleanup_files = downloaded_files + [concat_file_path]
        for f in cleanup_files:
            if os.path.exists(f):
                os.remove(f)

        logger.info(f"Job {job_id}: Video merge completed successfully: {output_path}")
        return output_path

    except ffmpeg.Error as e:
        # Clean up files on FFmpeg error
        cleanup_files = downloaded_files + [concat_file_path]
        for f in cleanup_files:
            if os.path.exists(f):
                os.remove(f)
        
        error_message = f"FFmpeg error during merge: {e.stderr.decode() if e.stderr else str(e)}"
        logger.error(f"Job {job_id}: {error_message}")
        raise Exception(error_message)
        
    except Exception as e:
        # Clean up files on general error
        cleanup_files = downloaded_files + [concat_file_path]
        for f in cleanup_files:
            if os.path.exists(f):
                os.remove(f)
        
        logger.error(f"Job {job_id}: Video merge failed: {str(e)}")
        raise


def create_smooth_concat(input_files, video_info, crossfade_duration, job_id):
    """Create concatenated video with smooth audio crossfades between segments."""
    temp_concat_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_temp_concat.mp4")
    
    try:
        # Create complex filter for smooth audio transitions
        inputs = [ffmpeg.input(f) for f in input_files]
        
        # Separate video and audio streams
        video_streams = [inp['v'] for inp in inputs]
        audio_streams = []
        
        current_time = 0
        for i, (inp, info) in enumerate(zip(inputs, video_info)):
            if info['has_audio']:
                if i == 0:
                    # First audio stream - no fade in needed
                    if len(video_info) > 1 and crossfade_duration > 0:
                        # Fade out at the end
                        audio = ffmpeg.filter(
                            inp['a'], 
                            'afade', 
                            type='out', 
                            start_time=info['duration'] - crossfade_duration, 
                            duration=crossfade_duration
                        )
                    else:
                        audio = inp['a']
                elif i == len(video_info) - 1:
                    # Last audio stream - only fade in
                    audio = ffmpeg.filter(
                        inp['a'], 
                        'afade', 
                        type='in', 
                        start_time=0, 
                        duration=crossfade_duration
                    )
                else:
                    # Middle audio streams - fade in and out
                    audio = ffmpeg.filter(
                        inp['a'], 
                        'afade', 
                        type='in', 
                        start_time=0, 
                        duration=crossfade_duration
                    )
                    audio = ffmpeg.filter(
                        audio, 
                        'afade', 
                        type='out', 
                        start_time=info['duration'] - crossfade_duration, 
                        duration=crossfade_duration
                    )
                
                # Add delay for proper synchronization
                if current_time > 0:
                    audio = ffmpeg.filter(audio, 'adelay', delays=f"{int(current_time * 1000)}")
                
                audio_streams.append(audio)
            
            current_time += info['duration']
        
        # Concatenate video streams
        video_concat = ffmpeg.filter(video_streams, 'concat', n=len(video_streams), v=1, a=0)
        
        if audio_streams:
            # Mix all audio streams
            if len(audio_streams) == 1:
                audio_concat = audio_streams[0]
            else:
                audio_concat = ffmpeg.filter(
                    audio_streams, 
                    'amix', 
                    inputs=len(audio_streams), 
                    duration='longest'
                )
            
            # Output with both video and audio
            (
                ffmpeg.output(
                    video_concat,
                    audio_concat,
                    temp_concat_path,
                    vcodec='libx264',
                    acodec='aac',
                    preset='medium',
                    crf=23,
                    pix_fmt='yuv420p',
                    movflags='faststart'
                )
                .run(overwrite_output=True, quiet=False)
            )
        else:
            # Output video only
            (
                ffmpeg.output(
                    video_concat,
                    temp_concat_path,
                    vcodec='libx264',
                    preset='medium',
                    crf=23,
                    pix_fmt='yuv420p',
                    movflags='faststart'
                )
                .run(overwrite_output=True, quiet=False)
            )
            
        logger.info(f"Job {job_id}: Smooth concatenation completed")
        return temp_concat_path
        
    except Exception as e:
        logger.warning(f"Job {job_id}: Smooth concat failed, falling back to standard: {e}")
        # Fall back to standard concatenation
        concat_file_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_concat_list.txt")
        return create_standard_concat(input_files, concat_file_path, job_id)


def create_standard_concat(input_files, concat_file_path, job_id):
    """Create concatenated video using standard concat demuxer."""
    temp_concat_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_temp_concat.mp4")
    
    # Create concat list file - use absolute paths and proper escaping
    with open(concat_file_path, 'w', encoding='utf-8') as concat_file:
        for input_file in input_files:
            abs_path = os.path.abspath(input_file).replace("'", "'\"'\"'")
            concat_file.write(f"file '{abs_path}'\n")
    
    logger.info(f"Job {job_id}: Starting standard video concatenation...")
    
    # Use concat demuxer with stream copy to preserve quality and audio
    (
        ffmpeg.input(concat_file_path, format='concat', safe=0)
        .output(temp_concat_path,
                c='copy',  # Copy all streams without re-encoding
                avoid_negative_ts='make_zero'
        ).run(overwrite_output=True, quiet=False)
    )
    
    logger.info(f"Job {job_id}: Standard concatenation completed")
    return temp_concat_path