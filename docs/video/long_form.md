# Long-Form Video Generation Endpoint (v1)

## 1. Overview

The `/v1/video/long-form` endpoint is designed specifically for creating professional, structured long-form videos optimized for YouTube and educational platforms. This endpoint transforms source videos into comprehensive commentary-style content ranging from 5-60 minutes, with intelligent script structuring, professional audio mixing, and automatic language detection. Unlike viral shorts, this endpoint focuses on educational value, detailed analysis, and professional presentation quality.

## 2. Endpoint

**URL:** `/v1/video/long-form`
**Method:** `POST`

## 3. Request

### Headers

- `x-api-key`: Required. The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `video_url` (string, required): The URL of the source video from which the long-form content will be generated.
- `target_duration` (integer, optional): Target duration for the final video in seconds. Range: 300-3600 (5-60 minutes). Default: 600 (10 minutes).
- `content_style` (string, optional): The style of content to generate. Options: "educational", "commentary", "documentary", "analysis". Default: "educational".
- `script_tone` (string, optional): The tone for the generated script. Options: "professional", "casual", "academic", "conversational". Default: "professional".
- `video_format` (string, optional): Output video format and aspect ratio. Options: "landscape" (16:9), "portrait" (9:16), "square" (1:1), "original". Default: "landscape".
- `resolution` (object, optional): Custom video resolution settings:
  - `width` (integer, 720-4096): Video width in pixels
  - `height` (integer, 480-4096): Video height in pixels
- `audio_strategy` (string, optional): Audio mixing strategy. Options: "commentary_focused", "balanced", "original_focused", "background_only". Default: "commentary_focused".
- `add_background_music` (boolean, optional): Whether to add background music. Default: false. (Future feature)
- `normalize_audio` (boolean, optional): Whether to normalize audio levels for broadcast quality. Default: true.
- `fade_transitions` (boolean, optional): Whether to add fade transitions between sections. Default: true.
- `add_captions` (boolean, optional): Whether to automatically add professional captions. Default: true.
- `context` (string, optional): Additional context to help AI generate better content specific to your needs.
- `tts_voice` (string, optional): Voice for TTS generation. This also determines the script language (e.g., "fr-CA-ThierryNeural" generates French content). Default: "en-US-AvaNeural".
- `cookies_content` (string, optional): YouTube cookies content for authentication.
- `cookies_url` (string, optional): URL to download YouTube cookies from.
- `auth_method` (string, optional): YouTube authentication method. Options: "auto", "oauth2", "cookies_content", "cookies_url", "cookies_file". Default: "auto".
- `webhook_url` (string, optional): URL to receive completion notification.
- `id` (string, optional): Request identifier.

### Example Requests

#### Example 1: Basic Educational Long-Form Video

```json
{
    "video_url": "https://example.com/lecture.mp4",
    "target_duration": 900,
    "content_style": "educational"
}
```

#### Example 2: French Documentary-Style Analysis

```json
{
    "video_url": "https://example.com/documentary.mp4",
    "target_duration": 1200,
    "content_style": "documentary",
    "script_tone": "academic",
    "tts_voice": "fr-FR-DeniseNeural",
    "video_format": "landscape",
    "context": "Analyse approfondie du contenu historique"
}
```

#### Example 3: Professional Commentary for YouTube

```json
{
    "video_url": "https://www.youtube.com/watch?v=example",
    "target_duration": 600,
    "content_style": "commentary",
    "script_tone": "professional",
    "video_format": "landscape",
    "audio_strategy": "balanced",
    "add_captions": true,
    "normalize_audio": true
}
```

#### Example 4: Casual Analysis with Custom Resolution

```json
{
    "video_url": "https://example.com/tutorial.mp4",
    "target_duration": 1800,
    "content_style": "analysis",
    "script_tone": "conversational",
    "video_format": "landscape",
    "resolution": {
        "width": 1920,
        "height": 1080
    },
    "audio_strategy": "commentary_focused",
    "context": "Break down the technical aspects for developers"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
        "video_url": "https://example.com/conference_talk.mp4",
        "target_duration": 900,
        "content_style": "educational",
        "script_tone": "professional",
        "video_format": "landscape"
    }' \
    https://your-api-endpoint.com/v1/video/long-form
```

## 4. Content Styles and AI Optimization

### Educational Style
Designed for instructional and learning content:

#### Features
- **Clear learning objectives**: Each section has defined takeaways
- **Progressive structure**: Builds from basic to advanced concepts
- **Examples and explanations**: Includes practical applications
- **Knowledge reinforcement**: Periodic summaries and key points
- **Student-focused language**: Clear, accessible explanations

#### Best For
- Tutorial explanations
- Course material creation
- Skill development content
- How-to guides and instructions

### Commentary Style  
Perfect for reaction and analysis content:

#### Features
- **Context and background**: Provides necessary information for understanding
- **Multiple perspectives**: Explores different viewpoints and opinions
- **Critical analysis**: Examines key moments and decisions
- **Personal insights**: Adds expert commentary and observations
- **Engaging discussion**: Poses thought-provoking questions

#### Best For
- Reaction videos
- Event analysis
- Opinion pieces
- Discussion content

### Documentary Style
Creates narrative-driven, storytelling content:

#### Features
- **Compelling storytelling**: Clear narrative arc with beginning, middle, end
- **Historical context**: Background information and timeline
- **Character development**: Focus on people and human interest
- **Dramatic pacing**: Builds tension and emotional engagement
- **Factual accuracy**: Well-researched, evidence-based content

#### Best For
- Historical analysis
- Biography content
- Event reconstruction
- Investigative pieces

### Analysis Style
Provides systematic, data-driven examination:

#### Features
- **Systematic breakdown**: Methodical examination of components
- **Evidence-based insights**: Uses data and facts to support conclusions
- **Comparative analysis**: Benchmarks against standards or alternatives  
- **Professional evaluation**: Expert-level assessment and judgment
- **Actionable recommendations**: Practical next steps and suggestions

#### Best For
- Technical analysis
- Business case studies
- Performance reviews
- Research presentations

## 5. Advanced Audio Mixing Strategies

### Commentary Focused (Default)
Optimized for educational and commentary content:
- **Original audio**: 20% volume
- **Commentary**: 120% volume  
- **Best for**: Educational content where your voice is primary
- **Professional mixing**: Ensures commentary clarity

### Balanced Mixing
Equal emphasis on both audio sources:
- **Original audio**: 50% volume
- **Commentary**: 100% volume
- **Best for**: Discussion and reaction content
- **Natural blend**: Maintains original atmosphere

### Original Focused
Preserves original audio prominence:
- **Original audio**: 80% volume
- **Commentary**: 60% volume
- **Best for**: Music analysis, preserving original quality
- **Subtle enhancement**: Adds commentary without overwhelming

### Background Only
Complete commentary replacement:
- **Original audio**: 0% volume
- **Commentary**: 100% volume
- **Best for**: Full narration over visuals
- **Clean audio**: Professional voice-over style

### Advanced Audio Features

#### Broadcast-Quality Normalization
- **Loudness standards**: Meets broadcast audio requirements (-23 LUFS)
- **Dynamic range**: Optimal balance between quiet and loud sections
- **Consistent levels**: Even audio throughout long-form content
- **Professional polish**: Studio-quality audio output

#### Intelligent Fade Transitions
- **Smooth transitions**: Natural audio flow between sections
- **Section-based mixing**: Different levels for intro, main content, conclusion
- **Temporal optimization**: Audio adjusts based on content timing
- **Professional polish**: Eliminates abrupt audio changes

## 6. Video Format and Resolution Options

### Landscape Format (16:9) - Default
**Resolution**: 1920x1080 pixels
- **YouTube optimized**: Perfect for YouTube's primary format
- **Desktop viewing**: Ideal for computer and TV screens
- **Professional standard**: Broadcast and professional video format
- **Wide compatibility**: Works across all major platforms

### Portrait Format (9:16)
**Resolution**: 1080x1920 pixels
- **YouTube Shorts**: Optimized for vertical short-form content
- **Mobile first**: Perfect for smartphone viewing
- **Social media**: Instagram Reels, TikTok compatibility
- **Engaging format**: Captures full mobile screen

### Square Format (1:1)
**Resolution**: 1080x1080 pixels
- **Instagram posts**: Perfect for Instagram feed content
- **Social sharing**: Consistent appearance across platforms
- **Versatile display**: Works on both mobile and desktop
- **Compact format**: Efficient use of screen space

### Original Format
Maintains source video dimensions:
- **No conversion**: Preserves exact original resolution
- **Quality preservation**: No quality loss from scaling
- **Authentic presentation**: Maintains creator's intended format
- **Flexibility**: Supports any source video format

### Custom Resolution
Specify exact dimensions for specialized needs:
- **Precise control**: Set exact width and height
- **Aspect ratio handling**: Automatic padding to maintain proportions
- **Quality optimization**: Smart scaling for best results
- **Professional requirements**: Meet specific technical specifications

## 7. Automatic Language Detection and Localization

### Voice-Based Language Detection
The system automatically detects target language from the `tts_voice` parameter:

#### Supported Languages
- **English**: `"en-US-AvaNeural"` → English content
- **French**: `"fr-CA-ThierryNeural"` → French content
- **Spanish**: `"es-ES-AlvaroNeural"` → Spanish content
- **German**: `"de-DE-KlarissaNeural"` → German content
- **Italian**: `"it-IT-ElsaNeural"` → Italian content
- **Portuguese**: `"pt-BR-FranciscaNeural"` → Portuguese content

#### Language-Aware Features
- **Script generation**: AI creates content in detected language
- **Cultural adaptation**: Content adapts to cultural context
- **Professional localization**: Native-level language quality
- **Caption synchronization**: Captions match script language automatically

### International Content Support
- **UTF-8 encoding**: Full support for international characters
- **Accent handling**: Proper support for accented characters
- **Emoji support**: International emoji and special characters
- **Cultural context**: AI adapts content style to target culture

## 8. Professional Captions System

### Long-Form Optimized Captions
Designed specifically for educational and professional content:

#### Caption Features
- **Classic styling**: Professional appearance suitable for educational content
- **Readable fonts**: Clear, legible text optimized for long viewing
- **Subtle presentation**: Doesn't distract from main content
- **High contrast**: White text with black outline for visibility
- **Bottom positioning**: Standard placement for professional content

#### Caption Quality
- **Perfect synchronization**: Generated from TTS timing for exact match
- **Sentence-based timing**: Natural reading pace and rhythm
- **Language matching**: Captions automatically match script language
- **Professional formatting**: Proper capitalization and punctuation

### Accessibility Features
- **Screen reader compatible**: Meets accessibility standards
- **High visibility**: Optimized for viewers with visual impairments
- **Consistent styling**: Uniform appearance throughout video
- **Multiple language support**: Works with all supported languages

## 9. Response

### Success Response

- `video_url` (string): The cloud URL of the generated long-form video file.
- `job_id` (string): A unique identifier for the job.
- `script_data` (object): The complete structured script with sections.
- `content_style` (string): The content style used for generation.
- `target_duration` (integer): The requested target duration in seconds.
- `actual_duration` (integer): The estimated actual duration based on script.
- `video_format` (string): The output video format applied.
- `audio_strategy` (string): The audio mixing strategy used.
- `language` (string): The language used for script generation.
- `captions_added` (boolean): Whether captions were added to the video.
- `message` (string): Success confirmation message.

Example:

```json
{
    "video_url": "https://cloud.example.com/long-form-video.mp4",
    "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "script_data": {
        "title": "Understanding Advanced Machine Learning Concepts",
        "introduction": "Welcome to this comprehensive guide...",
        "main_sections": [
            {
                "title": "Neural Network Fundamentals",
                "content": "Neural networks form the backbone...",
                "duration_estimate": 180
            },
            {
                "title": "Deep Learning Applications", 
                "content": "Deep learning has revolutionized...",
                "duration_estimate": 240
            }
        ],
        "conclusion": "In conclusion, machine learning...",
        "total_duration_estimate": 600
    },
    "content_style": "educational",
    "target_duration": 600,
    "actual_duration": 600,
    "video_format": "landscape",
    "audio_strategy": "commentary_focused",
    "language": "en",
    "captions_added": true,
    "message": "Long-form video created successfully"
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
    "error": "Failed to generate long-form script: Gemini AI analysis failed"
}
```

#### Video Processing Failure
**Status Code:** 500 Internal Server Error

```json
{
    "error": "Audio mixing failed: FFmpeg process error"
}
```

## 10. Environment Variables

### Required Variables
- `API_KEY`: Main API authentication key
- `GEMINI_API_KEY`: Google Gemini AI API key for script generation and video analysis

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

## 11. Usage Notes

- The `video_url` must be a valid and accessible URL pointing to a video file.
- Ensure that the `GEMINI_API_KEY` environment variable is correctly configured for AI analysis.
- The `tts_voice` parameter determines both the voice and the language for script generation.
- `target_duration` helps the AI structure content appropriately - longer durations allow for more detailed analysis.
- Choose `content_style` based on your target audience: "educational" for learning, "commentary" for reactions, "documentary" for storytelling, "analysis" for technical content.
- `script_tone` affects the formality level: "professional" for business content, "casual" for informal discussions, "academic" for scholarly content, "conversational" for friendly presentations.
- Video format should match your target platform: "landscape" for YouTube, "portrait" for mobile-first content, "square" for social media.
- Audio strategies can be mixed: "commentary_focused" for education, "balanced" for discussions, "background_only" for pure narration.
- Professional audio normalization ensures consistent volume levels throughout long-form content.
- Captions are automatically generated and synchronized for professional presentation.
- All text content supports UTF-8 encoding including international characters and emojis.
- Use the `context` parameter to provide specific guidance on content focus and target audience.

## 12. Common Issues

- Invalid `video_url` causing download failures.
- Missing `GEMINI_API_KEY` preventing AI analysis.
- Video upload to Gemini AI failing (automatically falls back to transcript analysis).
- Issues with the TTS service (e.g., invalid `tts_voice`).
- Audio mixing failures due to corrupted files or unsupported formats.
- Network issues during video processing or upload.
- Insufficient context leading to generic content (provide detailed context for better results).

## 13. Best Practices

### Content Planning
- Provide detailed `context` describing your target audience and content goals
- Choose appropriate `content_style` and `script_tone` for your intended use
- Set realistic `target_duration` based on source material complexity
- Consider your target platform when selecting `video_format`

### Technical Optimization
- Use `commentary_focused` audio strategy for educational content
- Enable `normalize_audio` for professional broadcast quality
- Keep `add_captions` enabled for accessibility and engagement
- Choose appropriate `tts_voice` to match your content language and style

### Language and Localization
- Select TTS voices that match your target language and region
- Provide context in the target language for better AI understanding
- Consider cultural context when creating international content
- Test with sample content before processing large batches

### Quality Assurance
- Monitor logs for detailed processing information
- Use webhooks for asynchronous processing of long-form content
- Validate input parameters before sending requests
- Test audio quality with different mixing strategies for your content type

## 14. Performance Considerations

- Long-form video processing takes significantly longer than shorts (5-30 minutes depending on target duration)
- Video upload to Gemini AI may take time for large files but provides superior script quality
- Fallback to transcript analysis ensures reliable processing even with upload failures
- Professional audio mixing and normalization add processing time but significantly improve quality
- Caption generation is optimized for long-form content pacing
- Cloud storage integration ensures scalable handling of large video files
- Asynchronous processing via webhooks is highly recommended for production applications

## 15. Integration Examples

### Educational Content Pipeline
```python
import requests

def create_educational_series(video_urls, target_language="en"):
    results = []
    
    for i, url in enumerate(video_urls):
        voice_map = {
            "en": "en-US-AvaNeural",
            "fr": "fr-CA-ThierryNeural", 
            "es": "es-ES-AlvaroNeural"
        }
        
        response = requests.post(
            'https://api.example.com/v1/video/long-form',
            headers={'x-api-key': 'your_api_key'},
            json={
                'video_url': url,
                'target_duration': 900,  # 15 minutes
                'content_style': 'educational',
                'script_tone': 'professional',
                'tts_voice': voice_map.get(target_language, "en-US-AvaNeural"),
                'video_format': 'landscape',
                'add_captions': True,
                'context': f'This is lesson {i+1} in a comprehensive educational series'
            }
        )
        results.append(response.json())
    
    return results
```

### Multi-Language Content Creation
```python
def create_multilingual_content(video_url, languages):
    results = {}
    
    language_configs = {
        'en': {'voice': 'en-US-AvaNeural', 'tone': 'professional'},
        'fr': {'voice': 'fr-CA-ThierryNeural', 'tone': 'professional'},
        'es': {'voice': 'es-ES-AlvaroNeural', 'tone': 'conversational'},
        'de': {'voice': 'de-DE-KlarissaNeural', 'tone': 'academic'}
    }
    
    for lang in languages:
        config = language_configs.get(lang, language_configs['en'])
        
        response = requests.post(
            'https://api.example.com/v1/video/long-form',
            headers={'x-api-key': 'your_api_key'},
            json={
                'video_url': video_url,
                'target_duration': 600,
                'content_style': 'commentary',
                'script_tone': config['tone'],
                'tts_voice': config['voice'],
                'video_format': 'landscape',
                'context': f'Create engaging commentary in {lang} for international audience'
            }
        )
        results[lang] = response.json()
    
    return results
```