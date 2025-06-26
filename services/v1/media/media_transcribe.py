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
from config import LOCAL_STORAGE_PATH

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def process_transcribe_media(media_source, task, include_text, include_srt, include_segments, word_timestamps, response_type, language, job_id, words_per_line=None):
    """Transcribe or translate media and return the transcript/translation, SRT or VTT file path.
    
    Args:
        media_source: Either a URL string or a local file path
    """
    
    # Check if media_source is a local file path or a URL
    if os.path.exists(media_source):
        # It's a local file path (uploaded file)
        logger.info(f"Starting {task} for uploaded file: {media_source}")
        input_filename = media_source
        should_cleanup_input = False  # Don't delete the uploaded file here, it's handled in the route
    else:
        # It's a URL, download it
        logger.info(f"Starting {task} for media URL: {media_source}")
        input_filename = download_file(media_source, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_input"))
        logger.info(f"Downloaded media to local file: {input_filename}")
        should_cleanup_input = True  # We should clean up downloaded files

    try:
        # Use base model as preferred
        model_size = "base"
        model = whisper.load_model(model_size)
        logger.info(f"Using Whisper model: {model_size}")

        # Enhanced options for better non-English accuracy
        options = {
            "task": task,
            "word_timestamps": word_timestamps,
            "verbose": False,
            "temperature": 0.0,  # Reduce hallucinations
            "compression_ratio_threshold": 2.4,  # Detect repetition
            "logprob_threshold": -1.0,  # Quality threshold
            "no_speech_threshold": 0.6,  # Silence detection
        }

        # Enhanced language handling for better non-English support
        if language:
            options["language"] = language
            logger.info(f"Language specified: {language}")
        # No else needed, Whisper will auto-detect if not set

        # For larger models, use additional parameters for better quality
        if model_size in ["large", "large-v2", "large-v3"]:
            options.update({
                "best_of": 5,        # Multiple attempts for better accuracy
                "beam_size": 5,      # Beam search for better results
                "patience": 1.0,     # Wait for better alternatives
                "length_penalty": 1.0,
                "suppress_tokens": "-1",  # Suppress less likely tokens
            })
            logger.info("Using enhanced accuracy settings for large model")
        else:
            logger.info("Using base model with standard settings")

        result = model.transcribe(input_filename, **options)
        
        # Log detected language for debugging
        if "language" in result:
            detected_lang = result["language"]
            logger.info(f"Detected language: {detected_lang}")
        
        # For translation task, the result['text'] will be in English
        text = None
        srt_text = None
        segments_json = None

        logger.info(f"Generated {task} output")

        if include_text is True:
            text = result['text']

        if include_srt is True:
            srt_subtitles = []
            subtitle_index = 1
            
            if words_per_line and words_per_line > 0:
                # Collect all words and their timings
                all_words = []
                word_timings = []
                
                for segment in result['segments']:
                    words = segment['text'].strip().split()
                    segment_start = segment['start']
                    segment_end = segment['end']
                    
                    # Calculate timing for each word
                    if words:
                        duration_per_word = (segment_end - segment_start) / len(words)
                        for i, word in enumerate(words):
                            word_start = segment_start + (i * duration_per_word)
                            word_end = word_start + duration_per_word
                            all_words.append(word)
                            word_timings.append((word_start, word_end))
                
                # Process words in chunks of words_per_line
                current_word = 0
                while current_word < len(all_words):
                    # Get the next chunk of words
                    chunk = all_words[current_word:current_word + words_per_line]
                    
                    # Calculate timing for this chunk
                    chunk_start = word_timings[current_word][0]
                    chunk_end = word_timings[min(current_word + len(chunk) - 1, len(word_timings) - 1)][1]
                    
                    # Create the subtitle
                    srt_subtitles.append(srt.Subtitle(
                        subtitle_index,
                        timedelta(seconds=chunk_start),
                        timedelta(seconds=chunk_end),
                        ' '.join(chunk)
                    ))
                    subtitle_index += 1
                    current_word += words_per_line
            else:
                # Original behavior - one subtitle per segment
                for segment in result['segments']:
                    start = timedelta(seconds=segment['start'])
                    end = timedelta(seconds=segment['end'])
                    segment_text = segment['text'].strip()
                    srt_subtitles.append(srt.Subtitle(subtitle_index, start, end, segment_text))
                    subtitle_index += 1
            
            srt_text = srt.compose(srt_subtitles)

        if include_segments is True:
            segments_json = result['segments']

        if should_cleanup_input:
            os.remove(input_filename)
            logger.info(f"Removed local file: {input_filename}")
        logger.info(f"{task.capitalize()} successful, output type: {response_type}")

        if response_type == "direct":
            return text, srt_text, segments_json
        else:
            
            text_filename = None
            srt_filename = None
            segments_filename = None
            
            if include_text is True and text is not None:
                text_filename = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.txt")
                with open(text_filename, 'w') as f:
                    f.write(text)
            
            if include_srt is True and srt_text is not None:
                srt_filename = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.srt")
                with open(srt_filename, 'w') as f:
                    f.write(srt_text)

            if include_segments is True and segments_json is not None:
                segments_filename = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.json")
                with open(segments_filename, 'w') as f:
                    f.write(str(segments_json))

            return text_filename, srt_filename, segments_filename

    except Exception as e:
        logger.error(f"{task.capitalize()} failed: {str(e)}")
        raise
