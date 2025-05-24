# Short Video Creation API

## Overview
API endpoints for creating professional short-form videos with text-to-speech, background videos, captions, and music. Ideal for TikTok, Instagram Reels, and YouTube Shorts.

## Base URL
```
https://api.example.com/v1/video/short
```

## Endpoints

### 1. Create Short Video

```http
POST /create
```

Creates a new short video with specified scenes and configuration.

**Request Body**
```json
{
  "scenes": [
    {
      "text": "This is the first scene",
      "search_terms": ["nature", "mountains"]
    },
    {
      "text": "Here's the second scene",
      "search_terms": ["ocean", "sunset"]
    }
  ],
  "config": {
    "voice": "kokoro:af_sarah",
    "orientation": "portrait",
    "caption_position": "bottom",
    "caption_background_color": "#000000",
    "music": "upbeat",
    "music_volume": "medium",
    "padding_back": 0.5
  },
  "webhook_url": "https://your-webhook.com/callback",
  "id": "optional-custom-id"
}
```

**Parameters**

Scenes:
- `text` (required) - Text to convert to speech and display as captions
- `search_terms` (required) - Keywords for background video search

Configuration:
- `voice` (required) - TTS voice identifier
- `orientation` (optional) - "portrait" (9:16) or "landscape" (16:9), default "portrait"
- `caption_position` (optional) - "top", "center", or "bottom", default "bottom"
- `caption_background_color` (optional) - Caption background color in hex, default "#000000"
- `music` (optional) - Music mood category
- `music_volume` (optional) - "high", "medium", "low", or "muted", default "medium"
- `padding_back` (optional) - Padding between scenes in seconds, default 0.5

Other:
- `webhook_url` (optional) - URL for completion callback
- `id` (optional) - Custom identifier for tracking

**Response**
```json
{
  "job_id": "vid_12345abcde",
  "status": "processing",
  "message": "Video creation started",
  "estimated_duration": 180
}
```

### 2. Check Video Status

```http
GET /status/{job_id}
```

Get the current status of a video creation job.

**Parameters**
- `job_id` (path parameter) - Job ID from create response

**Response**
```json
{
  "status": "processing",
  "progress": 75,
  "current_stage": "video_rendering",
  "total_scenes": 2,
  "current_scene": 2,
  "output_url": "https://your-cdn.com/videos/output.mp4",
  "error": null
}
```

**Status Values**
- `queued` - Job is in queue
- `processing` - Job is being processed
- `completed` - Job finished successfully
- `failed` - Job failed (see error field)

## Voice Options

### Kokoro TTS
- `kokoro:af_sarah` - Natural female English
- `kokoro:am_john` - Natural male English
- `kokoro:af_emma` - British female English

### Edge TTS
- `edge-tts:en-US-AriaNeural` - US female
- `edge-tts:en-GB-RyanNeural` - British male

### Streamlabs Polly
- `streamlabs-polly:Brian` - British male
- `streamlabs-polly:Emma` - British female
- `streamlabs-polly:Joey` - US male

## Output Formats

### Portrait Mode (Default)
- Resolution: 1080x1920 (9:16)
- FPS: 30
- Codec: H.264
- Audio: AAC stereo

### Landscape Mode
- Resolution: 1920x1080 (16:9)
- FPS: 30
- Codec: H.264
- Audio: AAC stereo

## Webhook Notifications

When a webhook_url is provided, the system sends POST requests with status updates:

```json
{
  "job_id": "vid_12345abcde",
  "status": "completed",
  "output_url": "https://your-cdn.com/videos/output.mp4",
  "duration": 180,
  "size": 15728640,
  "created_at": "2025-05-23T23:30:00Z"
}
```

## Rate Limiting

- Maximum 10 concurrent jobs per API key
- Maximum 100 jobs per hour
- Maximum total duration: 30 minutes per hour

## Error Responses

Error responses include:
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

Common error codes:
- `INVALID_VOICE` - Specified voice not found
- `INVALID_CONFIG` - Configuration validation failed
- `QUEUE_FULL` - Maximum concurrent jobs reached
- `RATE_LIMITED` - Hour limit exceeded
- `PROCESSING_ERROR` - Error during video creation

## Related Resources

- [Music Management](music.md) - Background music endpoints
- [Prompt Guidelines](../prompt_guidelines.md) - Tips for writing effective video scripts
