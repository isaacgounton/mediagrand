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
import logging
from typing import Union
from services.file_management import download_file
from config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)

def process_extract_frame(video_url: str, seconds: Union[int, float] = 0, job_id: Union[str, None] = None) -> str:
    """
    Extracts an image frame from a video at a specified time.
    
    Args:
        video_url: URL or path to the video file
        seconds: Time in seconds to extract the frame from (default: 0)
        job_id: Job identifier for tracking
    
    Returns:
        str: Path to the extracted frame image
    """
    video_file = None
    cleanup_video = False
    
    try:
        logger.info(f"Job {job_id}: Starting frame extraction from video at {seconds} seconds")

        # Download video if it's a URL
        if os.path.isfile(video_url):
            video_file = video_url
            cleanup_video = False
        else:
            video_file = download_file(video_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_video"))
            cleanup_video = True

        # Prepare output path
        output_filename = f"{job_id}_frame.jpg"
        output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)

        # Build FFmpeg command to extract frame
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-i", video_file,  # Input video
            "-ss", str(seconds),  # Seek to specified time
            "-vframes", "1",  # Extract only one frame
            "-q:v", "2",  # High quality
            "-f", "image2",  # Output format
            output_path
        ]

        logger.info(f"Job {job_id}: Executing frame extraction: {' '.join(cmd)}")

        # Execute the command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Clean up downloaded video file if needed
        if cleanup_video and video_file and os.path.exists(video_file):
            os.remove(video_file)

        logger.info(f"Job {job_id}: Frame extraction completed successfully: {output_path}")

        # Check if the output file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output frame {output_path} does not exist after extraction.")

        return output_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Job {job_id}: FFmpeg failed: {e.stderr}")
        # Clean up on error
        if cleanup_video and video_file and os.path.exists(video_file):
            os.remove(video_file)
        raise Exception(f"Frame extraction failed: {e.stderr}")
    
    except Exception as e:
        logger.error(f"Job {job_id}: Frame extraction failed: {str(e)}")
        # Clean up on error
        if cleanup_video and video_file and os.path.exists(video_file):
            os.remove(video_file)
        raise