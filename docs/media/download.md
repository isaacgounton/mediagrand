# Media Download API

Downloads media from various sources including YouTube, with support for transcripts and age-restricted content.

## Endpoint

`POST /v1/BETA/media/download`

Downloads media from URLs with support for YouTube-specific features like transcripts, age-restricted content, and various formats.

## Request Body

```json
{
    "media_url": "https://www.youtube.com/watch?v=...",
    "cookies_content": "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t...",  // Optional: Netscape format cookies for age-restricted videos
    "cookies_url": "https://example.com/cookies.txt",  // Optional: URL to cookies file for age-restricted videos
    "transcript": {  // Optional: For YouTube videos only
        "languages": ["en", "es"],  // Language preference order
        "preserve_formatting": false,  // Keep HTML tags
        "translate_to": "fr"  // Translate transcript to this language
    },
    "format": {  // Optional
        "quality": "best",
        "format_id": "mp4",
        "resolution": "1080p",
        "video_codec": "h264",
        "audio_codec": "aac"
    },
    "audio": {  // Optional
        "extract": true,
        "format": "mp3",
        "quality": "192k"
    },
    "thumbnails": {  // Optional
        "download": true,
        "download_all": false,
        "formats": ["jpg", "webp"],
        "convert": true,
        "embed_in_audio": false
    },
    "subtitles": {  // Optional
        "download": true,
        "languages": ["en", "es"],
        "formats": ["vtt", "srt"]
    },
    "download": {  // Optional
        "max_filesize": 1000000000,  // In bytes
        "rate_limit": "1M",  // 1 MB/s
        "retries": 3
    }
}
```

## Response

```json
{
    "media": {
        "media_url": "https://storage.example.com/video.mp4",
        "video_id": "dQw4w9WgXcQ",  // Only for YouTube videos
        "title": "Video Title",
        "format_id": "137+140",
        "ext": "mp4",
        "resolution": "1080p",
        "filesize": 12345678,
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "video_codec": "h264",
        "audio_codec": "aac",
        "upload_date": "20240522",
        "duration": 180,
        "view_count": 1000000,
        "uploader": "Channel Name",
        "uploader_id": "UCxxxxxxxx",
        "description": "Video description"
    },
    "thumbnails": [  // Only if requested
        {
            "id": "maxres",
            "image_url": "https://storage.example.com/thumbnail.jpg",
            "width": 1920,
            "height": 1080,
            "original_format": "jpg",
            "converted": false
        }
    ],
    "transcript": {  // Only for YouTube videos when requested
        "language": {
            "name": "English",
            "code": "en"
        },
        "metadata": {
            "is_generated": false,
            "translation_languages": ["fr", "es", "de"],
            "preserve_formatting": false
        },
        "snippets": [
            {
                "text": "Transcript text here",
                "start": 0.0,
                "duration": 2.5
            }
        ],
        "translated_to": "fr"  // Only if translation was requested
    }
}
```

---

### Media Download Endpoint

The media download endpoint now supports multiple authentication methods:

```bash
# With authentication method selection
curl -X POST https://your-domain.com/v1/BETA/media/download \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_API_KEY' \
  -d '{
    "media_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  }'

# With cookies content
curl -X POST https://your-domain.com/v1/BETA/media/download \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_API_KEY' \
  -d '{
    "media_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "cookies_content": "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t..."
  }'

# With cookies URL
curl -X POST https://your-domain.com/v1/BETA/media/download \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_API_KEY' \
  -d '{
    "media_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "cookies_url": "https://your-secure-url.com/youtube_cookies.txt"
  }'
```

## Troubleshooting

### Common Issues

1. **"Sign in to confirm you're not a bot"**
   - Solution: Export fresh cookies from browser (see [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies) for details)


3. **Cookies not working**
   - Ensure cookies are in Netscape format
   - Check that cookies contain essential YouTube authentication cookies
   - Try exporting fresh cookies from browser

### Logs

(See <attachments> above for file contents. You may not need to search or read the file again.)

## Cookie Authentication

For age-restricted or private videos, the endpoint will first try to access the content without authentication. If that fails, it will use the provided cookies file.

You can provide cookies in two ways:
1. `cookies_content`: Netscape format cookies for age-restricted videos
2. `cookies_url`: A URL to a cookies file that will be downloaded automatically

You can obtain YouTube cookies using:

1. yt-dlp's `--cookies-from-browser` option:
```bash
yt-dlp --cookies-from-browser firefox
```

2. Browser extensions that export cookies in Netscape format

The cookies file should be in Netscape format.

## Error Handling

The API handles various errors with clear messages:

1. Age-restricted videos:
```json
{
    "error": "Age-restricted or private video requires authentication",
    "solution": "Please provide a cookies_content parameter with valid YouTube cookies or a cookies_url parameter with a URL to a valid cookies file..."
}
```

2. Bot verification:
```json
{
    "error": "YouTube is requesting verification",
    "solution": "Please provide a cookies_content parameter with valid YouTube cookies or a cookies_url parameter with a URL to a valid cookies file..."
}
```

3. Private videos:
```json
{
    "error": "This is a private video",
    "solution": "If you have access to this video, provide a cookies_content parameter with valid YouTube cookies or a cookies_url parameter with a URL to a valid cookies file."
}
```

4. Unavailable videos:
```json
{
    "error": "Video is not available",
    "details": "This video has been removed..."
}
```

5. Translation errors:
```json
{
    "error": "Selected transcript cannot be translated"
}
```

6. Missing transcript:
```json
{
    "error": "No transcript available for this video"
}
```

## Notes

1. For YouTube videos, the endpoint automatically detects if it's a YouTube URL and enables additional features like transcript support.
2. Cookies are only used when necessary (age restrictions, bot verification, private videos).
3. Transcripts can be fetched along with the video in a single request.
4. Translation is supported for transcripts of videos that allow it.
5. All downloaded media and thumbnails are automatically uploaded to cloud storage.
