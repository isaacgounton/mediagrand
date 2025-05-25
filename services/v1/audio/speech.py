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
import gc
import json
import time
import logging
import tempfile
import warnings
from typing import List, Tuple, Dict, Any
from config import LOCAL_STORAGE_PATH
import ffmpeg
import re
import requests
import edge_tts
import asyncio
import kokoro_onnx
import wget
import nltk
import soundfile as sf

logger = logging.getLogger(__name__)

# Suppress phonemizer warnings that clutter logs
warnings.filterwarnings('ignore', category=UserWarning, module='phonemizer')

# Download kokoro model files if they don't exist
MODEL_PATH = os.path.join(LOCAL_STORAGE_PATH, 'kokoro-v1.0.onnx')
VOICES_PATH = os.path.join(LOCAL_STORAGE_PATH, 'voices-v1.0.bin')

# Download NLTK punkt tokenizer if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
    except Exception as e:
        print(f"Warning: Could not download NLTK punkt: {str(e)}")

def ensure_kokoro_files():
    """Download kokoro model files if they don't exist"""
    if not os.path.exists(MODEL_PATH):
        wget.download(
            "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
            MODEL_PATH
        )
    if not os.path.exists(VOICES_PATH):
        wget.download(
            "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
            VOICES_PATH
        )

async def get_edge_voices():
    """Get list of available Edge TTS voices"""
    voices = await edge_tts.list_voices()
    return [
        {
            'name': voice['ShortName'],
            'gender': voice['Gender'],
            'locale': voice['Locale'],
            'engine': 'edge-tts'
        }
        for voice in voices
    ]

def get_streamlabs_voices():
    """Get list of available Streamlabs Polly voices"""
    VALID_VOICES = [
        "Brian", "Emma", "Russell", "Joey", "Matthew", "Joanna", "Kimberly", 
        "Amy", "Geraint", "Nicole", "Justin", "Ivy", "Kendra", "Salli", "Raveena"
    ]
    return [
        {
            'name': voice,
            'engine': 'streamlabs-polly',
            'locale': 'en-US'
        }
        for voice in VALID_VOICES
    ]

def get_kokoro_voices():
    """Get list of available Kokoro voices"""
    ensure_kokoro_files()
    kokoro = kokoro_onnx.Kokoro(MODEL_PATH, VOICES_PATH)
    voices = kokoro.get_voices()
    return [
        {
            'name': voice,
            'engine': 'kokoro',
            'locale': 'en-US'  # Kokoro currently supports English
        }
        for voice in voices
    ]

async def _list_voices_async():
    """Internal async function to list all available voices"""
    edge_voices = await get_edge_voices()
    streamlabs_voices = get_streamlabs_voices()
    kokoro_voices = get_kokoro_voices()
    return edge_voices + streamlabs_voices + kokoro_voices

def list_voices():
    """List all available voices from all TTS engines"""
    return asyncio.run(_list_voices_async())

def check_ratelimit(response: requests.Response) -> bool:
    """
    Checks if the response is a ratelimit response (status code 429).
    If it is, it sleeps for the time specified in the response's 'X-RateLimit-Reset' header.
    """
    if response.status_code == 429:
        try:
            reset_time = int(response.headers["X-RateLimit-Reset"])
            sleep_duration = reset_time - int(time.time())
            if sleep_duration > 0:
                print(f"Rate limit hit. Sleeping for {sleep_duration} seconds.")
                time.sleep(sleep_duration)
                return False  # Do not retry immediately; wait for the specified time
        except KeyError:
            print("Rate limit hit, but no 'X-RateLimit-Reset' header found.")
            return False
    return True  # Return True if no rate limit, or if we handled the rate limit correctly

def chunk_text_for_tts(text, max_chars):
    # Normalize whitespace
    text = text.replace("\n", " ").strip()

    # Split by paragraphs (if labeled) or just treat as one big paragraph
    paragraphs = re.split(r"(?i)paragraph \d+\.?", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]  # Remove blanks

    all_chunks = []

    for paragraph in paragraphs:
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += sentence + " "
            else:
                all_chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk.strip():
            all_chunks.append(current_chunk.strip())

    return all_chunks

def handle_streamlabs_polly_tts(text, voice, job_id, rate=None, volume=None, pitch=None):
    """
    Generate TTS audio using Streamlabs Polly and save it to LOCAL_STORAGE_PATH.
    Handles long text by chunking and combining audio files using ffmpeg.
    """
    # Define the valid voices inside the function
    # https://lazypy.ro/tts/
    VALID_VOICES = [
        "Brian", "Emma", "Russell", "Joey", "Matthew", "Joanna", "Kimberly", 
        "Amy", "Geraint", "Nicole", "Justin", "Ivy", "Kendra", "Salli", "Raveena"
    ]

    if not voice:
        voice = "Brian"

    # Validate the voice to make sure it's in the valid voices list
    if voice not in VALID_VOICES:
        raise ValueError(f"Invalid voice: {voice}. Valid voices are: {', '.join(VALID_VOICES)}")

    # Chunk the text to avoid exceeding the limit for Streamlabs Polly TTS
    chunks = chunk_text_for_tts(text,550)
    audio_chunk_paths = []

    # Loop through each chunk and request audio from Streamlabs Polly
    for idx, chunk in enumerate(chunks):
        body = {"voice": voice, "text": chunk, "service": "polly"}
        headers = {"Referer": "https://streamlabs.com/"}

        while True:
            response = requests.post("https://streamlabs.com/polly/speak", headers=headers, data=body)

            if check_ratelimit(response):  # If rate limit isn't hit, break out of retry loop
                if response.status_code == 200:  # Success
                    try:
                        # Get the audio URL from the response and download the audio file
                        voice_data = requests.get(response.json()["speak_url"])
                        chunk_filename = f"{job_id}_part_{idx}.mp3"
                        chunk_path = os.path.join(LOCAL_STORAGE_PATH, chunk_filename)

                        # Save the audio to the file system
                        with open(chunk_path, "wb") as f:
                            f.write(voice_data.content)

                        audio_chunk_paths.append(chunk_path)
                        print(f"Chunk {idx} saved successfully.")
                        break  # Break out of the retry loop once successful
                    except (KeyError, requests.exceptions.JSONDecodeError):
                        print(f"Error occurred while downloading audio for chunk {idx}")
                        return None
                else:
                    print(f"Error {response.status_code} occurred for chunk {idx}.")
                    return None
            else:
                print(f"Rate limit hit for chunk {idx}, retrying...")

    # Combine all the audio chunks into one file using ffmpeg
    if not audio_chunk_paths:
        print("No audio files were generated.")
        return None

    output_filename = f"{job_id}.mp3"
    output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)

    try:
        # Create the concat list for ffmpeg
        concat_file_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_concat_list.txt")
        with open(concat_file_path, 'w') as concat_file:
            for path in audio_chunk_paths:
                concat_file.write(f"file '{os.path.abspath(path)}'\n")

        # Concatenate the audio files using ffmpeg
        ffmpeg.input(concat_file_path, format='concat', safe=0).output(output_path, c='copy').run(overwrite_output=True)

        # Clean up chunk files and concat file
        for path in audio_chunk_paths:
            os.remove(path)
        os.remove(concat_file_path)

        print(f"Audio combination successful: {output_path}")

        # Ensure the final output file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} does not exist after combination.")

        return output_path
    except Exception as e:
        print(f"Audio combination failed: {str(e)}")
        raise

def handle_edge_tts(text, voice, job_id, rate=None, volume=None, pitch=None):
    """
    Generate TTS audio using edge-tts, upload to cloud, and return the cloud URL.
    """
    speed=1.0
    format="mp3"

    async def _generate_tts_async(text, voice, output_path, rate="+0%", format="mp3"):
        # Fetch available voices
        voices = await edge_tts.list_voices()
        valid_voices = {v["ShortName"] for v in voices}
        # Default or validate voice
        if not voice:
            voice = "en-US-AvaNeural"
        elif voice not in valid_voices:
            raise ValueError(
                f"Invalid voice: {voice}.\n"
                f"You can preview voice samples at: https://tts.travisvn.com/\n\n"
                f"Available voices are:\n" + ", ".join(sorted(valid_voices))
            )
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_path)

    # Prepare output path
    output_filename = f"{job_id}.{format}"
    output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)

    # Convert speed to edge-tts rate string
    rate_percent = int((speed - 1.0) * 100)
    rate_str = f"{rate_percent:+d}%"

    # Run edge-tts asynchronously
    asyncio.run(_generate_tts_async(text, voice, output_path, rate=rate_str, format=format))

    return output_path

def handle_kokoro_tts(text, voice, job_id, rate=None, volume=None, pitch=None):
    """
    Generate TTS audio using kokoro-onnx and save it to LOCAL_STORAGE_PATH.
    Uses Kokoro-82M model with ONNX runtime.

    Parameters:
        text (str): Text to convert to speech
        voice (str): Voice ID to use
        job_id (str): Unique job identifier
        rate (float): Speech speed multiplier (1.0 is normal speed)
        volume (float): Audio volume (not implemented)
        pitch (str): Pitch adjustment (not implemented)
    """
    ensure_kokoro_files()  # Ensure model files are downloaded
    timestamps_file = None

    try:
        # Initialize Kokoro with model files
        kokoro = kokoro_onnx.Kokoro(MODEL_PATH, VOICES_PATH)
        
        # Get available voices if none specified
        if not voice:
            voice = "af_sarah"  # Default voice (English)
        
        # Create options dictionary for kokoro.create()
        options = {
            'voice': voice,
            'lang': 'en-us'
        }

        # Add speed if specified (default is 1.0)
        if rate is not None:
            try:
                speed = float(rate)
                if 0.5 <= speed <= 2.0:  # Reasonable speed range
                    options['speed'] = speed
            except (ValueError, TypeError):
                pass  # Invalid speed value, use default

        # Generate audio (returns numpy array and sample rate)
        # Note: Kokoro ONNX doesn't support word-level timestamps yet
        samples, sr = kokoro.create(text, **options)
        timestamps = None
        # Prepare output paths
        output_filename = f"{job_id}.wav"
        wav_output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)
        timestamps_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_timestamps.json")
        
        # Ensure the target directory exists
        os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)

        # Save audio using soundfile to WAV
        sf.write(wav_output_path, samples, sr)

        # Since Kokoro ONNX doesn't provide timestamps, we estimate basic timing
        # by dividing total duration by word count for basic subtitle support
        try:
            words = nltk.word_tokenize(text)
            duration = len(samples) / sr  # Duration in seconds
            word_duration = duration / len(words)
            
            # Create estimated timestamps
            timestamps = []
            current_time = 0
            for word in words:
                timestamps.append({
                    'word': word,
                    'start': current_time,
                    'end': current_time + word_duration
                })
                current_time += word_duration
                
            # Save estimated timestamps
            with open(timestamps_path, 'w') as f:
                json.dump(timestamps, f)
            timestamps_file = timestamps_path
        except Exception as e:
            print(f"Error generating estimated timestamps: {str(e)}")
            timestamps_file = None
        
        return wav_output_path, timestamps_file

    except Exception as e:
        print(f"Error generating audio with Kokoro: {str(e)}")
        raise

TTS_HANDLERS = {
    'edge-tts': handle_edge_tts,
    'streamlabs-polly': handle_streamlabs_polly_tts,
    'kokoro': handle_kokoro_tts
}

class OptimizedTTSProcessor:
    """
    Optimized TTS processor that handles extremely long texts by intelligently 
    chunking them and managing memory usage.
    """
    
    def __init__(self, max_chunk_chars: int = 1000, max_memory_mb: int = 8192):
        """
        Initialize the optimized TTS processor.
        
        Args:
            max_chunk_chars: Maximum characters per chunk for TTS processing
            max_memory_mb: Maximum memory usage threshold in MB
        """
        self.max_chunk_chars = max_chunk_chars
        self.max_memory_mb = max_memory_mb
        self.temp_files = []  # Track temporary files for cleanup
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        
    def cleanup(self):
        """Clean up temporary files and memory."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Could not clean up temp file {temp_file}: {e}")
        self.temp_files.clear()
        gc.collect()  # Force garbage collection
        
    def intelligent_text_chunking(self, text: str, max_chars: int = None) -> List[str]:
        """
        Intelligently chunk text at natural break points.
        
        Args:
            text: Input text to chunk
            max_chars: Maximum characters per chunk (defaults to instance setting)
            
        Returns:
            List of text chunks
        """
        if max_chars is None:
            max_chars = self.max_chunk_chars
            
        if len(text) <= max_chars:
            return [text]
            
        chunks = []
        current_chunk = ""
        
        # Split into sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        for sentence in sentences:
            # If a single sentence is too long, split it further
            if len(sentence) > max_chars:
                # Split at commas or other natural break points
                sub_parts = re.split(r'(?<=[,;:])\s+', sentence)
                for part in sub_parts:
                    if len(current_chunk) + len(part) + 1 <= max_chars:
                        current_chunk += part + " "
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = part + " "
            else:
                # Check if adding this sentence would exceed limit
                if len(current_chunk) + len(sentence) + 1 <= max_chars:
                    current_chunk += sentence + " "
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + " "
        
        # Add the last chunk if it exists
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        logger.info(f"Split {len(text)} characters into {len(chunks)} chunks")
        return chunks
        
    def process_kokoro_chunk(self, text: str, voice: str, chunk_id: str, rate: float = None) -> Tuple[str, List[Dict]]:
        """
        Process a single text chunk with Kokoro TTS with memory optimization.
        
        Args:
            text: Text chunk to process
            voice: Voice to use
            chunk_id: Unique identifier for this chunk
            rate: Speech rate
            
        Returns:
            Tuple of (audio_file_path, timestamps)
        """
        try:
            ensure_kokoro_files()
            
            # Import here to avoid keeping models in memory when not needed
            import kokoro_onnx
            import soundfile as sf
            
            # Initialize Kokoro
            MODEL_PATH = os.path.join(LOCAL_STORAGE_PATH, 'kokoro-v1.0.onnx')
            VOICES_PATH = os.path.join(LOCAL_STORAGE_PATH, 'voices-v1.0.bin')
            
            kokoro = kokoro_onnx.Kokoro(MODEL_PATH, VOICES_PATH)
            
            # Create options
            options = {
                'voice': voice or 'af_sarah',
                'lang': 'en-us'
            }
            if rate is not None:
                options['speed'] = max(0.5, min(2.0, float(rate)))
                
            # Generate audio
            logger.info(f"Processing chunk {chunk_id} with {len(text)} characters")
            samples, sr = kokoro.create(text, **options)            # Save audio
            output_path = os.path.join(LOCAL_STORAGE_PATH, f"{chunk_id}.wav")
            sf.write(output_path, samples, sr)
            self.temp_files.append(output_path)
            
            # Generate basic timestamps (estimated)
            try:
                import nltk
                
                # Check if punkt tokenizer is available
                punkt_available = False
                try:
                    nltk.data.find('tokenizers/punkt')
                    punkt_available = True
                except LookupError:
                    # Try to download punkt tokenizer
                    try:
                        logger.info(f"Downloading NLTK punkt tokenizer for chunk {chunk_id}")
                        nltk.download('punkt', quiet=True)
                        punkt_available = True
                    except Exception as download_error:
                        logger.warning(f"Could not download NLTK punkt for chunk {chunk_id}: {download_error}")
                        punkt_available = False
                
                if punkt_available:
                    # Use NLTK tokenization
                    words = nltk.word_tokenize(text)
                else:
                    # Fallback to simple whitespace tokenization
                    logger.info(f"Using fallback tokenization for chunk {chunk_id}")
                    words = text.split()
                
                duration = len(samples) / sr
                word_duration = duration / len(words) if words else 1.0
                
                timestamps = []
                current_time = 0
                for word in words:
                    timestamps.append({
                        'word': word,
                        'start': current_time,
                        'end': current_time + word_duration
                    })
                    current_time += word_duration
                    
            except ImportError as e:
                logger.warning(f"NLTK not available for chunk {chunk_id}: {e}. Using simple tokenization.")
                # Fallback to simple word splitting
                words = text.split()
                duration = len(samples) / sr
                word_duration = duration / len(words) if words else 1.0
                
                timestamps = []
                current_time = 0
                for word in words:
                    timestamps.append({
                        'word': word,
                        'start': current_time,
                        'end': current_time + word_duration
                    })
                    current_time += word_duration
                    
            except Exception as e:
                logger.warning(f"Could not generate timestamps for chunk {chunk_id}: {e}")
                timestamps = []
            
            # Clean up memory immediately
            del kokoro
            del samples
            gc.collect()
            
            return output_path, timestamps
            
        except Exception as e:
            logger.error(f"Error processing Kokoro chunk {chunk_id}: {e}")
            raise
            
    def combine_audio_chunks(self, chunk_paths: List[str], output_path: str) -> str:
        """
        Combine multiple audio chunks into a single file using FFmpeg.
        
        Args:
            chunk_paths: List of audio file paths to combine
            output_path: Output file path
            
        Returns:
            Path to combined audio file
        """
        if not chunk_paths:
            raise ValueError("No audio chunks to combine")
            
        if len(chunk_paths) == 1:
            # Just copy the single file
            import shutil
            shutil.copy2(chunk_paths[0], output_path)
            return output_path
            
        try:
            # Create concat file for ffmpeg
            concat_file_path = os.path.join(LOCAL_STORAGE_PATH, f"concat_{int(time.time())}.txt")
            with open(concat_file_path, 'w') as f:
                for path in chunk_paths:
                    f.write(f"file '{os.path.abspath(path)}'\n")
            
            self.temp_files.append(concat_file_path)
            
            # Combine using ffmpeg
            (
                ffmpeg
                .input(concat_file_path, format='concat', safe=0)
                .output(output_path, acodec='copy')
                .run(overwrite_output=True, quiet=True)
            )
            
            logger.info(f"Successfully combined {len(chunk_paths)} audio chunks")
            return output_path
            
        except Exception as e:
            logger.error(f"Error combining audio chunks: {e}")
            raise
            
    def combine_timestamps(self, chunk_timestamps: List[List[Dict]], chunk_durations: List[float]) -> List[Dict]:
        """
        Combine timestamps from multiple chunks, adjusting timing offsets.
        
        Args:
            chunk_timestamps: List of timestamp lists from each chunk
            chunk_durations: Duration of each audio chunk
            
        Returns:
            Combined timestamps list
        """
        combined_timestamps = []
        time_offset = 0
        
        for i, (timestamps, duration) in enumerate(zip(chunk_timestamps, chunk_durations)):
            for timestamp in timestamps:
                combined_timestamps.append({
                    'word': timestamp['word'],
                    'start': timestamp['start'] + time_offset,
                    'end': timestamp['end'] + time_offset
                })
            time_offset += duration
            
        return combined_timestamps
        
    def generate_subtitles(self, timestamps: List[Dict], output_path: str, format: str = "srt") -> str:
        """
        Generate subtitle file from timestamps.
        
        Args:
            timestamps: List of timestamp dictionaries
            output_path: Output subtitle file path
            format: Subtitle format ('srt' or 'vtt')
            
        Returns:
            Path to subtitle file
        """
        if not timestamps:
            # Create basic subtitle without timestamps
            with open(output_path, 'w', encoding='utf-8') as f:
                if format.lower() == "vtt":
                    f.write("WEBVTT\n\n1\n00:00:00.000 --> 00:00:10.000\n[Generated Audio]\n\n")
                else:
                    f.write("1\n00:00:00,000 --> 00:00:10,000\n[Generated Audio]\n\n")
            return output_path
            
        # Group words into phrases (5-7 words per subtitle)
        phrases = []
        current_phrase = []
        current_start = None
        
        for timestamp in timestamps:
            word = timestamp.get('word', '')
            start_time = timestamp.get('start', 0)
            end_time = timestamp.get('end', start_time + 0.5)
            
            if not current_start:
                current_start = start_time
                
            current_phrase.append(word)
            
            # Create new phrase after 5-7 words or on punctuation
            if len(current_phrase) >= 7 or (word and word.rstrip()[-1:] in '.!?'):
                phrases.append({
                    'text': ' '.join(current_phrase),
                    'start': current_start,
                    'end': end_time
                })
                current_phrase = []
                current_start = None
                
        # Add remaining words
        if current_phrase:
            phrases.append({
                'text': ' '.join(current_phrase),
                'start': current_start or 0,
                'end': timestamps[-1].get('end', current_start + 2) if timestamps else 2
            })
            
        # Write subtitle file
        with open(output_path, 'w', encoding='utf-8') as f:
            if format.lower() == "vtt":
                f.write("WEBVTT\n\n")
                for i, phrase in enumerate(phrases, 1):
                    start_time = phrase['start']
                    end_time = phrase['end']
                    
                    start_hrs = int(start_time // 3600)
                    start_mins = int((start_time % 3600) // 60)
                    start_secs = int(start_time % 60)
                    start_ms = int((start_time % 1) * 1000)
                    
                    end_hrs = int(end_time // 3600)
                    end_mins = int((end_time % 3600) // 60)
                    end_secs = int(end_time % 60)
                    end_ms = int((end_time % 1) * 1000)
                    
                    start_str = f"{start_hrs:02d}:{start_mins:02d}:{start_secs:02d}.{start_ms:03d}"
                    end_str = f"{end_hrs:02d}:{end_mins:02d}:{end_secs:02d}.{end_ms:03d}"
                    
                    f.write(f"{i}\n{start_str} --> {end_str}\n{phrase['text']}\n\n")
            else:
                # SRT format
                for i, phrase in enumerate(phrases, 1):
                    start_time = phrase['start']
                    end_time = phrase['end']
                    
                    start_hrs = int(start_time // 3600)
                    start_mins = int((start_time % 3600) // 60)
                    start_secs = int(start_time % 60)
                    start_ms = int((start_time % 1) * 1000)
                    
                    end_hrs = int(end_time // 3600)
                    end_mins = int((end_time % 3600) // 60)
                    end_secs = int(end_time % 60)
                    end_ms = int((end_time % 1) * 1000)
                    
                    start_str = f"{start_hrs:02d}:{start_mins:02d}:{start_secs:02d},{start_ms:03d}"
                    end_str = f"{end_hrs:02d}:{end_mins:02d}:{end_secs:02d},{end_ms:03d}"
                    
                    f.write(f"{i}\n{start_str} --> {end_str}\n{phrase['text']}\n\n")
                    
        return output_path

def generate_tts_optimized(tts: str, text: str, voice: str, job_id: str,
                          output_format: str = "mp3",
                          rate: str = None, volume: float = None, pitch: str = None,
                          subtitle_format: str = "srt",
                          max_chunk_chars: int = 1000) -> Tuple[str, str]:
    """
    Optimized TTS generation that handles extremely long texts efficiently.
    
    Args:
        tts: TTS engine ('kokoro', 'edge-tts', 'streamlabs-polly')
        text: Text to convert to speech
        voice: Voice to use
        job_id: Unique job identifier
        output_format: Output audio format
        rate: Speech rate
        volume: Audio volume
        pitch: Pitch adjustment
        subtitle_format: Subtitle format
        max_chunk_chars: Maximum characters per chunk
        
    Returns:
        Tuple of (audio_file_path, subtitle_file_path)
    """
    logger.info(f"Starting optimized TTS generation for {len(text)} characters")
    
    # For short texts, use original implementation
    if len(text) <= max_chunk_chars:
        logger.info("Text is short enough, using original TTS implementation")
        from services.v1.audio.speech import generate_tts
        return generate_tts(tts, text, voice, job_id, output_format, rate, volume, pitch, subtitle_format)
    
    # For long texts, use optimized chunked processing
    with OptimizedTTSProcessor(max_chunk_chars=max_chunk_chars) as processor:
        
        if tts == 'kokoro':
            # Use optimized Kokoro processing for long texts
            chunks = processor.intelligent_text_chunking(text, max_chunk_chars)
            logger.info(f"Processing {len(chunks)} chunks with Kokoro TTS")
            
            chunk_paths = []
            chunk_timestamps = []
            chunk_durations = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{job_id}_chunk_{i}"
                try:
                    audio_path, timestamps = processor.process_kokoro_chunk(
                        chunk, voice, chunk_id, float(rate) if rate else None
                    )
                    chunk_paths.append(audio_path)
                    chunk_timestamps.append(timestamps)
                    
                    # Get duration from audio file
                    try:
                        import soundfile as sf
                        data, sr = sf.read(audio_path)
                        duration = len(data) / sr
                        chunk_durations.append(duration)
                    except Exception:
                        # Fallback duration estimation
                        duration = len(chunk) * 0.05  # Rough estimate
                        chunk_durations.append(duration)
                        
                    logger.info(f"Completed chunk {i+1}/{len(chunks)}")
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {i}: {e}")
                    raise
            
            # Combine audio chunks
            final_audio_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.wav")
            processor.combine_audio_chunks(chunk_paths, final_audio_path)
            
            # Convert to MP3 if requested
            if output_format.lower() == 'mp3':
                mp3_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.mp3")
                try:
                    (
                        ffmpeg
                        .input(final_audio_path)
                        .output(mp3_path, acodec='libmp3lame', **{'q:a': 2})
                        .run(overwrite_output=True, quiet=True)
                    )
                    final_audio_path = mp3_path
                except Exception as e:
                    logger.warning(f"Could not convert to MP3: {e}")
            
            # Combine timestamps and generate subtitles
            all_timestamps = processor.combine_timestamps(chunk_timestamps, chunk_durations)
            subtitle_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.{subtitle_format}")
            processor.generate_subtitles(all_timestamps, subtitle_path, subtitle_format)
            
            return final_audio_path, subtitle_path
            
        else:
            # For Edge TTS and Streamlabs, use chunked approach with original handlers
            chunks = processor.intelligent_text_chunking(text, max_chunk_chars)
            logger.info(f"Processing {len(chunks)} chunks with {tts}")
            
            chunk_paths = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{job_id}_chunk_{i}"
                
                if tts == 'edge-tts':
                    audio_path = handle_edge_tts(chunk, voice, chunk_id, rate, volume, pitch)
                elif tts == 'streamlabs-polly':
                    audio_path = handle_streamlabs_polly_tts(chunk, voice, chunk_id, rate, volume, pitch)
                else:
                    raise ValueError(f"Unsupported TTS engine: {tts}")
                    
                chunk_paths.append(audio_path)
                processor.temp_files.append(audio_path)
                logger.info(f"Completed chunk {i+1}/{len(chunks)}")
            
            # Combine chunks
            final_audio_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.mp3")
            processor.combine_audio_chunks(chunk_paths, final_audio_path)
            
            # Generate basic subtitle
            subtitle_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.{subtitle_format}")
            processor.generate_subtitles([], subtitle_path, subtitle_format)
            
            return final_audio_path, subtitle_path

def generate_tts(tts: str, text: str, voice: str, job_id: str,
                 output_format: str = "mp3",
                 rate: str = None, volume: float = None, pitch: str = None,
                 subtitle_format: str = "srt"):
    """
    Generate TTS audio and subtitle files using the specified tts.
    This function provides backward compatibility with the original speech.py interface.
    
    For short texts (< 2000 chars), uses the original handlers directly.
    For long texts, automatically uses the optimized chunking approach.
    
    Parameters:
        tts (str): TTS engine to use ('edge-tts', 'streamlabs-polly', or 'kokoro')
        text (str): Text to convert to speech
        voice (str): Voice ID to use
        job_id (str): Unique job identifier
        output_format (str): Output audio format ('mp3' or 'wav')
        rate (str): Speech speed adjustment
        volume (float): Audio volume
        pitch (str): Pitch adjustment
        subtitle_format (str): Format for subtitle file ('srt' or 'vtt')
    
    Returns:
        tuple: (audio_file_path, subtitle_file_path)
        The subtitle file will include accurate timestamps if the TTS engine supports them.
    """
    if tts not in TTS_HANDLERS:
        raise ValueError(f"Unsupported tts: {tts}")

    # For short texts, use original approach for best compatibility
    if len(text) < 2000:
        # Generate audio file using the appropriate handler
        result = TTS_HANDLERS[tts](text, voice, job_id, rate, volume, pitch)
        
        if isinstance(result, tuple):
            raw_audio_file_path, timestamps_file = result
        else:
            raw_audio_file_path = result
            timestamps_file = None
        
        final_audio_file_path = raw_audio_file_path

        if tts == 'kokoro':
            # Kokoro handler now returns a .wav file path: /tmp/{job_id}.wav
            if output_format.lower() == 'mp3':
                wav_path = raw_audio_file_path
                # Ensure wav_path ends with .wav before trying to replace extension
                if isinstance(wav_path, str) and wav_path.lower().endswith(".wav"):
                    mp3_path = os.path.splitext(wav_path)[0] + ".mp3"
                else: # Should not happen if kokoro handler is correct and returns a string path
                    print(f"Warning: Kokoro handler returned unexpected path for WAV: {wav_path}. Attempting MP3 conversion with default naming.")
                    mp3_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.mp3")

                try:
                    (
                        ffmpeg
                        .input(wav_path)
                        .output(mp3_path, acodec='libmp3lame', **{'q:a': 2})
                        .run(cmd=['ffmpeg', '-nostdin'], overwrite_output=True, quiet=True)
                    )
                    # Cleanup original WAV if conversion was successful and paths are different
                    if os.path.exists(wav_path) and wav_path != mp3_path and os.path.exists(mp3_path):
                        os.remove(wav_path)
                    final_audio_file_path = mp3_path
                except ffmpeg.Error as e:
                    # Use print as logger might not be configured when this module is imported/used standalone
                    print(f"FFmpeg error during WAV to MP3 conversion in generate_tts for job {job_id}: {e.stderr.decode('utf8') if e.stderr else str(e)}")
                    # Fallback to returning WAV path if conversion fails
                    final_audio_file_path = wav_path 
            elif output_format.lower() == 'wav':
                final_audio_file_path = raw_audio_file_path # Already WAV
            else:
                raise ValueError(f"Unsupported output_format '{output_format}' for Kokoro TTS. Choose 'mp3' or 'wav'.")
        
        # For other TTS engines (edge-tts, streamlabs-polly), they already output MP3.
        # The output_format parameter is primarily for Kokoro.
        # If they were to support WAV, similar logic would be needed here.
        # If output_format is 'wav' for an mp3-only engine, we currently just return the mp3.
        elif output_format.lower() == 'wav' and final_audio_file_path.lower().endswith('.mp3'):
            print(f"Warning: Requested 'wav' output for TTS engine '{tts}' which produces MP3. Returning MP3 path: {final_audio_file_path}")

        # Generate subtitle file with timestamps if available
        subtitle_file = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.srt")
        
        if timestamps_file and os.path.exists(timestamps_file):
            try:
                with open(timestamps_file, 'r') as f:
                    timestamps = json.load(f)
                
                # Group words into phrases (roughly 5-7 words per subtitle)
                phrases = []
                current_phrase = []
                current_start = None
                
                for segment in timestamps:
                    word = segment.get('word', '')
                    start_time = segment.get('start', 0)
                    end_time = segment.get('end', start_time + 0.5)
                    
                    if not current_start:
                        current_start = start_time
                    
                    current_phrase.append(word)
                    
                    # Create a new phrase after 5-7 words or on punctuation
                    if len(current_phrase) >= 7 or word.rstrip()[-1] in '.!?':
                        phrases.append({
                            'text': ' '.join(current_phrase),
                            'start': current_start,
                            'end': end_time
                        })
                        current_phrase = []
                        current_start = None
                
                # Add any remaining words
                if current_phrase:
                    phrases.append({
                        'text': ' '.join(current_phrase),
                        'start': current_start or 0,
                        'end': timestamps[-1].get('end', current_start + 2)
                    })
                
                # Write phrases as subtitles in requested format
                if subtitle_format.lower() == "vtt":
                    # WebVTT format
                    subtitle_file = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.vtt")
                    with open(subtitle_file, 'w', encoding='utf-8') as f:
                        f.write("WEBVTT\n\n")
                        for i, phrase in enumerate(phrases, 1):
                            # Convert times to VTT format (HH:MM:SS.mmm)
                            # Convert seconds to timestamp (WebVTT format)
                            start_hrs = int(phrase['start'] // 3600)
                            start_mins = int((phrase['start'] % 3600) // 60)
                            start_secs = int(phrase['start'] % 60)
                            start_ms = int((phrase['start'] % 1) * 1000)
                            
                            end_hrs = int(phrase['end'] // 3600)
                            end_mins = int((phrase['end'] % 3600) // 60)
                            end_secs = int(phrase['end'] % 60)
                            end_ms = int((phrase['end'] % 1) * 1000)
                            
                            start_str = f"{start_hrs:02d}:{start_mins:02d}:{start_secs:02d}.{start_ms:03d}"
                            end_str = f"{end_hrs:02d}:{end_mins:02d}:{end_secs:02d}.{end_ms:03d}"
                            
                            f.write(f"{i}\n")
                            f.write(f"{start_str} --> {end_str}\n")
                            f.write(f"{phrase['text']}\n\n")
                else:
                    # SRT format
                    subtitle_file = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.srt")
                    with open(subtitle_file, 'w', encoding='utf-8') as f:
                        for i, phrase in enumerate(phrases, 1):
                            # Convert times to SRT format (HH:MM:SS,mmm)
                            start_hrs = int(phrase['start'] // 3600)
                            start_mins = int((phrase['start'] % 3600) // 60)
                            start_secs = int(phrase['start'] % 60)
                            start_ms = int((phrase['start'] % 1) * 1000)
                            
                            end_hrs = int(phrase['end'] // 3600)
                            end_mins = int((phrase['end'] % 3600) // 60)
                            end_secs = int(phrase['end'] % 60)
                            end_ms = int((phrase['end'] % 1) * 1000)
                            
                            start_str = f"{start_hrs:02d}:{start_mins:02d}:{start_secs:02d},{start_ms:03d}"
                            end_str = f"{end_hrs:02d}:{end_mins:02d}:{end_secs:02d},{end_ms:03d}"
                            
                            f.write(f"{i}\n")
                            f.write(f"{start_str} --> {end_str}\n")
                            f.write(f"{phrase['text']}\n\n")
                
                # Clean up timestamps file
                os.remove(timestamps_file)
            except Exception as e:
                print(f"Error processing timestamps: {str(e)}")
                # Fall back to basic subtitle generation
                with open(subtitle_file, 'w', encoding='utf-8') as f:
                    # Write basic subtitle in selected format
                    if subtitle_format.lower() == "vtt":
                        subtitle_file = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.vtt")
                        with open(subtitle_file, 'w', encoding='utf-8') as f:
                            f.write("WEBVTT\n\n")
                            f.write("1\n")
                            f.write("00:00:00.000 --> 00:00:10.000\n")
                            f.write(text + "\n\n")
                    else:
                        subtitle_file = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.srt")
                        with open(subtitle_file, 'w', encoding='utf-8') as f:
                            f.write("1\n")
                            f.write("00:00:00,000 --> 00:00:10,000\n")
                            f.write(text + "\n\n")
        else:
            # Generate segmented subtitles without timestamps
            _generate_segmented_subtitles(text, subtitle_file, subtitle_format)
        
        return final_audio_file_path, subtitle_file
    
    else:
        # For long texts, use the optimized approach
        return generate_tts_optimized(tts, text, voice, job_id, output_format, rate, volume, pitch, subtitle_format)

def _generate_segmented_subtitles(text: str, subtitle_file: str, subtitle_format: str = "srt"):
    """
    Generate segmented subtitles by breaking text into logical chunks.
    This creates a better subtitle experience when precise timestamps aren't available.
    """
    import re
    
    # Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    # Group sentences into subtitle chunks (3-4 sentences or ~100-150 chars per subtitle)
    subtitle_chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If adding this sentence would make chunk too long, start new chunk
        if (len(current_chunk) >= 3 or 
            current_length + len(sentence) > 150) and current_chunk:
            subtitle_chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_length = len(sentence)
        else:
            current_chunk.append(sentence)
            current_length += len(sentence) + 1  # +1 for space
    
    # Add remaining chunk
    if current_chunk:
        subtitle_chunks.append(' '.join(current_chunk))
    
    # If no sentences were found, split by words as fallback
    if not subtitle_chunks:
        words = text.split()
        words_per_chunk = max(5, min(15, len(words) // 10))  # 5-15 words per subtitle
        for i in range(0, len(words), words_per_chunk):
            chunk = ' '.join(words[i:i + words_per_chunk])
            subtitle_chunks.append(chunk)
    
    # Generate subtitle file with estimated timing (5 seconds per chunk)
    with open(subtitle_file, 'w', encoding='utf-8') as f:
        if subtitle_format.lower() == "vtt":
            f.write("WEBVTT\n\n")
            for i, chunk in enumerate(subtitle_chunks, 1):
                start_time = (i - 1) * 5
                end_time = i * 5
                
                start_hrs = start_time // 3600
                start_mins = (start_time % 3600) // 60
                start_secs = start_time % 60
                
                end_hrs = end_time // 3600
                end_mins = (end_time % 3600) // 60
                end_secs = end_time % 60
                
                start_str = f"{start_hrs:02d}:{start_mins:02d}:{start_secs:02d}.000"
                end_str = f"{end_hrs:02d}:{end_mins:02d}:{end_secs:02d}.000"
                
                f.write(f"{i}\n{start_str} --> {end_str}\n{chunk}\n\n")
        else:
            # SRT format
            for i, chunk in enumerate(subtitle_chunks, 1):
                start_time = (i - 1) * 5
                end_time = i * 5
                
                start_hrs = start_time // 3600
                start_mins = (start_time % 3600) // 60
                start_secs = start_time % 60
                
                end_hrs = end_time // 3600
                end_mins = (end_time % 3600) // 60
                end_secs = end_time % 60
                
                start_str = f"{start_hrs:02d}:{start_mins:02d}:{start_secs:02d},000"
                end_str = f"{end_hrs:02d}:{end_mins:02d}:{end_secs:02d},000"
                
                f.write(f"{i}\n{start_str} --> {end_str}\n{chunk}\n\n")
