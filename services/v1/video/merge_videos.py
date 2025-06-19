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
import subprocess
import json
import time
import logging
from services.file_management import download_file
from config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)

def get_video_info(file_path):
    """
    Retrieves video information such as duration, width, height, codec, fps, etc.
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-select_streams", "v:0",  # Select first video stream
            file_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(result.stdout)

        # Extract format information
        format_info = probe_data.get("format", {})
        streams = probe_data.get("streams", [])

        if not streams:
            raise Exception("No video stream found in file")

        video_stream = streams[0]

        video_info = {
            "duration": float(format_info.get("duration", 0)),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
        }

        return video_info

    except Exception as e:
        logger.error(f"Error getting video info for {file_path}: {str(e)}")
        return {}

def execute_ffmpeg_command(cmd, operation_name, expected_duration=None):
    """
    Execute an ffmpeg command with proper logging and progress tracking.
    """
    try:
        logger.info(f"Executing {operation_name}: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            text=True,
        )

        # Process the output line by line for progress tracking
        if process.stderr:
            for line in process.stderr:
                if expected_duration and "time=" in line and "speed=" in line:
                    try:
                        # Extract the time information for progress
                        time_str = line.split("time=")[1].split(" ")[0]
                        # Convert HH:MM:SS.MS format to seconds
                        h, m, s = time_str.split(":")
                        seconds = float(h) * 3600 + float(m) * 60 + float(s)
                        
                        # Calculate progress percentage
                        progress = min(100, (seconds / expected_duration) * 100)
                        logger.info(f"{operation_name}: {progress:.2f}% complete")
                    except (ValueError, IndexError):
                        # If parsing fails, continue silently
                        pass

        # Wait for the process to complete
        return_code = process.wait()
        if return_code != 0:
            logger.error(f"FFmpeg exited with code: {return_code} for {operation_name}")
            return False

        logger.info(f"{operation_name} completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error executing ffmpeg command for {operation_name}: {str(e)}")
        return False

def process_video_merge(video_urls, background_music_url=None, background_music_volume=0.5, job_id=None):
    """
    Merges multiple videos into one, optionally with background music.
    
    Args:
        video_urls: List of video URLs to merge
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

        # Get dimensions from the first video
        first_video_info = get_video_info(input_files[0])
        if not first_video_info:
            raise Exception("Failed to get video info from first video")

        target_width = first_video_info.get("width", 1080)
        target_height = first_video_info.get("height", 1920)
        target_dimensions = f"{target_width}:{target_height}"

        # Base command
        cmd = ["ffmpeg", "-y"]

        # Add input video files
        for video_path in input_files:
            cmd.extend(["-i", video_path])

        # Download and add background music if provided
        music_input_index = None
        music_file = None
        if background_music_url:
            if os.path.isfile(background_music_url):
                music_file = background_music_url
            else:
                music_file = download_file(background_music_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_music"))
                downloaded_files.append(music_file)
            
            cmd.extend(["-i", music_file])
            music_input_index = len(input_files)

        # Create filter complex for concatenating videos
        if len(input_files) == 1:
            # Single video - re-encode to ensure consistency
            if background_music_url:
                cmd.extend([
                    "-filter_complex",
                    f"[0:v]scale={target_dimensions}:force_original_aspect_ratio=decrease,pad={target_dimensions}:(ow-iw)/2:(oh-ih)/2:black,fps=30[v];[{music_input_index}:a]volume={background_music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first[a]",
                    "-map", "[v]",
                    "-map", "[a]",
                ])
            else:
                cmd.extend([
                    "-filter_complex",
                    f"[0:v]scale={target_dimensions}:force_original_aspect_ratio=decrease,pad={target_dimensions}:(ow-iw)/2:(oh-ih)/2:black,fps=30[v]",
                    "-map", "[v]",
                    "-map", "0:a",
                ])
        else:
            # Multiple videos - normalize and concatenate
            normalize_filters = []
            for i in range(len(input_files)):
                normalize_filters.append(
                    f"[{i}:v]scale={target_dimensions}:force_original_aspect_ratio=decrease,pad={target_dimensions}:(ow-iw)/2:(oh-ih)/2:black,fps=30,format=yuv420p[v{i}n]"
                )

            # Create the concat filter using normalized streams
            concat_inputs = ""
            for i in range(len(input_files)):
                concat_inputs += f"[v{i}n][{i}:a]"

            # Combine all filters
            filter_complex = (
                ";".join(normalize_filters)
                + f";{concat_inputs}concat=n={len(input_files)}:v=1:a=1[v][a]"
            )

            if background_music_url:
                # Mix the concatenated audio with background music
                filter_complex += f";[{music_input_index}:a]volume={background_music_volume}[bg];[a][bg]amix=inputs=2:duration=first[final_a]"
                cmd.extend([
                    "-filter_complex", filter_complex,
                    "-map", "[v]",
                    "-map", "[final_a]",
                ])
            else:
                cmd.extend([
                    "-filter_complex", filter_complex,
                    "-map", "[v]",
                    "-map", "[a]",
                ])

        # Video codec settings
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
        ])

        # Audio codec settings
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])

        # Other settings
        cmd.extend(["-pix_fmt", "yuv420p", output_path])

        # Calculate expected duration for progress tracking
        expected_duration = 0
        for video_path in input_files:
            video_info = get_video_info(video_path)
            expected_duration += video_info.get("duration", 0)

        # Execute the command
        success = execute_ffmpeg_command(cmd, "merge videos", expected_duration)

        if not success:
            raise Exception("FFmpeg failed to merge videos")

        # Clean up downloaded files
        for f in downloaded_files:
            if os.path.exists(f):
                os.remove(f)

        logger.info(f"Job {job_id}: Video merge completed successfully: {output_path}")

        # Check if the output file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} does not exist after merge.")

        return output_path

    except Exception as e:
        # Clean up downloaded files on error
        for f in downloaded_files:
            if os.path.exists(f):
                os.remove(f)
        
        logger.error(f"Job {job_id}: Video merge failed: {str(e)}")
        raise