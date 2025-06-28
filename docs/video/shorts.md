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
- `context` (string, optional): Additional context to help the AI generate better scripts. This can include information about the video topic, target audience, or specific points to emphasize. If not provided, video metadata (title, description, uploader) will be used automatically.
- `tts_voice` (string, optional): The voice to be used for the generated voiceover. This should be a valid voice identifier from the integrated Text-to-Speech service (e.g., "en-US-AvaNeural"). Defaults to "en-US-AvaNeural".
- `cookies_content` (string, optional): YouTube cookies content for authentication when downloading restricted videos.
- `cookies_url` (string, optional): URL to download YouTube cookies from for authentication.
- `auth_method` (string, optional): YouTube authentication method. Options: "auto", "oauth2", "cookies_content", "cookies_url", "cookies_file". Defaults to "auto".
- `shorts_config` (object, optional): Advanced configuration for shorts generation:
  - `num_shorts` (integer, 1-10): Number of shorts to generate from the video. Default: 1. Uses AI-powered video analysis to identify the most interesting segments.
  - `short_duration` (integer, 15-180): Duration of each short in seconds. Default: 60.
  - `keep_original_voice` (boolean): Whether to keep the original audio instead of generating TTS. Default: false.
  - `add_captions` (boolean): Whether to add captions to the video. Default: true.
  - `segment_method` (string): How to segment long videos. Options: "auto", "equal_parts", "highlights", "chapters". Default: "auto".
    - `"auto"`: Automatically chooses the best method based on video content and available transcription
    - `"highlights"`: Uses AI analysis to detect interesting segments based on audio energy, transcription keywords, and scene changes
    - `"equal_parts"`: Divides the video into equal time segments
    - `"chapters"`: Uses video chapters if available (falls back to equal_parts)
  - `transition_effects` (boolean): Whether to add transition effects. Default: false. (Future feature)
  - `background_music` (boolean): Whether to add background music. Default: false. (Future feature)
  - `video_format` (string): Output video orientation and aspect ratio. Options: "portrait" (9:16), "landscape" (16:9), "square" (1:1). Default: "portrait".
  - `resolution` (object, optional): Custom video resolution settings:
    - `width` (integer, 480-4096): Video width in pixels
    - `height` (integer, 480-4096): Video height in pixels
  - `hook_style` (object, optional): Custom styling for hook presentation:
    - `position` (string): Hook text position. Options: "top_center", "top_left", "top_right", "middle_center", "bottom_center". Default: "top_center".
    - `font_size_multiplier` (number, 0.8-2.0): Size multiplier relative to main text. Default: 1.2.
    - `background_opacity` (number, 0.0-1.0): Background opacity for better readability. Default: 0.3.
    - `show_separately` (boolean): Whether to position hook differently from main content. Default: false.
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

#### Example 4: AI-Powered Multiple Shorts Generation
```json
{
    "video_url": "https://www.youtube.com/watch?v=example",
    "shorts_config": {
        "num_shorts": 3,
        "short_duration": 60,
        "segment_method": "highlights",
        "keep_original_voice": false,
        "add_captions": true
    },
    "tts_voice": "en-US-AriaNeural",
    "context": "Educational content about technology trends"
}
```

#### Example 6: Landscape Format with Custom Resolution
```json
{
    "video_url": "https://example.com/my_video.mp4",
    "script_text": "This landscape short is perfect for YouTube Shorts and TikTok horizontal content.",
    "tts_voice": "fr-CA-ThierryNeural",
    "shorts_config": {
        "video_format": "landscape",
        "short_duration": 45,
        "add_captions": true
    },
    "caption_settings": {
        "font_size": 32,
        "position": "bottom_center",
        "line_color": "#FFFFFF"
    }
}
```

#### Example 7: Square Format with Custom Resolution
```json
{
    "video_url": "https://example.com/podcast.mp4",
    "tts_voice": "es-ES-AlvaroNeural",
    "shorts_config": {
        "video_format": "square",
        "resolution": {
            "width": 1080,
            "height": 1080
        },
        "short_duration": 30,
        "hook_style": {
            "position": "top_center",
            "font_size_multiplier": 1.3,
            "background_opacity": 0.4,
            "show_separately": true
        }
    }
}
```

#### Example 8: Enhanced Hook Presentation with Custom Styling
```json
{
    "video_url": "https://example.com/engaging_content.mp4",
    "tts_voice": "fr-CA-ThierryNeural",
    "shorts_config": {
        "video_format": "portrait",
        "short_duration": 60,
        "add_captions": true,
        "hook_style": {
            "position": "top_center",
            "font_size_multiplier": 1.4,
            "background_opacity": 0.5,
            "show_separately": true
        }
    },
    "caption_settings": {
        "font_size": 26,
        "line_color": "#FFFFFF",
        "outline_color": "#000000",
        "outline_width": 2,
        "position": "bottom_center"
    }
}
```

#### Example 5: Advanced Configuration with Original Voice and YouTube Authentication
```json
{
    "video_url": "https://www.youtube.com/watch?v=example",
    "cookies_content": "your_youtube_cookies_here",
    "auth_method": "cookies_content",
    "shorts_config": {
        "short_duration": 90,
        "keep_original_voice": true,
        "add_captions": true,
        "segment_method": "highlights"
    },
    "caption_settings": {
        "line_color": "#FFFFFF",
        "word_color": "#FFFF00",
        "font_size": 24
    }
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

## 5. AI-Powered Video Analysis Features

### Intelligent Segment Detection
The shorts endpoint uses advanced AI analysis to automatically identify the most interesting parts of videos for shorts generation:

#### Audio Energy Analysis
- **RMS Energy Detection**: Analyzes audio energy levels to find exciting moments
- **Spectral Centroid Analysis**: Detects brightness and tonal changes in audio
- **Dynamic Range Scoring**: Identifies segments with high audio activity and engagement

#### Transcription-Based Analysis
- **Keyword Detection**: Scans transcriptions for engaging words and phrases that typically indicate interesting content
- **Emotional Language**: Identifies excitement, surprise, controversy, and other engaging emotional markers
- **Question and Answer Patterns**: Detects interactive content that performs well in short-form videos

#### Visual Scene Analysis
- **Scene Change Detection**: Uses computer vision to identify significant visual transitions
- **Frame Difference Analysis**: Calculates visual changes between frames to find dynamic content
- **Content Variety Scoring**: Prioritizes segments with visual diversity and movement

#### Combined Scoring Algorithm
- **Multi-factor Analysis**: Combines audio, transcription, and visual scores with weighted importance
- **Temporal Optimization**: Ensures selected segments meet target duration requirements
- **Overlap Resolution**: Intelligently merges overlapping high-scoring segments
- **Quality Ranking**: Sorts all potential segments by combined engagement score

### Segment Method Options
- **"highlights"**: Uses full AI analysis pipeline to find the most engaging content
- **"auto"**: Automatically chooses between highlights and equal_parts based on content availability
- **"equal_parts"**: Divides video into equal time segments for consistent coverage
- **"chapters"**: Uses video chapter markers when available (future enhancement)

## 6. AI Script Generation Features

### Structured Script Generation
When `script_text` is not provided, the endpoint uses an advanced AI system to generate structured scripts with two components:
- **Hook**: A compelling opening line (1-2 sentences) designed to grab viewer attention
- **Script**: The main content that explains what's happening and why it's worth watching

### Language Detection and Localization
The system automatically detects the target language from the `tts_voice` parameter and generates content accordingly:
- **Automatic Language Detection**: Extracts language code from voice names (e.g., "fr-CA-ThierryNeural" → French)
- **Localized Content Generation**: AI generates scripts in the target language based on the voice selection
- **Clean Text Processing**: Advanced text cleaning removes JSON formatting artifacts and unwanted explanatory text

### Enhanced Script Cleaning
The system now intelligently removes unwanted AI-generated formatting:
- **Prefix Removal**: Automatically removes "Hook:", "Script:", "Title:" prefixes that AI might add
- **JSON Artifact Cleaning**: Removes phrases like "Here is a JSON object containing..."
- **Format Cleaning**: Strips curly braces, extra quotes, and other formatting artifacts
- **AI Instruction Enhancement**: Explicit instructions prevent AI from adding explanatory text

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

## 7. Enhanced Caption System

### Intelligent Caption Timing
The caption system has been enhanced with proper timing segmentation:
- **Sentence-Based Timing**: Captions are split into individual sentences with proper timing
- **Duration Estimation**: Smart duration calculation based on word count and speech patterns
- **Synchronized Display**: Each caption appears at the correct moment instead of showing all text at once

### SRT Generation Improvements
- **Multi-Segment Captions**: Creates multiple SRT entries for better readability
- **Proper Timing Format**: Accurate start/end timestamps for each caption segment
- **Language-Aware Processing**: Caption processing respects the detected voice language

## 8. Video Format and Resolution Control

### Format Options
The endpoint now supports multiple video orientations and aspect ratios:
- **Portrait (9:16)**: Default format, optimized for mobile platforms like TikTok and Instagram Reels
- **Landscape (16:9)**: Traditional horizontal format, suitable for YouTube Shorts and wider displays
- **Square (1:1)**: Perfect for Instagram posts and square video requirements

### Resolution Control
- **Predefined Formats**: Each format comes with optimized default resolutions
- **Custom Resolution**: Override defaults with specific width and height values
- **Aspect Ratio Preservation**: Automatic scaling maintains original video proportions with black padding
- **Quality Optimization**: Smart scaling ensures high-quality output across all formats

### Format-Specific Defaults
- **Portrait**: 1080x1920 (9:16 aspect ratio)
- **Landscape**: 1920x1080 (16:9 aspect ratio) 
- **Square**: 1080x1080 (1:1 aspect ratio)

## 9. Advanced Hook Presentation

### Hook Styling System
The endpoint provides sophisticated control over how hook text appears in your videos:

### Position Control
- **Top Positioning**: Place hooks at the top to avoid blocking important video content
- **Center Options**: Traditional center positioning for emphasis
- **Bottom Placement**: Alternative positioning for specific design needs

### Visual Enhancement
- **Size Control**: Make hooks larger (up to 2x) or smaller (down to 0.8x) than main content
- **Background Opacity**: Add semi-transparent backgrounds (0-100%) for better readability
- **Smart Detection**: Automatically identifies hook content within generated scripts

### Separate Hook Styling
When `show_separately` is enabled:
- **Intelligent Parsing**: Automatically detects hook text within the full script
- **Position Override**: Hook appears at specified position while main content uses caption settings
- **Enhanced Readability**: Different styling ensures hook stands out from main content

### Best Practices for Hook Presentation
- **Top Center**: Recommended for most content to avoid blocking important video elements
- **Size Multiplier 1.3-1.4**: Optimal size increase for emphasis without overwhelming
- **Background Opacity 0.3-0.5**: Sufficient transparency for readability while preserving video visibility
- **Separate Styling**: Enable for professional-looking differentiation between hook and main content

## 6. Response

### Success Response

The response format depends on the number of shorts generated:

#### Single Short Response (num_shorts = 1)

- `short_url` (string): The cloud URL of the generated short video file.
- `job_id` (string): A unique identifier for the job.

Example:

```json
{
    "short_url": "https://cloud.example.com/generated-short-video.mp4",
    "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

#### Multiple Shorts Response (num_shorts > 1)

- `shorts` (array): Array of generated short video objects.
- `job_id` (string): A unique identifier for the job.
- `total_shorts` (integer): Total number of shorts generated.

Each short object contains:
- `short_url` (string): The cloud URL of the generated short video file.
- `segment_info` (object): Information about the video segment used.
- `segment_index` (integer): The index of this segment (1-based).

Example:

```json
{
    "shorts": [
        {
            "short_url": "https://cloud.example.com/short-1.mp4",
            "segment_info": {
                "start_time": 45.2,
                "end_time": 105.2,
                "score": 0.85,
                "reason": "High audio energy and engaging keywords"
            },
            "segment_index": 1
        },
        {
            "short_url": "https://cloud.example.com/short-2.mp4",
            "segment_info": {
                "start_time": 180.5,
                "end_time": 240.5,
                "score": 0.78,
                "reason": "Scene change detected with keyword matches"
            },
            "segment_index": 2
        }
    ],
    "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "total_shorts": 2
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

## 9. Usage Notes

- The `video_url` must be a valid and accessible URL pointing to a video file.
- If `script_text` is not provided, ensure that the `OPENAI_API_KEY` environment variable is correctly configured on the server for AI script generation.
- The `tts_voice` parameter should correspond to an available voice from the TTS service and determines the language for script generation and captions.
- For detailed `caption_settings` options, refer to the [Video Captioning Endpoint documentation](caption_video.md).
- Use the `webhook_url` parameter to receive asynchronous notifications about the job status.
- Provide a unique `id` for each request to easily track and identify responses.
- All text content supports UTF-8 encoding including accented characters and international scripts.
- The `video_format` parameter controls the output orientation: use "landscape" for YouTube Shorts, "portrait" for TikTok/Instagram Reels, or "square" for Instagram posts.
- Custom `resolution` settings override the default format dimensions if you need specific video sizes.
- Caption timing is now properly synchronized - each sentence appears at the correct moment during playback.
- Use `hook_style` to customize how hook text appears: position it at the top to avoid blocking video content, adjust size for emphasis, and add background opacity for better readability.
- Set `show_separately: true` in hook_style to automatically position hooks differently from main content for professional-looking results.

## 10. Common Issues

- Invalid `video_url` causing download failures.
- Missing `OPENAI_API_KEY` when `script_text` is not provided.
- Issues with the TTS service (e.g., invalid `tts_voice`).
- Problems during video merging or captioning due to corrupted files or unsupported formats.
- UTF-8 encoding issues (now resolved with proper encoding support).
- Caption timing issues (now resolved with enhanced SRT generation).
- Language mismatch between TTS voice and generated content (now automatically synchronized).

## 11. Best Practices

- Always validate input parameters before sending requests.
- Utilize webhooks for asynchronous processing and to avoid long-polling.
- Monitor logs for detailed error information during development and production.
- Optimize source video quality and duration for best shorts generation results.
- Use the `context` parameter to provide additional information for better AI script generation.
- The system fully supports international content - feel free to use accented characters, emojis, and non-Latin scripts.
- For best results with AI script generation, ensure your video has clear audio for transcription.
- Choose the appropriate `video_format` based on your target platform:
  - **TikTok/Instagram Reels**: Use "portrait" format
  - **YouTube Shorts**: Use "landscape" or "portrait" format  
  - **Instagram Posts**: Use "square" format
- When using non-English voices, the system will automatically generate content in the corresponding language.
- Caption timing is now optimized - you no longer need to worry about text appearing all at once.
- For engaging hook presentation, use `"position": "top_center"` with `"font_size_multiplier": 1.3-1.4` to make hooks stand out without overwhelming the video.
- Enable `"show_separately": true` in hook_style for automatic hook detection and separate positioning from main content.
- Use background opacity (0.3-0.5) when text readability is challenging due to video content complexity.
