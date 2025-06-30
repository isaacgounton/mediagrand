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
import subprocess
import json
from services.file_management import download_file
from config import LOCAL_STORAGE_PATH

def get_extension_from_format(format_name):
    # Mapping of common format names to file extensions
    format_to_extension = {
        'mp4': 'mp4',
        'mov': 'mov',
        'avi': 'avi',
        'mkv': 'mkv',
        'webm': 'webm',
        'gif': 'gif',
        'apng': 'apng',
        'jpg': 'jpg',
        'jpeg': 'jpg',
        'png': 'png',
        'image2': 'png',  # Assume png for image2 format
        'rawvideo': 'raw',
        'mp3': 'mp3',
        'wav': 'wav',
        'aac': 'aac',
        'flac': 'flac',
        'ogg': 'ogg',
        'm4a': 'm4a',
        'opus': 'opus',
        'vorbis': 'ogg',
        'h264': 'h264',
        'h265': 'h265',
        'hevc': 'hevc'
    }
    return format_to_extension.get(format_name.lower(), 'mp4')  # Default to mp4 if unknown

def get_metadata(filename, metadata_requests, job_id):
    metadata = {}
    if metadata_requests.get('thumbnail'):
        thumbnail_filename = f"{os.path.splitext(filename)[0]}_thumbnail.jpg"
        thumbnail_command = [
            'ffmpeg',
            '-i', filename,
            '-vf', 'select=eq(n\,0)',
            '-vframes', '1',
            thumbnail_filename
        ]
        try:
            subprocess.run(thumbnail_command, check=True, capture_output=True, text=True)
            if os.path.exists(thumbnail_filename):
                metadata['thumbnail'] = thumbnail_filename  # Return local path instead of URL
        except subprocess.CalledProcessError as e:
            print(f"Thumbnail generation failed: {e.stderr}")

    if metadata_requests.get('filesize'):
        metadata['filesize'] = os.path.getsize(filename)

    if metadata_requests.get('encoder') or metadata_requests.get('duration') or metadata_requests.get('bitrate'):
        ffprobe_command = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            filename
        ]
        result = subprocess.run(ffprobe_command, capture_output=True, text=True)
        probe_data = json.loads(result.stdout)
        
        if metadata_requests.get('duration'):
            metadata['duration'] = float(probe_data['format']['duration'])
        if metadata_requests.get('bitrate'):
            metadata['bitrate'] = int(probe_data['format']['bit_rate'])
        
        if metadata_requests.get('encoder'):
            metadata['encoder'] = {}
            for stream in probe_data['streams']:
                if stream['codec_type'] == 'video':
                    metadata['encoder']['video'] = stream.get('codec_name', 'unknown')
                elif stream['codec_type'] == 'audio':
                    metadata['encoder']['audio'] = stream.get('codec_name', 'unknown')

    return metadata

def process_ffmpeg_compose(data, job_id):
    output_filenames = []
    
    # Build FFmpeg command
    command = ["ffmpeg"]
    
    # Add global options
    for option in data.get("global_options", []):
        command.append(option["option"])
        if "argument" in option and option["argument"] is not None:
            command.append(str(option["argument"]))
    
    # Add inputs
    for input_data in data["inputs"]:
        if "options" in input_data:
            for option in input_data["options"]:
                command.append(option["option"])
                if "argument" in option and option["argument"] is not None:
                    command.append(str(option["argument"]))
        input_path = download_file(input_data["file_url"], LOCAL_STORAGE_PATH)
        command.extend(["-i", input_path])
    
    # Add filters (both simple and complex)
    if data.get("filters"):
        # Check if we should use simple filters or complex filters
        use_simple_video = data.get("use_simple_video_filter", False)
        use_simple_audio = data.get("use_simple_audio_filter", False)
        
        if use_simple_video or use_simple_audio:
            # Handle simple filters
            video_filters = []
            audio_filters = []
            
            for filter_obj in data["filters"]:
                if filter_obj.get("type") == "video" and use_simple_video:
                    video_filters.append(filter_obj["filter"])
                elif filter_obj.get("type") == "audio" and use_simple_audio:
                    audio_filters.append(filter_obj["filter"])
            
            if video_filters:
                command.extend(["-vf", ",".join(video_filters)])
            if audio_filters:
                command.extend(["-af", ",".join(audio_filters)])
        else:
            # Default to complex filter
            filter_complex = ";".join(filter_obj["filter"] for filter_obj in data["filters"])
            command.extend(["-filter_complex", filter_complex])
    
    # Add stream mappings
    if data.get("stream_mappings"):
        for mapping in data["stream_mappings"]:
            command.extend(["-map", mapping])
    
    # Add outputs
    for i, output in enumerate(data["outputs"]):
        # Add any stream-specific mappings for this output
        if "stream_mappings" in output:
            for mapping in output["stream_mappings"]:
                command.extend(["-map", mapping])
        
        # Determine output format
        format_name = None
        for option in output["options"]:
            if option["option"] == "-f":
                format_name = option.get("argument")
                break
        
        extension = get_extension_from_format(format_name) if format_name else 'mp4'
        output_filename = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_output_{i}.{extension}")
        output_filenames.append(output_filename)
        
        # Add output options
        for option in output["options"]:
            command.append(option["option"])
            if "argument" in option and option["argument"] is not None:
                command.append(str(option["argument"]))
        
        command.append(output_filename)
    
    # Execute FFmpeg command
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"FFmpeg command executed successfully: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg command: {' '.join(command)}")
        raise Exception(f"FFmpeg command failed: {e.stderr}")
    
    # Clean up input files
    for input_data in data["inputs"]:
        input_path = os.path.join(LOCAL_STORAGE_PATH, os.path.basename(input_data["file_url"]))
        if os.path.exists(input_path):
            os.remove(input_path)
    
    # Get metadata if requested
    metadata = []
    if data.get("metadata"):
        for output_filename in output_filenames:
            metadata.append(get_metadata(output_filename, data["metadata"], job_id))
    
    return output_filenames, metadata

