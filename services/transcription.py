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
import whisper
import srt
from datetime import timedelta
from whisper.utils import WriteSRT, WriteVTT
from services.file_management import download_file
import logging
import uuid
import librosa
import numpy as np
import subprocess
import json
import time
from typing import List, Dict, Any, Optional, Tuple


class TranscriptionError(Exception):
    """Base exception for transcription errors."""
    pass


class AudioProcessingError(TranscriptionError):
    """Error during audio processing."""
    pass


class SpeechDetectionError(TranscriptionError):
    """Error during speech detection."""
    pass


class ModelLoadError(TranscriptionError):
    """Error loading the Whisper model."""
    pass


class SegmentExtractionError(TranscriptionError):
    """Error extracting audio segments."""
    pass

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Set the default local storage directory
STORAGE_PATH = "/tmp/"

def detect_speech_segments(audio_path: str, min_speech_duration: float = 0.5, min_silence_duration: float = 0.3) -> List[Dict[str, float]]:
    """Detect speech segments using librosa for VAD (Voice Activity Detection)."""
    logger.info(f"Detecting speech segments in: {audio_path}")
    
    if not os.path.exists(audio_path):
        raise SpeechDetectionError(f"Audio file not found: {audio_path}")
    
    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=16000)
        
        if len(y) == 0:
            raise SpeechDetectionError("Audio file is empty or corrupted")
        
        # Compute energy-based VAD
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.01 * sr)    # 10ms hop
        
        # Compute short-time energy
        energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        
        if len(energy) == 0:
            raise SpeechDetectionError("Failed to compute audio energy features")
        
        # Threshold for speech detection (adaptive)
        energy_threshold = np.percentile(energy, 30)  # Bottom 30% considered silence
        
        # Convert to time-based segments
        times = librosa.frames_to_time(np.arange(len(energy)), sr=sr, hop_length=hop_length)
        
        # Find speech segments
        speech_frames = energy > energy_threshold
        
        segments = []
        in_speech = False
        start_time = 0
        
        for i, (time_val, is_speech) in enumerate(zip(times, speech_frames)):
            if is_speech and not in_speech:
                # Start of speech
                start_time = time_val
                in_speech = True
            elif not is_speech and in_speech:
                # End of speech
                duration = time_val - start_time
                if duration >= min_speech_duration:
                    segments.append({
                        'start': start_time,
                        'end': time_val,
                        'duration': duration
                    })
                in_speech = False
        
        # Handle case where audio ends during speech
        if in_speech:
            duration = times[-1] - start_time
            if duration >= min_speech_duration:
                segments.append({
                    'start': start_time,
                    'end': times[-1],
                    'duration': duration
                })
        
        logger.info(f"Detected {len(segments)} speech segments")
        return segments
        
    except librosa.LibrosaError as e:
        error_msg = f"Librosa error during speech detection: {str(e)}"
        logger.error(error_msg)
        raise SpeechDetectionError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error in speech detection: {str(e)}"
        logger.error(error_msg)
        # Fallback: return full audio as single segment
        try:
            duration = librosa.get_duration(path=audio_path)
            logger.warning("Falling back to full audio transcription")
            return [{'start': 0, 'end': duration, 'duration': duration}]
        except Exception:
            raise SpeechDetectionError(error_msg) from e


def extract_audio_segment(input_path: str, start_time: float, duration: float, output_path: str) -> bool:
    """Extract audio segment using FFmpeg with enhanced processing."""
    if not os.path.exists(input_path):
        raise SegmentExtractionError(f"Input file not found: {input_path}")
    
    if duration <= 0:
        raise SegmentExtractionError(f"Invalid duration: {duration}")
    
    try:
        # Enhanced FFmpeg command with audio processing
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',      # Mono
            '-af', 'volume=2.0,highpass=f=200,lowpass=f=3000,loudnorm=I=-16:TP=-1.5:LRA=11',
            '-c:a', 'libmp3lame',
            '-q:a', '2',
            '-y',  # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(output_path):
            # Check if file has reasonable size
            size = os.path.getsize(output_path)
            if size > 512:  # At least 512 bytes
                return True
            else:
                logger.warning(f"Audio segment too small: {size} bytes")
                return False
        else:
            error_msg = f"FFmpeg failed with return code {result.returncode}: {result.stderr}"
            logger.error(error_msg)
            return False
            
    except subprocess.TimeoutExpired:
        error_msg = f"FFmpeg timeout for segment {start_time}-{start_time + duration}"
        logger.error(error_msg)
        return False
    except FileNotFoundError:
        error_msg = "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
        logger.error(error_msg)
        raise AudioProcessingError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error extracting audio segment: {str(e)}"
        logger.error(error_msg)
        return False


def update_progress(job_id: str, progress_data: Dict[str, Any]) -> None:
    """Update job progress for tracking."""
    if not job_id:
        return  # Skip if no job_id provided
    
    try:
        from app_utils import log_job_status
        log_job_status(job_id, {
            'status': 'in_progress',
            'progress': progress_data,
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Error updating progress for job {job_id}: {str(e)}")


def process_transcription_chunked(media_url: str, output_type: str, max_chars: int = 56, 
                                 language: Optional[str] = None, job_id: Optional[str] = None,
                                 chunk_duration: float = 30.0, min_speech_duration: float = 0.5) -> str:
    """Enhanced transcription with chunked processing and VAD."""
    logger.info(f"Starting chunked transcription for: {media_url}")
    
    # Download media file
    input_filename = download_file(media_url, os.path.join(STORAGE_PATH, 'input_media'))
    logger.info(f"Downloaded media to: {input_filename}")
    
    temp_files = []
    
    try:
        # Update progress
        if job_id:
            update_progress(job_id, {
                'stage': 'speech_detection',
                'message': 'Detecting speech segments...',
                'percent': 10
            })
        
        # Detect speech segments
        speech_segments = detect_speech_segments(input_filename, min_speech_duration)
        
        if not speech_segments:
            raise SpeechDetectionError("No speech segments detected in audio")
        
        # Load Whisper model
        try:
            model = whisper.load_model("base")
            logger.info("Loaded Whisper model")
        except Exception as e:
            error_msg = f"Failed to load Whisper model: {str(e)}"
            logger.error(error_msg)
            raise ModelLoadError(error_msg) from e
        
        if job_id:
            update_progress(job_id, {
                'stage': 'processing_segments',
                'message': f'Processing {len(speech_segments)} speech segments...',
                'total_segments': len(speech_segments),
                'percent': 20
            })
        
        # Process segments in batches
        all_segments = []
        batch_size = 5  # Process 5 segments at a time
        
        for batch_idx, i in enumerate(range(0, len(speech_segments), batch_size)):
            batch = speech_segments[i:i + batch_size]
            batch_results = []
            
            for seg_idx, segment in enumerate(batch):
                global_idx = i + seg_idx
                
                if job_id:
                    update_progress(job_id, {
                        'stage': 'processing_segment',
                        'message': f'Processing segment {global_idx + 1}/{len(speech_segments)}',
                        'current_segment': global_idx + 1,
                        'total_segments': len(speech_segments),
                        'percent': 20 + (global_idx / len(speech_segments)) * 60
                    })
                
                # Extract audio segment
                segment_path = os.path.join(STORAGE_PATH, f'segment_{global_idx}_{uuid.uuid4().hex[:8]}.mp3')
                temp_files.append(segment_path)
                
                if extract_audio_segment(input_filename, segment['start'], segment['duration'], segment_path):
                    try:
                        # Transcribe segment
                        result = model.transcribe(segment_path, language=language)
                        
                        # Add timing information
                        for seg in result.get('segments', []):
                            seg['start'] += segment['start']
                            seg['end'] += segment['start']
                            
                        batch_results.extend(result.get('segments', []))
                        
                        logger.info(f"Transcribed segment {global_idx + 1}: {result.get('text', '')[:50]}...")
                        
                    except Exception as e:
                        logger.error(f"Error transcribing segment {global_idx + 1}: {str(e)}")
                        # Create placeholder segment
                        batch_results.append({
                            'start': segment['start'],
                            'end': segment['start'] + segment['duration'],
                            'text': '[Transcription failed]'
                        })
                else:
                    logger.warning(f"Skipped segment {global_idx + 1}: audio extraction failed")
                    # Create placeholder for failed extraction
                    batch_results.append({
                        'start': segment['start'],
                        'end': segment['start'] + segment['duration'],
                        'text': '[Audio extraction failed]'
                    })
            
            all_segments.extend(batch_results)
            
            # Rate limiting between batches
            if batch_idx < len(range(0, len(speech_segments), batch_size)) - 1:
                time.sleep(1)  # 1 second delay between batches
        
        # Combine results
        final_result = {
            'text': ' '.join([seg.get('text', '').strip() for seg in all_segments if seg.get('text', '').strip()]),
            'segments': sorted(all_segments, key=lambda x: x['start'])
        }
        
        if job_id:
            update_progress(job_id, {
                'stage': 'generating_output',
                'message': 'Generating final output...',
                'percent': 85
            })
        
        # Generate output based on type
        if output_type == 'transcript':
            output = final_result['text']
        elif output_type in ['srt', 'vtt']:
            output = generate_subtitle_file(final_result, output_type)
        elif output_type == 'ass':
            output = generate_ass_file(final_result, max_chars)
        else:
            raise ValueError(f"Invalid output type: {output_type}")
        
        if job_id:
            update_progress(job_id, {
                'stage': 'complete',
                'message': 'Transcription completed successfully',
                'percent': 100
            })
        
        logger.info(f"Chunked transcription completed successfully")
        return output
        
    except (TranscriptionError, ModelLoadError, SpeechDetectionError, AudioProcessingError) as e:
        error_msg = f"Chunked transcription failed: {str(e)}"
        logger.error(error_msg)
        if job_id:
            update_progress(job_id, {
                'stage': 'error',
                'message': error_msg,
                'error_type': type(e).__name__,
                'percent': 0
            })
        raise TranscriptionError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error in chunked transcription: {str(e)}"
        logger.error(error_msg)
        if job_id:
            update_progress(job_id, {
                'stage': 'error',
                'message': error_msg,
                'error_type': 'UnexpectedError',
                'percent': 0
            })
        raise TranscriptionError(error_msg) from e
    finally:
        # Cleanup
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {str(e)}")
        
        try:
            if os.path.exists(input_filename):
                os.remove(input_filename)
        except Exception as e:
            logger.warning(f"Failed to cleanup input file {input_filename}: {str(e)}")


def generate_subtitle_file(result: Dict[str, Any], output_type: str) -> str:
    """Generate SRT or VTT subtitle file."""
    srt_subtitles = []
    for i, segment in enumerate(result['segments'], start=1):
        start = timedelta(seconds=segment['start'])
        end = timedelta(seconds=segment['end'])
        text = segment['text'].strip()
        if text:  # Only add non-empty segments
            srt_subtitles.append(srt.Subtitle(i, start, end, text))
    
    output_content = srt.compose(srt_subtitles)
    
    # Write to file
    output_filename = os.path.join(STORAGE_PATH, f"{uuid.uuid4()}.{output_type}")
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(output_content)
    
    return output_filename


def generate_ass_file(result: Dict[str, Any], max_chars: int) -> str:
    """Generate ASS subtitle file with word-level timestamps."""
    # For ASS format, we need word-level timestamps
    # Since we don't have them from chunked processing, we'll use segment-level
    ass_content = generate_ass_subtitle_from_segments(result['segments'], max_chars)
    
    output_filename = os.path.join(STORAGE_PATH, f"{uuid.uuid4()}.ass")
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    return output_filename


def generate_ass_subtitle_from_segments(segments: List[Dict[str, Any]], max_chars: int) -> str:
    """Generate ASS subtitle content from segments."""
    def format_time(t):
        hours = int(t // 3600)
        minutes = int((t % 3600) // 60)
        seconds = int(t % 60)
        centiseconds = int(round((t - int(t)) * 100))
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"
    
    ass_content = ""
    
    for segment in segments:
        text = segment.get('text', '').strip()
        if not text:
            continue
            
        start_time = segment['start']
        end_time = segment['end']
        
        # Split long text into multiple lines if needed
        if len(text) > max_chars:
            words = text.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 > max_chars:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = len(word)
                else:
                    current_line.append(word)
                    current_length += len(word) + 1
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Create dialogue for each line
            line_duration = (end_time - start_time) / len(lines)
            for i, line in enumerate(lines):
                line_start = start_time + i * line_duration
                line_end = start_time + (i + 1) * line_duration
                
                start = format_time(line_start)
                end = format_time(line_end)
                
                ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{line}\n"
        else:
            start = format_time(start_time)
            end = format_time(end_time)
            ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"
    
    return ass_content


def process_transcription(media_url, output_type, max_chars=56, language=None, job_id=None, use_chunked=True):
    """Transcribe media and return the transcript, SRT or ASS file path.
    
    Args:
        media_url: URL of the media file to transcribe
        output_type: Type of output ('transcript', 'srt', 'vtt', 'ass')
        max_chars: Maximum characters per line for ASS format
        language: Language for transcription (optional)
        job_id: Job ID for progress tracking (optional)
        use_chunked: Whether to use chunked processing (default: True)
    """
    logger.info(f"Starting transcription for media URL: {media_url} with output type: {output_type}")
    
    # Use chunked processing by default for better performance
    if use_chunked:
        try:
            return process_transcription_chunked(
                media_url=media_url,
                output_type=output_type,
                max_chars=max_chars,
                language=language,
                job_id=job_id
            )
        except TranscriptionError as e:
            logger.warning(f"Chunked processing failed: {str(e)}. Falling back to standard processing.")
            # Fall back to standard processing
            pass
        except Exception as e:
            logger.error(f"Unexpected error in chunked processing: {str(e)}. Falling back to standard processing.")
            # Fall back to standard processing
            pass
    
    # Standard processing (fallback or when chunked is disabled)
    input_filename = download_file(media_url, os.path.join(STORAGE_PATH, 'input_media'))
    logger.info(f"Downloaded media to local file: {input_filename}")

    try:
        try:
            model = whisper.load_model("base")
            logger.info("Loaded Whisper model")
        except Exception as e:
            error_msg = f"Failed to load Whisper model: {str(e)}"
            logger.error(error_msg)
            raise ModelLoadError(error_msg) from e

        if output_type == 'transcript':
            result = model.transcribe(input_filename, language=language)
            output = result['text']
            logger.info("Generated transcript output")
        elif output_type in ['srt', 'vtt']:
            result = model.transcribe(input_filename, language=language)
            srt_subtitles = []
            for i, segment in enumerate(result['segments'], start=1):
                start = timedelta(seconds=segment['start'])
                end = timedelta(seconds=segment['end'])
                text = segment['text'].strip()
                if text:  # Only add non-empty segments
                    srt_subtitles.append(srt.Subtitle(i, start, end, text))
            
            output_content = srt.compose(srt_subtitles)
            
            # Write the output to a file
            output_filename = os.path.join(STORAGE_PATH, f"{uuid.uuid4()}.{output_type}")
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(output_content)
            
            output = output_filename
            logger.info(f"Generated {output_type.upper()} output: {output}")

        elif output_type == 'ass':
            result = model.transcribe(
                input_filename,
                word_timestamps=True,
                task='transcribe',
                verbose=False,
                language=language
            )
            logger.info("Transcription completed with word-level timestamps")
            # Generate ASS subtitle content
            ass_content = generate_ass_subtitle(result, max_chars)
            logger.info("Generated ASS subtitle content")
            
            # Write the ASS content to a file
            output_filename = os.path.join(STORAGE_PATH, f"{uuid.uuid4()}.{output_type}")
            with open(output_filename, 'w', encoding='utf-8') as f:
               f.write(ass_content) 
            output = output_filename
            logger.info(f"Generated {output_type.upper()} output: {output}")
        else:
            raise ValueError("Invalid output type. Must be 'transcript', 'srt', 'vtt', or 'ass'.")

        os.remove(input_filename)
        logger.info(f"Removed local file: {input_filename}")
        logger.info(f"Transcription successful, output type: {output_type}")
        return output
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise


def generate_ass_subtitle(result, max_chars):
    """Generate ASS subtitle content with highlighted current words, showing one line at a time."""
    logger.info("Generate ASS subtitle content with highlighted current words")
    # ASS file header
    ass_content = ""

    # Helper function to format time
    def format_time(t):
        hours = int(t // 3600)
        minutes = int((t % 3600) // 60)
        seconds = int(t % 60)
        centiseconds = int(round((t - int(t)) * 100))
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

    max_chars_per_line = max_chars  # Maximum characters per line

    # Process each segment
    for segment in result['segments']:
        words = segment.get('words', [])
        if not words:
            continue  # Skip if no word-level timestamps

        # Group words into lines
        lines = []
        current_line = []
        current_line_length = 0
        for word_info in words:
            word_length = len(word_info['word']) + 1  # +1 for space
            if current_line_length + word_length > max_chars_per_line:
                lines.append(current_line)
                current_line = [word_info]
                current_line_length = word_length
            else:
                current_line.append(word_info)
                current_line_length += word_length
        if current_line:
            lines.append(current_line)

        # Generate events for each line
        for line in lines:
            line_start_time = line[0]['start']
            line_end_time = line[-1]['end']

            # Generate events for highlighting each word
            for i, word_info in enumerate(line):
                start_time = word_info['start']
                end_time = word_info['end']
                current_word = word_info['word']

                # Build the line text with highlighted current word
                caption_parts = []
                for w in line:
                    word_text = w['word']
                    if w == word_info:
                        # Highlight current word
                        caption_parts.append(r'{\c&H00FFFF&}' + word_text)
                    else:
                        # Default color
                        caption_parts.append(r'{\c&HFFFFFF&}' + word_text)
                caption_with_highlight = ' '.join(caption_parts)

                # Format times
                start = format_time(start_time)
                # End the dialogue event when the next word starts or at the end of the line
                if i + 1 < len(line):
                    end_time = line[i + 1]['start']
                else:
                    end_time = line_end_time
                end = format_time(end_time)

                # Add the dialogue line
                ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{caption_with_highlight}\n"

    return ass_content