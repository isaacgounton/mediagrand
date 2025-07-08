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
import json
import subprocess
import logging
import re
import numpy as np
import librosa
import scipy.signal
from typing import List, Dict, Any, Optional, Tuple
from services.file_management import download_file
from config import LOCAL_STORAGE_PATH

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Check for required dependencies
try:
    import librosa
    import scipy.signal
    ADVANCED_VAD_AVAILABLE = True
    logger.info("Advanced VAD dependencies available")
except ImportError as e:
    ADVANCED_VAD_AVAILABLE = False
    logger.warning(f"Advanced VAD dependencies missing: {e}. Only basic FFmpeg detection available.")

def detect_speech_segments_vad(media_url: str, volume_threshold: float = 40.0, 
                               min_speech_duration: float = 0.5, speech_padding_ms: int = 50,
                               silence_padding_ms: int = 450, frame_duration_ms: int = 30,
                               job_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Advanced Voice Activity Detection using librosa and energy-based analysis.
    
    Args:
        media_url: URL of the media file to analyze
        volume_threshold: Volume threshold percentage (0-100) for speech detection
        min_speech_duration: Minimum duration in seconds for a speech segment
        speech_padding_ms: Padding around speech segments in milliseconds
        silence_padding_ms: Padding for silence removal in milliseconds
        frame_duration_ms: Frame duration for analysis in milliseconds
        job_id: Unique job identifier
        
    Returns:
        List of speech segments with start, end times and metadata
    """
    logger.info(f"Starting advanced VAD for media URL: {media_url}")
    input_filename = download_file(media_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_vad_input"))
    logger.info(f"Downloaded media to local file: {input_filename}")
    
    try:
        # Load audio with librosa (automatically converts to mono)
        y, sr = librosa.load(input_filename, sr=16000, mono=True)
        logger.info(f"Loaded audio: duration={len(y)/sr:.2f}s, sample_rate={sr}Hz")
        
        if len(y) == 0:
            raise ValueError("Audio file is empty or corrupted")
        
        # Calculate frame parameters
        frame_length = int((frame_duration_ms / 1000) * sr)  # Frame size in samples
        hop_length = frame_length // 2  # 50% overlap
        
        # Compute short-time energy (RMS)
        rms_energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Convert to time frames
        times = librosa.frames_to_time(np.arange(len(rms_energy)), sr=sr, hop_length=hop_length)
        
        # Convert RMS to decibels
        rms_db = librosa.amplitude_to_db(rms_energy, ref=np.max)
        
        # Calculate dynamic threshold based on audio characteristics
        min_db = np.percentile(rms_db[rms_db > -100], 5)  # Bottom 5% excluding silence
        max_db = np.percentile(rms_db, 95)  # Top 5%
        
        # Convert volume threshold percentage to dB threshold
        db_threshold = min_db + ((max_db - min_db) * volume_threshold) / 100
        
        logger.info(f"Dynamic thresholds - Min: {min_db:.1f}dB, Max: {max_db:.1f}dB, Threshold: {db_threshold:.1f}dB")
        
        # Initial speech detection based on energy
        speech_flags = rms_db > db_threshold
        
        # Apply temporal smoothing to reduce noise
        speech_flags = apply_temporal_smoothing(speech_flags, sr, hop_length, min_speech_duration)
        
        # Extract speech segments
        segments = extract_speech_segments(speech_flags, times, min_speech_duration)
        
        # Apply padding
        total_duration = len(y) / sr
        padded_segments = apply_segment_padding(segments, speech_padding_ms / 1000, total_duration)
        
        # Merge close segments if silence padding is specified
        if silence_padding_ms > 0:
            merged_segments = merge_close_segments(padded_segments, silence_padding_ms / 1000)
        else:
            merged_segments = padded_segments
        
        # Convert to output format with metadata
        result_segments = []
        for i, segment in enumerate(merged_segments):
            result_segments.append({
                "id": i + 1,
                "start": round(segment['start'], 3),
                "end": round(segment['end'], 3),
                "duration": round(segment['end'] - segment['start'], 3),
                "start_formatted": format_time(segment['start']),
                "end_formatted": format_time(segment['end']),
                "confidence": calculate_segment_confidence(y, sr, segment['start'], segment['end'])
            })
        
        # Clean up
        os.remove(input_filename)
        logger.info(f"VAD completed: {len(result_segments)} speech segments detected")
        
        return result_segments
        
    except Exception as e:
        logger.error(f"VAD failed: {str(e)}")
        if os.path.exists(input_filename):
            os.remove(input_filename)
        raise


def apply_temporal_smoothing(speech_flags: np.ndarray, sr: int, hop_length: int, 
                           min_duration: float) -> np.ndarray:
    """Apply temporal smoothing to reduce noise in speech detection."""
    # Convert minimum duration to frames
    min_frames = int((min_duration * sr) / hop_length)
    
    # Apply median filter to remove isolated spikes
    kernel_size = min(min_frames // 2, 5)  # Adaptive kernel size
    if kernel_size > 1:
        speech_flags = scipy.signal.medfilt(speech_flags.astype(float), kernel_size=kernel_size) > 0.5
    
    # Fill short gaps between speech segments
    gap_fill_frames = min_frames // 4
    speech_flags = fill_short_gaps(speech_flags, gap_fill_frames)
    
    return speech_flags


def fill_short_gaps(speech_flags: np.ndarray, max_gap_frames: int) -> np.ndarray:
    """Fill short gaps between speech segments."""
    result = speech_flags.copy()
    
    # Find transitions
    diff = np.diff(speech_flags.astype(int))
    speech_ends = np.where(diff == -1)[0]
    speech_starts = np.where(diff == 1)[0]
    
    # Fill gaps between speech segments
    for end_idx in speech_ends:
        # Find next speech start
        next_starts = speech_starts[speech_starts > end_idx]
        if len(next_starts) > 0:
            next_start = next_starts[0]
            gap_size = next_start - end_idx
            
            # Fill if gap is small enough
            if gap_size <= max_gap_frames:
                result[end_idx:next_start+1] = True
    
    return result


def extract_speech_segments(speech_flags: np.ndarray, times: np.ndarray, 
                          min_duration: float) -> List[Dict[str, float]]:
    """Extract speech segments from boolean flags."""
    segments = []
    in_speech = False
    segment_start = 0
    
    for i, (time_val, is_speech) in enumerate(zip(times, speech_flags)):
        if is_speech and not in_speech:
            # Start of speech
            segment_start = time_val
            in_speech = True
        elif not is_speech and in_speech:
            # End of speech
            duration = time_val - segment_start
            if duration >= min_duration:
                segments.append({
                    'start': segment_start,
                    'end': time_val
                })
            in_speech = False
    
    # Handle case where audio ends during speech
    if in_speech and len(times) > 0:
        duration = times[-1] - segment_start
        if duration >= min_duration:
            segments.append({
                'start': segment_start,
                'end': times[-1]
            })
    
    return segments


def apply_segment_padding(segments: List[Dict[str, float]], padding: float, 
                         total_duration: float) -> List[Dict[str, float]]:
    """Apply padding around speech segments."""
    padded_segments = []
    
    for segment in segments:
        padded_start = max(0, segment['start'] - padding)
        padded_end = min(total_duration, segment['end'] + padding)
        
        padded_segments.append({
            'start': padded_start,
            'end': padded_end
        })
    
    return padded_segments


def merge_close_segments(segments: List[Dict[str, float]], 
                        max_gap: float) -> List[Dict[str, float]]:
    """Merge segments that are close together."""
    if not segments:
        return []
    
    # Sort segments by start time
    sorted_segments = sorted(segments, key=lambda x: x['start'])
    merged = [sorted_segments[0]]
    
    for current in sorted_segments[1:]:
        last_merged = merged[-1]
        
        # Check if segments should be merged
        gap = current['start'] - last_merged['end']
        if gap <= max_gap:
            # Merge segments
            merged[-1]['end'] = max(last_merged['end'], current['end'])
        else:
            # Add as new segment
            merged.append(current)
    
    return merged


def calculate_segment_confidence(y: np.ndarray, sr: int, start_time: float, 
                               end_time: float) -> float:
    """Calculate confidence score for a speech segment."""
    try:
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        
        if start_sample >= len(y) or end_sample <= start_sample:
            return 0.0
        
        # Extract segment audio
        segment_audio = y[start_sample:end_sample]
        
        # Calculate various features
        rms = np.sqrt(np.mean(segment_audio ** 2))
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(segment_audio))
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=segment_audio, sr=sr))
        
        # Normalize and combine features
        rms_score = min(1.0, rms * 10)  # Normalize RMS
        zcr_score = min(1.0, zero_crossing_rate * 5)  # Normalize ZCR
        sc_score = min(1.0, spectral_centroid / 4000)  # Normalize spectral centroid
        
        # Weighted combination
        confidence = (rms_score * 0.5 + zcr_score * 0.3 + sc_score * 0.2)
        
        return round(confidence, 3)
        
    except Exception as e:
        logger.warning(f"Error calculating confidence: {e}")
        return 0.5  # Default confidence


def detect_silence(media_url, start_time=None, end_time=None, noise_threshold="-30dB", min_duration=0.5, mono=False, job_id=None):
    """
    Detect silence in media files using FFmpeg's silencedetect filter.
    Note: This is the legacy method. For better results, use detect_speech_segments_vad().
    
    Args:
        media_url (str): URL of the media file to analyze
        start_time (str, optional): Start time in format HH:MM:SS.mmm
        end_time (str, optional): End time in format HH:MM:SS.mmm
        noise_threshold (str, optional): Noise tolerance threshold, default "-30dB"
        min_duration (float, optional): Minimum silence duration to detect in seconds
        mono (bool, optional): Whether to convert stereo to mono before analysis
        job_id (str, optional): Unique job identifier
        
    Returns:
        list: List of dictionaries containing silence intervals with start, end, and duration
    """
    logger.info(f"Starting silence detection for media URL: {media_url}")
    input_filename = download_file(media_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_input"))
    logger.info(f"Downloaded media to local file: {input_filename}")
    
    try:
        # For reliable silence detection with time constraints, we need a different approach
        # We'll use FFmpeg without any time constraints and process the results later
        cmd = ['ffmpeg', '-i', input_filename]
        
        # We won't use audio trim filters as they're causing issues with silence detection
        # Instead, we'll filter the results after the analysis is complete
        segment_filter = ""
        
        # Save the start and end times for post-processing
        start_seconds = 0
        end_seconds = float('inf')
        
        if start_time:
            try:
                # Parse the start time to seconds
                h, m, s = start_time.split(':')
                start_seconds = int(h) * 3600 + int(m) * 60 + float(s)
                logger.info(f"Will filter results starting from {start_seconds} seconds")
            except ValueError:
                logger.warning(f"Could not parse start time '{start_time}', using 0")
                
        if end_time:
            try:
                # Parse the end time to seconds
                h, m, s = end_time.split(':')
                end_seconds = int(h) * 3600 + int(m) * 60 + float(s)
                logger.info(f"Will filter results ending at {end_seconds} seconds")
            except ValueError:
                logger.warning(f"Could not parse end time '{end_time}', using infinity")
            
        # Add audio processing options
        cmd.extend(['-af'])
        
        # Build the filter string
        filter_string = ""
        
        # First add the segment filter if needed
        filter_string += segment_filter
        
        # Then add mono conversion if needed
        if mono:
            filter_string += "pan=mono|c0=0.5*c0+0.5*c1,"
            
        # Add the silencedetect filter
        filter_string += f"silencedetect=noise={noise_threshold}:d={min_duration}"
        cmd.append(filter_string)
        
        # Output to null, we only want the filter output
        cmd.extend(['-f', 'null', '-'])
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        
        # Run the FFmpeg command and capture stderr for silence detection output
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
        
        # Parse the silence detection output
        silence_intervals = []
        
        # Regular expressions to match the silence detection output
        silence_start_pattern = r'silence_start: (\d+\.?\d*)'
        silence_end_pattern = r'silence_end: (\d+\.?\d*) \| silence_duration: (\d+\.?\d*)'
        
        # Find all silence start times
        silence_starts = re.findall(silence_start_pattern, result.stderr)
        
        # Find all silence end times and durations
        silence_ends_durations = re.findall(silence_end_pattern, result.stderr)
        
        # Combine the results into a list of silence intervals
        for i, (end, duration) in enumerate(silence_ends_durations):
            # For the first silence period, the start time might not be detected correctly
            # if the media starts with silence
            start = silence_starts[i] if i < len(silence_starts) else "0.0"
            
            # Convert to float 
            start_time_float = float(start) 
            end_time_float = float(end)
            duration_float = float(duration)
            
            # Filter the results based on the specified time range
            # Only include silence periods that overlap with our requested range
            
            # Skip if silence ends before our start time
            if end_time_float < start_seconds:
                logger.info(f"Skipping silence at {start_time_float}-{end_time_float} as it ends before requested start time {start_seconds}")
                continue
                
            # Skip if silence starts after our end time
            if start_time_float > end_seconds:
                logger.info(f"Skipping silence at {start_time_float}-{end_time_float} as it starts after requested end time {end_seconds}")
                continue
                
            # Format time as HH:MM:SS.mmm
            start_formatted = format_time(start_time_float)
            end_formatted = format_time(end_time_float)
            
            silence_intervals.append({
                "start": start_formatted,
                "end": end_formatted,
                "duration": round(duration_float, 2)
            })
        
        # Clean up the downloaded file
        os.remove(input_filename)
        logger.info(f"Removed local file: {input_filename}")
        
        return silence_intervals
        
    except Exception as e:
        logger.error(f"Silence detection failed: {str(e)}")
        # Make sure to clean up even on error
        if os.path.exists(input_filename):
            os.remove(input_filename)
        raise

def detect_silence_segments(media_url: str, volume_threshold: float = 40.0,
                           use_advanced_vad: bool = True, **kwargs) -> List[Dict[str, Any]]:
    """Enhanced silence detection with automatic method selection.
    
    Args:
        media_url: URL of the media file to analyze
        volume_threshold: Volume threshold for speech detection (0-100)
        use_advanced_vad: Whether to use advanced VAD (True) or legacy FFmpeg (False)
        **kwargs: Additional parameters for the selected method
        
    Returns:
        List of segments (speech segments if VAD, silence segments if legacy)
    """
    if use_advanced_vad:
        try:
            # Use advanced VAD for speech detection
            return detect_speech_segments_vad(
                media_url=media_url,
                volume_threshold=volume_threshold,
                **{k: v for k, v in kwargs.items() if k in [
                    'min_speech_duration', 'speech_padding_ms', 'silence_padding_ms',
                    'frame_duration_ms', 'job_id'
                ]}
            )
        except Exception as e:
            logger.warning(f"Advanced VAD failed: {e}. Falling back to legacy method.")
            # Fall back to legacy method
            pass
    
    # Use legacy FFmpeg silence detection
    return detect_silence(
        media_url=media_url,
        noise_threshold=f"-{100-volume_threshold}dB",  # Convert percentage to dB
        **{k: v for k, v in kwargs.items() if k in [
            'start_time', 'end_time', 'min_duration', 'mono', 'job_id'
        ]}
    )


def analyze_audio_characteristics(media_url: str, job_id: Optional[str] = None) -> Dict[str, Any]:
    """Analyze audio characteristics for optimal processing parameters.
    
    Args:
        media_url: URL of the media file to analyze
        job_id: Unique job identifier
        
    Returns:
        Dictionary containing audio analysis results
    """
    logger.info(f"Analyzing audio characteristics for: {media_url}")
    input_filename = download_file(media_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_analysis"))
    
    try:
        # Load audio
        y, sr = librosa.load(input_filename, sr=None, mono=True)
        
        # Basic characteristics
        duration = len(y) / sr
        rms = np.sqrt(np.mean(y ** 2))
        
        # Dynamic range analysis
        rms_frames = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        rms_db = librosa.amplitude_to_db(rms_frames, ref=np.max)
        
        # Speech characteristics
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        
        # Recommended thresholds
        noise_floor = np.percentile(rms_db[rms_db > -100], 10)
        speech_level = np.percentile(rms_db, 80)
        
        # Calculate recommended volume threshold
        dynamic_range = speech_level - noise_floor
        if dynamic_range > 30:  # High dynamic range
            recommended_threshold = 30
        elif dynamic_range > 20:  # Medium dynamic range
            recommended_threshold = 40
        else:  # Low dynamic range
            recommended_threshold = 50
        
        analysis = {
            "duration": round(duration, 2),
            "sample_rate": sr,
            "rms_level": round(float(rms), 4),
            "noise_floor_db": round(float(noise_floor), 1),
            "speech_level_db": round(float(speech_level), 1),
            "dynamic_range_db": round(float(dynamic_range), 1),
            "zero_crossing_rate": round(float(zero_crossing_rate), 4),
            "spectral_centroid_hz": round(float(spectral_centroid), 1),
            "recommended_volume_threshold": recommended_threshold,
            "audio_quality": "high" if dynamic_range > 25 else "medium" if dynamic_range > 15 else "low"
        }
        
        # Clean up
        os.remove(input_filename)
        logger.info(f"Audio analysis completed: {analysis['audio_quality']} quality, {dynamic_range:.1f}dB range")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Audio analysis failed: {str(e)}")
        if os.path.exists(input_filename):
            os.remove(input_filename)
        raise


def format_time(seconds: float) -> str:
    """
    Format time in seconds to HH:MM:SS.mmm format
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"