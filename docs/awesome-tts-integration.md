# AwesomeTTS Integration Documentation

## Overview

The speech functionality has been refactored to use the AwesomeTTS backend running at `https://tts.dahopevi.com/api`. This replaces the previous complex multi-engine implementation with a unified, centralized TTS service.

## What Changed

### Before (Original Implementation)
- Multiple TTS engines: Edge TTS, Streamlabs Polly, Kokoro, OpenAI Edge TTS
- Complex voice mapping and fallback systems
- Direct API calls to various TTS services
- Large dependency footprint (edge-tts, kokoro-onnx, etc.)
- Complex chunking and optimization for long texts

### After (AwesomeTTS Integration)
- Unified backend: All TTS requests go through AwesomeTTS API
- Simplified voice management
- Centralized engine selection
- Reduced dependencies
- Consistent API interface

## New Architecture

### Components

1. **`services/awesome_tts.py`** - Core AwesomeTTS API client
2. **`services/v1/audio/speech_awesome.py`** - Compatibility layer for existing API
3. **`routes/v1/audio/speech.py`** - Updated routes using AwesomeTTS backend

### API Endpoints

#### Existing Endpoints (Maintained for Compatibility)
- `GET/POST /v1/models` - List available TTS models
- `GET/POST /v1/voices` - List available voices (OpenAI compatible)
- `GET /v1/audio/speech/voices` - List voices with filtering
- `POST /v1/audio/speech` - Generate text-to-speech

#### New Endpoints
- `GET /v1/audio/speech/health` - Check AwesomeTTS backend health
- `POST /v1/audio/speech/legacy` - Legacy compatibility endpoint

### Enhanced Features

#### New Request Parameters
- `engine` - Explicit engine selection (optional)
- `speed` - Direct speed control (0.5-2.0)
- `subtitle_format` - Choose between 'srt' or 'vtt'
- `output_format` - Support for 'mp3', 'wav', 'ogg'

#### Example Request
```json
{
  "text": "Hello, this is a test of the AwesomeTTS integration.",
  "voice": "en-US-AriaNeural",
  "engine": "edge-tts",
  "speed": 1.2,
  "output_format": "mp3",
  "subtitle_format": "srt"
}
```

#### Example Response
```json
{
  "audio_url": "https://storage.url/audio.mp3",
  "subtitle_url": "https://storage.url/subtitles.srt",
  "backend": "AwesomeTTS",
  "voice_used": "en-US-AriaNeural",
  "engine_used": "edge-tts",
  "format": "mp3"
}
```

## Backward Compatibility

### Maintained Compatibility
- All existing API endpoints continue to work
- Same request/response format for core functionality
- Voice names and parameters are mapped appropriately
- Legacy TTS engine names are supported

### Migration Path
1. **Immediate**: Existing clients continue to work without changes
2. **Recommended**: Update clients to use new parameters for enhanced features
3. **Future**: Migrate to direct AwesomeTTS API calls for optimal performance

### Legacy Engine Mapping
- `edge-tts` → AwesomeTTS with Edge TTS engine
- `openai-edge-tts` → AwesomeTTS with OpenAI TTS engine
- `streamlabs-polly` → AwesomeTTS with Edge TTS engine (fallback)
- `kokoro` → AwesomeTTS with Edge TTS engine (fallback)

## Configuration

### Environment Variables
```bash
# AwesomeTTS Backend URL (default: https://tts.dahopevi.com/api)
AWESOME_TTS_BASE_URL=https://tts.dahopevi.com/api

# Request timeout in seconds (default: 120)
AWESOME_TTS_TIMEOUT=120

# Voice cache timeout in seconds (default: 3600)
AWESOME_TTS_VOICES_CACHE_TIMEOUT=3600
```

### Health Monitoring

Check backend health:
```bash
curl -X GET "/v1/audio/speech/health"
```

Response:
```json
{
  "status": "healthy",
  "backend": "AwesomeTTS",
  "api_info": {
    "api": "AwesomeTTS",
    "version": "1.0.0",
    "base_url": "https://tts.dahopevi.com/api"
  },
  "available": true
}
```

## Error Handling

### Common Errors

1. **Backend Unavailable**
   - Status: 503
   - Fallback: Returns cached voices or default voice list

2. **Rate Limiting**
   - Status: 429
   - Behavior: Automatic retry with backoff

3. **Invalid Voice**
   - Behavior: Falls back to default voice for language

4. **Engine Not Available**
   - Behavior: Falls back to default engine (Edge TTS)

### Error Response Format
```json
{
  "error": "Backend unavailable",
  "status": "error",
  "backend": "AwesomeTTS",
  "available": false
}
```

## Performance Benefits

### Reduced Complexity
- Single API integration vs. multiple engines
- Centralized voice and engine management
- Simplified error handling

### Improved Reliability
- Backend handles engine-specific optimizations
- Centralized rate limiting and retry logic
- Better resource management

### Enhanced Features
- More engines available through single API
- Consistent voice quality across engines
- Better subtitle generation

## Development

### Testing

1. **Unit Tests**
   ```bash
   python -m pytest tests/test_awesome_tts.py
   ```

2. **Integration Tests**
   ```bash
   python -m pytest tests/test_speech_integration.py
   ```

3. **Health Check**
   ```bash
   curl -X GET "http://localhost:8080/v1/audio/speech/health"
   ```

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger('services.awesome_tts').setLevel(logging.DEBUG)
```

### Local Development

For local development, you can point to a local AwesomeTTS instance:
```bash
export AWESOME_TTS_BASE_URL=http://localhost:3000/api
```

## Migration Notes

### File Changes
- **Backed up**: Original files saved with `.backup` extension
- **New files**: AwesomeTTS integration files added
- **Updated**: Main speech route updated to use AwesomeTTS

### Dependencies
The following dependencies are no longer required:
- `edge-tts`
- `kokoro-onnx`
- `soundfile`
- Engine-specific libraries

New dependency:
- `requests` (already present)

### Rollback Plan
To rollback to the original implementation:
1. Restore `routes/v1/audio/speech.py` from `.backup` file
2. Restore `services/v1/audio/speech.py` from backup
3. Remove AwesomeTTS-related files
4. Update imports in `app.py`

## Future Enhancements

### Planned Features
1. **Voice Cloning**: Support for custom voice models
2. **Real-time TTS**: Streaming audio generation
3. **Advanced Controls**: Emotion, emphasis, pause controls
4. **Multi-language**: Better language detection and voice selection

### API Evolution
1. **v2 API**: Native AwesomeTTS API without legacy compatibility
2. **WebSocket**: Real-time streaming TTS
3. **Batch Processing**: Multiple texts in single request

## Support

For issues related to:
- **API Integration**: Check this documentation and logs
- **Voice Quality**: Contact AwesomeTTS backend team
- **Performance**: Monitor backend health endpoint
- **Feature Requests**: Submit through normal channels

## Conclusion

The AwesomeTTS integration simplifies the codebase while providing enhanced functionality and better reliability. The backward compatibility ensures a smooth transition for existing clients while enabling new features for future development.
