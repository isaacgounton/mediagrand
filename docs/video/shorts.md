# Video Shorts Generation Endpoint (v1)

## 1. Overview

The `/v1/video/shorts` endpoint is part of the Video API and is responsible for generating short, engaging videos from a provided video URL. It automatically handles advanced video downloading (with bot detection avoidance and authentication), script generation (if not provided), voiceover creation, merging audio with video, and applying captions. The endpoint leverages existing internal services including the advanced `/v1/media/download` service for robust video acquisition, providing a streamlined solution for creating viral-ready video shorts.

## 2. Endpoint

**URL:** `/v1/video/shorts`
**Method:** `POST`

## 3. Request

### Headers

- `x-api-key`: Required. The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `video_url` (string, required): The URL of the source video from which the short will be generated.
- `script_text` (string, optional): The script for the voiceover. If not provided, an AI model (OpenAI-compatible API) will automatically generate a structured script with hook and main content based on the video content. Supports UTF-8 and accent languages.
- `context` (string, optional): Additional context to help the AI generate better scripts. This can include information about the video topic, target audience, or specific points to emphasize.
- `tts_voice` (string, optional): The voice to be used for the generated voiceover. This should be a valid voice identifier from the integrated Text-to-Speech service (e.g., "en-US-AvaNeural"). Defaults to "en-US-AvaNeural".
- `caption_settings` (object, optional): An object containing various styling options for the video captions. These settings are passed directly to the `/v1/video/caption` endpoint. See the [Video Captioning Endpoint documentation](caption_video.md) for available options and their schema.
- `webhook_url` (string, optional): A URL to receive a webhook notification when the shorts generation process is complete.
- `id` (string, optional): An identifier for the request.

#### `caption_settings` Schema

The schema for `caption_settings` is identical to the `settings` parameter in the [Video Captioning Endpoint documentation](caption_video.md).

### Example Requests

#### Example 1: Generate Short with AI-Generated Script and Default Settings
```json
{
    "video_url": "https://example.com/long_video.mp4"
}
```
This minimal request will download the video, generate a script using AI, create a voiceover with the default voice, merge it with the video, and add captions with default styling.

#### Example 2: Generate Short with AI Script and Context
```json
{
    "video_url": "https://example.com/tech_interview.mp4",
    "context": "This is a tech interview discussing AI and machine learning trends for 2024",
    "tts_voice": "en-US-GuyNeural"
}
```

#### Example 3: Generate Short with Provided Script and Custom Voice
```json
{
    "video_url": "https://example.com/my_podcast_clip.mp4",
    "script_text": "Welcome to my channel! In this short, we'll discuss the latest tech trends.",
    "tts_voice": "en-US-GuyNeural"
}
```

#### Example 3: Generate Short with Custom Caption Styling
```json
{
    "video_url": "https://example.com/tutorial_video.mp4",
    "script_text": "This short explains a complex concept simply.",
    "caption_settings": {
        "style": "karaoke",
        "line_color": "#FFFFFF",
        "word_color": "#FFFF00",
        "outline_color": "#000000",
        "font_family": "Arial",
        "font_size": 28,
        "position": "bottom_center",
        "all_caps": true
    },
    "webhook_url": "https://my-app.com/shorts-callback",
    "id": "my-shorts-request-001"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
        "video_url": "https://example.com/my_video.mp4",
        "script_text": "This is a custom script for my short video.",
        "tts_voice": "en-US-JennyNeural",
        "caption_settings": {
            "font_size": 30,
            "line_color": "#FFD700",
            "outline_color": "#8B0000"
        }
    }' \
    https://your-api-endpoint.com/v1/video/shorts
```

## 4. Advanced Video Download Features

The shorts endpoint uses the sophisticated `/v1/media/download` service, which provides:

### YouTube Authentication & Bot Detection Avoidance
- **Multiple authentication methods**: OAuth2, cookies, automatic fallback strategies
- **Bot detection avoidance**: Enhanced yt-dlp options with random delays and user agent rotation
- **Retry strategies**: Multiple download attempts with different authentication methods
- **Error handling**: Comprehensive error messages with helpful solutions for common issues

### Format & Quality Options
- **Best quality selection**: Automatically selects the best available video quality
- **Format flexibility**: Supports various video formats and codecs
- **Metadata extraction**: Retrieves video title, duration, view count, and other metadata

### Enhanced Reliability
- **Fallback mechanisms**: Multiple strategies ensure successful downloads even with restricted content
- **Cloud integration**: Seamless integration with cloud storage for temporary file handling
- **Comprehensive logging**: Detailed logging for troubleshooting download issues

## 5. AI Script Generation Features

### Structured Script Generation
When `script_text` is not provided, the endpoint uses an advanced AI system to generate structured scripts with two components:
- **Hook**: A compelling opening line (1-2 sentences) designed to grab viewer attention
- **Script**: The main content that explains what's happening and why it's worth watching

### UTF-8 and International Language Support
The endpoint fully supports UTF-8 encoding and international characters, including:
- Accented characters (é, ñ, ü, etc.)
- Non-Latin scripts (Arabic, Chinese, Japanese, etc.)
- Emoji and special characters
- All content is properly encoded throughout the pipeline

### Context-Aware Generation
Use the `context` parameter to provide additional information that helps the AI generate better scripts:
- Video topic or theme
- Target audience information
- Specific points to emphasize
- Tone or style preferences

## 6. Response

### Success Response

The response will be a JSON object with the following properties:

- `short_url` (string): The cloud URL of the generated short video file.
- `job_id` (string): A unique identifier for the job.

Example:

```json
{
    "short_url": "https://cloud.example.com/generated-short-video.mp4",
    "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

### Error Responses

#### Missing or Invalid Parameters

**Status Code:** 400 Bad Request

```json
{
    "error": "Missing 'video_url' parameter",
    "code": 400
}
```

#### Internal Server Error

**Status Code:** 500 Internal Server Error

```json
{
    "error": "An unexpected error occurred during shorts generation.",
    "code": 500
}
```

## 5. Error Handling

The endpoint handles the following common errors:

- **Missing or Invalid Parameters**: If any required parameters are missing or invalid, a 400 Bad Request error is returned with a descriptive error message.
- **Internal Service Errors**: Errors from internal services (e.g., video download failure, TTS generation failure, merge failure, captioning failure) will result in a 500 Internal Server Error.
- **Queue Overload**: If the maximum queue length is set and the queue size reaches that limit, a 429 Too Many Requests error is returned (handled by `app_utils.queue_task_wrapper`).

## 7. Environment Variables

The following environment variables are required for the shorts endpoint to function properly:

### Required Variables
- `API_KEY`: Main API authentication key
- `OPENAI_API_KEY`: API key for OpenAI-compatible AI service (used for script generation)

### Optional Variables (with defaults)
- `OPENAI_MODEL`: AI model to use (default: `google/gemma-3-12b-it:free`)
- `OPENAI_BASE_URL`: Base URL for OpenAI-compatible API (default: `https://openrouter.ai/api/v1`)
- `LOCAL_STORAGE_PATH`: Path for temporary file storage (default: `/app/data/tmp`)
- `TTS_SERVER_URL`: URL for TTS service (default: `https://tts.dahopevi.com/api`)

### Example Configuration
```bash
# Required
API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional (with defaults shown)
OPENAI_MODEL=google/gemma-3-12b-it:free
OPENAI_BASE_URL=https://openrouter.ai/api/v1
LOCAL_STORAGE_PATH=/app/data/tmp
TTS_SERVER_URL=https://tts.dahopevi.com/api
```

## 8. Usage Notes

- The `video_url` must be a valid and accessible URL pointing to a video file.
- If `script_text` is not provided, ensure that the `OPENAI_API_KEY` environment variable is correctly configured on the server for AI script generation.
- The `tts_voice` parameter should correspond to an available voice from the TTS service.
- For detailed `caption_settings` options, refer to the [Video Captioning Endpoint documentation](caption_video.md).
- Use the `webhook_url` parameter to receive asynchronous notifications about the job status.
- Provide a unique `id` for each request to easily track and identify responses.
- All text content supports UTF-8 encoding including accented characters and international scripts.

## 9. Common Issues

- Invalid `video_url` causing download failures.
- Missing `OPENAI_API_KEY` when `script_text` is not provided.
- Issues with the TTS service (e.g., invalid `tts_voice`).
- Problems during video merging or captioning due to corrupted files or unsupported formats.
- UTF-8 encoding issues (now resolved with proper encoding support).

## 10. Best Practices

- Always validate input parameters before sending requests.
- Utilize webhooks for asynchronous processing and to avoid long-polling.
- Monitor logs for detailed error information during development and production.
- Optimize source video quality and duration for best shorts generation results.
- Use the `context` parameter to provide additional information for better AI script generation.
- The system fully supports international content - feel free to use accented characters, emojis, and non-Latin scripts.
- For best results with AI script generation, ensure your video has clear audio for transcription.
