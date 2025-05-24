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
from config import LOCAL_STORAGE_PATH

def process_video_concatenate(media_urls, job_id, webhook_url=None):
    """Combine multiple videos into one."""
    input_files = []
    downloaded_files = []  # Track which files we downloaded to clean up later
    output_filename = f"{job_id}.mp4"
    output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)

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
                input_filename = download_file(url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_input_{i}"))
                input_files.append(input_filename)
                downloaded_files.append(input_filename)  # Track downloaded files

        # Generate an absolute path concat list file for FFmpeg
        concat_file_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_concat_list.txt")
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
