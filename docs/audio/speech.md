# Audio Speech Endpoint

## 1. Overview

The `/v1/audio/speech` endpoint is a part of the Audio API and is responsible for converting text to speech using Microsoft Edge TTS. This endpoint fits into the overall API structure as a part of the version 1 (v1) routes, specifically under the `/v1/audio` namespace. It uses an integrated edge-tts implementation that provides high-quality text-to-speech generation with support for multiple languages and voices, including OpenAI-compatible voice names.

## 2. Endpoint

**URL Path:** `/v1/audio/speech`
**HTTP Method:** `POST`

## 3. Request

### Headers

- `x-api-key` (required): The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `model` (optional, string): The TTS model to use. Options: "tts-1" (standard quality) or "tts-1-hd" (high definition). Default: "tts-1".
- `input` (required, string): The text to convert to speech (OpenAI standard parameter).
- `voice` (required, string): Voice ID to use. Supports both edge-tts voice names (e.g., "en-US-AvaNeural") and OpenAI-compatible names (e.g., "alloy", "echo", "fable", "onyx", "nova", "shimmer").
- `response_format` (optional, string): The audio format. Options: "mp3", "opus", "aac", "flac", "wav", "pcm". Default: "mp3".
- `speed` (optional, number): Speech speed multiplier (0.5 to 2.0). Default: 1.0.

**Legacy Parameters (for backward compatibility):**
- `text` (string): Alternative to `input` parameter.
- `output_format` (string): Alternative to `response_format` parameter.
- `rate` (string): Speech rate adjustment (e.g., "+50%", "-20%").
- `volume` (string): Volume adjustment (not supported by edge-tts, parameter ignored).
- `pitch` (string): Pitch adjustment (not supported by edge-tts, parameter ignored).
- `speed` (optional, number): Speed multiplier between 0.5 and 2.0 (alternative to rate). Can be provided as a number (1.2) or string ("1.2").
- `output_format` (optional, string): Audio output format - "mp3", "wav", or "ogg" (default: "mp3").
- `subtitle_format` (optional, string): Subtitle format - "srt" or "vtt" (default: "srt").
- `webhook_url` (optional, string, URI format): The URL to which the response should be sent as a webhook.
- `id` (optional, string): An identifier for the request.

The `validate_payload` decorator in the routes file enforces the following JSON schema for the request body:

```json
{
    "type": "object",
    "properties": {
        "model": {"type": "string", "enum": ["tts-1", "tts-1-hd"], "default": "tts-1"},
        "input": {"type": "string"},
        "text": {"type": "string"},
        "voice": {"type": "string"},
        "response_format": {"type": "string", "enum": ["mp3", "opus", "aac", "flac", "wav", "pcm"], "default": "mp3"},
        "speed": {"type": "number", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
        "rate": {"type": "string", "pattern": "^[+-]?\\d+%?$|^\\d*\\.?\\d+$"},
        "volume": {"type": "string", "pattern": "^[+-]?\\d+%?$|^\\d*\\.?\\d+$"},
        "pitch": {"type": "string", "pattern": "^[+-]?\\d+Hz?$|^\\d*\\.?\\d+$"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"},
        "output_format": {"type": "string", "enum": ["mp3", "wav", "ogg"], "default": "mp3"},
        "subtitle_format": {"type": "string", "enum": ["srt", "vtt"], "default": "srt"}
    },
    "required": [],
    "additionalProperties": false
}
```

### Example Request

**OpenAI-Compatible Request:**
```json
{
    "model": "tts-1",
    "input": "Hello, this is a sample text for speech generation.",
    "voice": "alloy",
    "response_format": "mp3",
    "speed": 1.2
}
```

**Using Edge-TTS Voice:**
```json
{
    "model": "tts-1-hd",
    "input": "Hello, this is a sample text for speech generation using integrated edge-tts.",
    "voice": "en-US-AvaNeural",
    "response_format": "wav",
    "speed": 1.0,
    "webhook_url": "https://example.com/webhook",
    "id": "speech-request-123"
}
```

**Legacy Format (backward compatibility):**
```json
{
    "text": "Hello, this is a sample text for speech generation.",
    "voice": "alloy",
    "rate": "+20%",
    "output_format": "wav",
    "id": "speech-request-456"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
        "model": "tts-1",
        "input": "Hello, this is a sample text for speech generation.",
        "voice": "alloy",
        "response_format": "mp3",
        "speed": 1.2
     }' \
     https://your-api-endpoint.com/v1/audio/speech
```

## 4. Response

### Success Response

The success response follows the general response format defined in the `app.py` file. Here's an example:

```json
{
    "endpoint": "/v1/audio/speech",
    "code": 200,
    "id": "speech-request-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "response": {
        "audio_url": "https://cloud-storage.example.com/generated-speech.mp3",
        "subtitle_url": "https://cloud-storage.example.com/generated-subtitles.srt",
        "model": "tts-1",
        "voice": "alloy",
        "format": "mp3"
    },
    "message": "success",
    "pid": 12345,
    "run_time": 3.456,
    "queue_time": 0.789,
    "total_time": 4.245,
    "queue_length": 0,
    "build_number": "1.0.0"
}
```

The `response` field contains an object with URLs to the generated audio and subtitle files.

### Error Responses

- **400 Bad Request**: Returned when the request body is missing or invalid.

  ```json
  {
    "code": 400,
    "message": "Invalid request payload"
  }
  ```

- **401 Unauthorized**: Returned when the `x-api-key` header is missing or invalid.

  ```json
  {
    "code": 401,
    "message": "Unauthorized"
  }
  ```

- **429 Too Many Requests**: Returned when the maximum queue length is reached.

  ```json
  {
    "code": 429,
    "id": "speech-request-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "message": "MAX_QUEUE_LENGTH (100) reached",
    "pid": 12345,
    "queue_length": 100,
    "build_number": "1.0.0"
  }
  ```

- **500 Internal Server Error**: Returned when an unexpected error occurs during the speech generation process.

  ```json
  {
    "code": 500,
    "message": "An error occurred during TTS generation"
  }
  ```

## 5. Error Handling

The endpoint handles the following common errors:

- **Missing or invalid request body**: If the request body is missing or does not conform to the expected JSON schema, a 400 Bad Request error is returned.
- **Missing or invalid API key**: If the `x-api-key` header is missing or invalid, a 401 Unauthorized error is returned.
- **Queue length exceeded**: If the maximum queue length is reached (determined by the `MAX_QUEUE_LENGTH` environment variable), a 429 Too Many Requests error is returned.
- **Unexpected errors during speech generation**: If an unexpected error occurs during the TTS generation process, a 500 Internal Server Error is returned with the error message.

The main application context (`app.py`) also includes error handling for the task queue. If the queue length exceeds the `MAX_QUEUE_LENGTH` limit, the request is rejected with a 429 Too Many Requests error.

## 6. Usage Notes

- The text input is processed by the selected TTS provider to generate natural-sounding speech.
- Both `tts` and `provider` parameters are accepted for backward compatibility, with `provider` taking precedence.
- The `speed` parameter is automatically converted to a `rate` percentage if provided.
- Generated subtitles include timing information synchronized with the audio.
- Different providers support different voices and features (e.g., voice cloning with Chatterbox).
- If the `webhook_url` parameter is provided, the response will be sent as a webhook to the specified URL.
- The `id` parameter can be used to identify the request in the response.
- Processing time varies based on text length and selected provider.

## 7. Common Issues

- Providing invalid or unsupported voice IDs for the selected provider.
- Using extreme rate, volume, or pitch values that may affect audio quality.
- Text that is too long, which may cause processing delays or timeouts.
- Unavailable TTS service or provider connectivity issues.
- Invalid format combinations that are not supported by the selected provider.
- Exceeding the maximum queue length, which can lead to requests being rejected with a 429 Too Many Requests error.
- Encountering unexpected errors during the speech generation process, which can result in a 500 Internal Server Error.

**Note:** The API automatically converts string numbers to actual numbers for parameters like `speed`, so both `"speed": "1.2"` and `"speed": 1.2` are accepted and equivalent.

## 8. Best Practices

- Validate text input to ensure it contains speakable content and is within reasonable length limits.
- Test different voices and providers to find the optimal combination for your use case.
- Use appropriate speed/rate adjustments to maintain natural speech flow.
- Monitor TTS service health using the `/v1/audio/speech/health` endpoint.
- Cache generated audio files when possible to avoid repeated processing of identical text.
- Monitor the queue length and adjust the `MAX_QUEUE_LENGTH` value accordingly to prevent requests from being rejected due to a full queue.
- Implement retry mechanisms for handling temporary errors or failures during the speech generation process.
- Provide meaningful and descriptive `id` values to easily identify requests in the response.
- Consider the target audience when selecting voices and speech parameters.

## 9. Related Endpoints

### List Available Models

**GET** `/v1/models`

Returns a list of available TTS models.

**Example Response:**
```json
{
    "data": [
        {"id": "tts-1", "name": "Text-to-speech v1", "description": "Standard quality text-to-speech"},
        {"id": "tts-1-hd", "name": "Text-to-speech v1 HD", "description": "High definition text-to-speech"}
    ]
}
```

### List Available Voices

**GET** `/v1/audio/speech/voices`

Returns a list of available voices. Supports optional language filtering via query parameter.

**Query Parameters:**
- `language` (optional): Filter voices by language code (e.g., "en-US", "fr-FR", "es-ES")

**GET** `/v1/audio/speech/voices/all`

Returns all available voices without any filtering.

**Examples:**
```bash
# Get all voices
GET /v1/audio/speech/voices

# Get voices for specific language
GET /v1/audio/speech/voices?language=en-US

# Get all voices (explicit)
GET /v1/audio/speech/voices/all
```

### Health Check

**GET** `/v1/audio/speech/health`

Checks the health status of the integrated TTS service and returns availability information.

## 10. Supported Voices

The integrated edge-tts service supports a wide variety of voices across multiple languages. You can use either:

### Edge-TTS Voice Names
Direct voice IDs from Microsoft Edge TTS (e.g., "en-US-AvaNeural", "en-GB-SoniaNeural", "fr-FR-DeniseNeural")

### OpenAI-Compatible Voice Names
Simplified voice names that map to popular edge-tts voices:

| OpenAI Name | Edge-TTS Voice | Description |
|-------------|----------------|-------------|
| `alloy` | en-US-AvaNeural | Clear, neutral American English voice |
| `echo` | en-US-AndrewNeural | Deep, resonant American English voice |
| `fable` | en-GB-SoniaNeural | British English voice with clear articulation |
| `onyx` | en-US-EricNeural | Strong, confident American English voice |
| `nova` | en-US-SteffanNeural | Warm, friendly American English voice |
| `shimmer` | en-US-EmmaNeural | Bright, energetic American English voice |

## 11. Configuration

The endpoint uses an integrated edge-tts implementation and supports the following optional environment variables:

```env
# TTS Configuration (all optional)
TTS_DEFAULT_VOICE=en-US-AvaNeural
TTS_DEFAULT_FORMAT=mp3
TTS_DEFAULT_SPEED=1.0
TTS_DEFAULT_LANGUAGE=en-US
TTS_REMOVE_FILTER=false
TTS_DETAILED_LOGGING=true
```

No external TTS server configuration is required as the service is fully integrated.
