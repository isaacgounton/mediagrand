# TTS Captioned Video Endpoint

## 1. Overview

The `/v1/video/tts-captioned` endpoint is a part of the Video API and is responsible for creating captioned videos from background images and text or audio. This endpoint combines text-to-speech generation, audio transcription, and video composition to produce videos with synchronized captions. This endpoint fits into the overall API structure as a part of the version 1 (v1) routes, specifically under the `/v1/video` namespace.

## 2. Endpoint

**URL Path:** `/v1/video/tts-captioned`
**HTTP Method:** `POST`

## 3. Request

### Headers

- `x-api-key` (required): The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `background_url` (required, string, URI format): The URL of the background image to be used in the video.
- `text` (conditional, string): Text to generate speech from (required if `audio_url` not provided).
- `audio_url` (conditional, string, URI format): URL of existing audio file (required if `text` not provided).
- `width` (optional, number): Width of the video in pixels (default: 1080, minimum: 1).
- `height` (optional, number): Height of the video in pixels (default: 1920, minimum: 1).
- `provider` (optional, string): TTS provider to use - "kokoro", "chatterbox", or "openai-edge-tts" (default: "openai-edge-tts").
- `voice` (optional, string): Voice for text-to-speech generation (default: "en-US-AriaNeural").
- `speed` (optional, number): Speed of speech (default: 1.0, range: 0.1 to 3.0).
- `webhook_url` (optional, string, URI format): The URL to which the response should be sent as a webhook.
- `id` (optional, string): An identifier for the request.

The `validate_payload` decorator in the routes file enforces the following JSON schema for the request body:

```json
{
    "type": "object",
    "properties": {
        "background_url": {
            "type": "string",
            "format": "uri",
            "description": "URL of the background image"
        },
        "text": {
            "type": "string",
            "description": "Text to generate speech from (required if audio_url not provided)"
        },
        "audio_url": {
            "type": "string",
            "format": "uri",
            "description": "URL of existing audio file (required if text not provided)"
        },
        "width": {
            "type": "number",
            "minimum": 1,
            "description": "Width of the video (default: 1080)"
        },
        "height": {
            "type": "number",
            "minimum": 1,
            "description": "Height of the video (default: 1920)"
        },
        "provider": {
            "type": "string",
            "enum": ["kokoro", "chatterbox", "openai-edge-tts"],
            "description": "TTS provider to use (default: openai-edge-tts)"
        },
        "voice": {
            "type": "string",
            "description": "Voice for text-to-speech (default: en-US-AriaNeural)"
        },
        "speed": {
            "type": "number",
            "minimum": 0.1,
            "maximum": 3.0,
            "description": "Speed of speech (default: 1.0)"
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["background_url"],
    "additionalProperties": false,
    "anyOf": [
        {"required": ["text"]},
        {"required": ["audio_url"]}
    ]
}
```

### Example Request

**Using Text-to-Speech:**
```json
{
    "background_url": "https://example.com/background-image.jpg",
    "text": "Welcome to our amazing product demonstration. Let's explore the features together.",
    "width": 1080,
    "height": 1920,
    "provider": "openai-edge-tts",
    "voice": "en-US-AriaNeural",
    "speed": 1.2,
    "webhook_url": "https://example.com/webhook",
    "id": "tts-video-123"
}
```

**Using Existing Audio:**
```json
{
    "background_url": "https://example.com/background-image.jpg",
    "audio_url": "https://example.com/voiceover.mp3",
    "width": 1920,
    "height": 1080,
    "webhook_url": "https://example.com/webhook",
    "id": "tts-video-124"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
        "background_url": "https://example.com/background-image.jpg",
        "text": "Welcome to our amazing product demonstration. Let us explore the features together.",
        "width": 1080,
        "height": 1920,
        "provider": "openai-edge-tts",
        "voice": "en-US-AriaNeural",
        "speed": 1.2,
        "webhook_url": "https://example.com/webhook",
        "id": "tts-video-123"
     }' \
     https://your-api-endpoint.com/v1/video/tts-captioned
```

## 4. Response

### Success Response

The success response follows the general response format defined in the `app.py` file. Here's an example:

```json
{
    "endpoint": "/v1/video/tts-captioned",
    "code": 200,
    "id": "tts-video-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "response": "https://cloud-storage.example.com/captioned-video.mp4",
    "message": "success",
    "pid": 12345,
    "run_time": 25.234,
    "queue_time": 3.345,
    "total_time": 28.579,
    "queue_length": 0,
    "build_number": "1.0.0"
}
```

The `response` field contains the URL of the generated captioned video uploaded to cloud storage.

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
    "id": "tts-video-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "message": "MAX_QUEUE_LENGTH (100) reached",
    "pid": 12345,
    "queue_length": 100,
    "build_number": "1.0.0"
  }
  ```

- **500 Internal Server Error**: Returned when an unexpected error occurs during the video generation process.

  ```json
  {
    "code": 500,
    "message": "An error occurred during TTS captioned video generation"
  }
  ```

## 5. Error Handling

The endpoint handles the following common errors:

- **Missing or invalid request body**: If the request body is missing or does not conform to the expected JSON schema, a 400 Bad Request error is returned.
- **Missing required conditional parameters**: If neither `text` nor `audio_url` is provided, a validation error is returned.
- **Missing or invalid API key**: If the `x-api-key` header is missing or invalid, a 401 Unauthorized error is returned.
- **Queue length exceeded**: If the maximum queue length is reached (determined by the `MAX_QUEUE_LENGTH` environment variable), a 429 Too Many Requests error is returned.
- **Unexpected errors during video generation**: If an unexpected error occurs during the TTS captioned video generation process, a 500 Internal Server Error is returned with the error message.

The main application context (`app.py`) also includes error handling for the task queue. If the queue length exceeds the `MAX_QUEUE_LENGTH` limit, the request is rejected with a 429 Too Many Requests error.

## 6. Usage Notes

- Either `text` or `audio_url` must be provided, but not both.
- The background image will be scaled and padded to fit the specified video dimensions while maintaining aspect ratio.
- When using `text`, the system will generate speech using the specified provider, voice, and speed settings.
- When using `audio_url`, the system will use the provided audio and display a simple caption.
- Captions are positioned at 80% down the video height by default.
- The video duration matches the audio duration automatically.
- The `provider` parameter aligns with the `/v1/audio/speech` endpoint providers.
- The `voice` parameter should match the voice IDs available for the selected provider.
- If the `webhook_url` parameter is provided, the response will be sent as a webhook to the specified URL.
- The `id` parameter can be used to identify the request in the response.
- Processing time varies based on text length, audio duration, and video dimensions.

## 7. Common Issues

- Providing both `text` and `audio_url` parameters (only one should be provided).
- Using invalid or inaccessible background image URLs.
- Using invalid or inaccessible audio URLs when using the `audio_url` option.
- Specifying invalid voice names for the selected TTS provider.
- Using extreme speed values that may affect audio quality.
- Background images with very low resolution that don't scale well to video dimensions.
- Mismatched provider and voice combinations (e.g., using a Kokoro voice with OpenAI Edge TTS provider).
- Using non-numeric values for width, height, or speed parameters.
- Exceeding the maximum queue length, which can lead to requests being rejected with a 429 Too Many Requests error.
- Encountering unexpected errors during the video generation process, which can result in a 500 Internal Server Error.

## 8. Best Practices

- Validate background image and audio URLs before sending the request to ensure they are accessible.
- Use high-resolution background images for better video quality.
- Test different provider and voice combinations to find the optimal settings for your content.
- Keep text length reasonable to avoid excessively long videos.
- Choose video dimensions that match your target platform requirements (e.g., 1920x1080 for landscape, 1080x1920 for portrait).
- Use appropriate speed adjustments to maintain natural speech flow.
- Consult the `/v1/audio/speech/voices` endpoint to get available voices for each provider.
- Monitor the queue length and adjust the `MAX_QUEUE_LENGTH` value accordingly to prevent requests from being rejected due to a full queue.
- Implement retry mechanisms for handling temporary errors or failures during the video generation process.
- Provide meaningful and descriptive `id` values to easily identify requests in the response.
- Consider the total processing time when dealing with long text or audio content.

## 9. Use Cases

- **Social Media Content**: Create captioned videos for Instagram Stories, TikTok, or YouTube Shorts.
- **Educational Content**: Generate instructional videos with synchronized captions.
- **Marketing Videos**: Create promotional videos with voice-over and captions.
- **Accessibility**: Add captions to existing audio content for hearing-impaired audiences.
- **Multilingual Content**: Generate videos with different voice languages and caption styles.
- **Podcast Visualization**: Convert audio podcasts into captioned video format for video platforms.

## 10. Integration with Speech API

This endpoint integrates with the `/v1/audio/speech` API for text-to-speech generation:

- **Provider Compatibility**: Uses the same provider system (`kokoro`, `chatterbox`, `openai-edge-tts`)
- **Voice Selection**: Supports the same voice IDs as the speech API
- **Parameter Alignment**: `provider`, `voice`, and `speed` parameters work identically
- **Voice Discovery**: Use `/v1/audio/speech/voices/{provider}` to discover available voices

## 11. Related Endpoints

### List Available Voices by Provider
**GET** `/v1/audio/speech/voices/{provider}`

Returns available voices for a specific TTS provider.

### Speech Generation
**POST** `/v1/audio/speech`

Generate audio-only speech without video components.

### List TTS Providers
**GET** `/v1/audio/speech/providers`

Returns available TTS providers and their capabilities.