"""
Video Source Handler - Detects and processes different video input types
Supports YouTube URLs and direct video file uploads
"""

import os
import logging
import tempfile
import shutil
import re
from urllib.parse import urlparse
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

class VideoSourceHandler:
    """Handles different video input sources (YouTube URLs vs direct files)"""
    
    SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.webm', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v'}
    YOUTUBE_DOMAINS = {'youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com'}
    
    @classmethod
    def detect_video_source_type(cls, video_input: str) -> str:
        """
        Detect the type of video input
        
        Args:
            video_input: Can be a URL or file path
            
        Returns:
            'youtube' | 'direct_file' | 'unknown'
        """
        try:
            # Check if it's a URL
            parsed = urlparse(video_input)
            
            if parsed.scheme in ('http', 'https'):
                # It's a URL - check if it's YouTube
                if parsed.netloc.lower() in cls.YOUTUBE_DOMAINS:
                    return 'youtube'
                elif cls._is_direct_video_url(video_input):
                    return 'direct_file'
                else:
                    return 'unknown'
            
            # Check if it's a local file path
            elif os.path.exists(video_input):
                if cls._is_video_file(video_input):
                    return 'direct_file'
                else:
                    return 'unknown'
            
            # Could be a YouTube URL without explicit scheme
            elif 'youtube.com' in video_input.lower() or 'youtu.be' in video_input.lower():
                return 'youtube'
            
            return 'unknown'
            
        except Exception as e:
            logger.warning(f"Error detecting video source type: {e}")
            return 'unknown'
    
    @classmethod
    def _is_video_file(cls, file_path: str) -> bool:
        """Check if file has a supported video extension"""
        _, ext = os.path.splitext(file_path.lower())
        return ext in cls.SUPPORTED_VIDEO_EXTENSIONS
    
    @classmethod
    def _is_direct_video_url(cls, url: str) -> bool:
        """Check if URL points directly to a video file"""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            _, ext = os.path.splitext(path)
            return ext in cls.SUPPORTED_VIDEO_EXTENSIONS
        except:
            return False
    
    @classmethod
    def process_video_source(
        cls, 
        video_input: str, 
        job_id: str,
        temp_dir: str,
        cookies_content: Optional[str] = None,
        cookies_url: Optional[str] = None,
        auth_method: str = 'auto'
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process video source and return local file path
        
        Args:
            video_input: Video URL or file path
            job_id: Job identifier for logging
            temp_dir: Temporary directory for downloads
            cookies_content: Optional cookies content for YouTube
            cookies_url: Optional cookies URL for YouTube
            auth_method: Authentication method for YouTube
            
        Returns:
            Tuple of (local_video_path, metadata)
        """
        source_type = cls.detect_video_source_type(video_input)
        logger.info(f"Job {job_id}: Detected video source type: {source_type}")
        
        if source_type == 'youtube':
            return cls._process_youtube_source(
                video_input, job_id, temp_dir, cookies_content, cookies_url, auth_method
            )
        elif source_type == 'direct_file':
            return cls._process_direct_file_source(video_input, job_id, temp_dir)
        else:
            raise ValueError(f"Unsupported video source: {video_input}")
    
    @classmethod
    def _process_youtube_source(
        cls, 
        youtube_url: str, 
        job_id: str,
        temp_dir: str,
        cookies_content: Optional[str] = None,
        cookies_url: Optional[str] = None,
        auth_method: str = 'auto'
    ) -> Tuple[str, Dict[str, Any]]:
        """Process YouTube URL and download video"""
        logger.info(f"Job {job_id}: Processing YouTube URL: {youtube_url}")
        
        try:
            from services.simone.utils.downloader import Downloader
            
            # Create downloader with authentication if provided
            downloader = Downloader(
                url=youtube_url, 
                cookies_content=cookies_content, 
                cookies_url=cookies_url
            )
            
            # Change to temp directory for download
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Download video (saves as 'video.mp4')
                downloader.video()
                downloaded_video_path = os.path.join(temp_dir, 'video.mp4')
                
                if not os.path.exists(downloaded_video_path):
                    raise Exception("YouTube download failed - file not found")
                
                logger.info(f"Job {job_id}: YouTube video downloaded successfully")
                
                # Get video metadata
                metadata = {
                    'source_type': 'youtube',
                    'original_url': youtube_url,
                    'file_size': os.path.getsize(downloaded_video_path),
                    'download_method': 'youtube-dl'
                }
                
                return downloaded_video_path, metadata
                
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"Job {job_id}: YouTube download failed: {e}")
            raise Exception(f"YouTube download failed: {e}")
    
    @classmethod
    def _process_direct_file_source(
        cls, 
        video_input: str, 
        job_id: str,
        temp_dir: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Process direct video file (URL or local path)"""
        logger.info(f"Job {job_id}: Processing direct video file: {video_input}")
        
        try:
            if os.path.exists(video_input):
                # Local file path
                if not cls._is_video_file(video_input):
                    raise ValueError(f"File is not a supported video format: {video_input}")
                
                # Copy to temp directory for consistent processing
                filename = os.path.basename(video_input)
                local_path = os.path.join(temp_dir, filename)
                shutil.copy2(video_input, local_path)
                
                metadata = {
                    'source_type': 'local_file',
                    'original_path': video_input,
                    'file_size': os.path.getsize(local_path),
                    'filename': filename
                }
                
                logger.info(f"Job {job_id}: Local file copied successfully")
                return local_path, metadata
                
            else:
                # Direct video URL - download it
                import requests
                from urllib.parse import urlparse
                
                parsed = urlparse(video_input)
                filename = os.path.basename(parsed.path) or 'video.mp4'
                
                # Ensure it has a video extension
                if not cls._is_video_file(filename):
                    filename += '.mp4'
                
                local_path = os.path.join(temp_dir, filename)
                
                logger.info(f"Job {job_id}: Downloading direct video URL...")
                
                # Download with streaming to handle large files
                response = requests.get(video_input, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if not os.path.exists(local_path):
                    raise Exception("Direct video download failed - file not found")
                
                metadata = {
                    'source_type': 'direct_url',
                    'original_url': video_input,
                    'file_size': os.path.getsize(local_path),
                    'filename': filename,
                    'content_type': response.headers.get('content-type', 'video/mp4')
                }
                
                logger.info(f"Job {job_id}: Direct video URL downloaded successfully")
                return local_path, metadata
                
        except Exception as e:
            logger.error(f"Job {job_id}: Direct file processing failed: {e}")
            raise Exception(f"Direct file processing failed: {e}")
    
    @classmethod
    def validate_video_input(cls, video_input: str) -> Dict[str, Any]:
        """
        Validate video input and return information about it
        
        Args:
            video_input: Video URL or file path
            
        Returns:
            Dictionary with validation results and metadata
        """
        source_type = cls.detect_video_source_type(video_input)
        
        result = {
            'valid': False,
            'source_type': source_type,
            'input': video_input,
            'errors': []
        }
        
        if source_type == 'unknown':
            result['errors'].append('Unsupported video source format')
            return result
        
        if source_type == 'youtube':
            # Validate YouTube URL format
            if not cls._is_valid_youtube_url(video_input):
                result['errors'].append('Invalid YouTube URL format')
                return result
        
        elif source_type == 'direct_file':
            if os.path.exists(video_input):
                # Local file validation
                if not os.path.isfile(video_input):
                    result['errors'].append('Path exists but is not a file')
                    return result
                if not cls._is_video_file(video_input):
                    result['errors'].append('File does not have a supported video extension')
                    return result
            else:
                # URL validation
                try:
                    parsed = urlparse(video_input)
                    if not parsed.scheme or not parsed.netloc:
                        result['errors'].append('Invalid URL format')
                        return result
                except:
                    result['errors'].append('Invalid URL format')
                    return result
        
        result['valid'] = True
        return result
    
    @classmethod
    def _is_valid_youtube_url(cls, url: str) -> bool:
        """Validate YouTube URL format"""
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
            r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=[\w-]+',
        ]
        
        for pattern in youtube_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        return False