# Music Management API for Short Videos

## Overview
Comprehensive endpoints for managing background music in short videos. Supports mood-based music selection, tempo filtering, content type recommendations, custom music uploads, and music library management.

## Base URLs
```
/v1/video/short/music    # V1 API endpoints
/                        # Alternative music API endpoints
```

## V1 API Endpoints

### 1. Get Available Music Tags

```http
GET /v1/video/short/music-tags
```

Get all available music moods/tags for background music selection.

**Response**
```json
[
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
```

### 2. Get Music by Mood

```http
GET /v1/video/short/music-by-mood/{mood}
```

Get music tracks filtered by specific mood.

**Parameters**
- `mood` (path parameter) - Music mood (happy, sad, epic, calm, dark, energetic, upbeat, chill, dramatic)

**Response**
```json
[
  {
    "tag": "happy",
    "path": "/storage/music/happy_track.mp3",
    "description": "Happy music"
  }
]
```

### 3. Get Music by Tempo

```http
GET /v1/video/short/music-by-tempo/{tempo}
```

Get music tracks filtered by tempo.

**Parameters**
- `tempo` (path parameter) - Music tempo (slow, medium, fast)

**Response**
```json
[
  {
    "tag": "calm",
    "tempo": "slow",
    "path": "/storage/music/calm_track.mp3",
    "description": "Calm slow tempo music"
  }
]
```

### 4. Get Music Recommendations

```http
GET /v1/video/short/music-recommendations/{content_type}
```

Get music recommendations based on content type.

**Parameters**
- `content_type` (path parameter) - Content type (tutorial, gaming, vlog, product, story, comedy, educational, travel, food, fitness)

**Response**
```json
[
  {
    "tag": "upbeat",
    "content_type": "tutorial",
    "path": "/storage/music/upbeat_track.mp3",
    "description": "Upbeat music recommended for tutorial content"
  }
]
```

## Alternative Music API Endpoints

### 5. List Available Music Moods

```http
GET /moods
```

Lists all available mood categories for background music.

**Response**
```json
{
  "moods": [
    "happy",
    "sad", 
    "epic",
    "calm",
    "dark",
    "energetic",
    "upbeat",
    "chill",
    "dramatic"
  ]
}
```

### 6. Upload Music Track

```http
POST /upload
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

**Status Codes**
- `200` - Successfully uploaded
- `400` - Invalid request (missing file/mood or invalid mood)
- `500` - Server error

### 7. Get Music Tracks by Mood

```http
GET /{mood}
```

Retrieves a list of music tracks for a specific mood with detailed information.

**Parameters**
- `mood` (path parameter) - Mood category to filter by

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

### 8. Get Music Tags (Alternative)

```http
GET /tags
```

Alternative endpoint to get available music tags.

**Response**
```json
{
  "tags": [
    {"tag": "happy", "description": "Happy music"},
    {"tag": "sad", "description": "Sad music"}
  ]
}
```

### 9. Get Music by Tempo (Alternative)

```http
GET /by-tempo/{tempo}
```

Alternative endpoint for tempo-based music filtering.

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

### 10. Get Music Recommendations (Alternative)

```http
GET /recommendations/{content_type}
```

Alternative endpoint for content-based music recommendations.

**Parameters**
- `content_type` (path parameter) - Content type

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

## Music Selection System

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

## Music Manager Implementation

### File Naming Convention
Music files are automatically prefixed with mood categories:
- `happy_track.mp3`
- `epic_cinematic_music.mp3`
- `calm_peaceful_sounds.wav`

### Direct Filename Selection
You can reference specific music files by their exact filename:
```json
{
  "config": {
    "music": "music_Aurora_on_the_Boulevard_-_National_Sweetheart"
  }
}
```

### Mood-Based Random Selection
When using mood categories, the system randomly selects from matching files:
```json
{
  "config": {
    "music": "happy"  // Randomly selects from happy_* files
  }
}
```

## File Requirements

### Supported Audio Formats
- **MP3** (recommended)
- **WAV** 
- **M4A**
- **OGG**

### File Management
- Music files are stored in `LOCAL_STORAGE_PATH/music/` directory
- Files are automatically organized by mood prefix
- Supports random selection within mood categories
- Automatic file extension detection

### Quality Requirements
- No explicit file size limits
- Duration automatically detected using FFmpeg
- All standard audio bitrates and sample rates supported

## Usage with Short Video Creation

### Primary Music Selection Methods

1. **Direct URL** (highest priority):
```json
{
  "config": {
    "music_url": "https://example.com/background-music.mp3"
  }
}
```

2. **Mood-based selection**:
```json
{
  "config": {
    "music": "upbeat",
    "music_volume": "medium"
  }
}
```

3. **Specific filename**:
```json
{
  "config": {
    "music": "music_specific_track_name"
  }
}
```

### Volume Levels
- `low` - Reduced volume for background ambiance
- `medium` - Standard volume (default)
- `high` - Louder volume for prominent music
- `muted` - No background music

### Multi-Scene Video Behavior
- Background music is applied to the entire video
- For multi-scene videos, music is only applied to the first scene to avoid overlap
- Subsequent scenes have volume set to "muted" automatically

## Authentication & Authorization

All V1 API endpoints require authentication using the `@authenticate` decorator. Alternative endpoints may have different authentication requirements.

## Error Handling

### Common Error Responses
```json
{
  "error": "Error message description",
  "timestamp": "2025-05-25T04:33:00Z"
}
```

### File Not Found Handling
- If specific music file not found, returns None
- Mood-based selection falls back to available tracks
- System uses default background music from environment variable as final fallback

### Upload Error Handling
- Invalid mood categories are rejected
- File format validation using extension detection
- Duplicate filename handling with automatic renaming

## Environment Configuration

### Required Environment Variables
- `DEFAULT_BACKGROUND_MUSIC` - Path to fallback music file when no matches found

### Storage Configuration
- Music directory: `LOCAL_STORAGE_PATH/music/`
- Automatic directory creation if not exists
- File cleanup and organization handled automatically

## Performance Considerations

### File Selection
- Random selection from matching files for mood-based queries
- Efficient file system scanning with pattern matching
- Cached file listings for improved performance

### Processing
- FFmpeg integration for duration detection
- Automatic format conversion if needed
- Background processing for large file uploads
