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
POST /v1/video/short/create
```

Creates a new short video with specified scenes and configuration.

**Request Body**
```json
{
  "scenes": [
    {
      "text": "This is the first scene",
      "search_terms": ["nature", "mountains"],
      "bg_video_url": "https://example.com/background-video.mp4",
      "person_image_url": "https://example.com/person.jpg",
      "person_name": "John Doe"
    },
    {
      "text": "Here's the second scene",
      "search_terms": ["ocean", "sunset"],
      "person_image_url": "https://example.com/speaker.png",
      "person_name": "Jane Smith"
    }
  ],
  "config": {
    "voice": "kokoro:af_sarah",
    "orientation": "portrait",
    "caption_position": "bottom",
    "caption_background_color": "#000000",
    "music": "upbeat",
    "music_url": "https://example.com/background-music.mp3",
    "music_volume": "medium",
    "padding_back": 0.5
  },
  "webhook_url": "https://your-webhook.com/callback",
  "id": "optional-custom-id"
}
```

**Parameters**

Scenes (array, required, minimum 1 item):
- `text` (string, required, minimum 1 character) - Text to convert to speech and display as captions
- `search_terms` (array of strings, optional, minimum 1 item when provided) - Keywords for background video search from Pexels/Pixabay APIs
- `bg_video_url` (string, optional, URL format) - Direct URL to background video file. Takes priority over search_terms
- `person_image_url` (string, optional, URL format) - URL to person image for static overlay (JPG, PNG, etc.)
- `person_name` (string, optional) - Name to display as text overlay separate from captions

Configuration (object, optional):
- `voice` (string, optional) - TTS voice identifier, default "kokoro:af_sarah"
- `orientation` (string, optional) - "portrait" (9:16) or "landscape" (16:9), default "portrait"
- `caption_position` (string, optional) - "top", "center", or "bottom", default "bottom"
- `caption_background_color` (string, optional) - Caption background color in hex format, default "#000000"
- `music` (string, optional) - Music mood category (ignored if music_url is provided)
- `music_url` (string, optional, URL format) - Direct URL to background music file (MP3, WAV, etc.). Takes priority over music mood selection
- `music_volume` (string, optional) - "low", "medium", "high", or "muted", default "medium"
- `padding_back` (number, optional, minimum 0) - Padding between scenes in seconds, default 0.5

Other:
- `webhook_url` (string, optional, URL format) - URL for completion callback
- `id` (string, optional) - Custom identifier for tracking (overrides generated job_id)

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
GET /v1/video/short/{video_id}/status
```

Get the current status of a video creation job.

**Parameters**
- `video_id` (path parameter) - Video/Job ID from create response

**Response**
```json
{
  "job_id": "vid_12345abcde",
  "user_id": "user123",
  "status": "processing",
  "progress": 75,
  "scenes_count": 2,
  "current_scene": 1,
  "config": {
    "voice": "kokoro:af_sarah",
    "orientation": "portrait"
  },
  "created_at": "2025-05-25T04:33:00Z",
  "updated_at": "2025-05-25T04:35:30Z",
  "estimated_completion": "2025-05-25T04:36:45Z",
  "cloud_url": "https://your-cdn.com/videos/output.mp4",
  "error_message": null,
  "processing_stages": {
    "tts_generation": "completed",
    "video_search": "completed", 
    "caption_generation": "processing",
    "video_rendering": "pending",
    "upload": "pending"
  }
}
```

**Status Values**
- `processing` - Job is being processed
- `completed` - Job finished successfully
- `failed` - Job failed (see error_message field)

**Processing Stages**
- `tts_generation` - Text-to-speech audio and caption generation
- `video_search` - Background video search and download
- `caption_generation` - Caption timing and formatting
- `video_rendering` - Final video composition and rendering
- `upload` - Cloud storage upload

**Stage Status Values**
- `pending` - Stage not started
- `processing` - Stage in progress
- `completed` - Stage finished successfully
- `failed` - Stage failed

### 3. List User Videos

```http
GET /v1/video/short/list
```

List all short videos for the authenticated user with pagination.

**Query Parameters**
- `limit` (integer, optional) - Maximum number of videos to return, default 50
- `offset` (integer, optional) - Number of videos to skip, default 0

**Response**
```json
{
  "videos": [
    {
      "job_id": "vid_12345abcde",
      "status": "completed",
      "progress": 100,
      "created_at": "2025-05-25T04:33:00Z",
      "cloud_url": "https://your-cdn.com/videos/output.mp4"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

## Music Management Endpoints

### 4. Get Available Music Tags

```http
GET /v1/video/short/music/tags
```

Get all available music moods/tags for background music selection.

**Response**
```json
{
  "tags": [
    {"tag": "happy", "description": "Happy music"},
    {"tag": "sad", "description": "Sad music"},
    {"tag": "epic", "description": "Epic music"},
    {"tag": "calm", "description": "Calm music"},
    {"tag": "dark", "description": "Dark music"},
    {"tag": "energetic", "description": "Energetic music"},
    {"tag": "upbeat", "description": "Upbeat music"},
    {"tag": "chill", "description": "Chill music"},
    {"tag": "dramatic", "description": "Dramatic music"}
  ]
}
```

### 5. List Available Music Moods

```http
GET /v1/video/short/music/moods
```

Lists all available mood categories for background music.

**Response**
```json
{
  "moods": ["happy", "sad", "epic", "calm", "dark", "energetic", "upbeat", "chill", "dramatic"]
}
```

### 6. Get Music by Mood

```http
GET /v1/video/short/music/{mood}
```

Get list of music tracks for a specific mood with detailed information.

**Parameters**
- `mood` (path parameter) - Music mood (happy, sad, epic, calm, dark, energetic, upbeat, chill, dramatic)

**Response**
```json
{
  "tracks": [
    {
      "id": "music_track_name",
      "name": "track.mp3",
      "mood": "happy",
      "duration": 180.5,
      "url": "/music/happy_track.mp3"
    }
  ]
}
```

### 7. Get Music by Tempo

```http
GET /v1/video/short/music/by-tempo/{tempo}
```

Get music tracks filtered by tempo.

**Parameters**
- `tempo` (path parameter) - Music tempo (slow, medium, fast)

**Response**
```json
{
  "tracks": [
    {
      "tag": "calm",
      "tempo": "slow",
      "path": "/storage/music/calm_track.mp3",
      "description": "Calm slow tempo music"
    }
  ]
}
```

### 8. Get Music Recommendations

```http
GET /v1/video/short/music/recommendations/{content_type}
```

Get music recommendations based on content type.

**Parameters**
- `content_type` (path parameter) - Content type (tutorial, gaming, vlog, product, story, comedy, educational, travel, food, fitness)

**Response**
```json
{
  "recommendations": [
    {
      "tag": "upbeat",
      "content_type": "tutorial",
      "path": "/storage/music/upbeat_track.mp3",
      "description": "Upbeat music recommended for tutorial content"
    }
  ]
}
```

### 9. Upload Music Track

```http
POST /v1/video/short/music/upload
Content-Type: multipart/form-data
```

Upload a new music track with mood categorization.

**Request Parameters**
- `file` (required) - Music file (MP3, WAV, M4A, OGG format)
- `mood` (required) - Mood category for the track

**Response**
```json
{
  "id": "music_track_name",
  "name": "track.mp3",
  "mood": "happy",
  "duration": 180.5,
  "url": "/music/happy_track.mp3"
}
```

## Voice Options

The API supports multiple TTS (Text-to-Speech) engines. Format: `engine:voice_name`

### Kokoro TTS (Default)
- `kokoro:af_sarah` - Natural female English (default)
- `kokoro:am_john` - Natural male English
- `kokoro:af_emma` - British female English

### Edge TTS
- `edge-tts:en-US-AriaNeural` - US female
- `edge-tts:en-GB-RyanNeural` - British male

### Streamlabs Polly
- `streamlabs-polly:Brian` - British male
- `streamlabs-polly:Emma` - British female
- `streamlabs-polly:Joey` - US male

## Background Video Sources

The API automatically searches for background videos using multiple providers:

### Primary Sources
1. **Pexels API** - High-quality stock videos with orientation filtering
2. **Pixabay API** - Alternative stock video source
3. **Direct URLs** - Custom video files via `bg_video_url` parameter
4. **Default Fallback** - System default video if no matches found

### Video Selection Priority
1. Direct `bg_video_url` if provided
2. Pexels search using `search_terms` with orientation matching
3. Pixabay search using `search_terms` with orientation matching  
4. Default background video from environment variable

## Music Sources and Moods

### Available Music Moods
- `happy` - Upbeat and cheerful music
- `sad` - Melancholic and emotional music
- `epic` - Cinematic and dramatic music
- `calm` - Peaceful and relaxing music
- `dark` - Mysterious and brooding music
- `energetic` - High-energy and dynamic music
- `upbeat` - Positive and lively music
- `chill` - Relaxed and laid-back music
- `dramatic` - Intense and emotional music

### Music Selection Priority
1. Direct `music_url` if provided (highest priority)
2. Mood-based selection using `music` parameter
3. Default background music from environment variable

### Tempo Categories
- `slow` - Maps to calm, sad moods
- `medium` - Maps to happy, chill moods  
- `fast` - Maps to energetic, upbeat, dramatic moods

### Content Type Recommendations
- `tutorial` - calm, upbeat
- `gaming` - energetic, epic
- `vlog` - happy, chill
- `product` - upbeat, happy
- `story` - dramatic, epic
- `comedy` - happy, upbeat
- `educational` - calm, happy
- `travel` - upbeat, epic
- `food` - happy, calm
- `fitness` - energetic, upbeat

## Video Processing Pipeline

### Single Scene Videos
1. **TTS Generation** - Convert text to speech and generate captions with timing
2. **Video Search** - Find or download background video
3. **Video Rendering** - Compose final video with MoviePy renderer
4. **Upload** - Upload to cloud storage

### Multi-Scene Videos  
1. **TTS Generation** - Process all scenes for speech and captions
2. **Video Search** - Find background videos for each scene
3. **Scene Rendering** - Render each scene individually
4. **Concatenation** - Combine scenes using FFmpeg
5. **Upload** - Upload final concatenated video

### Caption Processing
- Captions are generated from TTS output in SRT format
- Timing is automatically synchronized with audio
- Position can be top, center, or bottom
- Background color is customizable (hex format)

### Person Overlays
- **Person Image Overlay**: Static image overlay positioned in the top-right corner
  - Supported formats: JPG, PNG, GIF
  - Automatically resized and positioned based on video orientation
  - Portrait: 200x200px, Landscape: 250x250px
  - Maintains aspect ratio with intelligent cropping
- **Person Name Overlay**: Text overlay displaying the person's name
  - Positioned below the person image
  - Styled with outline for visibility
  - Font size adapts to video orientation
  - Available for the entire video duration

### Music Integration
- Background music is applied to the entire video
- For multi-scene videos, music is only applied to the first scene to avoid overlap
- Volume levels: low, medium, high, muted
- Supports various audio formats: MP3, WAV, M4A, OGG

## Output Formats

### Portrait Mode (Default)
- Resolution: 1080x1920 (9:16)
- FPS: 30
- Codec: H.264
- Audio: AAC stereo
- Optimized for TikTok, Instagram Reels, YouTube Shorts

### Landscape Mode
- Resolution: 1920x1080 (16:9)
- FPS: 30
- Codec: H.264
- Audio: AAC stereo
- Optimized for YouTube, Facebook, traditional platforms

## Authentication & Authorization

All endpoints require authentication using the `@authenticate` decorator. The system tracks user-specific video creation and retrieval.

## Environment Variables

Required environment variables:
- `PEXELS_API_KEY` - API key for Pexels video search
- `PIXABAY_API_KEY` - API key for Pixabay video search  
- `DEFAULT_BACKGROUND_VIDEO` - Path to fallback video
- `DEFAULT_BACKGROUND_MUSIC` - Path to fallback music

## Error Handling

### Common Error Responses
```json
{
  "error": "Error message description",
  "timestamp": "2025-05-25T04:33:00Z"
}
```

### Processing Errors
- Video search failures automatically fallback to alternative sources
- Missing environment variables cause startup failures
- Invalid configurations are rejected with validation errors
- Processing errors are tracked in job status with detailed error messages

### File Cleanup
- Temporary files are automatically cleaned up after processing
- Individual scene videos are removed after concatenation
- Failed jobs retain temporary files for debugging

## Webhook Notifications

When a webhook_url is provided, the system sends POST requests with status updates:

```json
{
  "job_id": "vid_12345abcde",
  "status": "completed",
  "output_url": "https://your-cdn.com/videos/output.mp4",
  "duration": 180,
  "size": 15728640,
  "created_at": "2025-05-25T04:33:00Z"
}
```

## Performance & Limitations

### Processing Time
- Single scene: ~30-60 seconds
- Multi-scene: ~45-90 seconds per scene
- Depends on TTS processing and video search time

### File Size Limits
- No explicit limits on input text length
- Background videos are downloaded and processed locally
- Output videos are uploaded to cloud storage

### Concurrent Processing
- Jobs are processed through a queue system
- Status tracking allows monitoring of multiple concurrent jobs
- User-specific job isolation and tracking

## Related Resources

- [Music Management](music.md) - Background music endpoints and management
- [Video Composition Service](../../video_composition.md) - MoviePy rendering details
- [Audio Speech Service](../../audio/speech.md) - TTS generation details
