"""
Enhanced YouTube authentication service for yt-dlp
Supports OAuth2, browser cookies, and fallback methods
"""

import os
import logging
import tempfile
import requests
from typing import Optional, Dict, Any
import yt_dlp

logger = logging.getLogger(__name__)

class YouTubeAuthenticator:
    """Handles various YouTube authentication methods for yt-dlp"""
    
    def __init__(self):
        self.oauth_cache_dir = os.environ.get('YOUTUBE_OAUTH_CACHE_DIR', '/tmp/youtube_oauth')
        self.cookies_dir = os.environ.get('YOUTUBE_COOKIES_DIR', '/tmp/youtube_cookies')
        
        # Create directories if they don't exist
        os.makedirs(self.oauth_cache_dir, exist_ok=True)
        os.makedirs(self.cookies_dir, exist_ok=True)
    
    def get_enhanced_ydl_opts(self, temp_dir: str, auth_method: str = 'auto', cookies_content: Optional[str] = None, cookies_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get yt-dlp options with enhanced authentication

        Args:
            temp_dir: Temporary directory for downloads
            auth_method: Authentication method ('oauth2', 'cookies_content', 'cookies_url', 'cookies_file', 'auto')
            cookies_content: Raw cookie content as string
            cookies_url: URL to download cookies from
        """
        
        # Base options with enhanced anti-detection
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'extractor_retries': 5,
            'socket_timeout': 60,
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'sleep_interval_requests': 1,
            'sleep_interval_subtitles': 1,
        }
        
        # Apply authentication method
        if auth_method == 'auto':
            self._apply_auto_auth(ydl_opts, cookies_content, cookies_url)
        elif auth_method == 'oauth2':
            self._apply_oauth2_auth(ydl_opts)
        elif auth_method == 'cookies_content' and cookies_content:
            self._apply_cookies_content_auth(ydl_opts, cookies_content)
        elif auth_method == 'cookies_url' and cookies_url:
            self._apply_cookies_url_auth(ydl_opts, cookies_url)
        elif auth_method == 'cookies_file':
            self._apply_cookies_file_auth(ydl_opts)
        
        return ydl_opts
    
    def _apply_auto_auth(self, ydl_opts: Dict[str, Any], cookies_content: Optional[str] = None, cookies_url: Optional[str] = None) -> None:
        """Apply authentication methods in order of preference"""

        # Try OAuth2 first (most reliable)
        if self._apply_oauth2_auth(ydl_opts):
            logger.info("Using OAuth2 authentication")
            return

        # Try cookies content if provided
        if cookies_content and self._apply_cookies_content_auth(ydl_opts, cookies_content):
            logger.info("Using cookies content authentication")
            return

        # Try cookies URL if provided
        if cookies_url and self._apply_cookies_url_auth(ydl_opts, cookies_url):
            logger.info("Using cookies URL authentication")
            return

        # Try cookies file as fallback
        if self._apply_cookies_file_auth(ydl_opts):
            logger.info("Using cookies file authentication")
            return

        logger.warning("No authentication method available, proceeding without auth")
    
    def _apply_oauth2_auth(self, ydl_opts: Dict[str, Any]) -> bool:
        """Apply OAuth2 authentication using yt-dlp-youtube-oauth2 plugin"""
        try:
            # Check if OAuth2 plugin is available
            import yt_dlp_youtube_oauth2
            
            # Configure OAuth2 cache directory
            ydl_opts['cachedir'] = self.oauth_cache_dir
            
            # Enable OAuth2 authentication
            ydl_opts['username'] = 'oauth2'
            ydl_opts['password'] = ''
            
            # OAuth2 specific options
            ydl_opts['youtube_include_dash_manifest'] = False
            
            logger.info("OAuth2 authentication configured")
            return True
            
        except ImportError:
            logger.warning("yt-dlp-youtube-oauth2 plugin not available")
            return False
        except Exception as e:
            logger.warning(f"Failed to configure OAuth2 authentication: {e}")
            return False
    
    def _apply_cookies_content_auth(self, ydl_opts: Dict[str, Any], cookies_content: str) -> bool:
        """Apply authentication using cookies content passed as parameter"""
        try:
            if not cookies_content:
                return False

            # Validate cookies content
            if not self._validate_cookies_content(cookies_content):
                logger.warning("Invalid cookies content provided")
                return False

            # Create temporary cookies file
            temp_cookies_path = os.path.join(self.cookies_dir, 'temp_cookies.txt')
            with open(temp_cookies_path, 'w') as f:
                f.write(cookies_content)

            ydl_opts['cookiefile'] = temp_cookies_path
            logger.info("Using cookies content authentication")
            return True

        except Exception as e:
            logger.warning(f"Failed to configure cookies content authentication: {e}")
            return False

    def _apply_cookies_url_auth(self, ydl_opts: Dict[str, Any], cookies_url: str) -> bool:
        """Apply authentication using cookies downloaded from URL"""
        try:
            if not cookies_url:
                return False

            # Download cookies from URL
            response = requests.get(cookies_url, timeout=30)
            response.raise_for_status()
            cookies_content = response.text

            # Validate cookies content
            if not self._validate_cookies_content(cookies_content):
                logger.warning("Invalid cookies content from URL")
                return False

            # Create temporary cookies file
            temp_cookies_path = os.path.join(self.cookies_dir, 'url_cookies.txt')
            with open(temp_cookies_path, 'w') as f:
                f.write(cookies_content)

            ydl_opts['cookiefile'] = temp_cookies_path
            logger.info("Using cookies URL authentication")
            return True

        except Exception as e:
            logger.warning(f"Failed to configure cookies URL authentication: {e}")
            return False
    
    def _apply_cookies_file_auth(self, ydl_opts: Dict[str, Any]) -> bool:
        """Apply cookies file authentication (fallback method)"""
        try:
            # Look for cookies file in the cookies directory
            cookies_files = [
                os.path.join(self.cookies_dir, 'youtube_cookies.txt'),
                os.path.join(self.cookies_dir, 'cookies.txt'),
                '/app/cookies/youtube_cookies.txt',  # Common Docker path
                '/tmp/cookies.txt'  # Fallback path
            ]
            
            for cookies_path in cookies_files:
                if os.path.exists(cookies_path) and os.path.getsize(cookies_path) > 0:
                    # Validate cookies file
                    if self._validate_cookies_file(cookies_path):
                        ydl_opts['cookiefile'] = cookies_path
                        logger.info(f"Using cookies file: {cookies_path}")
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to configure cookies file authentication: {e}")
            return False
    
    def _validate_cookies_content(self, cookies_content: str) -> bool:
        """Validate that cookies content contains essential YouTube cookies"""
        try:
            # Check for essential YouTube cookies
            essential_cookies = ['__Secure-1PSID', '__Secure-3PSID', 'SAPISID', 'APISID']
            found_count = sum(1 for cookie in essential_cookies if cookie in cookies_content)

            return found_count >= 2

        except Exception as e:
            logger.warning(f"Failed to validate cookies content: {e}")
            return False

    def _validate_cookies_file(self, cookies_path: str) -> bool:
        """Validate that cookies file contains essential YouTube cookies"""
        try:
            with open(cookies_path, 'r') as f:
                cookies_content = f.read()

            return self._validate_cookies_content(cookies_content)

        except Exception as e:
            logger.warning(f"Failed to validate cookies file {cookies_path}: {e}")
            return False
    

