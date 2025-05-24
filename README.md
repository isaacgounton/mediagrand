# Short Video Creation Service

This service creates short-form videos suitable for platforms like TikTok, Instagram Reels, and YouTube Shorts.

## Features

- **Text-to-Speech with Multiple Engines**
  - Kokoro-ONNX for natural voices
  - Edge TTS for real-time synthesis
  - Streamlabs Polly for professional voices

- **Professional Video Composition**
  - Remotion-powered dynamic compositions
  - Portrait (9:16) and Landscape (16:9) formats
  - Customizable caption styles and positions
  - Synchronized audio and captions
  - Background music with mood selection
  - High-quality video rendering with FFmpeg

- **Content Sources**
  - Pexels API integration for background videos
  - Built-in mood-based music library
  - Support for custom video and audio assets
- Mood-based background music selection
- Portrait and landscape video support
- Customizable captions with timing
- Progress tracking and status updates
- Webhook notifications for completion

## API Endpoints

### Create Short Video
```http
POST /v1/video/short/create
```

Request body:
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

### Check Video Status
```http
GET /v1/video/short/status/{job_id}
```

Response:
```json
{
  "status": "processing|completed|failed",
  "progress": 75,
  "current_stage": "video_rendering",
  "total_scenes": 2,
  "current_scene": 2,
  "output_url": "https://your-cdn.com/videos/output.mp4"
}
```

### List Available Music Moods
```http
GET /v1/video/music/moods
```

Response:
```json
{
  "moods": [
    "upbeat",
    "happy",
    "calm",
    "chill",
    "epic",
    "dramatic",
    "dark",
    "sad"
  ]
}
```

### Upload Music Track
```http
POST /v1/video/music/upload
Content-Type: multipart/form-data
```

Request parameters:
- `file`: Music file (MP3/WAV)
- `mood`: Music mood category
- `name`: Optional custom name

Response:
```json
{
  "id": "music_12345",
  "name": "uploaded_track.mp3",
  "mood": "upbeat",
  "duration": 180.5,
  "url": "https://your-cdn.com/music/uploaded_track.mp3"
}
```

### Get Music by Mood
```http
GET /v1/video/music/{mood}
```

Response:
```json
{
  "tracks": [
    {
      "id": "music_12345",
      "name": "happy_tune_1.mp3",
      "mood": "upbeat",
      "duration": 180.5,
      "url": "https://your-cdn.com/music/happy_tune_1.mp3"
    },
    {
      "id": "music_12346",
      "name": "happy_tune_2.mp3",
      "mood": "upbeat",
      "duration": 150.0,
      "url": "https://your-cdn.com/music/happy_tune_2.mp3"
    }
  ]
}
```

## Configuration Options

### Voice Options
- `kokoro:af_sarah` - Natural English voice (Kokoro)
- `edge-tts:en-US-AriaNeural` - Microsoft Edge TTS
- `streamlabs-polly:Brian` - Amazon Polly voice

### Caption Positions
- `top`
- `center`
- `bottom`

### Music Moods
- `upbeat`
- `happy`
- `calm`
- `chill`
- `epic`
- `dramatic`
- `dark`
- `sad`

### Music Volumes
- `high` (30% volume)
- `medium` (20% volume)
- `low` (10% volume)
- `muted` (0% volume)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
cd remotion && bash init.sh
```

2. Install background music:
```bash
bash scripts/install_music.sh
```

3. Set environment variables:
```bash
export PEXELS_API_KEY="your-pexels-api-key"
```

## Docker Deployment

Build and run with Docker:
```bash
docker build -t short-video-maker .
docker run -p 8080:8080 -e PEXELS_API_KEY="your-key" short-video-maker
```

## Processing Stages

1. **TTS Generation**
   - AI-powered voice synthesis
   - Automatic caption timing
   - Multi-engine support (Kokoro/Edge/Polly)

2. **Video Search & Processing**
   - Intelligent background video search (Pexels)
   - Smart video cropping and resizing
   - Format optimization for target platforms
   - Cache management for frequently used assets

3. **Professional Video Composition**
   - Dynamic React-based compositions (Remotion)
   - Professional motion graphics
   - Synchronized audio/video/captions
   - Mood-matched background music
   - High-quality FFmpeg encoding

## Contributing

1. Choose royalty-free music files
2. Add them to `storage/music/` with appropriate mood prefixes
3. Test with different voice and music combinations
