from __future__ import annotations

import yt_dlp
import os
import time
import random
import logging
from services.youtube_auth import YouTubeAuthenticator

logger = logging.getLogger(__name__)


class Downloader:
    def __init__(self, url, cookies_content=None, cookies_url=None):
        self.url = url
        self.cookies_content = cookies_content
        self.cookies_url = cookies_url
        self.auth = YouTubeAuthenticator()

    def _get_ydl_opts(self, format_selector, output_filename, auth_method='auto'):
        """Get yt-dlp options with enhanced authentication and anti-detection measures"""
        # Get base options with authentication from YouTubeAuthenticator
        temp_dir = os.path.dirname(output_filename) if os.path.dirname(output_filename) else '.'
        ydl_opts = self.auth.get_enhanced_ydl_opts(temp_dir, auth_method, self.cookies_content, self.cookies_url)

        # Override format and output template
        ydl_opts['format'] = format_selector
        ydl_opts['outtmpl'] = output_filename

        return ydl_opts

    def audio(self):
        """Download audio using yt-dlp with multiple authentication and format strategies"""
        # Prioritize methods based on what's available
        auth_methods = []
        if self.cookies_content:
            auth_methods.append('cookies_content')
        if self.cookies_url:
            auth_methods.append('cookies_url')
        auth_methods.extend(['oauth2', 'cookies_file', 'auto'])

        format_strategies = [
            ('bestaudio[ext=m4a]', 'audio.m4a'),
            ('bestaudio[ext=mp4]', 'audio.mp4'),
            ('bestaudio/best', 'audio.%(ext)s'),
        ]

        for auth_method in auth_methods:
            logger.info(f"Trying audio download with auth method: {auth_method}")

            for format_selector, output_template in format_strategies:
                try:
                    # Add random delay to avoid rate limiting
                    time.sleep(random.uniform(0.5, 1.5))

                    ydl_opts = self._get_ydl_opts(format_selector, output_template, auth_method)

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([self.url])

                    # Check if file was downloaded and rename to expected filename
                    downloaded_files = [f for f in os.listdir('.') if f.startswith('audio.')]
                    if downloaded_files:
                        downloaded_file = downloaded_files[0]
                        if downloaded_file != 'audio.mp4':
                            os.rename(downloaded_file, 'audio.mp4')
                        logger.info(f"Audio downloaded successfully as audio.mp4 using {auth_method}")
                        return

                except Exception as e:
                    logger.debug(f"Audio download failed with {auth_method} and format {format_selector}: {e}")
                    continue

            # If we get here, all formats failed for this auth method
            logger.warning(f"All audio formats failed for auth method: {auth_method}")

        raise Exception("All audio download strategies and authentication methods failed")

    def video(self):
        """Download video using yt-dlp with multiple authentication and format strategies"""
        # Prioritize methods based on what's available
        auth_methods = []
        if self.cookies_content:
            auth_methods.append('cookies_content')
        if self.cookies_url:
            auth_methods.append('cookies_url')
        auth_methods.extend(['oauth2', 'cookies_file', 'auto'])

        format_strategies = [
            ('best[height<=720][ext=mp4]', 'video.mp4'),
            ('best[ext=mp4]', 'video.mp4'),
            ('best', 'video.%(ext)s'),
        ]

        for auth_method in auth_methods:
            logger.info(f"Trying video download with auth method: {auth_method}")

            for format_selector, output_template in format_strategies:
                try:
                    # Add random delay to avoid rate limiting
                    time.sleep(random.uniform(0.5, 1.5))

                    ydl_opts = self._get_ydl_opts(format_selector, output_template, auth_method)

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([self.url])

                    # Check if file was downloaded and rename to expected filename
                    downloaded_files = [f for f in os.listdir('.') if f.startswith('video.')]
                    if downloaded_files:
                        downloaded_file = downloaded_files[0]
                        if downloaded_file != 'video.mp4':
                            os.rename(downloaded_file, 'video.mp4')
                        logger.info(f"Video downloaded successfully as video.mp4 using {auth_method}")
                        return

                except Exception as e:
                    logger.debug(f"Video download failed with {auth_method} and format {format_selector}: {e}")
                    continue

            # If we get here, all formats failed for this auth method
            logger.warning(f"All video formats failed for auth method: {auth_method}")

        raise Exception("All video download strategies and authentication methods failed")
