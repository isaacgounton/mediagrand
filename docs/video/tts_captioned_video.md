# TTS Captioned Video Endpoint

## 1. Overview

The `/v1/video/tts-captioned` endpoint is a part of the Video API and is responsible for creating captioned videos from background images and text or audio. This endpoint combines local text-to-speech generation, audio transcription, and video composition to produce videos with synchronized captions. The TTS functionality uses a local edge-tts service (Micros## 8. Common Issues

- Providing both `text` and `audio_url` parameters (only one should be provided).
- Using invalid or inaccessible background image URLs.
- Using invalid or inaccessible audio URLs when using the `audio_url` option.
- Specifying invalid voice names for the selected TTS provider.
- Using extreme speed values that may affect audio quality.
- Background images with very low resolution that don't scale well to video dimensions.
- Mismatched provider and voice combinations (e.g., using a Kokoro voice with OpenAI Edge TTS provider).
- Using non-numeric values for width, height, or speed parameters.
- **Invalid color formats**: Color parameters must be in hex format (#RRGGBB), e.g., "#FF0000" for red.
- **Font not found**: Specifying a font family that doesn't exist - use `/v1/video/fonts` to check available fonts.
- **Invalid image effects**: Using effect names not in the supported list (none, ken_burns, zoom_in, zoom_out, pan_left, pan_right, pan_up, pan_down).
- **Caption positioning conflicts**: Some combinations of font size and position may cause text overflow.
- **Text wrapping issues**: Very long words may not wrap properly with restrictive character limits.
- **Shadow/stroke conflicts**: Very high stroke sizes combined with shadows may reduce readability.
- Exceeding the maximum queue length, which can lead to requests being rejected with a 429 Too Many Requests error.
- Encountering unexpected errors during the video generation process, which can result in a 500 Internal Server Error.) without requiring any external API dependencies. This endpoint fits into the overall API structure as a part of the version 1 (v1) routes, specifically under the `/v1/video` namespace.

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
- `language` (optional, string): Language for TTS voice selection (default: "en").
- `image_effect` (optional, string): Visual effect to apply to background image - "none", "ken_burns", "zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down" (default: "none").
- `caption_font_name` (optional, string): Font family name for captions (default: "Arial").
- `caption_font_size` (optional, number): Font size for captions in pixels (default: 120, range: 8-200).
- `caption_font_bold` (optional, boolean): Enable bold font weight (default: false).
- `caption_font_italic` (optional, boolean): Enable italic font style (default: false).
- `caption_font_color` (optional, string): Font color in hex format (default: "#ffffff").
- `caption_position` (optional, string): Caption position - "top", "center", "bottom" (default: "bottom").
- `caption_shadow_color` (optional, string): Shadow color in hex format (default: "#000000").
- `caption_shadow_transparency` (optional, number): Shadow transparency (default: 0.4, range: 0.0-1.0).
- `caption_shadow_blur` (optional, number): Shadow blur amount (default: 3, range: 0-20).
- `caption_stroke_size` (optional, number): Stroke/outline size in pixels (default: 0, range: 0-10).
- `caption_stroke_color` (optional, string): Stroke color in hex format (default: "#000000").
- `caption_line_count` (optional, number): Maximum number of lines for text wrapping (default: 2, range: 1-5).
- `caption_max_chars_per_line` (optional, number): Maximum characters per line (default: 60, range: 1-200).
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
        "language": {
            "type": "string",
            "description": "Language for TTS voice selection (default: en)"
        },
        "image_effect": {
            "type": "string",
            "enum": ["none", "ken_burns", "zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down"],
            "description": "Visual effect for background image (default: none)"
        },
        "caption_font_name": {
            "type": "string",
            "description": "Font family name for captions (default: Arial)"
        },
        "caption_font_size": {
            "type": "number",
            "minimum": 8,
            "maximum": 200,
            "description": "Font size in pixels (default: 120)"
        },
        "caption_font_bold": {
            "type": "boolean",
            "description": "Enable bold font weight (default: false)"
        },
        "caption_font_italic": {
            "type": "boolean",
            "description": "Enable italic font style (default: false)"
        },
        "caption_font_color": {
            "type": "string",
            "pattern": "^#[0-9A-Fa-f]{6}$",
            "description": "Font color in hex format (default: #ffffff)"
        },
        "caption_position": {
            "type": "string",
            "enum": ["top", "center", "bottom"],
            "description": "Caption position (default: bottom)"
        },
        "caption_shadow_color": {
            "type": "string",
            "pattern": "^#[0-9A-Fa-f]{6}$",
            "description": "Shadow color in hex format (default: #000000)"
        },
        "caption_shadow_transparency": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Shadow transparency (default: 0.4)"
        },
        "caption_shadow_blur": {
            "type": "number",
            "minimum": 0,
            "maximum": 20,
            "description": "Shadow blur amount (default: 3)"
        },
        "caption_stroke_size": {
            "type": "number",
            "minimum": 0,
            "maximum": 10,
            "description": "Stroke size in pixels (default: 0)"
        },
        "caption_stroke_color": {
            "type": "string",
            "pattern": "^#[0-9A-Fa-f]{6}$",
            "description": "Stroke color in hex format (default: #000000)"
        },
        "caption_line_count": {
            "type": "number",
            "minimum": 1,
            "maximum": 5,
            "description": "Maximum lines for text wrapping (default: 2)"
        },
        "caption_max_chars_per_line": {
            "type": "number",
            "minimum": 1,
            "maximum": 200,
            "description": "Maximum characters per line (default: 60)"
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

**Using Text-to-Speech with Basic Settings:**
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

**Using Advanced Image Effects and Caption Styling:**
```json
{
    "background_url": "https://example.com/background-image.jpg",
    "text": "Professional video content with stunning visual effects and custom typography.",
    "width": 1080,
    "height": 1920,
    "provider": "openai-edge-tts",
    "voice": "en-US-AriaNeural",
    "speed": 1.0,
    "language": "en",
    "image_effect": "ken_burns",
    "caption_font_name": "Roboto",
    "caption_font_size": 140,
    "caption_font_bold": true,
    "caption_font_color": "#FFD700",
    "caption_position": "center",
    "caption_shadow_color": "#000000",
    "caption_shadow_transparency": 0.6,
    "caption_shadow_blur": 5,
    "caption_stroke_size": 3,
    "caption_stroke_color": "#FFFFFF",
    "caption_line_count": 3,
    "caption_max_chars_per_line": 40,
    "webhook_url": "https://example.com/webhook",
    "id": "advanced-tts-video-456"
}
```

**Using Existing Audio with Visual Effects:**
```json
{
    "background_url": "https://example.com/background-image.jpg",
    "audio_url": "https://example.com/voiceover.mp3",
    "width": 1920,
    "height": 1080,
    "image_effect": "zoom_in",
    "caption_font_name": "DejaVuSans",
    "caption_font_size": 100,
    "caption_position": "top",
    "caption_font_color": "#FFFFFF",
    "caption_stroke_size": 2,
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
        "text": "Create stunning videos with advanced effects and professional typography.",
        "width": 1080,
        "height": 1920,
        "provider": "openai-edge-tts",
        "voice": "en-US-AriaNeural",
        "speed": 1.2,
        "language": "en",
        "image_effect": "ken_burns",
        "caption_font_name": "Arial",
        "caption_font_size": 120,
        "caption_font_bold": true,
        "caption_font_color": "#FFFFFF",
        "caption_position": "bottom",
        "caption_shadow_transparency": 0.5,
        "caption_stroke_size": 2,
        "webhook_url": "https://example.com/webhook",
        "id": "enhanced-tts-video-123"
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
- When using `text`, the system will generate speech using the local edge-tts service with the specified provider, voice, and speed settings.
- When using `audio_url`, the system will use the provided audio and display captions based on transcription.
- The video duration matches the audio duration automatically.
- **Advanced Image Effects**: Seven visual effects available (none, ken_burns, zoom_in, zoom_out, pan_left, pan_right, pan_up, pan_down) for cinematic background presentation.
- **Professional Caption Styling**: Full control over font family, size, weight, color, positioning, shadows, and stroke effects.
- **Smart Text Processing**: Intelligent text wrapping with configurable line count and character limits per line.
- **Language Support**: Automatic voice selection based on language parameter for multilingual content.
- The `provider` parameter aligns with the `/v1/audio/speech` endpoint providers (all processed locally).
- The `voice` parameter should match the voice IDs available for the selected provider from the local edge-tts service.
- **Font Management**: Use the `/v1/video/fonts` endpoint to discover available fonts with family grouping.
- **Color Format**: All color parameters accept hex format (#RRGGBB) for precise color control.
- **Caption Positioning**: Captions can be positioned at top (10%), center (50%), or bottom (80%) of video height.
- If the `webhook_url` parameter is provided, the response will be sent as a webhook to the specified URL.
- The `id` parameter can be used to identify the request in the response.
- Processing time varies based on text length, audio duration, video dimensions, and selected image effects.
- No internet connection required for TTS processing as all voice generation is handled locally.

## 7. Advanced Features

### Image Effects
The endpoint supports seven sophisticated visual effects for background images:

- **none**: Basic image scaling without effects (default)
- **ken_burns**: Cinematic slow zoom and pan effect for professional video feel
- **zoom_in**: Gradual zoom into the image center
- **zoom_out**: Gradual zoom out from image center
- **pan_left**: Smooth pan from right to left across the image
- **pan_right**: Smooth pan from left to right across the image
- **pan_up**: Smooth pan from bottom to top
- **pan_down**: Smooth pan from top to bottom

### Caption Styling Options
Professional typography control with comprehensive styling options:

- **Font Selection**: Choose from 70+ available fonts with family grouping
- **Typography**: Bold, italic, and size control (8-200px)
- **Positioning**: Top, center, or bottom alignment
- **Color Control**: Custom font color, shadow color, and stroke color in hex format
- **Shadow Effects**: Transparency and blur control for depth
- **Stroke/Outline**: Configurable stroke size and color for readability
- **Text Layout**: Smart line wrapping with configurable line count and character limits

### Language Support
- Automatic voice selection based on language parameter
- Integration with local edge-tts service for multilingual content
- Supports all languages available in the Microsoft Edge TTS service

### Font Management
- **Font Discovery**: `/v1/video/fonts` endpoint returns available fonts grouped by family
- **Smart Resolution**: Automatic font family matching with style fallbacks
- **Standardized Naming**: All fonts follow consistent `FontFamily-Style.ttf` format
- **Wide Selection**: 70+ fonts including Arial, Roboto, DejaVu Sans, Comic Neue, Noto Sans, and more

## 8. Common Issues

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

## 9. Best Practices

- Validate background image and audio URLs before sending the request to ensure they are accessible.
- Use high-resolution background images for better video quality, especially when using zoom or pan effects.
- Test different provider and voice combinations to find the optimal settings for your content.
- Keep text length reasonable to avoid excessively long videos.
- Choose video dimensions that match your target platform requirements (e.g., 1920x1080 for landscape, 1080x1920 for portrait).
- Use appropriate speed adjustments to maintain natural speech flow.
- **Image Effects**: Choose effects that complement your content - ken_burns for storytelling, zoom effects for emphasis, pan effects for wide images.
- **Font Selection**: Use the `/v1/video/fonts` endpoint to discover available fonts and test readability with your color scheme.
- **Color Contrast**: Ensure sufficient contrast between font color and background for readability.
- **Caption Positioning**: Test different positions based on image content - avoid placing text over busy image areas.
- **Text Layout**: For longer text, increase line count and adjust character limits for better readability.
- **Shadow and Stroke**: Use shadows for text over bright backgrounds, use stroke for text over varied backgrounds.
- **Language Matching**: Ensure the language parameter matches the text content for proper voice selection.
- Consult the `/v1/audio/speech/voices` endpoint to get available voices for each provider.
- Monitor the queue length and adjust the `MAX_QUEUE_LENGTH` value accordingly to prevent requests from being rejected due to a full queue.
- Implement retry mechanisms for handling temporary errors or failures during the video generation process.
- Provide meaningful and descriptive `id` values to easily identify requests in the response.
- Consider the total processing time when dealing with long text, audio content, or complex image effects.

## 10. Use Cases

### Basic Content Creation
- **Social Media Content**: Create captioned videos for Instagram Stories, TikTok, or YouTube Shorts.
- **Educational Content**: Generate instructional videos with synchronized captions.
- **Marketing Videos**: Create promotional videos with voice-over and captions.
- **Accessibility**: Add captions to existing audio content for hearing-impaired audiences.

### Professional Content
- **Corporate Presentations**: Use ken_burns effects and professional typography for business content.
- **Brand Videos**: Apply custom colors and fonts matching brand guidelines.
- **Product Demonstrations**: Use zoom effects to highlight product features.
- **Testimonials**: Apply appropriate visual effects to enhance customer testimonials.

### Advanced Applications
- **Multilingual Content**: Generate videos with different voice languages and caption styles for international audiences.
- **Cinematic Content**: Use sophisticated image effects and typography for film-style videos.
- **Training Materials**: Create professional training videos with clear, readable captions.
- **Podcast Visualization**: Convert audio podcasts into captioned video format with visual effects for video platforms.
- **Documentary Style**: Use pan effects and professional typography for documentary-style content.
- **News Content**: Apply news-appropriate styling with clear fonts and positioning.

## 10. Integration with Speech API

This endpoint integrates with the `/v1/audio/speech` API for text-to-speech generation:

- **Local TTS Service**: Uses the integrated local edge-tts service (no external API required)
- **Provider Compatibility**: Supports edge-tts voices with OpenAI-compatible naming
- **Voice Selection**: Supports the same voice IDs as the speech API (both edge-tts and OpenAI-compatible names)
- **Parameter Alignment**: `voice`, `speed`, and provider parameters work identically
- **Voice Discovery**: Use `/v1/audio/speech/voices` to discover available voices from the local service
- **No External Dependencies**: All TTS processing is handled locally using Microsoft Edge TTS technology

## 12. Related Endpoints

### Get Available Fonts

**GET** `/v1/video/fonts`

Returns available fonts grouped by family with style information.

Example response:
```json
{
  "fonts": {
    "Arial": ["Regular", "Bold", "Italic", "BoldItalic"],
    "Roboto": ["Regular", "Bold", "Light", "Medium"],
    "DejaVuSans": ["Regular", "Bold", "Oblique", "BoldOblique"],
    "ComicNeue": ["Regular", "Bold", "Light", "Italic"],
    "NotoSansTC": ["Regular", "Bold", "Light", "Medium"]
  },
  "total_fonts": 73,
  "font_families": 15
}
```

### List Available Voices

**GET** `/v1/audio/speech/voices`

Returns available voices from the integrated edge-tts service.

### Speech Generation

**POST** `/v1/audio/speech`

Generate audio-only speech without video components.