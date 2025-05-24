# Music Management API for Short Videos

## Overview
Endpoints for managing background music in short videos. Supports mood-based music selection, custom music uploads, and music library management.

## Base URL
```
https://api.example.com/v1/video/short/music
```

## Endpoints

### 1. List Available Music Moods

```http
GET /moods
```

Lists all available mood categories for background music.

**Response**
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

**Status Codes**
- `200` - Success
- `500` - Server error

### 2. Upload Music Track

```http
POST /upload
Content-Type: multipart/form-data
```

Upload a new music track with mood categorization.

**Request Parameters**
- `file` (required) - Music file (MP3/WAV format)
- `mood` (required) - Mood category for the track
- `name` (optional) - Custom name for the track

**Curl Example**
```bash
curl -X POST https://api.example.com/v1/video/short/music/upload \
  -F "file=@track.mp3" \
  -F "mood=upbeat" \
  -F "name=my_happy_tune"
```

**Response**
```json
{
  "id": "music_12345",
  "name": "my_happy_tune.mp3",
  "mood": "upbeat",
  "duration": 180.5,
  "url": "https://api.example.com/music/my_happy_tune.mp3"
}
```

**Status Codes**
- `200` - Successfully uploaded
- `400` - Invalid request (missing file/mood or invalid mood)
- `500` - Server error

### 3. Get Music by Mood

```http
GET /{mood}
```

Retrieves a list of music tracks for a specific mood.

**Parameters**
- `mood` (path parameter) - Mood category to filter by

**Response**
```json
{
  "tracks": [
    {
      "id": "music_12345",
      "name": "happy_tune_1.mp3",
      "mood": "upbeat",
      "duration": 180.5,
      "url": "https://api.example.com/music/happy_tune_1.mp3"
    },
    {
      "id": "music_12346",
      "name": "happy_tune_2.mp3",
      "mood": "upbeat",
      "duration": 150.0,
      "url": "https://api.example.com/music/happy_tune_2.mp3"
    }
  ]
}
```

**Status Codes**
- `200` - Success (empty array if no tracks found)
- `400` - Invalid mood category
- `500` - Server error

## File Requirements

### Supported Audio Formats
- MP3 (recommended)
- WAV

### File Size Limits
- Maximum file size: 50MB
- Recommended duration: 30 seconds to 5 minutes

### Quality Requirements
- Minimum bitrate: 128kbps
- Recommended bitrate: 256kbps
- Sample rate: 44.1kHz or higher

## Usage with Short Video Creation

When creating short videos, specify the music settings in the video creation request:

```json
{
  "config": {
    "music": "upbeat",      // Mood category
    "music_volume": "medium" // Volume level
  }
}
```

### Volume Levels
- `high` (30% of original)
- `medium` (20% of original)
- `low` (10% of original)
- `muted` (0% - no music)

## Rate Limiting

- Maximum 100 requests per hour per API key
- Maximum 50MB total upload size per hour
- Maximum 1000 tracks in library per account
