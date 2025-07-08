# Enhanced Silence & Speech Detection API

## 1. Overview

The `/v1/media/silence` endpoint provides advanced audio analysis capabilities using both traditional silence detection and modern Voice Activity Detection (VAD). This enhanced API can detect speech segments with high accuracy using librosa-based audio analysis, while maintaining backwards compatibility with the original FFmpeg-based silence detection.

### 🚀 Enhanced Features
- **Advanced Voice Activity Detection (VAD)**: Uses librosa and energy-based analysis for precise speech detection
- **Configurable Volume Thresholds**: Dynamic threshold calculation based on audio characteristics
- **Temporal Smoothing**: Reduces noise and improves segment quality
- **Automatic Audio Analysis**: Provides optimal parameter recommendations
- **Backwards Compatibility**: Supports legacy FFmpeg silence detection
- **Confidence Scoring**: Assigns confidence scores to detected segments

## 2. Endpoints

### Main Detection Endpoint
```
POST /v1/media/silence
```

### Audio Analysis Endpoint
```
POST /v1/media/silence/analyze
```

## 3. Request

### Headers

- `x-api-key` (required): The API key for authentication.

### Body Parameters

#### Enhanced Parameters (Recommended)
- `media_url` (required, string): The URL of the media file to be processed.
- `volume_threshold` (optional, number): Volume threshold percentage (0-100) for speech detection. Default is `40`.
- `use_advanced_vad` (optional, boolean): Enable advanced VAD processing. Default is `true`.
- `min_speech_duration` (optional, number): Minimum duration (in seconds) for a speech segment. Default is `0.5`.
- `speech_padding_ms` (optional, integer): Padding around speech segments in milliseconds. Default is `50`.
- `silence_padding_ms` (optional, integer): Padding for segment merging in milliseconds. Default is `450`.
- `webhook_url` (optional, string): The URL to which the response should be sent as a webhook.
- `id` (optional, string): A unique identifier for the request.

#### Legacy Parameters (Backwards Compatibility)
- `start` (optional, string): Start time in format `HH:MM:SS.ms` (FFmpeg mode only).
- `end` (optional, string): End time in format `HH:MM:SS.ms` (FFmpeg mode only).
- `noise` (optional, string): Noise threshold in decibels (e.g., `-30dB`) (FFmpeg mode only).
- `duration` (optional, number): Minimum silence duration in seconds (FFmpeg mode only).
- `mono` (optional, boolean): Process as mono audio (FFmpeg mode only). Default is `true`.

The enhanced API supports the following JSON schema:

```python
{
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "volume_threshold": {"type": "number", "minimum": 0, "maximum": 100},
        "use_advanced_vad": {"type": "boolean"},
        "min_speech_duration": {"type": "number", "minimum": 0.1},
        "speech_padding_ms": {"type": "integer", "minimum": 0},
        "silence_padding_ms": {"type": "integer", "minimum": 0},
        "start": {"type": "string"},
        "end": {"type": "string"},
        "noise": {"type": "string"},
        "duration": {"type": "number", "minimum": 0.1},
        "mono": {"type": "boolean"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["media_url"],
    "additionalProperties": False
}
```

### Example Requests

#### Enhanced VAD Detection (Recommended)

```json
{
    "media_url": "https://example.com/audio.mp3",
    "volume_threshold": 40,
    "use_advanced_vad": true,
    "min_speech_duration": 0.5,
    "speech_padding_ms": 100,
    "silence_padding_ms": 500,
    "webhook_url": "https://example.com/webhook",
    "id": "vad-detection-001"
}
```

```bash
curl -X POST \
  https://api.example.com/v1/media/silence \
  -H 'x-api-key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "media_url": "https://example.com/audio.mp3",
    "volume_threshold": 40,
    "use_advanced_vad": true,
    "min_speech_duration": 0.5,
    "speech_padding_ms": 100,
    "silence_padding_ms": 500,
    "webhook_url": "https://example.com/webhook",
    "id": "vad-detection-001"
  }'
```

#### Legacy FFmpeg Detection

```json
{
    "media_url": "https://example.com/audio.mp3",
    "use_advanced_vad": false,
    "start": "00:00:10.0",
    "end": "00:01:00.0",
    "noise": "-25dB",
    "duration": 0.5,
    "mono": false,
    "webhook_url": "https://example.com/webhook",
    "id": "legacy-detection-001"
}
```

#### Audio Analysis Request

```bash
curl -X POST \
  https://api.example.com/v1/media/silence/analyze \
  -H 'x-api-key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "media_url": "https://example.com/audio.mp3",
    "id": "audio-analysis-001"
  }'
```

## 4. Response

### Success Responses

#### Enhanced VAD Detection Response

```json
{
    "endpoint": "/v1/media/silence",
    "code": 200,
    "id": "vad-detection-001",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "response": {
        "type": "speech_segments",
        "method": "advanced_vad",
        "segments": [
            {
                "id": 1,
                "start": 2.150,
                "end": 8.750,
                "duration": 6.600,
                "start_formatted": "00:00:02.150",
                "end_formatted": "00:00:08.750",
                "confidence": 0.892
            },
            {
                "id": 2,
                "start": 12.300,
                "end": 18.950,
                "duration": 6.650,
                "start_formatted": "00:00:12.300",
                "end_formatted": "00:00:18.950",
                "confidence": 0.945
            }
        ],
        "total_segments": 2,
        "parameters": {
            "volume_threshold": 40,
            "min_duration": 0.5,
            "speech_padding_ms": 100,
            "silence_padding_ms": 500
        }
    },
    "message": "success",
    "pid": 12345,
    "queue_id": 1234567890,
    "run_time": 2.134,
    "queue_time": 0.089,
    "total_time": 2.223,
    "queue_length": 0,
    "build_number": "1.0.0"
}
```

#### Audio Analysis Response

```json
{
    "endpoint": "/v1/media/silence/analyze",
    "code": 200,
    "id": "audio-analysis-001",
    "job_id": "b2c3d4e5-f6g7-h8i9-j0k1-l2m3n4o5p6q7",
    "response": {
        "duration": 45.67,
        "sample_rate": 44100,
        "rms_level": 0.0234,
        "noise_floor_db": -42.3,
        "speech_level_db": -18.7,
        "dynamic_range_db": 23.6,
        "zero_crossing_rate": 0.0891,
        "spectral_centroid_hz": 2341.2,
        "recommended_volume_threshold": 35,
        "audio_quality": "high"
    },
    "message": "success",
    "run_time": 1.456,
    "total_time": 1.456
}
```

#### Legacy FFmpeg Response

```json
{
    "endpoint": "/v1/media/silence",
    "code": 200,
    "id": "legacy-detection-001",
    "job_id": "c3d4e5f6-g7h8-i9j0-k1l2-m3n4o5p6q7r8",
    "response": {
        "type": "silence_intervals",
        "method": "ffmpeg_silencedetect",
        "segments": [
            {
                "start": "00:00:10.500",
                "end": "00:00:15.200",
                "duration": 4.7
            },
            {
                "start": "00:00:20.000",
                "end": "00:00:25.700",
                "duration": 5.7
            }
        ],
        "total_segments": 2,
        "parameters": {
            "volume_threshold": 70,
            "min_duration": 0.5,
            "speech_padding_ms": 50,
            "silence_padding_ms": 450
        }
    },
    "message": "success",
    "run_time": 1.234,
    "total_time": 1.234
}
```

### Error Responses

- **400 Bad Request**: Invalid request parameters or missing required fields:

```json
{
    "code": 400,
    "message": "Invalid payload: volume_threshold must be between 0 and 100"
}
```

- **401 Unauthorized**: Missing or invalid API key:

```json
{
    "code": 401,
    "message": "Unauthorized"
}
```

- **500 Internal Server Error**: Processing errors with detailed messages:

```json
{
    "endpoint": "/v1/media/silence",
    "code": 500,
    "id": "detection-001",
    "job_id": "error-job-id",
    "response": null,
    "message": "VAD processing failed: Audio file is empty or corrupted. Fallback to FFmpeg mode also failed.",
    "run_time": 0.123,
    "total_time": 0.123
}
```

## 5. Error Handling

The endpoint handles the following common errors:

- Missing or invalid request parameters: Returns a 400 Bad Request error.
- Missing or invalid `x-api-key` header: Returns a 401 Unauthorized error.
- Unexpected exceptions during the detection process: Returns a 500 Internal Server Error.

The main application context (`app.py`) also includes error handling for situations where the task queue has reached its maximum length (`MAX_QUEUE_LENGTH`). In such cases, a 429 Too Many Requests error is returned.

## 6. Usage Notes

### Enhanced VAD Mode (Recommended)
- **Volume Threshold**: Values 20-60 work best. Lower values detect more speech (including quiet segments), higher values are more selective.
- **Audio Analysis**: Use `/v1/media/silence/analyze` first to get optimal parameter recommendations.
- **Automatic Fallback**: If VAD fails, the system automatically falls back to FFmpeg mode.
- **Dynamic Thresholds**: The system calculates optimal thresholds based on your audio's characteristics.
- **Confidence Scores**: Each segment includes a confidence score (0.0-1.0) for quality assessment.

### Legacy FFmpeg Mode
- **Backwards Compatibility**: All original parameters are still supported.
- **Time Range**: Use `start` and `end` parameters to focus on specific time ranges.
- **Noise Threshold**: Lower dB values (e.g., `-40dB`) detect more silence, higher values (e.g., `-20dB`) detect less.
- **Mono Processing**: Set `mono: true` for single-channel analysis.

### Parameter Optimization
- **High-Quality Audio**: Use lower volume thresholds (20-30) for clean recordings.
- **Noisy Audio**: Use higher volume thresholds (50-70) for recordings with background noise.
- **Podcast/Interview**: `speech_padding_ms: 100-200`, `silence_padding_ms: 300-500`.
- **Music/Mixed Content**: `speech_padding_ms: 50`, `silence_padding_ms: 200-300`.

## 7. Common Issues

### Audio Processing Issues
- **Invalid Media URL**: Ensure the URL is accessible and points to a valid audio/video file.
- **Unsupported Format**: VAD mode works best with common formats (MP3, WAV, MP4, M4A).
- **Poor Audio Quality**: Low-quality audio may affect VAD accuracy; consider using legacy mode.
- **No Speech Detected**: Very quiet audio may require lower volume thresholds (10-20).

### Parameter Issues
- **Volume Threshold Too High**: Results in missing quiet speech segments.
- **Volume Threshold Too Low**: Results in false positives from background noise.
- **Minimum Duration Too Low**: Creates too many short segments.
- **Excessive Padding**: May merge unrelated speech segments.

### Processing Issues
- **Memory Usage**: Very long audio files (>1 hour) may require more memory in VAD mode.
- **Processing Time**: VAD mode is more CPU-intensive but provides better accuracy.
- **Dependencies**: Missing librosa/scipy will automatically fall back to FFmpeg mode.

## 8. Best Practices

### Getting Started
1. **Use Audio Analysis First**: Call `/v1/media/silence/analyze` to get optimal parameter recommendations.
2. **Start with Defaults**: Begin with default VAD parameters and adjust based on results.
3. **Test with Sample**: Process a short segment first to validate parameters.

### Parameter Tuning
1. **Volume Threshold Selection**:
   - Start with the recommended threshold from audio analysis
   - Decrease by 10-20 if missing speech segments
   - Increase by 10-20 if detecting too much noise

2. **Padding Optimization**:
   - Use longer speech padding (100-200ms) for natural speech flow
   - Use longer silence padding (400-600ms) to merge related segments
   - Reduce padding for music or mixed content

3. **Quality Validation**:
   - Check confidence scores in results (aim for >0.7)
   - Validate segment boundaries make sense
   - Adjust parameters if too many low-confidence segments

### Production Considerations
1. **Method Selection**:
   - Use VAD mode for speech-focused content (podcasts, interviews, calls)
   - Use FFmpeg mode for mixed content or when speed is critical
   - Monitor processing times and adjust accordingly

2. **Error Handling**:
   - Implement fallback logic for when VAD mode fails
   - Monitor for consistent parameter recommendations
   - Log processing method used for debugging

3. **Performance Optimization**:
   - Cache audio analysis results for repeated processing
   - Use appropriate volume thresholds based on content type
   - Consider processing in chunks for very long audio files

### Content-Specific Guidelines

#### Podcasts/Interviews
```json
{
    "volume_threshold": 30,
    "min_speech_duration": 0.3,
    "speech_padding_ms": 150,
    "silence_padding_ms": 500
}
```

#### Phone Calls/Poor Quality
```json
{
    "volume_threshold": 50,
    "min_speech_duration": 0.5,
    "speech_padding_ms": 200,
    "silence_padding_ms": 300
}
```

#### High-Quality Studio Recordings
```json
{
    "volume_threshold": 25,
    "min_speech_duration": 0.2,
    "speech_padding_ms": 100,
    "silence_padding_ms": 400
}
```