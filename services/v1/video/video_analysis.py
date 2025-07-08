import os
import logging
import tempfile
import json
import re
from typing import List, Dict, Tuple, Optional
from collections import Counter

# Import optional dependencies with fallbacks
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    from moviepy.editor import VideoFileClip
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False
    VideoFileClip = None

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    librosa = None

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    cv2 = None

logger = logging.getLogger(__name__)

class VideoAnalyzer:
    """
    Analyzes video content to identify interesting segments for shorts generation.
    Uses multiple analysis methods: transcription analysis, audio energy detection,
    scene change detection, and keyword scoring.
    """
    
    def __init__(self, video_path: str, transcription_text: Optional[str] = None, job_id: Optional[str] = None):
        self.video_path = video_path
        self.transcription_text = transcription_text
        self.job_id = job_id or "video_analysis"
        self.video_clip = None
        self.audio_data = None
        self.sample_rate = None
        
    def __enter__(self):
        """Context manager entry - load video"""
        if not HAS_MOVIEPY:
            raise ImportError("MoviePy is required for video analysis. Please install with: pip install moviepy")

        try:
            self.video_clip = VideoFileClip(self.video_path)
            logger.info(f"Job {self.job_id}: Loaded video - Duration: {self.video_clip.duration}s")
            return self
        except Exception as e:
            logger.error(f"Job {self.job_id}: Failed to load video: {str(e)}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        if self.video_clip:
            self.video_clip.close()
    
    def analyze_segments(self, segment_method: str = "auto", num_segments: int = 1, 
                        segment_duration: int = 60) -> List[Dict]:
        """
        Analyze video and return interesting segments based on the specified method.
        
        Args:
            segment_method: Method to use ("auto", "highlights", "equal_parts", "chapters")
            num_segments: Number of segments to return
            segment_duration: Target duration for each segment in seconds
            
        Returns:
            List of segment dictionaries with start_time, end_time, score, and reason
        """
        logger.info(f"Job {self.job_id}: Analyzing video with method '{segment_method}' for {num_segments} segments")
        
        if segment_method == "equal_parts":
            return self._get_equal_parts_segments(num_segments, segment_duration)
        elif segment_method == "highlights":
            return self._get_highlight_segments(num_segments, segment_duration)
        elif segment_method == "chapters":
            return self._get_chapter_segments(num_segments, segment_duration)
        elif segment_method == "auto":
            return self._get_auto_segments(num_segments, segment_duration)
        else:
            logger.warning(f"Job {self.job_id}: Unknown segment method '{segment_method}', using auto")
            return self._get_auto_segments(num_segments, segment_duration)
    
    def _get_equal_parts_segments(self, num_segments: int, segment_duration: int) -> List[Dict]:
        """Divide video into equal parts"""
        segments = []
        video_duration = self.video_clip.duration
        
        if num_segments == 1:
            # Single segment from the middle of the video
            start_time = max(0, (video_duration - segment_duration) / 2)
            end_time = min(video_duration, start_time + segment_duration)
            segments.append({
                "start_time": start_time,
                "end_time": end_time,
                "score": 1.0,
                "reason": "Middle segment of video"
            })
        else:
            # Multiple equal segments
            segment_size = video_duration / num_segments
            for i in range(num_segments):
                start_time = i * segment_size
                end_time = min(video_duration, start_time + segment_duration)
                
                # Adjust if segment would be too short
                if end_time - start_time < segment_duration * 0.5:
                    start_time = max(0, end_time - segment_duration)
                
                segments.append({
                    "start_time": start_time,
                    "end_time": end_time,
                    "score": 1.0,
                    "reason": f"Equal part segment {i+1}/{num_segments}"
                })
        
        logger.info(f"Job {self.job_id}: Generated {len(segments)} equal parts segments")
        return segments
    
    def _get_highlight_segments(self, num_segments: int, segment_duration: int) -> List[Dict]:
        """Find highlight segments using AI analysis"""
        logger.info(f"Job {self.job_id}: Analyzing highlights using multiple methods")
        
        # Get candidate segments using different analysis methods
        audio_highlights = self._analyze_audio_energy()
        transcription_highlights = self._analyze_transcription_keywords()
        scene_highlights = self._analyze_scene_changes()
        
        # Combine and score all potential segments
        all_candidates = []
        
        # Add audio energy highlights
        for segment in audio_highlights:
            all_candidates.append({
                **segment,
                "audio_score": segment["score"],
                "transcription_score": 0,
                "scene_score": 0
            })
        
        # Add transcription highlights
        for segment in transcription_highlights:
            all_candidates.append({
                **segment,
                "audio_score": 0,
                "transcription_score": segment["score"],
                "scene_score": 0
            })
        
        # Add scene change highlights
        for segment in scene_highlights:
            all_candidates.append({
                **segment,
                "audio_score": 0,
                "transcription_score": 0,
                "scene_score": segment["score"]
            })
        
        # Merge overlapping segments and calculate combined scores
        merged_segments = self._merge_overlapping_segments(all_candidates, segment_duration)
        
        # Sort by combined score and return top segments
        merged_segments.sort(key=lambda x: x["score"], reverse=True)
        
        return merged_segments[:num_segments]
    
    def _get_chapter_segments(self, num_segments: int, segment_duration: int) -> List[Dict]:
        """Extract segments based on video chapters (if available)"""
        # For now, fall back to equal parts - chapter detection would require
        # more sophisticated video metadata analysis
        logger.info(f"Job {self.job_id}: Chapter detection not implemented, using equal parts")
        return self._get_equal_parts_segments(num_segments, segment_duration)
    
    def _get_auto_segments(self, num_segments: int, segment_duration: int) -> List[Dict]:
        """Automatically choose the best segmentation method"""
        video_duration = self.video_clip.duration
        
        # If video is short, use equal parts
        if video_duration <= segment_duration * 2:
            logger.info(f"Job {self.job_id}: Short video detected, using equal parts")
            return self._get_equal_parts_segments(num_segments, segment_duration)
        
        # If we have transcription, use highlights
        if self.transcription_text and len(self.transcription_text.strip()) > 50:
            logger.info(f"Job {self.job_id}: Transcription available, using highlights")
            return self._get_highlight_segments(num_segments, segment_duration)
        
        # Otherwise, use equal parts
        logger.info(f"Job {self.job_id}: No transcription, using equal parts")
        return self._get_equal_parts_segments(num_segments, segment_duration)

    def _analyze_audio_energy(self) -> List[Dict]:
        """Analyze audio energy to find exciting segments"""
        if not HAS_LIBROSA:
            logger.warning(f"Job {self.job_id}: Librosa not available, skipping audio analysis")
            return []

        try:
            logger.info(f"Job {self.job_id}: Analyzing audio energy")

            # Check if video has audio
            if not self.video_clip or not self.video_clip.audio:
                logger.warning(f"Job {self.job_id}: No audio track found in video")
                return []

            # Extract audio from video
            import tempfile
            audio_path = os.path.join(tempfile.gettempdir(), f"{self.job_id}_audio.wav")
            self.video_clip.audio.write_audiofile(audio_path, verbose=False, logger=None)

            # Load audio with librosa
            y, sr = librosa.load(audio_path, sr=None)
            self.audio_data = y
            self.sample_rate = sr

            # Calculate RMS energy in windows
            hop_length = sr // 2  # 0.5 second windows
            rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]

            # Calculate spectral centroid (brightness)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]

            # Calculate tempo and beat tracking
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)

            # Combine features for energy score
            energy_scores = []
            time_frames = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=hop_length)

            for i, (time, energy, brightness) in enumerate(zip(time_frames, rms, spectral_centroid)):
                # Normalize features
                energy_norm = energy / np.max(rms) if np.max(rms) > 0 else 0
                brightness_norm = brightness / np.max(spectral_centroid) if np.max(spectral_centroid) > 0 else 0

                # Combined score (weighted)
                combined_score = (energy_norm * 0.7) + (brightness_norm * 0.3)
                energy_scores.append((time, combined_score))

            # Find peaks in energy
            energy_values = [score for _, score in energy_scores]
            threshold = np.percentile(energy_values, 75)  # Top 25% energy segments

            segments = []
            for time, score in energy_scores:
                if score >= threshold:
                    segments.append({
                        "start_time": max(0, time - 5),  # 5 seconds before peak
                        "end_time": min(self.video_clip.duration, time + 5),  # 5 seconds after
                        "score": score,
                        "reason": f"High audio energy (score: {score:.2f})"
                    })

            # Clean up temp file
            if os.path.exists(audio_path):
                os.remove(audio_path)

            logger.info(f"Job {self.job_id}: Found {len(segments)} high-energy audio segments")
            return segments

        except Exception as e:
            logger.error(f"Job {self.job_id}: Audio analysis failed: {str(e)}")
            return []

    def _analyze_transcription_keywords(self) -> List[Dict]:
        """Analyze transcription for interesting keywords and phrases"""
        if not self.transcription_text:
            logger.info(f"Job {self.job_id}: No transcription available for keyword analysis")
            return []

        try:
            logger.info(f"Job {self.job_id}: Analyzing transcription keywords")

            # Define interesting keywords that typically indicate engaging content
            engaging_keywords = [
                # Excitement and emotion
                'amazing', 'incredible', 'unbelievable', 'wow', 'awesome', 'fantastic',
                'shocking', 'surprising', 'crazy', 'insane', 'mind-blowing',

                # Action and intensity
                'suddenly', 'immediately', 'quickly', 'instantly', 'rapidly',
                'breaking', 'urgent', 'critical', 'important', 'major',

                # Discovery and revelation
                'discovered', 'revealed', 'found', 'uncovered', 'exposed',
                'secret', 'hidden', 'mystery', 'truth', 'fact',

                # Superlatives
                'best', 'worst', 'biggest', 'smallest', 'fastest', 'slowest',
                'first', 'last', 'only', 'never', 'always',

                # Questions and engagement
                'what', 'how', 'why', 'when', 'where', 'who',
                'question', 'answer', 'explain', 'understand',

                # Controversy and debate
                'controversial', 'debate', 'argument', 'disagree', 'opinion',
                'wrong', 'right', 'mistake', 'error', 'problem'
            ]

            # Split transcription into sentences/segments
            sentences = re.split(r'[.!?]+', self.transcription_text.lower())

            segments = []
            video_duration = self.video_clip.duration

            for i, sentence in enumerate(sentences):
                if len(sentence.strip()) < 10:  # Skip very short sentences
                    continue

                # Count keyword matches
                keyword_count = sum(1 for keyword in engaging_keywords if keyword in sentence)

                if keyword_count > 0:
                    # Estimate timing (rough approximation)
                    segment_start = (i / len(sentences)) * video_duration
                    segment_duration = min(30, len(sentence.split()) * 0.5)  # ~0.5 seconds per word

                    segments.append({
                        "start_time": max(0, segment_start - 5),
                        "end_time": min(video_duration, segment_start + segment_duration + 5),
                        "score": keyword_count / len(engaging_keywords),  # Normalize score
                        "reason": f"Engaging keywords found: {keyword_count} matches"
                    })

            logger.info(f"Job {self.job_id}: Found {len(segments)} keyword-based segments")
            return segments

        except Exception as e:
            logger.error(f"Job {self.job_id}: Transcription analysis failed: {str(e)}")
            return []

    def _analyze_scene_changes(self) -> List[Dict]:
        """Analyze video for scene changes and visual interest"""
        if not HAS_CV2:
            logger.warning(f"Job {self.job_id}: OpenCV not available, skipping scene analysis")
            return []

        try:
            logger.info(f"Job {self.job_id}: Analyzing scene changes")

            # Sample frames at regular intervals (every 2 seconds)
            sample_interval = 2.0
            frames = []
            timestamps = []

            current_time = 0
            while current_time < self.video_clip.duration:
                frame = self.video_clip.get_frame(current_time)
                frames.append(frame)
                timestamps.append(current_time)
                current_time += sample_interval

            if len(frames) < 2:
                return []

            # Calculate frame differences to detect scene changes
            scene_changes = []
            for i in range(1, len(frames)):
                # Convert frames to grayscale for comparison
                gray1 = cv2.cvtColor(frames[i-1], cv2.COLOR_RGB2GRAY)
                gray2 = cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY)

                # Calculate structural similarity
                diff = cv2.absdiff(gray1, gray2)
                diff_score = np.mean(diff) / 255.0  # Normalize to 0-1

                if diff_score > 0.3:  # Threshold for significant scene change
                    scene_changes.append({
                        "start_time": max(0, timestamps[i] - 10),
                        "end_time": min(self.video_clip.duration, timestamps[i] + 10),
                        "score": diff_score,
                        "reason": f"Scene change detected (diff: {diff_score:.2f})"
                    })

            logger.info(f"Job {self.job_id}: Found {len(scene_changes)} scene changes")
            return scene_changes

        except Exception as e:
            logger.error(f"Job {self.job_id}: Scene analysis failed: {str(e)}")
            return []

    def _merge_overlapping_segments(self, segments: List[Dict], target_duration: int) -> List[Dict]:
        """Merge overlapping segments and calculate combined scores"""
        if not segments:
            return []

        # Sort segments by start time
        segments.sort(key=lambda x: x["start_time"])

        merged = []
        current_segment = segments[0].copy()

        for next_segment in segments[1:]:
            # Check if segments overlap or are close (within 10 seconds)
            if next_segment["start_time"] <= current_segment["end_time"] + 10:
                # Merge segments
                current_segment["end_time"] = max(current_segment["end_time"], next_segment["end_time"])

                # Combine scores (weighted average)
                current_segment["audio_score"] = max(
                    current_segment.get("audio_score", 0),
                    next_segment.get("audio_score", 0)
                )
                current_segment["transcription_score"] = max(
                    current_segment.get("transcription_score", 0),
                    next_segment.get("transcription_score", 0)
                )
                current_segment["scene_score"] = max(
                    current_segment.get("scene_score", 0),
                    next_segment.get("scene_score", 0)
                )

                # Update reason
                current_segment["reason"] = "Combined highlight segment"
            else:
                # No overlap, add current segment and start new one
                merged.append(current_segment)
                current_segment = next_segment.copy()

        # Add the last segment
        merged.append(current_segment)

        # Calculate final combined scores and adjust durations
        for segment in merged:
            audio_score = segment.get("audio_score", 0)
            transcription_score = segment.get("transcription_score", 0)
            scene_score = segment.get("scene_score", 0)

            # Weighted combination of scores
            segment["score"] = (audio_score * 0.4) + (transcription_score * 0.4) + (scene_score * 0.2)

            # Adjust segment duration to target
            current_duration = segment["end_time"] - segment["start_time"]
            if current_duration > target_duration:
                # Trim to target duration, keeping the middle part
                excess = current_duration - target_duration
                segment["start_time"] += excess / 2
                segment["end_time"] -= excess / 2
            elif current_duration < target_duration * 0.5:
                # Extend short segments
                extension = (target_duration - current_duration) / 2
                segment["start_time"] = max(0, segment["start_time"] - extension)
                if self.video_clip:
                    segment["end_time"] = min(self.video_clip.duration, segment["end_time"] + extension)

        return merged


def analyze_video_segments(video_path: str, transcription_text: Optional[str] = None,
                          segment_method: str = "auto", num_segments: int = 1,
                          segment_duration: int = 60, job_id: Optional[str] = None) -> List[Dict]:
    """
    Convenience function to analyze video segments.

    Args:
        video_path: Path to the video file
        transcription_text: Optional transcription text for analysis
        segment_method: Method to use ("auto", "highlights", "equal_parts", "chapters")
        num_segments: Number of segments to return
        segment_duration: Target duration for each segment in seconds
        job_id: Optional job identifier

    Returns:
        List of segment dictionaries with start_time, end_time, score, and reason
    """
    with VideoAnalyzer(video_path, transcription_text, job_id) as analyzer:
        return analyzer.analyze_segments(segment_method, num_segments, segment_duration)


def analyze_viral_compilation_segments(video_path: str, transcription_text: Optional[str] = None, 
                                     transcription_srt: Optional[str] = None, target_duration: int = 60, 
                                     min_segment_duration: int = 5, max_segment_duration: int = 15, 
                                     job_id: Optional[str] = None) -> Dict:
    """
    Enhanced analysis for creating viral compilation shorts with multiple segments.
    
    This function extracts multiple viral moments from a video and combines them
    into a compilation that maximizes engagement and viral potential.
    
    Args:
        video_path: Path to the video file
        transcription_text: Optional transcription text for keyword analysis
        transcription_srt: Optional SRT content for precise timestamp cutting
        target_duration: Target duration for the final compilation (seconds)
        min_segment_duration: Minimum duration for individual segments (seconds)
        max_segment_duration: Maximum duration for individual segments (seconds)
        job_id: Optional job ID for logging
    
    Returns:
        Dictionary containing:
        - segments: List of viral segments with precise timing
        - compilation_plan: Plan for combining segments
        - total_duration: Total duration of compilation
        - viral_score: Overall viral potential score
        - diversity_score: Content diversity score
    """
    if not job_id:
        job_id = "viral_compilation"
    
    logger.info(f"Job {job_id}: Starting viral compilation analysis for {target_duration}s compilation")
    
    # Initialize analyzer with enhanced viral detection
    analyzer = ViralCompilationAnalyzer(video_path, transcription_text, transcription_srt, job_id)
    
    # Get viral moments with enhanced scoring
    viral_segments = analyzer.extract_viral_moments(
        min_duration=min_segment_duration,
        max_duration=max_segment_duration
    )
    
    # Apply duplicate detection and filtering
    filtered_segments = analyzer.filter_duplicate_content(viral_segments)
    
    # Create optimal compilation plan
    compilation_plan = analyzer.create_compilation_plan(
        filtered_segments, 
        target_duration
    )
    
    # Add precision timing from SRT if available
    if transcription_srt:
        compilation_plan = analyzer.add_precision_timing(compilation_plan, transcription_srt)
    
    # Calculate engagement and diversity scores
    final_result = analyzer.calculate_compilation_metrics(compilation_plan)
    
    logger.info(f"Job {job_id}: Viral compilation analysis complete - {len(final_result['segments'])} segments, viral score: {final_result['viral_score']:.2f}")
    
    return final_result


class ViralCompilationAnalyzer:
    """Enhanced analyzer specifically for creating viral compilation shorts"""
    
    def __init__(self, video_path: str, transcription_text: Optional[str] = None, 
                 transcription_srt: Optional[str] = None, job_id: Optional[str] = None):
        self.video_path = video_path
        self.transcription_text = transcription_text
        self.transcription_srt = transcription_srt
        self.job_id = job_id or "viral_compilation"
        self.srt_segments = self._parse_srt_segments() if transcription_srt else []
        
        # Enhanced viral keywords for better detection
        self.viral_keywords = [
            # Emotion/Reaction words
            "amazing", "incredible", "unbelievable", "shocking", "wow", "omg", "insane",
            "crazy", "mind-blowing", "epic", "legendary", "viral", "trending",
            # Action words
            "watch", "look", "see", "check", "wait", "stop", "pause", "rewind",
            "happened", "happens", "doing", "show", "reveal", "expose",
            # Superlatives
            "best", "worst", "fastest", "slowest", "biggest", "smallest", "first", "last",
            "never", "always", "everyone", "nobody", "everything", "nothing",
            # Question/Curiosity words
            "why", "how", "what", "when", "where", "who", "secret", "trick", "hack",
            "method", "way", "reason", "because", "behind", "truth", "real",
            # Engagement words
            "you", "your", "need", "must", "should", "can't", "won't", "don't",
            "will", "going", "about", "right", "wrong", "mistake", "fail"
        ]
    
    def _parse_srt_segments(self) -> List[Dict]:
        """Parse SRT content into timestamped segments"""
        if not self.transcription_srt:
            return []
        
        import re
        segments = []
        
        # SRT pattern: number, time range, text
        pattern = r'(\d+)\n([\d:,]+) --> ([\d:,]+)\n([^\n]+(?:\n[^\n]+)*)'
        matches = re.findall(pattern, self.transcription_srt)
        
        for match in matches:
            index, start_time, end_time, text = match
            segments.append({
                'index': int(index),
                'start_time': self._srt_time_to_seconds(start_time),
                'end_time': self._srt_time_to_seconds(end_time),
                'start_time_str': start_time,
                'end_time_str': end_time,
                'text': text.strip(),
                'duration': self._srt_time_to_seconds(end_time) - self._srt_time_to_seconds(start_time)
            })
        
        return segments
    
    def _srt_time_to_seconds(self, time_str: str) -> float:
        """Convert SRT time format to seconds"""
        try:
            # Format: HH:MM:SS,mmm
            time_str = time_str.replace(',', '.')
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0.0
    
    def extract_viral_moments(self, min_duration: int = 5, max_duration: int = 15) -> List[Dict]:
        """Extract multiple viral moments with enhanced scoring"""
        logger.info(f"Job {self.job_id}: Extracting viral moments ({min_duration}-{max_duration}s each)")
        
        # Use existing VideoAnalyzer for base analysis
        with VideoAnalyzer(self.video_path, self.transcription_text, self.job_id) as base_analyzer:
            # Get many potential highlights (more than we need)
            potential_segments = base_analyzer._get_highlight_segments(
                num_segments=20,  # Get many candidates
                segment_duration=max_duration
            )
        
        # Enhanced viral scoring for each segment
        viral_segments = []
        for segment in potential_segments:
            viral_score = self._calculate_viral_score(segment)
            if viral_score > 0.3:  # Only keep segments with decent viral potential
                viral_segments.append({
                    **segment,
                    'viral_score': viral_score,
                    'original_duration': segment['end_time'] - segment['start_time']
                })
        
        # Sort by viral score
        viral_segments.sort(key=lambda x: x['viral_score'], reverse=True)
        
        logger.info(f"Job {self.job_id}: Found {len(viral_segments)} viral moments")
        return viral_segments
    
    def _calculate_viral_score(self, segment: Dict) -> float:
        """Calculate enhanced viral potential score"""
        base_score = segment.get('score', 0)
        
        # Bonus for transcription keywords
        keyword_bonus = 0
        if self.transcription_text:
            segment_text = self._get_segment_text(segment['start_time'], segment['end_time'])
            keyword_matches = sum(1 for keyword in self.viral_keywords if keyword.lower() in segment_text.lower())
            keyword_bonus = min(keyword_matches * 0.1, 0.3)  # Max 0.3 bonus
        
        # Bonus for audio energy
        audio_bonus = segment.get('audio_score', 0) * 0.2
        
        # Bonus for scene changes (indicates dynamic content)
        scene_bonus = segment.get('scene_score', 0) * 0.15
        
        # Penalty for very short or very long segments
        duration = segment['end_time'] - segment['start_time']
        duration_penalty = 0
        if duration < 3:
            duration_penalty = 0.2
        elif duration > 20:
            duration_penalty = 0.1
        
        viral_score = base_score + keyword_bonus + audio_bonus + scene_bonus - duration_penalty
        return max(0, min(1, viral_score))  # Clamp to 0-1
    
    def _get_segment_text(self, start_time: float, end_time: float) -> str:
        """Get transcription text for a specific time segment"""
        if not self.srt_segments:
            return ""
        
        segment_text = ""
        for srt_seg in self.srt_segments:
            if (srt_seg['start_time'] >= start_time and srt_seg['end_time'] <= end_time) or \
               (srt_seg['start_time'] <= start_time and srt_seg['end_time'] >= start_time) or \
               (srt_seg['start_time'] <= end_time and srt_seg['end_time'] >= end_time):
                segment_text += " " + srt_seg['text']
        
        return segment_text.strip()
    
    def filter_duplicate_content(self, segments: List[Dict]) -> List[Dict]:
        """Filter out duplicate or very similar content segments"""
        logger.info(f"Job {self.job_id}: Filtering duplicate content from {len(segments)} segments")
        
        if not segments:
            return []
        
        filtered = [segments[0]]  # Always keep the highest scoring segment
        
        for candidate in segments[1:]:
            is_duplicate = False
            
            for existing in filtered:
                # Check for time overlap (if segments overlap by >50%, consider duplicate)
                overlap_start = max(candidate['start_time'], existing['start_time'])
                overlap_end = min(candidate['end_time'], existing['end_time'])
                overlap_duration = max(0, overlap_end - overlap_start)
                
                candidate_duration = candidate['end_time'] - candidate['start_time']
                existing_duration = existing['end_time'] - existing['start_time']
                
                overlap_ratio = overlap_duration / min(candidate_duration, existing_duration)
                
                if overlap_ratio > 0.5:  # More than 50% overlap
                    is_duplicate = True
                    break
                
                # Check for content similarity using transcription
                if self.srt_segments:
                    candidate_text = self._get_segment_text(candidate['start_time'], candidate['end_time'])
                    existing_text = self._get_segment_text(existing['start_time'], existing['end_time'])
                    
                    if candidate_text and existing_text:
                        similarity = self._calculate_text_similarity(candidate_text, existing_text)
                        if similarity > 0.7:  # Very similar content
                            is_duplicate = True
                            break
            
            if not is_duplicate:
                filtered.append(candidate)
        
        logger.info(f"Job {self.job_id}: Filtered to {len(filtered)} unique segments")
        return filtered
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text segments"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0
    
    def create_compilation_plan(self, segments: List[Dict], target_duration: int) -> Dict:
        """Create optimal plan for combining segments into compilation"""
        logger.info(f"Job {self.job_id}: Creating compilation plan for {target_duration}s target")
        
        if not segments:
            return {
                'segments': [],
                'total_duration': 0,
                'compilation_strategy': 'no_segments_found'
            }
        
        # Strategy 1: Try to fill target duration with highest scoring segments
        selected_segments = []
        remaining_duration = target_duration
        
        for segment in segments:
            segment_duration = segment['end_time'] - segment['start_time']
            
            # Adjust segment duration if needed
            if segment_duration > remaining_duration:
                # Trim segment to fit remaining time
                segment = self._trim_segment_to_duration(segment, remaining_duration)
                segment_duration = remaining_duration
            
            if segment_duration >= 3:  # Only include segments that are at least 3 seconds
                selected_segments.append(segment)
                remaining_duration -= segment_duration
                
                if remaining_duration <= 0:
                    break
        
        # Calculate transition time (0.5s between segments)
        transition_time = max(0, len(selected_segments) - 1) * 0.5
        actual_duration = sum(seg['end_time'] - seg['start_time'] for seg in selected_segments) + transition_time
        
        return {
            'segments': selected_segments,
            'total_duration': actual_duration,
            'target_duration': target_duration,
            'transition_time': transition_time,
            'compilation_strategy': f'multi_segment_compilation_{len(selected_segments)}_segments'
        }
    
    def _trim_segment_to_duration(self, segment: Dict, max_duration: float) -> Dict:
        """Trim a segment to fit within max_duration while preserving viral content"""
        current_duration = segment['end_time'] - segment['start_time']
        
        if current_duration <= max_duration:
            return segment
        
        # Try to keep the most viral part (center of segment typically)
        excess = current_duration - max_duration
        trim_start = excess / 2
        trim_end = excess / 2
        
        new_start = segment['start_time'] + trim_start
        new_end = segment['end_time'] - trim_end
        
        return {
            **segment,
            'start_time': new_start,
            'end_time': new_end,
            'trimmed': True,
            'original_start': segment['start_time'],
            'original_end': segment['end_time']
        }
    
    def add_precision_timing(self, compilation_plan: Dict, transcription_srt: str) -> Dict:
        """Add precision timing using SRT boundaries to avoid cutting mid-word"""
        logger.info(f"Job {self.job_id}: Adding precision timing using SRT boundaries")
        
        if not self.srt_segments:
            return compilation_plan
        
        precision_segments = []
        
        for segment in compilation_plan['segments']:
            # Find SRT segments that overlap with this video segment
            overlapping_srt = []
            for srt_seg in self.srt_segments:
                if (srt_seg['start_time'] < segment['end_time'] and 
                    srt_seg['end_time'] > segment['start_time']):
                    overlapping_srt.append(srt_seg)
            
            if overlapping_srt:
                # Adjust segment boundaries to SRT boundaries
                # Start at the beginning of the first overlapping SRT segment
                # End at the end of the last overlapping SRT segment that fits
                
                adjusted_start = overlapping_srt[0]['start_time']
                adjusted_end = segment['end_time']
                
                # Find the last complete SRT segment that fits
                for srt_seg in overlapping_srt:
                    if srt_seg['end_time'] <= segment['end_time']:
                        adjusted_end = srt_seg['end_time']
                
                precision_segments.append({
                    **segment,
                    'start_time': adjusted_start,
                    'end_time': adjusted_end,
                    'precision_adjusted': True,
                    'original_start': segment['start_time'],
                    'original_end': segment['end_time'],
                    'srt_segments': overlapping_srt
                })
            else:
                precision_segments.append(segment)
        
        # Recalculate total duration
        new_total = sum(seg['end_time'] - seg['start_time'] for seg in precision_segments)
        new_total += compilation_plan.get('transition_time', 0)
        
        return {
            **compilation_plan,
            'segments': precision_segments,
            'total_duration': new_total,
            'precision_timing_applied': True
        }
    
    def calculate_compilation_metrics(self, compilation_plan: Dict) -> Dict:
        """Calculate final metrics for the compilation"""
        segments = compilation_plan.get('segments', [])
        
        if not segments:
            return {
                **compilation_plan,
                'viral_score': 0,
                'diversity_score': 0,
                'engagement_score': 0
            }
        
        # Calculate average viral score
        viral_scores = [seg.get('viral_score', seg.get('score', 0)) for seg in segments]
        avg_viral_score = sum(viral_scores) / len(viral_scores) if viral_scores else 0
        
        # Calculate diversity score (how spread out segments are in time)
        if len(segments) > 1:
            time_positions = [seg['start_time'] for seg in segments]
            time_spread = (max(time_positions) - min(time_positions)) / 60  # Normalize by minute
            diversity_score = min(1.0, time_spread / 5)  # Max score if segments span 5+ minutes
        else:
            diversity_score = 0.5  # Single segment gets medium diversity
        
        # Calculate engagement score (combines viral score and diversity)
        engagement_score = (avg_viral_score * 0.7) + (diversity_score * 0.3)
        
        return {
            **compilation_plan,
            'viral_score': avg_viral_score,
            'diversity_score': diversity_score,
            'engagement_score': engagement_score,
            'segment_count': len(segments),
            'average_segment_duration': sum(seg['end_time'] - seg['start_time'] for seg in segments) / len(segments) if segments else 0
        }
