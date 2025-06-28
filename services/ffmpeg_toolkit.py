# Copyright (c) 2025 Stephen G. Pope
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
import ffmpeg
import requests
from services.file_management import download_file

# Set the default local storage directory
STORAGE_PATH = "/tmp/"

def process_conversion(media_url, job_id, bitrate='128k', webhook_url=None):
    """Convert media to MP3 format with specified bitrate."""
    input_filename = download_file(media_url, os.path.join(STORAGE_PATH, f"{job_id}_input"))
    output_filename = f"{job_id}.mp3"
    output_path = os.path.join(STORAGE_PATH, output_filename)

    try:
        # Convert media file to MP3 with specified bitrate
        (
            ffmpeg
            .input(input_filename)
            .output(output_path, acodec='libmp3lame', audio_bitrate=bitrate)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        os.remove(input_filename)
        print(f"Conversion successful: {output_path} with bitrate {bitrate}")

        # Ensure the output file exists locally before attempting upload
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} does not exist after conversion.")

        return output_path

    except Exception as e:
        print(f"Conversion failed: {str(e)}")
        raise

def process_video_combination(media_urls, job_id, webhook_url=None):
    """Combine multiple videos into one."""
    input_files = []
    downloaded_files = []  # Track which files we downloaded to clean up later
    output_filename = f"{job_id}.mp4"
    output_path = os.path.join(STORAGE_PATH, output_filename)

    try:
        # Process all media files (download URLs or use local files)
        for i, media_item in enumerate(media_urls):
            url = media_item['video_url']
            
            # Check if it's a local file path or a URL
            if os.path.isfile(url):
                # It's a local file, use it directly
                input_files.append(url)
            else:
                # It's a URL, download it
                input_filename = download_file(url, os.path.join(STORAGE_PATH, f"{job_id}_input_{i}"))
                input_files.append(input_filename)
                downloaded_files.append(input_filename)  # Track downloaded files

        # Generate an absolute path concat list file for FFmpeg
        concat_file_path = os.path.join(STORAGE_PATH, f"{job_id}_concat_list.txt")
        with open(concat_file_path, 'w') as concat_file:
            for input_file in input_files:
                # Write absolute paths to the concat list
                concat_file.write(f"file '{os.path.abspath(input_file)}'\n")

        # Use the concat demuxer to concatenate the videos
        (
            ffmpeg.input(concat_file_path, format='concat', safe=0).
                output(output_path, c='copy').
                run(overwrite_output=True)
        )

        # Clean up only downloaded files (not original local files)
        for f in downloaded_files:
            os.remove(f)
            
        os.remove(concat_file_path)  # Remove the concat list file after the operation

        print(f"Video combination successful: {output_path}")

        # Check if the output file exists locally before upload
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} does not exist after combination.")

        return output_path
    except Exception as e:
        print(f"Video combination failed: {str(e)}")
        raise

def extract_audio_from_video(video_path, output_audio_path):
    """
    Extracts audio from a video file.

    Args:
        video_path (str): The path to the input video file.
        output_audio_path (str): The path where the extracted audio file will be saved.

    Returns:
        str: The path to the extracted audio file.
    """
    try:
        (
            ffmpeg
            .input(video_path)
            .output(output_audio_path, acodec='libmp3lame', audio_bitrate='192k')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f"Audio extracted successfully from {video_path} to {output_audio_path}")
        return output_audio_path
    except ffmpeg.Error as e:
        print(f"FFmpeg error extracting audio: {e.stderr.decode('utf8')}")
        raise
    except Exception as e:
        print(f"Error extracting audio: {str(e)}")
        raise

def merge_video_with_audio(video_path, audio_path, output_path):
    """
    Merge a video file with an audio file.
    The audio from the audio_path will be used, replacing any existing audio in the video.
    """
    try:
        (
            ffmpeg
            .input(video_path)
            .output(ffmpeg.input(audio_path), output_path, **{'map': ['0:v', '1:a']}, c='copy', shortest=None)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f"Video and audio merged successfully: {output_path}")
        return output_path
    except ffmpeg.Error as e:
        print(f"FFmpeg error merging video and audio: {e.stderr.decode('utf8')}")
        raise
    except Exception as e:
        print(f"Error merging video and audio: {str(e)}")
        raise
