from __future__ import annotations

import yt_dlp
import os
import time
import random


class Downloader:
    def __init__(self, url):
        self.url = url

    def _get_ydl_opts(self, format_selector, output_filename):
        """Get yt-dlp options with enhanced anti-detection measures"""
        return {
            'format': format_selector,
            'outtmpl': output_filename,
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

    def audio(self):
        """Download audio using yt-dlp with fallback strategies"""
        strategies = [
            ('bestaudio[ext=m4a]', 'audio.m4a'),
            ('bestaudio[ext=mp4]', 'audio.mp4'),
            ('bestaudio/best', 'audio.%(ext)s'),
        ]

        for format_selector, output_template in strategies:
            try:
                # Add random delay to avoid rate limiting
                time.sleep(random.uniform(0.5, 1.5))

                ydl_opts = self._get_ydl_opts(format_selector, output_template)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.url])

                # Check if file was downloaded and rename to expected filename
                downloaded_files = [f for f in os.listdir('.') if f.startswith('audio.')]
                if downloaded_files:
                    downloaded_file = downloaded_files[0]
                    if downloaded_file != 'audio.mp4':
                        os.rename(downloaded_file, 'audio.mp4')
                    print(f"Audio downloaded successfully as audio.mp4")
                    return

            except Exception as e:
                print(f"Audio download attempt failed with format {format_selector}: {e}")
                continue

        raise Exception("All audio download strategies failed")

    def video(self):
        """Download video using yt-dlp with fallback strategies"""
        strategies = [
            ('best[height<=720][ext=mp4]', 'video.mp4'),
            ('best[ext=mp4]', 'video.mp4'),
            ('best', 'video.%(ext)s'),
        ]

        for format_selector, output_template in strategies:
            try:
                # Add random delay to avoid rate limiting
                time.sleep(random.uniform(0.5, 1.5))

                ydl_opts = self._get_ydl_opts(format_selector, output_template)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.url])

                # Check if file was downloaded and rename to expected filename
                downloaded_files = [f for f in os.listdir('.') if f.startswith('video.')]
                if downloaded_files:
                    downloaded_file = downloaded_files[0]
                    if downloaded_file != 'video.mp4':
                        os.rename(downloaded_file, 'video.mp4')
                    print(f"Video downloaded successfully as video.mp4")
                    return

            except Exception as e:
                print(f"Video download attempt failed with format {format_selector}: {e}")
                continue

        raise Exception("All video download strategies failed")
