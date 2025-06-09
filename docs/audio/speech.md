# TTS (Text-to-Speech) API Endpoint Documentation

**Implemented by:** [Harrison Fisher](https://github.com/HarrisonFisher)

## Overview

The `/v1/audio/speech` endpoint allows clients to convert text into speech using different Text-to-Speech (TTS) engines. The service supports `edge-tts`, `streamlabs-polly`, `kokoro`, and `openai-edge-tts` as TTS providers, offering flexibility in the choice of voices and speech synthesis options. It integrates with the application's queuing system to manage potentially time-consuming operations, ensuring smooth processing of requests.

**🆕 Enhanced Features:**
- **Advanced Text Preprocessing**: Intelligent handling of markdown, emojis, code blocks, and HTML tags
- **Voice Filtering**: Filter voices by language, locale, or TTS engine
- **Multiple Audio Formats**: Support for MP3, WAV, AAC, OPUS, and FLAC formats
- **OpenAI API Compatibility**: Drop-in replacement endpoints for OpenAI TTS API
- **Optimized Long Text Processing**: Intelligent chunking for texts of any length

## Endpoints

### OpenAI TTS API Compatibility Endpoints

#### List Models (OpenAI Compatible)
- **URL**: `/v1/models`
- **Method**: `GET` or `POST`
- **Description**: Returns available TTS models (TTS-1 and TTS-1 HD) for OpenAI API compatibility
- **Use Case**: Third-party integrations that expect OpenAI TTS API format

#### List Voices (OpenAI Compatible)
- **URL**: `/v1/voices`
- **Method**: `GET` or `POST`
- **Description**: Returns voices with optional language filtering (OpenAI Edge TTS API compatible)
- **Parameters**: 
  - `language` or `locale` (optional): Filter voices by language (e.g., "en-US", "fr-FR")
- **Use Case**: Drop-in replacement for OpenAI's voice listing endpoint

### Dahopevi Native Endpoints (Recommended)

#### List Available Voices (Enhanced)
- **URL**: `/v1/audio/speech/voices`
- **Method**: `GET`
- **Description**: Returns a list of all available voices across all TTS engines with advanced filtering
- **Parameters**:
  - `language` or `locale` (optional): Filter by language (e.g., "en-US", "fr-FR", "all")
  - `engine` (optional): Filter by TTS engine ("edge-tts", "streamlabs-polly", "kokoro", "openai-edge-tts")

**Example Usage:**
```bash
# Get all English (US) voices
GET /v1/audio/speech/voices?language=en-US

# Get all Edge TTS voices
GET /v1/audio/speech/voices?engine=edge-tts

# Get all French voices from Edge TTS
GET /v1/audio/speech/voices?language=fr-FR&engine=edge-tts

# Get all voices
GET /v1/audio/speech/voices?language=all
```

#### Generate Speech (Enhanced)
- **URL**: `/v1/audio/speech`
- **Method**: `POST`
- **Description**: Converts text to speech with optional voice and adjustment parameters
- **Enhanced Features**:
  - **Smart Text Preprocessing**: Automatically handles markdown, emojis, code blocks
  - **Long Text Support**: Automatically chunks and processes texts of any length
  - **Multiple Output Formats**: MP3 (default) and WAV support

## Request

### Headers

- `x-api-key`: Required. Your API authentication key.

### Body Parameters

| Parameter     | Type   | Required | Description |
|---------------|--------|----------|-------------|
| `tts`         | String | No       | The TTS engine to use. Default is `edge-tts`. Options: `edge-tts`, `streamlabs-polly`, `kokoro`, `openai-edge-tts` |
| `text`        | String | Yes      | The text to convert to speech. **🆕 Supports markdown, emojis, code blocks** |
| `voice`       | String | No       | The voice to use. The valid voice list depends on the TTS engine. |
| `rate`        | String | No       | Speech rate adjustment (e.g., "+50%", "-20%"). Format: ^[+-]\\d+%$ |
| `volume`      | String | No       | Volume adjustment (e.g., "+50%", "-20%"). Format: ^[+-]\\d+%$ |
| `pitch`       | String | No       | Pitch adjustment in Hz (e.g., "+50Hz", "-20Hz"). Format: ^[+-]\\d+Hz$ |
| `output_format` | String | No    | Output audio format: "mp3" (default) or "wav" |
| `webhook_url` | String | No       | A URL to receive a callback notification when processing is complete. |
| `id`          | String | No       | A custom identifier for tracking the request. |

### Example Request

```json
{
  "tts": "edge-tts",
  "text": "Hello, world!",
  "voice": "en-US-AvaNeural",
  "rate": "+10%",
  "volume": "+20%",
  "pitch": "+5Hz",
  "output_format": "mp3",
  "webhook_url": "https://your-webhook-endpoint.com/callback",
  "id": "custom-request-id-123"
}
```

### Example Request with OpenAI Edge TTS (Enhanced)

```json
{
  "tts": "openai-edge-tts",
  "text": "# Welcome!\n\nThis is **bold text** with `code snippets` and emojis 🎉\n\n```python\nprint('Hello World')\n```",
  "voice": "alloy",
  "rate": "+5%",
  "volume": "+10%",
  "output_format": "mp3",
  "webhook_url": "https://your-webhook-endpoint.com/callback",
  "id": "openai-tts-request-456"
}
```

### Example Request with Long Text (Auto-Chunking)

```json
{
  "tts": "kokoro",
  "text": "This is a very long text that will be automatically chunked and processed efficiently. The system will handle texts of any length, breaking them into optimal chunks, processing each chunk, and then combining the results into a single audio file with accurate subtitles...",
  "voice": "af_sarah",
  "output_format": "wav"
}
```

### Example cURL Command

```bash
curl -X POST \
  https://api.example.com/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: your-api-key-here' \
  -d '{
    "tts": "openai-edge-tts",
    "text": "# Hello World!\n\nThis is **markdown text** with `code` and links [example](https://example.com)",
    "voice": "alloy",
    "rate": "+10%",
    "output_format": "mp3"
  }'
```

## Response

### List Voices Response (Enhanced)

```json
{
  "voices": [
    {
      "name": "en-US-AvaNeural",
      "gender": "Female",
      "locale": "en-US",
      "engine": "edge-tts"
    },
    {
      "name": "alloy",
      "gender": "female",
      "locale": "en-US",
      "engine": "openai-edge-tts"
    },
    {
      "name": "Brian",
      "locale": "en-US",
      "engine": "streamlabs-polly"
    },
    {
      "name": "af_sarah",
      "gender": "female",
      "locale": "en-US",
      "engine": "kokoro"
    }
  ]
}
```

### Synchronous Response (No webhook\_url provided)

```json
{
  "code": 200,
  "id": "custom-request-id-123",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": {
    "audio_url": "https://storage.example.com/audio-file.mp3",
    "subtitle_url": "https://storage.example.com/subtitle-file.srt"
  },
  "message": "success",
  "run_time": 2.345,
  "queue_time": 0,
  "total_time": 2.345,
  "pid": 12345,
  "queue_id": 67890,
  "queue_length": 0,
  "build_number": "1.0.123"
}
```

### Asynchronous Response (webhook\_url provided)

Initial response:
```json
{
  "code": 202,
  "id": "custom-request-id-123",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "processing",
  "pid": 12345,
  "queue_id": 67890,
  "max_queue_length": "unlimited",
  "queue_length": 1,
  "build_number": "1.0.123"
}
```

Webhook payload:
```json
{
  "endpoint": "/v1/audio/speech",
  "code": 200,
  "id": "custom-request-id-123",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": {
    "audio_url": "https://storage.example.com/audio-file.mp3",
    "subtitle_url": "https://storage.example.com/subtitle-file.srt"
  },
  "message": "success",
  "pid": 12345,
  "queue_id": 67890,
  "run_time": 3.456,
  "queue_time": 1.234,
  "total_time": 4.690,
  "queue_length": 0,
  "build_number": "1.0.123"
}
```

## Error Handling

* **Missing Required Parameters**: If `text` is missing or empty, a 400 Bad Request response will be returned.
* **Invalid TTS Engine**: If the `tts` parameter is invalid, a 400 Bad Request response will be returned.
* **Invalid Adjustments**: If rate, volume, or pitch values don't match the required format, a 400 Bad Request response will be returned.
* **Authentication Failure**: If the API key is invalid or missing, a 401 Unauthorized response will be returned.
* **Queue Limit**: If the queue is full (when MAX\_QUEUE\_LENGTH is set), a 429 Too Many Requests response will be returned.
* **Processing Errors**: Any errors during text processing, speech synthesis, or audio file generation will result in a 500 Internal Server Error response.

## TTS Engine Features

### edge-tts
- Supports extensive voice list in multiple languages
- Full support for rate, volume, and pitch adjustments
- Outputs MP3 format
- **🆕 Voice mapping for invalid voice names**
- **🆕 Automatic chunking for long texts**
- Preview voices at: https://tts.travisvn.com/

### streamlabs-polly
- High-quality voices based on Amazon Polly
- Limited support for adjustments
- Outputs MP3 format
- **🆕 Improved error handling and rate limiting**
- **🆕 Automatic chunking for long texts**
- Available voices: Brian, Emma, Russell, Joey, Matthew, Joanna, Kimberly, Amy, Geraint, Nicole, Justin, Ivy, Kendra, Salli, Raveena

### kokoro
- Uses Kokoro-82M model with ONNX runtime
- English language support
- Outputs WAV format (convertible to MP3)
- **🆕 Optimized memory management for long texts**
- **🆕 Enhanced timestamp generation**
- Voice list available at: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md

### openai-edge-tts (Enhanced) ⭐
- **🆕 Advanced text preprocessing** - Handles markdown, emojis, code blocks, HTML
- **🆕 Multiple audio formats** - MP3, AAC, WAV, OPUS, FLAC (via FFmpeg)
- **🆕 Better speed parameter handling** (0.25-4.0 range)
- High-quality voices powered by Edge TTS with OpenAI mapping
- Premium voice quality with natural-sounding speech
- Available voices: alloy, echo, fable, onyx, nova, shimmer
- Supports rate, volume, and pitch adjustments
- Excellent for professional applications requiring high-quality audio

## Enhanced Features

### 🆕 Advanced Text Preprocessing (openai-edge-tts)

The `openai-edge-tts` engine now includes sophisticated text preprocessing that handles:

- **Markdown Elements**:
  - Headers (`# Title` → "Title — Title")
  - Links (`[text](url)` → "text")
  - Code blocks (` ```code``` ` → "(code block omitted)")
  - Inline code (`` `code` `` → "code snippet: code")
  - Bold/italic formatting (`**bold**` → "bold")

- **Content Cleanup**:
  - Emoji removal for better pronunciation
  - HTML tag removal
  - Image syntax handling (`![alt](url)` → "Image: alt")
  - Text normalization and whitespace cleanup

**Example:**
```json
{
  "tts": "openai-edge-tts",
  "text": "# Hello World! 🎉\n\nThis is **important** text with `code` and [links](https://example.com).\n\n```python\nprint('hello')\n```",
  "voice": "alloy"
}
```

This will be processed as: "Title — Hello World! This is important text with code snippet: code and links. (code block omitted)"

### 🆕 Long Text Optimization

All TTS engines now support automatic chunking for texts of any length:

- **Intelligent Chunking**: Breaks text at natural sentence boundaries
- **Memory Management**: Optimized processing for very long texts
- **Seamless Audio Combining**: Automatic audio concatenation with FFmpeg
- **Accurate Subtitles**: Timeline-adjusted subtitle generation across chunks

### 🆕 Voice Filtering

Enhanced voice discovery with filtering options:

```bash
# Filter by language
GET /v1/audio/speech/voices?language=en-US
GET /v1/audio/speech/voices?locale=fr-FR

# Filter by engine
GET /v1/audio/speech/voices?engine=edge-tts

# Combine filters
GET /v1/audio/speech/voices?language=en-US&engine=openai-edge-tts

# Get all voices
GET /v1/audio/speech/voices?language=all
```

## Additional Features

1. **🆕 Smart Subtitle Generation**: Automatically generates intelligent SRT/VTT subtitle files with proper timing
2. **🆕 Multiple Audio Formats**: Support for MP3, WAV, AAC, OPUS, FLAC formats
3. **🆕 Optimized Text Chunking**: Intelligent text segmentation for long content
4. **Enhanced Rate Limiting**: Built-in rate limiting protection with automatic retry mechanism
5. **Cloud Storage Integration**: Generated audio and subtitle files are automatically uploaded to cloud storage
6. **🆕 Memory Optimization**: Efficient processing of very long texts without memory issues

## Best Practices

1. **Voice Selection**: Use the `/v1/audio/speech/voices` endpoint with filtering to find the perfect voice
   ```bash
   # Find English voices for openai-edge-tts
   GET /v1/audio/speech/voices?language=en-US&engine=openai-edge-tts
   ```

2. **Text Preprocessing**: Use `openai-edge-tts` for markdown content and formatted text
   ```json
   {
     "tts": "openai-edge-tts",
     "text": "# Article Title\n\nThis **article** has `code` and [links](url)",
     "voice": "alloy"
   }
   ```

3. **Long Text Processing**: The system automatically handles texts of any length - no manual chunking needed

4. **Audio Format Selection**: Choose the appropriate format for your use case
   - `mp3`: Best for web delivery and general use
   - `wav`: Best for further audio processing

5. **Asynchronous Processing**: For longer texts (>1000 chars), use webhooks to avoid timeouts

6. **Voice Optimization**: 
   - Use `alloy` or `shimmer` for female voices (openai-edge-tts)
   - Use `onyx` or `echo` for male voices (openai-edge-tts)
   - Use Edge TTS for multilingual content

7. **Rate Adjustments**: Start with small adjustments (±10%) and test results

8. **Error Handling**: Implement robust error handling for various HTTP status codes

9. **Rate Limits**: Be mindful of rate limits, especially with streamlabs-polly

## Migration from Standalone OpenAI Edge TTS

If you're migrating from a standalone OpenAI Edge TTS service, use these equivalent endpoints:

| Standalone OpenAI Edge TTS | Dahopevi Enhanced TTS |
|----------------------------|----------------------|
| `GET /v1/voices` | `GET /v1/audio/speech/voices` or `GET /v1/voices` |
| `GET /v1/models` | `GET /v1/models` |
| `POST /v1/audio/speech` | `POST /v1/audio/speech` (with `"tts": "openai-edge-tts"`) |

The enhanced version provides all the same functionality plus additional features like voice filtering, better text preprocessing, and long text support.
