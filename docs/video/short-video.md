# Short Video Creator API Endpoints

The Short Video Creator service provides endpoints for creating engaging short-form videos suitable for platforms like TikTok, Instagram Reels, and YouTube Shorts. It runs as a separate service alongside dahopevi and uses its TTS and processing capabilities.

## Base URL

The service runs on port 3123 by default:
```
http://localhost:3123
```

## Environment Variables

### Required Environment Variables

- **PEXELS_API_KEY**: Required for video background generation. Get your free API key from https://www.pexels.com/api/key/

### Optional Environment Variables

- **PORT**: Port number for the service (default: 3123)
- **LOG_LEVEL**: Logging level (default: "info")
- **WHISPER_VERBOSE**: Enable verbose Whisper output (default: false)
- **DOCKER**: Set to "true" when running in Docker
- **DEV**: Set to "true" for development mode
- **DATA_DIR_PATH**: Custom data directory path (default: ~/.ai-agents-az-video-generator)
- **SHARED_WHISPER_PATH**: Path to shared Whisper installation (for Docker environments)
- **DAHOPEVI_BASE_URL** or **DAHOPEVI_URL**: Base URL for dahopevi API (default: https://api.dahopevi.com)
- **DAHOPEVI_API_KEY**: API key for dahopevi services (required for Edge TTS)
- **WHISPER_MODEL**: Whisper model to use (default: "medium.en", options: "tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "medium.en", "large-v1", "large-v2", "large-v3", "large-v3-turbo")
- **KOKORO_MODEL_PRECISION**: Kokoro model precision (default: "fp32", options: "fp32", "fp16", "q8", "q4", "q4f16")
- **CONCURRENCY**: Number of concurrent video processing jobs (Docker performance setting)
- **VIDEO_CACHE_SIZE_IN_BYTES**: Video cache size limit in bytes (Docker memory management)

## Available Endpoints

### Create Short Video
- **URL**: `/api/short-video`
- **Method**: `POST`
- **Description**: Creates a short video from provided scenes and configuration

#### Request Body

```json
{
  "scenes": [
    {
      "text": "Text to be spoken in the video",
      "searchTerms": ["search", "terms", "for", "video"]
    }
  ],
  "config": {
    "paddingBack": 1500,
    "music": "happy",
    "captionPosition": "bottom",
    "captionBackgroundColor": "#0000ff",
    "voice": "af_heart",
    "ttsEngine": "kokoro",
    "orientation": "portrait",
    "musicVolume": "high"
  }
}
```

#### Required Parameters

**scenes** (array, required):
- `text` (string, required): Text to be spoken in the video
- `searchTerms` (array of strings, required): Search terms for video background - should be 1 word each, and at least 2-3 search terms recommended for each scene

**config** (object, required): Configuration object for rendering

#### Optional Config Parameters

- `paddingBack` (number, optional): Duration in ms to play after speech ends (default: 1500)
- `music` (string, optional): Music mood tag - valid values: `sad`, `melancholic`, `happy`, `euphoric/high`, `excited`, `chill`, `uneasy`, `angry`, `dark`, `hopeful`, `contemplative`, `funny/quirky`
- `captionPosition` (string, optional): Position of captions (`top`, `center`, `bottom`)
- `captionBackgroundColor` (string, optional): Background color for captions (valid CSS color like `#ff0000`)
- `voice` (string, optional): TTS voice to use (default: "af_heart") - see voice lists below
- `ttsEngine` (string, optional): TTS engine to use (`kokoro`, `edge-tts`, `streamlabs-polly`) (default: "kokoro")
- `orientation` (string, optional): Video orientation (`portrait`, `landscape`) (default: "portrait")
- `musicVolume` (string, optional): Volume of background music (`muted`, `low`, `medium`, `high`) (default: "high")

## TTS Engines and Voice Support

### Kokoro Engine (Default)
- **Engine ID**: `kokoro`
- **Description**: Local TTS engine with natural-sounding voices
- **Available Voices**: Use `/api/voices` or `/api/tts-voices/kokoro` to get current list
- **All Kokoro Voices**:
  - **Female (af_*)**: `af_heart`, `af_alloy`, `af_aoede`, `af_bella`, `af_jessica`, `af_kore`, `af_nicole`, `af_nova`, `af_river`, `af_sarah`, `af_sky`
  - **Male (am_*)**: `am_adam`, `am_echo`, `am_eric`, `am_fenrir`, `am_liam`, `am_michael`, `am_onyx`, `am_puck`, `am_santa`
  - **British Female (bf_*)**: `bf_emma`, `bf_isabella`, `bf_alice`, `bf_lily`
  - **British Male (bm_*)**: `bm_george`, `bm_lewis`, `bm_daniel`, `bm_fable`

### Edge TTS Engine
- **Engine ID**: `edge-tts`
- **Description**: Microsoft Edge TTS via dahopevi API
- **Available Voices**: Use `/api/tts-voices/edge-tts` to get current list
- **Common Voices**: `en-US-AriaNeural`, `en-US-JennyNeural`, `en-US-GuyNeural`, etc.
- **Note**: Requires DAHOPEVI_API_KEY environment variable

### Streamlabs Polly Engine
- **Engine ID**: `streamlabs-polly`
- **Description**: Amazon Polly via Streamlabs
- **Available Voices**: Use `/api/tts-voices/streamlabs-polly` to get current list

**Important**: Voice names are specific to each engine. Use the appropriate voice list endpoints to get valid voices for your chosen TTS engine.

#### Response

```json
{
  "videoId": "video_id"
}
```

### Get Video Status
- **URL**: `/api/short-video/:videoId/status`
- **Method**: `GET`
- **Description**: Gets the status of a video creation job

#### Response

```json
{
  "status": "ready" | "processing" | "failed"
}
```

### List Available Voices (Legacy - Kokoro only)
- **URL**: `/api/voices`
- **Method**: `GET`
- **Description**: Lists available TTS voices for Kokoro engine only

#### Response

```json
[
  "af_heart",
  "af_alloy", 
  "af_nova",
  "am_adam",
  "am_echo"
]
```

### List Available TTS Engines
- **URL**: `/api/tts-engines`
- **Method**: `GET`
- **Description**: Lists all available TTS engines

#### Response

```json
{
  "engines": [
    "kokoro",
    "edge-tts",
    "streamlabs-polly"
  ]
}
```

### List All TTS Voices
- **URL**: `/api/tts-voices`
- **Method**: `GET`
- **Description**: Lists all available TTS voices for all engines

#### Response

```json
{
  "voices": {
    "kokoro": ["af_heart", "af_alloy", "af_nova", "am_adam", "am_echo"],
    "edge-tts": ["en-US-AriaNeural", "en-US-JennyNeural", "en-US-GuyNeural"],
    "streamlabs-polly": ["Joanna", "Matthew", "Ivy"]
  }
}
```

### List Voices for Specific TTS Engine
- **URL**: `/api/tts-voices/:engine`
- **Method**: `GET`
- **Description**: Lists available voices for a specific TTS engine

#### Parameters
- `engine` (string): TTS engine name (`kokoro`, `edge-tts`, `streamlabs-polly`)

#### Response

```json
{
  "voices": [
    "af_heart",
    "af_alloy", 
    "af_nova",
    "am_adam",
    "am_echo"
  ]
}
```

### List Available Music Tags
- **URL**: `/api/music-tags`
- **Method**: `GET`
- **Description**: Lists all available music mood tags

#### Response

```json
[
  "happy",
  "sad",
  "excited",
  "chill"
]
```

### Get Video File
- **URL**: `/api/short-video/:videoId`
- **Method**: `GET`
- **Description**: Downloads the completed video file
- **Response**: Video file (MP4)

### Delete Video
- **URL**: `/api/short-video/:videoId`
- **Method**: `DELETE`
- **Description**: Deletes a video and its associated files

#### Response

```json
{
  "success": true
}
```

### List All Videos
- **URL**: `/api/short-videos`
- **Method**: `GET`
- **Description**: Lists all videos in the system

#### Response

```json
{
  "videos": [
    {
      "id": "video_id",
      "status": "ready"
    }
  ]
}
```

### Get Temporary File
- **URL**: `/api/tmp/:tmpFile`
- **Method**: `GET`
- **Description**: Downloads temporary files (audio/video) from the temp directory
- **Response**: Audio/Video file (MP3, WAV, MP4)

### Get Music File
- **URL**: `/api/music/:fileName`
- **Method**: `GET`
- **Description**: Downloads music files from the music directory
- **Response**: Audio file (MP3)

## Admin Endpoints

### Get Queue Status
- **URL**: `/api/admin/queue-status`
- **Method**: `GET`
- **Description**: Gets the current status of the video processing queue (for debugging stuck videos)

#### Response

```json
{
  "queueLength": 2,
  "isProcessing": true,
  "items": [
    {
      "id": "video_id_1",
      "timestamp": 1640995200000,
      "age": 120000
    },
    {
      "id": "video_id_2", 
      "timestamp": 1640995260000,
      "age": 60000
    }
  ]
}
```

#### Response Fields
- `queueLength`: Number of videos in the processing queue
- `isProcessing`: Whether the queue processor is currently running
- `items`: Array of queued items with their IDs, timestamps, and age in milliseconds

### Clear Stuck Videos
- **URL**: `/api/admin/clear-stuck-videos`
- **Method**: `POST`
- **Description**: Removes videos that have been stuck in the queue for more than 30 minutes

#### Response

```json
{
  "message": "Cleared stuck videos",
  "removed": 1,
  "clearedProcessing": true
}
```

#### Response Fields
- `removed`: Number of stuck videos removed from queue
- `clearedProcessing`: Whether the processing flag was reset due to empty queue

### Restart Queue Processing
- **URL**: `/api/admin/restart-queue`
- **Method**: `POST`
- **Description**: Forces the queue processor to restart (useful if it gets stuck)

#### Response

```json
{
  "message": "Queue processing restarted"
}
```

## MCP (Model Context Protocol) Support

The service provides MCP support for integration with AI assistants and automation tools.

### MCP Server Endpoints

- **SSE Connection**: `GET /api/mcp/sse`
- **Messages**: `POST /api/mcp/messages`

### Available MCP Tools

#### create-short-video
Creates a short video from a list of scenes with the same parameters as the REST API.

**Parameters:**
- `scenes`: Array of scene objects
- `config`: Configuration object for rendering

#### get-video-status
Gets the status of a video creation job by video ID.

**Parameters:**
- `videoId`: The ID of the video to check

#### list-available-voices
Lists all available TTS voices for all engines.

**Parameters:** None

**Returns:** JSON object with voices organized by engine:
```json
{
  "kokoro": ["af_heart", "af_alloy", ...],
  "edge-tts": ["en-US-AriaNeural", "fr-FR-DeniseNeural", ...],
  "streamlabs-polly": ["Joanna", "Matthew", ...]
}
```

#### list-voices-for-engine
Lists available voices for a specific TTS engine.

**Parameters:**
- `engine`: TTS engine name (`kokoro`, `edge-tts`, `streamlabs-polly`)

**Returns:** JSON object with engine name and its voices

#### list-tts-engines
Lists all available TTS engines.

**Parameters:** None

**Returns:** JSON object with available engines:
```json
{
  "engines": ["kokoro", "edge-tts", "streamlabs-polly"]
}
```

#### list-all-videos
Lists all videos in the system with their status.

**Parameters:** None

**Returns:** JSON object with videos and their status:
```json
{
  "videos": [
    {"id": "video_id", "status": "ready"},
    {"id": "video_id2", "status": "processing"}
  ]
}
```

#### list-music-tags
Lists all available music mood tags.

**Parameters:** None

**Returns:** JSON object with available music tags:
```json
{
  "musicTags": ["happy", "sad", "excited", "chill", ...]
}
```

### Admin MCP Tools

#### get-queue-status
Gets the current status of the video processing queue (admin tool).

**Parameters:** None

**Returns:** Queue status with processing state and item details

#### clear-stuck-videos
Removes videos that have been stuck in the queue for more than 30 minutes (admin tool).

**Parameters:** None

**Returns:** Number of videos removed and processing state changes

#### restart-queue
Forces restart of the video processing queue (admin tool).

**Parameters:** None

**Returns:** Confirmation message

## Error Responses

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid parameters or validation failed
- `404 Not Found`: Video not found
- `500 Internal Server Error`: Processing error

Example validation error response:
```json
{
  "error": "Validation failed",
  "message": "Validation failed for 2 field(s): scenes, config",
  "missingFields": {
    "scenes": "Required",
    "config": "Required"
  }
}
```

## Usage Examples

### Basic Example (Kokoro Engine)
```bash
curl -X POST https://shorts.dahopevi.com/api/short-video \
  -H 'Content-Type: application/json' \
  -d '{
    "scenes": [
      {
        "text": "Welcome to my channel",
        "searchTerms": ["welcome", "greeting", "friendly"]
      }
    ],
    "config": {
      "voice": "af_heart",
      "ttsEngine": "kokoro",
      "orientation": "portrait",
      "music": "happy"
    }
  }'
```

### Using Edge TTS Engine
```bash
curl -X POST https://shorts.dahopevi.com/api/short-video \
  -H 'Content-Type: application/json' \
  -d '{
    "scenes": [
      {
        "text": "Welcome to my channel",
        "searchTerms": ["welcome", "greeting", "friendly"]
      }
    ],
    "config": {
      "voice": "en-US-AriaNeural",
      "ttsEngine": "edge-tts",
      "orientation": "portrait",
      "music": "happy"
    }
  }'
```

### Multiple Scenes Example
```bash
curl -X POST https://shorts.dahopevi.com/api/short-video \
  -H 'Content-Type: application/json' \
  -d '{
    "scenes": [
      {
        "text": "Welcome to my channel",
        "searchTerms": ["welcome", "greeting"]
      },
      {
        "text": "Today we will learn something amazing",
        "searchTerms": ["learning", "education", "amazing"]
      }
    ],
    "config": {
      "voice": "bm_lewis",
      "ttsEngine": "kokoro",
      "orientation": "landscape",
      "music": "excited",
      "captionPosition": "center",
      "captionBackgroundColor": "#ff0000"
    }
  }'
```

Check status:
```bash
curl https://shorts.dahopevi.com/api/short-video/video_id/status
```

Download video:
```bash
curl -o video.mp4 https://shorts.dahopevi.com/api/short-video/video_id
```

## Troubleshooting

### Common Validation Errors

1. **Missing required fields**: Ensure both `scenes` and `config` objects are provided
2. **Invalid voice for engine**: Make sure the voice name is valid for the selected TTS engine
3. **Invalid search terms**: Search terms should be single words, provide 2-3 per scene
4. **Invalid enum values**: Check that orientation, music, captionPosition, etc. use valid enum values

### Voice Compatibility

- **Kokoro voices**: Use internal voice names like `af_heart`, `bm_lewis`
- **Edge TTS voices**: Use Microsoft voice names like `en-US-AriaNeural`, `en-US-JennyNeural`
- **Streamlabs Polly voices**: Use Amazon Polly voice names

Always check the current voice list using the appropriate `/api/tts-voices/:engine` endpoint before making requests.

### Video Processing Issues

If videos get stuck in "processing" status, use the admin endpoints:

#### Check Queue Status
```bash
curl https://shorts.dahopevi.com/api/admin/queue-status
```

#### Clear Stuck Videos (removes videos older than 30 minutes)
```bash
curl -X POST https://shorts.dahopevi.com/api/admin/clear-stuck-videos
```

#### Restart Queue Processing
```bash
curl -X POST https://shorts.dahopevi.com/api/admin/restart-queue
```

#### Common Processing Issues
1. **Videos stuck in processing**: Use `/api/admin/clear-stuck-videos` to remove old items
2. **Queue not processing**: Use `/api/admin/restart-queue` to force restart
3. **Multiple videos stuck**: Check `/api/admin/queue-status` for queue state and use clear/restart as needed
