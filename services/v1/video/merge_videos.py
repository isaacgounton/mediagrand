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

        # Download voice over audio if provided
        voice_file = None
        if audio_url:
            if os.path.isfile(audio_url):
                voice_file = audio_url
            else:
                voice_file = download_file(audio_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_voice"))
                downloaded_files.append(voice_file)
            logger.info(f"Job {job_id}: Voice over file: {voice_file}")

        # Download background music if provided
        music_file = None
        if background_music_url:
            if os.path.isfile(background_music_url):
                music_file = background_music_url
            else:
                music_file = download_file(background_music_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_music"))
                downloaded_files.append(music_file)
            logger.info(f"Job {job_id}: Background music file: {music_file}")

        # Create concat list file for video merging - same as concatenate service
        concat_file_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_concat_list.txt")
        with open(concat_file_path, 'w') as concat_file:
            for input_file in input_files:
                concat_file.write(f"file '{os.path.abspath(input_file)}'\n")

        # Concatenate videos first
        temp_concat_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_temp_concat.mp4")
        (
            ffmpeg.input(concat_file_path, format='concat', safe=0)
            .output(temp_concat_path,
                    vcodec='libx264',
                    acodec='aac',
                    r=30,
                    pix_fmt='yuv420p',
                    movflags='faststart'
            ).run(overwrite_output=True)
        )

        # Get video duration for alignment
        try:
            video_probe = ffmpeg.probe(temp_concat_path)
            video_duration = float(video_probe['format']['duration'])
            has_audio = any(stream['codec_type'] == 'audio' for stream in video_probe['streams'])
        except:
            has_audio = False
            video_duration = None

        video_input = ffmpeg.input(temp_concat_path)

        # Prepare audio streams
        audio_streams = []
        if has_audio:
            audio_streams.append(video_input['a'])
        if voice_file:
            # Loop or trim voice over to match video duration
            if video_duration:
                voice_input = ffmpeg.input(voice_file, t=video_duration)
            else:
                voice_input = ffmpeg.input(voice_file)
            audio_streams.append(voice_input['a'])
        if music_file:
            if video_duration:
                music_input = ffmpeg.input(music_file, stream_loop=-1, t=video_duration)
            else:
                music_input = ffmpeg.input(music_file)
            audio_streams.append(music_input['a'])

        # Mix audio streams if any, otherwise just use video
        if audio_streams:
            # If more than one audio stream, mix them
            if len(audio_streams) > 1:
                # Set weights: video/voice=1, music=background_music_volume
                weights = []
                for s in audio_streams:
                    if music_file and s == audio_streams[-1]:
                        weights.append(str(background_music_volume))
                    else:
                        weights.append("1")
                mixed_audio = ffmpeg.filter(audio_streams, 'amix', inputs=len(audio_streams), duration='longest', weights=' '.join(weights))
                (
                    ffmpeg.output(
                        video_input['v'],
                        mixed_audio,
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        pix_fmt='yuv420p',
                        preset='veryfast',
                        crf=23,
                        **{'b:a': '192k'}
                    )
                    .run(overwrite_output=True)
                )
            else:
                # Only one audio stream, just use it
                (
                    ffmpeg.output(
                        video_input['v'],
                        audio_streams[0],
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        pix_fmt='yuv420p',
                        preset='veryfast',
                        crf=23,
                        **{'b:a': '192k'}
                    )
                    .run(overwrite_output=True)
                )
        else:
            # No audio, just output video
            (
                ffmpeg.output(
                    video_input['v'],
                    output_path,
                    vcodec='libx264',
                    acodec='aac',
                    pix_fmt='yuv420p',
                    preset='veryfast',
                    crf=23,
                    **{'b:a': '192k'}
                )
                .run(overwrite_output=True)
            )

        # Clean up temp file
        if os.path.exists(temp_concat_path):
            os.remove(temp_concat_path)

        # Clean up downloaded files and concat list
        for f in downloaded_files:
            if os.path.exists(f):
                os.remove(f)
        
        if os.path.exists(concat_file_path):
            os.remove(concat_file_path)

        logger.info(f"Job {job_id}: Video merge completed successfully: {output_path}")

        # Check if the output file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} does not exist after merge.")

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