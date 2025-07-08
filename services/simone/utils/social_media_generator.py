from __future__ import annotations

import json
import logging
import re
import requests
from typing import List, Dict, Any, Optional, Tuple

from services.simone.utils.prompts import get_social_media_prompt, get_topic_identification_prompt, get_x_thread_prompt
from config import OPENAI_MODEL, OPENAI_BASE_URL


class SocialMediaGenerator:
    def __init__(self, api_key: str, transcription_filename: str, srt_filename: Optional[str] = None):
        self.api_key = api_key
        self.transcription_filename = transcription_filename
        self.srt_filename = srt_filename
        self.logger = logging.getLogger(__name__)

    def generate_post(self, platform: str, **kwargs) -> str:
        with open(self.transcription_filename, "r", encoding="utf-8") as file:
            transcript_content = file.read()

        prompt = get_social_media_prompt(platform, transcript_content, **kwargs)

        response = requests.post(
            url=f"{OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8"
            },
            data=json.dumps(
                {
                    "model": OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt},
                    ],
                },
                ensure_ascii=False
            ),
        )

        try:
            response.raise_for_status()
            response_text = response.text
            response_dict = json.loads(response_text)
            social_media_post = response_dict["choices"][0]["message"]["content"]
            return social_media_post
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred during social media generation: {http_err} - Response: {response.text}")
            raise ValueError(f"API request failed: {response.text}") from http_err
        except json.JSONDecodeError as json_err:
            logging.error(f"JSON decode error during social media generation: {json_err} - Response: {response.text}")
            raise ValueError(f"Invalid JSON response from API: {response.text}") from json_err
        except KeyError as key_err:
            logging.error(f"KeyError during social media generation: {key_err} in API response. Full response: {response.text}")
            raise ValueError(f"Unexpected API response format: Missing key {key_err}. Full response: {response.text}") from key_err
        except Exception as e:
            logging.error(f"An unexpected error occurred during social media generation API call: {e} - Response: {response.text}")
            raise ValueError(f"An unexpected error occurred: {e}. Full response: {response.text}") from e

    def identify_topics(self, min_topics: int = 3, max_topics: int = 10, 
                       include_timestamps: bool = True) -> Dict[str, Any]:
        """Identify viral topics from transcription with optional timestamp mapping."""
        with open(self.transcription_filename, "r", encoding="utf-8") as file:
            transcript_content = file.read()
        
        # Get timestamped segments if SRT file is available
        timestamped_segments = None
        if include_timestamps and self.srt_filename:
            timestamped_segments = self._parse_srt_segments()
        
        prompt = get_topic_identification_prompt(
            transcript_content, 
            min_topics=min_topics, 
            max_topics=max_topics,
            include_timestamps=include_timestamps,
            timestamped_segments=timestamped_segments
        )
        
        response = self._make_api_request(prompt, "topic identification")
        
        try:
            # Try to parse as JSON first
            topics_data = json.loads(response)
            return topics_data
        except json.JSONDecodeError:
            # Fallback: parse manually if not JSON
            self.logger.warning("API response not in JSON format, parsing manually")
            return self._parse_topics_from_text(response)
    
    def generate_x_thread(self, max_posts: int = 8, character_limit: int = 280,
                         thread_style: str = "viral", include_timestamps: bool = True,
                         topic_focus: Optional[str] = None) -> Dict[str, Any]:
        """Generate X/Twitter thread from transcription with time-stamped content mapping."""
        with open(self.transcription_filename, "r", encoding="utf-8") as file:
            transcript_content = file.read()
        
        # Get timestamped segments if available
        timestamped_segments = None
        if include_timestamps and self.srt_filename:
            timestamped_segments = self._parse_srt_segments()
        
        # Identify topics first if no specific focus provided
        topics_data = None
        if not topic_focus:
            try:
                topics_data = self.identify_topics(min_topics=3, max_topics=5, include_timestamps=True)
                if topics_data and 'topics' in topics_data:
                    # Use the highest scoring topic
                    top_topic = max(topics_data['topics'], key=lambda x: x.get('confidence', 0))
                    topic_focus = top_topic.get('topic', 'general insights')
            except Exception as e:
                self.logger.warning(f"Failed to identify topics: {e}")
                topic_focus = "key insights"
        
        prompt = get_x_thread_prompt(
            transcript_content,
            max_posts=max_posts,
            character_limit=character_limit,
            thread_style=thread_style,
            include_timestamps=include_timestamps,
            timestamped_segments=timestamped_segments,
            topic_focus=topic_focus
        )
        
        response = self._make_api_request(prompt, "X thread generation")
        
        try:
            # Try to parse as JSON first
            thread_data = json.loads(response)
            return self._validate_and_format_thread(thread_data, character_limit)
        except json.JSONDecodeError:
            # Fallback: parse manually if not JSON
            self.logger.warning("API response not in JSON format, parsing manually")
            return self._parse_thread_from_text(response, character_limit)
    
    def generate_viral_content_package(self, platforms: List[str] = None, 
                                     include_topics: bool = True,
                                     include_thread: bool = True,
                                     **kwargs) -> Dict[str, Any]:
        """Generate a complete viral content package with topics, threads, and platform-specific posts."""
        if platforms is None:
            platforms = ['x', 'linkedin', 'instagram']
        
        package = {
            'generated_at': self._get_timestamp(),
            'source': 'transcription',
            'content': {}
        }
        
        # Identify topics
        if include_topics:
            try:
                package['content']['topics'] = self.identify_topics(
                    min_topics=kwargs.get('min_topics', 3),
                    max_topics=kwargs.get('max_topics', 8),
                    include_timestamps=True
                )
            except Exception as e:
                self.logger.error(f"Failed to generate topics: {e}")
                package['content']['topics'] = {'error': str(e)}
        
        # Generate X thread
        if include_thread and 'x' in platforms:
            try:
                package['content']['x_thread'] = self.generate_x_thread(
                    max_posts=kwargs.get('max_posts', 8),
                    character_limit=kwargs.get('character_limit', 280),
                    thread_style=kwargs.get('thread_style', 'viral'),
                    include_timestamps=True
                )
            except Exception as e:
                self.logger.error(f"Failed to generate X thread: {e}")
                package['content']['x_thread'] = {'error': str(e)}
        
        # Generate platform-specific posts
        package['content']['posts'] = {}
        for platform in platforms:
            if platform == 'x' and include_thread:
                continue  # Already handled as thread
            
            try:
                package['content']['posts'][platform] = self.generate_post(platform, **kwargs)
            except Exception as e:
                self.logger.error(f"Failed to generate {platform} post: {e}")
                package['content']['posts'][platform] = {'error': str(e)}
        
        return package
    
    def _parse_srt_segments(self) -> List[Dict[str, Any]]:
        """Parse SRT file to extract timestamped segments."""
        if not self.srt_filename:
            return []
        
        try:
            with open(self.srt_filename, "r", encoding="utf-8") as file:
                srt_content = file.read()
            
            segments = []
            # Simple SRT parsing - matches subtitle blocks
            pattern = r'(\d+)\n([\d:,]+) --> ([\d:,]+)\n([\s\S]*?)(?=\n\n|\n$|$)'
            matches = re.findall(pattern, srt_content)
            
            for match in matches:
                index, start_time, end_time, text = match
                segments.append({
                    'index': int(index),
                    'start_time': start_time.strip(),
                    'end_time': end_time.strip(),
                    'start_seconds': self._time_to_seconds(start_time.strip()),
                    'end_seconds': self._time_to_seconds(end_time.strip()),
                    'text': text.strip()
                })
            
            return segments
        except Exception as e:
            self.logger.error(f"Failed to parse SRT file: {e}")
            return []
    
    def _time_to_seconds(self, time_str: str) -> float:
        """Convert SRT time format (HH:MM:SS,mmm) to seconds."""
        try:
            time_str = time_str.replace(',', '.')
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except Exception:
            return 0.0
    
    def _make_api_request(self, prompt: str, operation: str) -> str:
        """Make API request with error handling."""
        response = requests.post(
            url=f"{OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8"
            },
            data=json.dumps({
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an expert content strategist and social media specialist."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }, ensure_ascii=False),
        )
        
        try:
            response.raise_for_status()
            response_dict = json.loads(response.text)
            return response_dict["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error during {operation}: {http_err} - Response: {response.text}")
            raise ValueError(f"API request failed for {operation}: {response.text}") from http_err
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Parse error during {operation}: {e} - Response: {response.text}")
            raise ValueError(f"Invalid API response for {operation}: {response.text}") from e
    
    def _parse_topics_from_text(self, response: str) -> Dict[str, Any]:
        """Parse topics from plain text response."""
        topics = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('*') or line.startswith('-') or line.startswith('•')):
                topic_text = line.lstrip('*-•').strip()
                if topic_text:
                    topics.append({
                        'topic': topic_text,
                        'confidence': 0.8,  # Default confidence
                        'category': 'general'
                    })
        
        return {
            'topics': topics[:10],  # Limit to 10 topics
            'total_topics': len(topics),
            'extraction_method': 'manual_parsing'
        }
    
    def _parse_thread_from_text(self, response: str, character_limit: int) -> Dict[str, Any]:
        """Parse thread from plain text response."""
        posts = []
        lines = response.split('\n')
        current_post = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_post:
                    posts.append({
                        'post_number': len(posts) + 1,
                        'content': current_post.strip(),
                        'character_count': len(current_post.strip()),
                        'start_time': None,
                        'end_time': None
                    })
                    current_post = ""
            else:
                # Check if this looks like a new post indicator
                if re.match(r'^(\d+[./]|Post \d+|Tweet \d+)', line):
                    if current_post:
                        posts.append({
                            'post_number': len(posts) + 1,
                            'content': current_post.strip(),
                            'character_count': len(current_post.strip()),
                            'start_time': None,
                            'end_time': None
                        })
                    current_post = line
                else:
                    current_post += " " + line if current_post else line
        
        # Add final post
        if current_post:
            posts.append({
                'post_number': len(posts) + 1,
                'content': current_post.strip(),
                'character_count': len(current_post.strip()),
                'start_time': None,
                'end_time': None
            })
        
        return {
            'thread': posts,
            'total_posts': len(posts),
            'total_characters': sum(p['character_count'] for p in posts),
            'character_limit': character_limit,
            'parsing_method': 'manual'
        }
    
    def _validate_and_format_thread(self, thread_data: Dict[str, Any], character_limit: int) -> Dict[str, Any]:
        """Validate and format thread data."""
        if 'posts' in thread_data:
            posts = thread_data['posts']
        elif 'x_posts' in thread_data:
            posts = thread_data['x_posts']
        elif 'thread' in thread_data:
            posts = thread_data['thread']
        else:
            # Try to find posts in the data
            posts = []
            for key, value in thread_data.items():
                if isinstance(value, list):
                    posts = value
                    break
        
        # Format posts
        formatted_posts = []
        for i, post in enumerate(posts):
            if isinstance(post, str):
                content = post
                start_time = None
                end_time = None
            elif isinstance(post, dict):
                content = post.get('content', post.get('post_content', post.get('text', str(post))))
                start_time = post.get('start_time', post.get('start_timestamp'))
                end_time = post.get('end_time', post.get('end_timestamp'))
            else:
                content = str(post)
                start_time = None
                end_time = None
            
            # Ensure character limit
            if len(content) > character_limit:
                content = content[:character_limit-3] + "..."
            
            formatted_posts.append({
                'post_number': i + 1,
                'content': content,
                'character_count': len(content),
                'start_time': start_time,
                'end_time': end_time
            })
        
        return {
            'thread': formatted_posts,
            'total_posts': len(formatted_posts),
            'total_characters': sum(p['character_count'] for p in formatted_posts),
            'character_limit': character_limit,
            'validation': 'passed'
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
