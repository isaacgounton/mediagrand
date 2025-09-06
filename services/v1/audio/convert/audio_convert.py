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
import logging
import ffmpeg
import tempfile
from services.file_management import download_file
from config.config import LOCAL_STORAGE_PATH

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def process_audio_convert_from_file(audio_data, job_id, output_format='mp3', original_filename='audio'):
    """
    Convert audio from file data to specified format.
    
    Args:
        audio_data (bytes): Audio file data
        job_id (str): Unique job identifier
        output_format (str): Target format (mp3, ogg, oga)
        original_filename (str): Original filename for reference
        
    Returns:
        str: Path to the converted output file
    """
    # Validate format
    supported_formats = ['mp3', 'ogg', 'oga']
    if output_format.lower() not in supported_formats:
        raise ValueError(f"Unsupported format: {output_format}. Supported formats: {supported_formats}")
    
    # Determine source format from original filename
    source_format = os.path.splitext(original_filename)[1].lower().lstrip('.')
    if source_format == output_format.lower():
        raise ValueError("Source and target formats are the same")
    
    # Create temporary file for input
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{source_format}') as temp_file:
        temp_file.write(audio_data)
        input_filename = temp_file.name
    
    try:
        output_filename = f"{job_id}.{output_format}"
        output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)
        
        # Process audio using ffmpeg
        stream = ffmpeg.input(input_filename)
        
        # Configure output based on format
        output_options = {}
        if output_format == 'mp3':
            output_options['acodec'] = 'libmp3lame'
            output_options['ab'] = '128k'
        elif output_format == 'ogg':
            output_options['acodec'] = 'libvorbis'
            output_options['ab'] = '128k'
        elif output_format == 'oga':
            output_options['acodec'] = 'libvorbis'
            output_options['ab'] = '128k'
        
        # Configure output
        stream = ffmpeg.output(stream, output_path, **output_options)
        
        # Get the ffmpeg command for logging
        cmd = ffmpeg.compile(stream)
        logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
        
        # Run the conversion
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        # Clean up input file
        os.remove(input_filename)
        logger.info(f"Audio conversion successful: {output_path} to format {output_format}")
        
        # Ensure the output file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} does not exist after conversion.")
        
        return output_path
        
    except Exception as e:
        # Clean up input file if it exists
        if os.path.exists(input_filename):
            try:
                os.remove(input_filename)
            except Exception:
                pass
        
        # Handle ffmpeg errors specially to provide more context
        if hasattr(e, 'stderr') and e.stderr:
            stderr_output = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
            detailed_error = f"FFmpeg error details: {stderr_output}"
            logger.error(detailed_error)
            error_msg = f"Audio conversion failed: {str(e)} - {detailed_error}"
        else:
            error_msg = f"Audio conversion failed: {str(e)}"
        
        logger.error(error_msg)
        raise Exception(error_msg)

def process_audio_convert_from_url(audio_url, job_id, output_format='mp3'):
    """
    Convert audio from URL to specified format.
    
    Args:
        audio_url (str): URL of the audio to convert
        job_id (str): Unique job identifier
        output_format (str): Target format (mp3, ogg, oga)
        
    Returns:
        str: Path to the converted output file
    """
    # Validate format
    supported_formats = ['mp3', 'ogg', 'oga']
    if output_format.lower() not in supported_formats:
        raise ValueError(f"Unsupported format: {output_format}. Supported formats: {supported_formats}")
    
    # Download the audio file
    input_filename = download_file(audio_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_input"))
    
    try:
        output_filename = f"{job_id}.{output_format}"
        output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)
        
        # Process audio using ffmpeg
        stream = ffmpeg.input(input_filename)
        
        # Configure output based on format
        output_options = {}
        if output_format == 'mp3':
            output_options['acodec'] = 'libmp3lame'
            output_options['ab'] = '128k'
        elif output_format == 'ogg':
            output_options['acodec'] = 'libvorbis'
            output_options['ab'] = '128k'
        elif output_format == 'oga':
            output_options['acodec'] = 'libvorbis'
            output_options['ab'] = '128k'
        
        # Configure output
        stream = ffmpeg.output(stream, output_path, **output_options)
        
        # Get the ffmpeg command for logging
        cmd = ffmpeg.compile(stream)
        logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
        
        # Run the conversion
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        # Clean up input file
        os.remove(input_filename)
        logger.info(f"Audio conversion successful: {output_path} to format {output_format}")
        
        # Ensure the output file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} does not exist after conversion.")
        
        return output_path
        
    except Exception as e:
        # Clean up input file if it exists
        if 'input_filename' in locals() and os.path.exists(input_filename):
            try:
                os.remove(input_filename)
            except Exception:
                pass
        
        # Handle ffmpeg errors specially to provide more context
        if hasattr(e, 'stderr') and e.stderr:
            stderr_output = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
            detailed_error = f"FFmpeg error details: {stderr_output}"
            logger.error(detailed_error)
            error_msg = f"Audio conversion failed: {str(e)} - {detailed_error}"
        else:
            error_msg = f"Audio conversion failed: {str(e)}"
        
        logger.error(error_msg)
        raise Exception(error_msg)