# Audio Speech Endpoint

## 1. Overview

The `/v1/audio/speech` endpoint is a part of the Audio API and is responsible for converting text to speech using various TTS providers. This endpoint fits into the overall API structure as a part of the version 1 (v1) routes, specifically under the `/v1/audio` namespace. It integrates with the Awesome-TTS API gateway to support multiple TTS providers including Kokoro ONNX, Chatterbox TTS, and OpenAI Edge TTS.

## 2. Endpoint

**URL Path:** `/v1/audio/speech`
**HTTP Method:** `POST`

## 3. Request

### Headers

- `x-api-key` (required): The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `text` (required, string): The text to convert to speech.
- `tts` (optional, string): TTS provider to use (alias for `provider`, kept for backward compatibility).
- `provider` (optional, string): TTS provider to use: "kokoro", "chatterbox", or "openai-edge-tts" (default: "kokoro").
- `voice` (optional, string): Voice ID to use (provider-specific).
- `rate` (optional, string): Speech rate adjustment (e.g., "+50%", "-20%") - pattern: `^[+-]?\d+%?$|^\d*\.?\d+$`.
- `volume` (optional, string): Volume adjustment (e.g., "+10%", "-5%") - pattern: `^[+-]?\d+%?$|^\d*\.?\d+$`.
- `pitch` (optional, string): Pitch adjustment (e.g., "+50Hz", "-10Hz") - pattern: `^[+-]?\d+Hz?$|^\d*\.?\d+$`.
- `speed` (optional, number): Speed multiplier between 0.5 and 2.0 (alternative to rate).
- `output_format` (optional, string): Audio output format - "mp3", "wav", or "ogg" (default: "mp3").
- `subtitle_format` (optional, string): Subtitle format - "srt" or "vtt" (default: "srt").
- `webhook_url` (optional, string, URI format): The URL to which the response should be sent as a webhook.
- `id` (optional, string): An identifier for the request.

The `validate_payload` decorator in the routes file enforces the following JSON schema for the request body:

```json
{
    "type": "object",
    "properties": {
        "tts": {"type": "string"},
        "provider": {"type": "string"},
        "text": {"type": "string"},
        "voice": {"type": "string"},
        "rate": {"type": "string", "pattern": "^[+-]?\\d+%?$|^\\d*\\.?\\d+$"},
        "volume": {"type": "string", "pattern": "^[+-]?\\d+%?$|^\\d*\\.?\\d+$"},
        "pitch": {"type": "string", "pattern": "^[+-]?\\d+Hz?$|^\\d*\\.?\\d+$"},
        "speed": {"type": "number", "minimum": 0.5, "maximum": 2.0},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"},
        "output_format": {"type": "string", "enum": ["mp3", "wav", "ogg"], "default": "mp3"},
        "subtitle_format": {"type": "string", "enum": ["srt", "vtt"], "default": "srt"}
    },
    "required": ["text"],
    "additionalProperties": false
}
```

### Example Request

```json
{
    "text": "Hello, this is a sample text for speech generation using Awesome-TTS.",
    "provider": "kokoro",
    "voice": "af_heart",
    "speed": 1.2,
    "output_format": "mp3",
    "subtitle_format": "srt",
    "webhook_url": "https://example.com/webhook",
    "id": "speech-request-123"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
        "text": "Hello, this is a sample text for speech generation using Awesome-TTS.",
        "provider": "kokoro",
        "voice": "af_heart",
        "speed": 1.2,
        "output_format": "mp3",
        "subtitle_format": "srt",
        "webhook_url": "https://example.com/webhook",
        "id": "speech-request-123"
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
        "engine": "kokoro",
        "provider": "kokoro",
        "voice": "af_heart",
        "format": "mp3"
    },
    "message": "success",
    "pid": 12345,
    "run_time": 8.234,
    "queue_time": 1.345,
    "total_time": 9.579,
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

### List Available Voices
**GET** `/v1/audio/speech/voices`

Returns a list of available voices from all TTS providers.

### List Available Engines
**GET** `/v1/audio/speech/engines`

Returns a list of available TTS providers/engines.

### Health Check
**GET** `/v1/audio/speech/health`

Checks the health status of the TTS service and returns availability information.

## 10. Supported Providers

| Provider | Description | Features |
|----------|-------------|----------|
| `kokoro` | Kokoro ONNX | High-quality neural TTS with multi-language support |
| `chatterbox` | Chatterbox TTS | Voice cloning capabilities with reference audio |
| `openai-edge-tts` | OpenAI Edge TTS | Microsoft Edge TTS backend with extensive voice catalog |

## 11. Configuration

The endpoint requires the following environment configuration:

```env
TTS_SERVER_URL=https://your-awesome-tts-server.com
```

This should point to your Awesome-TTS API gateway instance that provides the actual TTS functionality.
