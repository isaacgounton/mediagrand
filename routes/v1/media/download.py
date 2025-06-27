from flask import Blueprint
from app_utils import *
import logging
import os
import yt_dlp
import tempfile
from werkzeug.utils import secure_filename
import uuid
from services.cloud_storage import upload_file
from services.authentication import authenticate
from services.file_management import download_file
from services.youtube_auth import YouTubeAuthenticator
from urllib.parse import quote, urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter
import time
import random
import requests

def extract_video_id(url):
    """Extract video ID from various forms of YouTube URLs."""
    if not url:
        return None
        
    parsed_url = urlparse(url)
    
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
        elif parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
        elif parsed_url.path.startswith('/v/'):
            return parsed_url.path.split('/')[2]
    elif parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    
    return None

def validate_cookies_content(cookies_content):
    """Validate if cookies content has essential YouTube authentication cookies"""
    essential_cookies = ['__Secure-1PSID', '__Secure-3PSID', 'SAPISID', 'APISID']
    found_count = sum(1 for cookie in essential_cookies if cookie in cookies_content)
    return found_count >= 2

def get_enhanced_ydl_opts(temp_dir, cookies_path=None, is_youtube=False, auth_method='auto', cookies_content=None, cookies_url=None):
    """Get enhanced yt-dlp options with better bot detection avoidance and authentication"""

    if is_youtube:
        # Use the new YouTube authenticator for YouTube videos
        auth = YouTubeAuthenticator()
        ydl_opts = auth.get_enhanced_ydl_opts(temp_dir, auth_method, cookies_content, cookies_url)

        # Override output template to match expected format
        ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')

        return ydl_opts
    else:
        # For non-YouTube videos, use the original logic
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
        }

        if cookies_path and os.path.exists(cookies_path):
            ydl_opts['cookiefile'] = cookies_path

        return ydl_opts

v1_media_download_bp = Blueprint('v1_media_download', __name__)
logger = logging.getLogger(__name__)



@v1_media_download_bp.route('/v1/BETA/media/download', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"},
        "cookies_content": {
            "type": "string",
            "description": "Raw cookie content in Netscape format"
        },
        "cookies_url": {
            "type": "string",
            "format": "uri",
            "description": "URL to download cookies from"
        },
        "auth_method": {
            "type": "string",
            "enum": ["auto", "oauth2", "cookies_content", "cookies_url", "cookies_file"],
            "default": "auto",
            "description": "Authentication method to use for YouTube videos"
        },
        "cloud_upload": {
            "type": "boolean",
            "default": True,
            "description": "Whether to upload the downloaded media to cloud storage. If false, returns direct URL."
        },
        "transcript": {
            "type": "object",
            "properties": {
                "languages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of language codes in order of preference (e.g. ['en', 'es'])"
                },
                "preserve_formatting": {
                    "type": "boolean",
                    "description": "Whether to preserve HTML formatting (e.g. <i>, <b>)"
                },
                "translate_to": {
                    "type": "string",
                    "description": "Language code to translate transcript to"
                }
            }
        },
        "format": {
            "type": "object",
            "properties": {
                "quality": {"type": "string"},
                "format_id": {"type": "string"},
                "resolution": {"type": "string"},
                "video_codec": {"type": "string"},
                "audio_codec": {"type": "string"}
            }
        },
        "audio": {
            "type": "object",
            "properties": {
                "extract": {"type": "boolean"},
                "format": {"type": "string"},
                "quality": {"type": "string"}
            }
        },
        "thumbnails": {
            "type": "object",
            "properties": {
                "download": {"type": "boolean"},
                "download_all": {"type": "boolean"},
                "formats": {"type": "array", "items": {"type": "string"}},
                "convert": {"type": "boolean"},
                "embed_in_audio": {"type": "boolean"}
            }
        },
        "subtitles": {
            "type": "object",
            "properties": {
                "download": {"type": "boolean"},
                "languages": {"type": "array", "items": {"type": "string"}},
                "formats": {"type": "array", "items": {"type": "string"}}
            }
        },
        "download": {
            "type": "object",
            "properties": {
                "max_filesize": {"type": "integer"},
                "rate_limit": {"type": "string"},
                "retries": {"type": "integer"}
            }
        }
    },
    "required": ["media_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def download_media(job_id, data):
    media_url = data['media_url']
    video_id = extract_video_id(media_url)
    
    format_options = data.get('format', {})
    audio_options = data.get('audio', {})
    thumbnail_options = data.get('thumbnails', {})
    subtitle_options = data.get('subtitles', {})
    download_options = data.get('download', {})
    transcript_options = data.get('transcript', {})
    cookies_content = data.get('cookies_content')
    cookies_url = data.get('cookies_url')
    auth_method = data.get('auth_method', 'auto')

    is_youtube = video_id is not None
    logger.info(f"Job {job_id}: Received download request for {'YouTube video' if is_youtube else 'media'} {media_url}")

    transcript_data = None

    try:
        # Create a temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            # Handle transcript request for YouTube videos
            if is_youtube and transcript_options:
                try:
                    languages = transcript_options.get('languages', ['en'])
                    preserve_formatting = transcript_options.get('preserve_formatting', False)
                    translate_to = transcript_options.get('translate_to')

                    # Add small delay to avoid rate limiting
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    
                    try:
                        # Find transcript in requested languages
                        transcript = transcript_list.find_transcript(languages)
                    except Exception as e:
                        logger.warning(f"Error finding transcript for video {video_id} in languages {languages}: {str(e)}")
                        transcript_data = {"error": f"No transcript available in requested languages: {languages}"}
                    else:
                        # Handle translation if requested
                        if translate_to:
                            if transcript.is_translatable:
                                transcript = transcript.translate(translate_to)
                            else:
                                transcript_data = {"error": "Selected transcript cannot be translated"}

                        if not transcript_data or "error" not in transcript_data:
                            # Fetch transcript data
                            fetched_transcript = transcript.fetch(preserve_formatting=preserve_formatting)

                            # Add transcript data to response
                            transcript_data = {
                                "language": {
                                    "name": transcript.language,
                                    "code": transcript.language_code,
                                },
                                "metadata": {
                                    "is_generated": transcript.is_generated,
                                    "preserve_formatting": preserve_formatting,
                                },
                                "snippets": [
                                    {
                                        "text": snippet['text'],
                                        "start": snippet['start'],
                                        "duration": snippet['duration']
                                    } for snippet in fetched_transcript
                                ]
                            }

                            if translate_to:
                                transcript_data["translated_to"] = translate_to

                except Exception as e:
                    error_str = str(e)
                    if "Could not retrieve a transcript" in error_str:
                        logger.warning(f"No transcript available for video {video_id}")
                        transcript_data = {"error": "No transcript available for this video"}
                    else:
                        logger.warning(f"Error getting transcript for video {video_id}: {error_str}")
                        transcript_data = {"error": f"Transcript error: {error_str}"}

            # Multiple download attempts with different strategies
            download_success = False
            last_error = None

            # Enhanced strategies with authentication methods for YouTube
            if is_youtube:
                # Use user-specified auth method or fallback strategies
                if auth_method != 'auto':
                    strategies = [(auth_method, auth_method)]
                else:
                    # Auto mode: try methods based on what's available
                    strategies = []
                    if cookies_content:
                        strategies.append(("cookies_content", 'cookies_content'))
                    if cookies_url:
                        strategies.append(("cookies_url", 'cookies_url'))
                    strategies.extend([
                        ("oauth2", 'oauth2'),
                        ("cookies_file", 'cookies_file'),
                        ("basic", None)  # Fallback without auth
                    ])
            else:
                strategies = [
                    ("basic", None),  # Non-YouTube videos
                ]

            for strategy_name, strategy_auth_method in strategies:
                if download_success:
                    break

                logger.info(f"Job {job_id}: Attempting download with strategy: {strategy_name}")

                try:
                    # Add random delay between attempts
                    if strategy_name != "basic":
                        time.sleep(random.uniform(2, 5))

                    # Get enhanced options with authentication
                    if is_youtube and strategy_auth_method:
                        ydl_opts = get_enhanced_ydl_opts(temp_dir, None, is_youtube, strategy_auth_method, cookies_content, cookies_url)
                    else:
                        # For non-YouTube or basic strategy
                        ydl_opts = get_enhanced_ydl_opts(temp_dir, None, is_youtube)
                    
                    # Apply format options
                    if format_options:
                        format_parts = []
                        if format_options.get('quality'):
                            if format_options['quality'] == 'best':
                                format_parts.append('best')
                            elif format_options['quality'] == 'worst':
                                format_parts.append('worst')
                            else:
                                format_parts.append(format_options['quality'])
                        
                        if format_options.get('resolution'):
                            if not format_parts or format_parts[0] not in ['best', 'worst']:
                                format_parts.append(f"height<={format_options['resolution'].replace('p', '')}")
                        
                        if format_parts:
                            ydl_opts['format'] = '+'.join(format_parts) if len(format_parts) > 1 else format_parts[0]

                    # Apply audio options
                    if audio_options and audio_options.get('extract'):
                        ydl_opts['format'] = 'bestaudio/best'
                        if audio_options.get('format'):
                            ydl_opts['postprocessors'] = [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': audio_options['format'],
                                'preferredquality': audio_options.get('quality', '192'),
                            }]

                    # Apply other options (thumbnails, subtitles, download settings)
                    if thumbnail_options:
                        ydl_opts['writethumbnail'] = thumbnail_options.get('download', False)
                        ydl_opts['writeallsubtitles'] = thumbnail_options.get('download_all', False)

                    if subtitle_options:
                        ydl_opts['writesubtitles'] = subtitle_options.get('download', False)
                        if subtitle_options.get('languages'):
                            ydl_opts['subtitleslangs'] = subtitle_options['languages']

                    if download_options:
                        if download_options.get('max_filesize'):
                            ydl_opts['max_filesize'] = download_options['max_filesize']
                        if download_options.get('rate_limit'):
                            ydl_opts['ratelimit'] = download_options['rate_limit']
                        if download_options.get('retries'):
                            ydl_opts['retries'] = download_options['retries']

                    # Special handling for fallback strategy
                    if strategy_name == "fallback":
                        ydl_opts.update({
                            'format': 'worst' if format_options.get('quality') != 'best' else 'best',
                            'extract_flat': False,
                            'force_generic_extractor': False,
                        })

                    # Attempt download
                    cloud_upload = data.get('cloud_upload', True)
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(media_url, download=cloud_upload)
                        
                        if cloud_upload:
                            filename = ydl.prepare_filename(info)
                            if not os.path.exists(filename):
                                # Sometimes the filename changes due to post-processing
                                for file in os.listdir(temp_dir):
                                    if file.startswith(info.get('title', '')[:20]):
                                        filename = os.path.join(temp_dir, file)
                                        break
                            
                            if os.path.exists(filename):
                                # Upload to cloud storage
                                media_url_response = upload_file(filename)
                                logger.info(f"Job {job_id}: Successfully uploaded file to cloud storage")
                            else:
                                raise Exception("Downloaded file not found")
                        else:
                            # Return direct URL without downloading
                            media_url_response = info.get('url', media_url)

                        # Prepare response
                        response = {
                            "media": {
                                "media_url": media_url_response,
                                "video_id": video_id if is_youtube else None,
                                "title": info.get('title'),
                                "format_id": info.get('format_id'),
                                "ext": info.get('ext'),
                                "resolution": info.get('resolution'),
                                "filesize": info.get('filesize'),
                                "width": info.get('width'),
                                "height": info.get('height'),
                                "fps": info.get('fps'),
                                "video_codec": info.get('vcodec'),
                                "audio_codec": info.get('acodec'),
                                "upload_date": info.get('upload_date'),
                                "duration": info.get('duration'),
                                "view_count": info.get('view_count'),
                                "uploader": info.get('uploader'),
                                "uploader_id": info.get('uploader_id'),
                                "description": info.get('description')
                            },
                            "download_strategy": strategy_name
                        }

                        # Add thumbnails if available and requested
                        if info.get('thumbnails') and thumbnail_options.get('download', False):
                            response["thumbnails"] = []
                            for thumbnail in info['thumbnails'][:5]:  # Limit to 5 thumbnails
                                if thumbnail.get('url'):
                                    try:
                                        thumbnail_path = download_file(thumbnail['url'], temp_dir)
                                        thumbnail_url = upload_file(thumbnail_path)
                                        
                                        response["thumbnails"].append({
                                            "id": thumbnail.get('id', 'default'),
                                            "image_url": thumbnail_url,
                                            "width": thumbnail.get('width'),
                                            "height": thumbnail.get('height'),
                                            "original_format": thumbnail.get('ext'),
                                        })
                                    except Exception as e:
                                        logger.error(f"Error processing thumbnail: {str(e)}")
                                        continue

                        # Add transcript data if available
                        if transcript_data:
                            response["transcript"] = transcript_data
                        
                        download_success = True
                        logger.info(f"Job {job_id}: Download successful using strategy: {strategy_name}")
                        return response, "/v1/media/download", 200

                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Job {job_id}: Strategy {strategy_name} failed: {last_error}")
                    continue

            # If all strategies failed
            if not download_success:
                error_str = last_error or "Unknown error"
                logger.error(f"Job {job_id}: All download strategies failed. Last error: {error_str}")
                
                # Return enhanced error messages
                if any(phrase in error_str.lower() for phrase in [
                    "sign in to confirm your age", 
                    "sign in to continue", 
                    "sign in to confirm you're not a bot",
                    "this helps protect our community"
                ]):
                    return {
                        "error": "YouTube requires authentication",
                        "details": error_str,
                        "solution": {
                            "description": "This video requires valid YouTube cookies for access",
                            "steps": [
                                "1. Login to YouTube in your browser",
                                "2. Complete any verification challenges",
                                "3. Export cookies using: `yt-dlp --cookies-from-browser chrome --cookies cookies.txt https://youtube.com`",
                                "4. Upload the cookies file and provide the URL in cookies_url parameter",
                                "5. Ensure cookies contain: __Secure-1PSID, __Secure-3PSID, SAPISID, APISID"
                            ],
                            "cookie_validation_url": "Use the cookie validation script to check your cookies"
                        }
                    }, "/v1/media/download", 401
                    
                elif "video unavailable" in error_str.lower() or "not available" in error_str.lower():
                    return {
                        "error": "Video is not available",
                        "details": error_str,
                        "possible_reasons": [
                            "Video may be deleted or private",
                            "Video may be geo-blocked in your region",
                            "Video may require special permissions"
                        ]
                    }, "/v1/media/download", 404
                    
                else:
                    return {
                        "error": "Download failed after multiple attempts",
                        "details": error_str,
                        "attempted_strategies": [s[0] for s in strategies],
                        "suggestion": "Try again later or check if the video URL is correct"
                    }, "/v1/media/download", 500

    except Exception as e:
        error_str = str(e)
        logger.error(f"Job {job_id}: Unexpected error during download process - {error_str}")
        return {
            "error": f"Unexpected error: {error_str}",
            "job_id": job_id
        }, "/v1/media/download", 500