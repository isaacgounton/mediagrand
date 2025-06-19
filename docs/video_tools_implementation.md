# Video Tools Implementation

This document describes the implementation of three new video processing endpoints copied from the ai-agents-no-code-tools repository and adapted to follow the dahopevi project patterns.

## Implemented Features

### 1. Video Merge (`/v1/video/merge`)
**POST** `/v1/video/merge`

Merges multiple videos together, optionally adding a background audio track.

#### Parameters:
- `video_urls` (array, required): List of video URLs to merge
- `background_music_url` (string, optional): URL of background music file
- `background_music_volume` (number, optional): Volume for background music (0.0 to 1.0, default: 0.5)

#### Features:
- Normalizes video dimensions and frame rates
- Supports background music mixing
- Maintains video quality with re-encoding
- Progress tracking during merge process

#### Example Request:
```json
{
  "video_urls": [
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4"
  ],
  "background_music_url": "https://example.com/music.mp3",
  "background_music_volume": 0.3
}
```

### 2. Frame Extraction (`/v1/video/extract-frame`)
**POST** `/v1/video/extract-frame`

Extracts an image frame from a video at a specified time.

#### Parameters:
- `video_url` (string, required): URL of the video to extract frame from
- `seconds` (number, optional): Time in seconds to extract the frame (default: 0)

#### Features:
- High-quality frame extraction
- Supports any video format supported by FFmpeg
- Returns JPEG image

#### Example Request:
```json
{
  "video_url": "https://example.com/video.mp4",
  "seconds": 30.5
}
```

### 3. TTS Captioned Video (`/v1/video/tts-captioned`)
**POST** `/v1/video/tts-captioned`

Creates a captioned text-to-speech video from background image and text or audio.

#### Parameters:
- `background_url` (string, required): URL of the background image
- `text` (string, conditional): Text to generate speech from (required if `audio_url` not provided)
- `audio_url` (string, conditional): URL of existing audio file (required if `text` not provided)
- `width` (integer, optional): Width of the video (default: 1080)
- `height` (integer, optional): Height of the video (default: 1920)
- `speech_voice` (string, optional): Voice for TTS (default: en-US-AriaNeural)
- `speech_speed` (number, optional): Speed of speech (default: 1.0)

#### Features:
- Text-to-speech generation using existing TTS service
- Automatic caption generation from audio
- ASS subtitle overlay with positioning
- Customizable video dimensions
- Background image scaling and padding

#### Example Request:
```json
{
  "background_url": "https://example.com/background.jpg",
  "text": "Hello, this is a sample text for speech generation.",
  "width": 1080,
  "height": 1920,
  "speech_voice": "en-US-AriaNeural",
  "speech_speed": 1.0
}
```

## Implementation Details

### Service Layer
Located in `services/v1/video/`:
- `merge_videos.py`: Video merging logic with FFmpeg
- `extract_frame.py`: Frame extraction using FFmpeg
- `tts_captioned_video.py`: TTS video generation with captions

### Route Layer
Located in `routes/v1/video/`:
- `merge.py`: API route for video merging
- `extract_frame.py`: API route for frame extraction
- `tts_captioned_video.py`: API route for TTS captioned videos

### Key Adaptations from ai-agents-no-code-tools

1. **Architecture**: Adapted from FastAPI to Flask with Blueprint pattern
2. **Authentication**: Uses dahopevi's existing authentication system
3. **Job Queue**: Integrated with dahopevi's Redis/RQ job system
4. **Storage**: Uses dahopevi's cloud storage upload system
5. **Error Handling**: Follows dahopevi's error handling patterns
6. **Validation**: Uses dahopevi's JSON schema validation
7. **Logging**: Integrated with dahopevi's logging system

### Dependencies

All required dependencies were already present in `requirements.txt`:
- `ffmpeg-python`: For video processing
- `openai-whisper`: For audio transcription
- `requests`: For file downloads
- `Flask`: Web framework
- `jsonschema`: Request validation

### File Structure

```
services/v1/video/
├── merge_videos.py
├── extract_frame.py
└── tts_captioned_video.py

routes/v1/video/
├── merge.py
├── extract_frame.py
└── tts_captioned_video.py
```

### API Documentation

Each endpoint includes an OPTIONS method that returns comprehensive API documentation including:
- Parameter descriptions and types
- Example requests and responses
- Error codes and messages

Access documentation via:
- `OPTIONS /v1/video/merge`
- `OPTIONS /v1/video/extract-frame`
- `OPTIONS /v1/video/tts-captioned`

### Integration with Existing Systems

The new endpoints integrate seamlessly with:
- **Authentication**: Uses `@authenticate` decorator
- **Job Queue**: Uses `@queue_task_wrapper` for async processing
- **Cloud Storage**: Automatically uploads results to cloud storage
- **Webhooks**: Supports webhook notifications on completion
- **Homepage**: Added to main API endpoint listing

## Usage

All endpoints support both synchronous and asynchronous processing:
- **Synchronous**: Omit `webhook_url` parameter
- **Asynchronous**: Include `webhook_url` parameter for job completion notification

The endpoints follow dahopevi's standard response format and job tracking system.