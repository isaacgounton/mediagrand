# Short Video Creator API Endpoints

The Short Video Creator service provides endpoints for creating engaging short-form videos suitable for platforms like TikTok, Instagram Reels, and YouTube Shorts. It runs as a separate service alongside dahopevi and uses its TTS and processing capabilities.

## Base URL

The service runs on port 3123 by default:
```
http://localhost:3123
```

## Available Endpoints

### Create Short Video
- **URL**: `/api/short/create`
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
    "captionBackgroundColor": "blue",
    "voice": "en-US-AvaNeural",
    "orientation": "portrait",
    "musicVolume": "high"
  }
}
```

#### Parameters

**scenes[]**:
- `text` (string): Text to be spoken in the video
- `searchTerms` (string[]): Search terms for video background (2-3 recommended)

**config**:
- `paddingBack` (number, optional): Duration in ms to play after speech ends (default: 1500)
- `music` (string, optional): Music mood tag (`sad`, `melancholic`, `happy`, `euphoric`, `excited`, `chill`, `uneasy`, `angry`, `dark`, `hopeful`, `contemplative`, `funny`)
- `captionPosition` (string, optional): Position of captions (`top`, `center`, `bottom`)
- `captionBackgroundColor` (string, optional): Background color for captions (CSS color)
- `voice` (string, optional): TTS voice to use (default: "af_heart")
- `ttsEngine` (string, optional): TTS engine to use (`kokoro`, `edge-tts`, `streamlabs-polly`) (default: "kokoro")
- `orientation` (string, optional): Video orientation (`portrait`, `landscape`)
- `musicVolume` (string, optional): Volume of background music (`muted`, `low`, `medium`, `high`)

#### Response

```json
{
  "id": "video_id",
  "status": "processing"
}
```

### Get Video Status
- **URL**: `/api/short/status/:id`
- **Method**: `GET`
- **Description**: Gets the status of a video creation job

#### Response

```json
{
  "id": "video_id",
  "status": "ready" | "processing" | "failed"
}
```

### List Available Voices (Legacy)
- **URL**: `/api/voices`
- **Method**: `GET`
- **Description**: Lists available TTS voices for Kokoro engine

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
    "edge-tts": ["af_heart", "af_alloy", "af_nova", "am_adam", "am_echo"],
    "streamlabs-polly": ["af_heart", "af_alloy", "af_nova", "am_adam", "am_echo"]
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
- **URL**: `/api/short/video/:id`
- **Method**: `GET`
- **Description**: Downloads the completed video file
- **Response**: Video file (MP4)

### Delete Video
- **URL**: `/api/short/video/:id`
- **Method**: `DELETE`
- **Description**: Deletes a video and its associated files

### List All Videos
- **URL**: `/api/short/videos`
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

## Error Responses

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Video not found
- `500 Internal Server Error`: Processing error

Example error response:
```json
{
  "error": "Video not found",
  "status": 404
}
```

## Usage Example

Create a short video:
```bash
curl -X POST http://localhost:3123/api/short/create \
  -H 'Content-Type: application/json' \
  -d '{
    "scenes": [
      {
        "text": "Welcome to my channel",
        "searchTerms": ["welcome", "greeting", "friendly"]
      }
    ],
    "config": {
      "voice": "en-US-AvaNeural",
      "orientation": "portrait",
      "music": "happy"
    }
  }'
```

Check status:
```bash
curl http://localhost:3123/api/short/status/video_id
```

Download video:
```bash
curl -o video.mp4 http://localhost:3123/api/short/video/video_id
