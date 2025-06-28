# Viral Shorts Generation Endpoint (v1)

## 1. Overview

The `/v1/video/viral-shorts` endpoint is a streamlined video API designed specifically for creating viral-quality short videos using advanced AI analysis. This endpoint is inspired by viral content creation best practices and focuses on generating engaging commentary-style shorts that blend original video content with AI-generated voiceover. Unlike the comprehensive `/v1/video/shorts` endpoint, this endpoint prioritizes viral content quality through visual AI analysis, intelligent audio mixing, and viral-focused script generation.

## 2. Endpoint

**URL:** `/v1/video/viral-shorts`
**Method:** `POST`

## 3. Request

### Headers

- `x-api-key`: Required. The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `video_url` (string, required): The URL of the source video from which the viral short will be generated.
- `context` (string, optional): Additional context to help the AI generate better viral scripts. This can include information about the video topic, target audience, or specific viral angles to emphasize.
- `tts_voice` (string, optional): The voice to be used for the generated commentary voiceover. This should be a valid voice identifier from the Text-to-Speech service (e.g., "en-US-AvaNeural"). Defaults to "en-US-AvaNeural".
- `cookies_content` (string, optional): YouTube cookies content for authentication when downloading restricted videos.
- `cookies_url` (string, optional): URL to download YouTube cookies from for authentication.
- `auth_method` (string, optional): YouTube authentication method. Options: "auto", "oauth2", "cookies_content", "cookies_url", "cookies_file". Defaults to "auto".
- `webhook_url` (string, optional): A URL to receive a webhook notification when the viral short generation process is complete.
- `id` (string, optional): An identifier for the request.

### Example Requests

#### Example 1: Basic Viral Short Generation
```json
{
    "video_url": "https://www.youtube.com/watch?v=example"
}
```
This minimal request will download the video, analyze it visually with AI, generate a viral script, create commentary voiceover, and intelligently mix it with the original audio.

#### Example 2: Viral Short with Context
```json
{
    "video_url": "https://example.com/interesting_content.mp4",
    "context": "This video shows an amazing life hack that everyone needs to know about",
    "tts_voice": "en-US-GuyNeural"
}
```

#### Example 3: French Viral Short with Custom Voice
```json
{
    "video_url": "https://example.com/french_content.mp4",
    "context": "Contenu viral français sur les nouvelles technologies",
    "tts_voice": "fr-CA-ThierryNeural"
}
```

#### Example 4: Viral Short with YouTube Authentication
```json
{
    "video_url": "https://www.youtube.com/watch?v=restricted_video",
    "cookies_content": "your_youtube_cookies_here",
    "auth_method": "cookies_content",
    "context": "Exclusive behind-the-scenes content that will go viral",
    "webhook_url": "https://my-app.com/viral-shorts-callback"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
        "video_url": "https://example.com/trending_video.mp4",
        "context": "Breaking down this viral moment everyone is talking about",
        "tts_voice": "en-US-AriaNeural"
    }' \
    https://your-api-endpoint.com/v1/video/viral-shorts
```

## 4. Advanced AI Analysis Features

### Visual Content Analysis with Gemini AI
The viral shorts endpoint uses Google's Gemini 2.0 AI for comprehensive video analysis:

#### Video Upload for AI Analysis
- **Direct Video Processing**: Uploads the entire video to Gemini AI for visual analysis, not just audio transcription
- **Visual Scene Understanding**: AI analyzes visual content, actions, and events happening in the video
- **Context Recognition**: Identifies objects, people, settings, and activities within the video frames

#### Fallback Transcript Analysis
- **Audio Transcription**: If video upload fails, automatically extracts audio and generates transcript
- **Intelligent Recovery**: Uses transcript-based analysis as a backup method
- **Seamless Transition**: Maintains script quality even when falling back to audio-only analysis

### Viral-Focused Script Generation
The endpoint uses specialized AI prompts designed specifically for viral content creation:

#### Structured Script Output
- **Hook Generation**: Creates compelling opening lines (1-2 sentences) designed to grab immediate attention
- **Main Script**: Generates engaging commentary that explains what's happening and why it's worth watching
- **JSON Schema Enforcement**: Ensures consistent output with separate "hook" and "script" fields

#### Viral Content Optimization
- **Engaging Language**: Emphasizes unusual, surprising, or humorous moments
- **Energy and Tone**: Maintains energetic, engaging language suitable for short-form content
- **Audience Focus**: Includes captivating hooks designed to stop viewers from scrolling
- **Brevity Focus**: Ensures content is concise while maintaining viewer understanding

#### System Instructions (Viral-Focused)
The AI uses these specific instructions for viral content:
- Analyze video content for unique and bizarre elements
- Emphasize unusual, surprising, or humorous moments
- Maintain energetic, engaging tone suitable for shorts
- Focus on brevity while ensuring viewer comprehension
- Include compelling hooks to grab attention immediately

## 5. Intelligent Audio Mixing System

### Advanced Audio Blending
Unlike traditional voiceover replacement, the viral shorts endpoint uses sophisticated audio mixing:

#### Dynamic Volume Control
- **Original Audio Reduction**: Reduces original video audio to 30% volume during commentary
- **Commentary Boost**: Amplifies generated commentary to 150% for clear audibility
- **Temporal Adjustment**: Adjusts volume levels based on commentary timing
- **Seamless Integration**: Creates natural-sounding blend between original and commentary audio

#### Viral-Style Audio Processing
- **Commentary-Over-Original**: Maintains original video atmosphere while adding engaging commentary
- **Professional Mixing**: Uses FFmpeg advanced audio filters for broadcast-quality results
- **Timing Synchronization**: Ensures commentary starts at optimal moments
- **Dynamic Range**: Preserves original audio dynamics while ensuring commentary clarity

### Audio Processing Pipeline
1. **Commentary Duration Analysis**: Determines length of generated speech
2. **Original Audio Adjustment**: Lowers original volume during commentary periods
3. **Audio Layering**: Combines adjusted original audio with boosted commentary
4. **Quality Optimization**: Applies professional audio encoding (AAC) for final output

## 6. Language Detection and Localization

### Automatic Language Processing
- **Voice-Based Language Detection**: Automatically detects target language from TTS voice parameter (e.g., "fr-CA-ThierryNeural" → French)
- **Localized Script Generation**: AI generates viral scripts in the detected language
- **UTF-8 Support**: Full support for international characters, accents, and emojis
- **Cultural Adaptation**: Scripts adapt to cultural context of the target language

### Multi-Language Examples
- **English**: `"en-US-AvaNeural"` → English viral script
- **French**: `"fr-CA-ThierryNeural"` → French viral script  
- **Spanish**: `"es-ES-AlvaroNeural"` → Spanish viral script
- **German**: `"de-DE-KlarissaNeural"` → German viral script

## 7. Response

### Success Response

- `short_url` (string): The cloud URL of the generated viral short video file.
- `job_id` (string): A unique identifier for the job.
- `script_data` (object): The AI-generated script data with hook and main content.
- `message` (string): Success confirmation message.

Example:

```json
{
    "short_url": "https://cloud.example.com/viral-short-video.mp4",
    "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "script_data": {
        "hook": "You won't believe what happens next in this viral moment!",
        "script": "This incredible footage shows exactly why this technique is taking social media by storm. The way they execute this move is absolutely mind-blowing and explains why everyone is talking about it."
    },
    "message": "Viral short created successfully"
}
```

### Error Responses

#### Missing or Invalid Parameters

**Status Code:** 400 Bad Request

```json
{
    "error": "Missing 'video_url' parameter"
}
```

#### AI Analysis Failure

**Status Code:** 500 Internal Server Error

```json
{
    "error": "Failed to generate viral script: Gemini AI analysis failed"
}
```

#### Audio Mixing Failure

**Status Code:** 500 Internal Server Error

```json
{
    "error": "Audio mixing failed: FFmpeg process error"
}
```

## 8. Environment Variables

The following environment variables are required for the viral shorts endpoint:

### Required Variables
- `API_KEY`: Main API authentication key
- `GEMINI_API_KEY`: Google Gemini AI API key for video analysis and script generation

### Optional Variables (with defaults)
- `LOCAL_STORAGE_PATH`: Path for temporary file storage (default: `/app/data/tmp`)
- `TTS_SERVER_URL`: URL for TTS service (default: `https://tts.dahopevi.com/api`)

### Example Configuration
```bash
# Required
API_KEY=your_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (with defaults shown)
LOCAL_STORAGE_PATH=/app/data/tmp
TTS_SERVER_URL=https://tts.dahopevi.com/api
```

## 9. Key Differences from Standard Shorts

### Viral-Focused Approach
- **Visual AI Analysis**: Uses Gemini AI to analyze video content visually, not just audio
- **Viral Script Prompts**: Specialized AI instructions for creating engaging, viral-ready content
- **Intelligent Audio Mixing**: Blends original audio with commentary instead of replacing it
- **Simplified Processing**: Streamlined pipeline focused on viral content quality

### Optimizations for Viral Content
- **Hook-First Design**: Prioritizes attention-grabbing opening moments
- **Energy Emphasis**: Focuses on unusual, surprising, or humorous elements
- **Professional Audio**: Advanced mixing creates broadcast-quality audio experience
- **Platform Optimization**: Output format optimized for viral short-form platforms

## 10. Usage Notes

- The `video_url` must be a valid and accessible URL pointing to a video file.
- Ensure that the `GEMINI_API_KEY` environment variable is correctly configured for AI analysis.
- The `tts_voice` parameter determines both the voice and the language for script generation.
- Visual AI analysis provides better results than audio-only analysis for viral content.
- The intelligent audio mixing preserves original video atmosphere while adding engaging commentary.
- All text content supports UTF-8 encoding including international characters and emojis.
- Use the `context` parameter to guide the AI toward specific viral angles or topics.

## 11. Common Issues

- Invalid `video_url` causing download failures.
- Missing `GEMINI_API_KEY` preventing AI analysis.
- Video upload to Gemini AI failing (automatically falls back to transcript analysis).
- Issues with the TTS service (e.g., invalid `tts_voice`).
- Audio mixing failures due to corrupted files or unsupported formats.
- Network issues during video upload or processing.

## 12. Best Practices

- Always validate input parameters before sending requests.
- Use descriptive `context` to guide AI toward specific viral angles.
- Choose voices that match your target audience and platform.
- Utilize webhooks for asynchronous processing to avoid timeouts.
- Monitor logs for detailed error information during development.
- For international content, use native language voices for better viral performance.
- Test with various video types to understand AI analysis capabilities.
- Provide clear, specific context for better viral script generation.
- Consider platform-specific viral trends when providing context guidance.

## 13. Performance Considerations

- Video upload to Gemini AI may take longer for large files but provides better analysis.
- Fallback to transcript analysis ensures reliable processing even with upload failures.
- Intelligent audio mixing adds processing time but significantly improves output quality.
- Cloud storage integration ensures scalable file handling for viral content distribution.
- Asynchronous processing via webhooks recommended for production applications.