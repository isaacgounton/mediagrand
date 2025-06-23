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
from config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)

def process_video_merge(
    video_urls,
    audio_url=None,  # Optional voice over
    background_music_url=None,
    background_music_volume=0.5,
    job_id=None
):
    """
    Merges multiple videos into one, optionally with voice over and/or background music.
    Uses the same pattern as the working concatenate service.
    
    Args:
        video_urls: List of video URLs to merge
        audio_url: Optional voice over audio URL
        background_music_url: Optional background music URL
        background_music_volume: Volume level for background music (0.0 to 1.0)
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

        # Download all video files - same pattern as concatenate
        for i, video_url in enumerate(video_urls):
            if os.path.isfile(video_url):
                input_files.append(video_url)
            else:
                input_filename = download_file(video_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_video_{i}"))
                input_files.append(input_filename)
                downloaded_files.append(input_filename)

        # Verify all video files exist and get their durations
        total_video_duration = 0
        for i, input_file in enumerate(input_files):
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Input video file {i} does not exist: {input_file}")
            
            try:
                probe = ffmpeg.probe(input_file)
                duration = float(probe['format']['duration'])
                total_video_duration += duration
                logger.info(f"Job {job_id}: Video {i} duration: {duration:.2f}s, file: {input_file}")
            except Exception as e:
                logger.warning(f"Job {job_id}: Could not get duration for video {i}: {e}")

        logger.info(f"Job {job_id}: Total expected video duration: {total_video_duration:.2f}s")

        # Download voice over audio if provided
        voice_file = None
        if audio_url:
            if os.path.isfile(audio_url):
                voice_file = audio_url
            else:
                voice_file = download_file(audio_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_voice"))
                downloaded_files.append(voice_file)
            
            if not os.path.exists(voice_file):
                logger.error(f"Job {job_id}: Voice file does not exist: {voice_file}")
                voice_file = None
            else:
                logger.info(f"Job {job_id}: Voice over file: {voice_file}")

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

        # Create concat list file for video merging - use absolute paths and proper escaping
        with open(concat_file_path, 'w', encoding='utf-8') as concat_file:
            for input_file in input_files:
                # Use absolute path and escape single quotes for FFmpeg
                abs_path = os.path.abspath(input_file).replace("'", "'\"'\"'")
                concat_file.write(f"file '{abs_path}'\n")
        
        # Debug: Log concat file contents and input files
        logger.info(f"Job {job_id}: Concat file created at {concat_file_path}")
        with open(concat_file_path, 'r', encoding='utf-8') as f:
            concat_lines = f.readlines()
        logger.info(f"Job {job_id}: Concat file lines: {len(concat_lines)}; Input files: {len(input_files)}")
        for idx, line in enumerate(concat_lines):
            logger.info(f"Job {job_id}: Concat line {idx}: {line.strip()}")

        # First, concatenate videos using concat demuxer with better options
        temp_concat_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_temp_concat.mp4")
        
        logger.info(f"Job {job_id}: Starting video concatenation...")
        try:
            (
                ffmpeg.input(concat_file_path, format='concat', safe=0)
                .output(temp_concat_path,
                        vcodec='libx264',
                        acodec='aac',
                        preset='medium',
                        crf=23,
                        pix_fmt='yuv420p',
                        movflags='faststart',
                        avoid_negative_ts='make_zero'
                ).run(overwrite_output=True, quiet=False)
            )
        except ffmpeg.Error as e:
            logger.error(f"Job {job_id}: FFmpeg concat error: {e.stderr.decode() if e.stderr else str(e)}")
            raise

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
            video_duration = total_video_duration if total_video_duration > 0 else 60  # fallback

        # Now handle audio mixing
        video_input = ffmpeg.input(temp_concat_path)
        
        # Prepare all audio inputs with proper duration handling
        audio_inputs = []
        
        # Add original video audio if it exists
        if has_video_audio:
            audio_inputs.append(video_input['a'])
            logger.info(f"Job {job_id}: Added original video audio")

        # Add voice over if provided
        if voice_file:
            try:
                voice_probe = ffmpeg.probe(voice_file)
                voice_duration = float(voice_probe['format']['duration'])
                logger.info(f"Job {job_id}: Voice duration: {voice_duration:.2f}s")
                
                # If voice is shorter than video, we might want to repeat it or pad it
                if voice_duration < video_duration:
                    # Option 1: Just use the voice as-is (it will end early)
                    voice_input = ffmpeg.input(voice_file)
                    # Option 2: Loop the voice to match video duration
                    # voice_input = ffmpeg.input(voice_file, stream_loop=-1, t=video_duration)
                else:
                    # Trim voice to match video duration
                    voice_input = ffmpeg.input(voice_file, t=video_duration)
                
                audio_inputs.append(voice_input['a'])
                logger.info(f"Job {job_id}: Added voice over audio")
            except Exception as e:
                logger.error(f"Job {job_id}: Error processing voice file: {e}")

        # Add background music if provided
        if music_file:
            try:
                music_probe = ffmpeg.probe(music_file)
                music_duration = float(music_probe['format']['duration'])
                logger.info(f"Job {job_id}: Music duration: {music_duration:.2f}s")
                
                # Loop music to match video duration and apply volume
                music_input = ffmpeg.input(music_file, stream_loop=-1, t=video_duration)
                music_audio = ffmpeg.filter(music_input['a'], 'volume', background_music_volume)
                audio_inputs.append(music_audio)
                logger.info(f"Job {job_id}: Added background music (volume: {background_music_volume})")
            except Exception as e:
                logger.error(f"Job {job_id}: Error processing music file: {e}")

        # Create final output
        logger.info(f"Job {job_id}: Creating final output with {len(audio_inputs)} audio streams...")
        
        if len(audio_inputs) == 0:
            # No audio at all - just copy video
            logger.info(f"Job {job_id}: No audio streams, copying video only")
            (
                ffmpeg.output(
                    video_input['v'],
                    output_path,
                    vcodec='copy',  # Copy video stream as-is since we just concatenated it
                    an=None  # No audio
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
                    vcodec='copy',  # Copy video stream as-is
                    acodec='aac',
                    **{'b:a': '192k'}
                )
                .run(overwrite_output=True, quiet=False)
            )
        else:
            # Multiple audio streams - mix them
            logger.info(f"Job {job_id}: Mixing {len(audio_inputs)} audio streams")
            mixed_audio = ffmpeg.filter(
                audio_inputs, 
                'amix', 
                inputs=len(audio_inputs), 
                duration='longest',
                normalize=0  # Don't auto-normalize to prevent clipping
            )
            
            (
                ffmpeg.output(
                    video_input['v'],
                    mixed_audio,
                    output_path,
                    vcodec='copy',  # Copy video stream as-is
                    acodec='aac',
                    **{'b:a': '192k'}
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
            logger.info(f"Job {job_id}: Final video duration: {final_duration:.2f}s, has audio: {final_has_audio}")
        except Exception as e:
            logger.warning(f"Job {job_id}: Could not probe final video: {e}")

        # Clean up downloaded files and concat list
        for f in downloaded_files:
            if os.path.exists(f):
                os.remove(f)
        
        if os.path.exists(concat_file_path):
            os.remove(concat_file_path)

        logger.info(f"Job {job_id}: Video merge completed successfully: {output_path}")
        return output_path

    except ffmpeg.Error as e:
        # Clean up files on FFmpeg error
        for f in downloaded_files:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(concat_file_path):
            os.remove(concat_file_path)
        
        error_message = f"FFmpeg error during merge: {e.stderr.decode() if e.stderr else str(e)}"
        logger.error(f"Job {job_id}: {error_message}")
        raise Exception(error_message)
        
    except Exception as e:
        # Clean up files on general error
        for f in downloaded_files:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(concat_file_path):
            os.remove(concat_file_path)
        
        logger.error(f"Job {job_id}: Video merge failed: {str(e)}")
        raise