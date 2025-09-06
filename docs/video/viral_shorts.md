# Enhanced Viral Shorts Generation Endpoint (v1)

## 1. Overview

The `/v1/video/viral-shorts` endpoint is an advanced video API designed specifically for creating viral-quality short videos using cutting-edge AI analysis and multi-segment compilation technology. This endpoint combines viral content creation best practices with innovative video repurposing features to generate engaging commentary-style shorts that maximize viral potential.

### 🚀 Enhanced Features (New)
- **Multi-Segment Viral Compilation**: Extracts and combines multiple viral moments from throughout the video
- **AI-Powered Duplicate Detection**: Filters out repetitive content for maximum engagement diversity  
- **Precision Timestamp Cutting**: Uses SRT transcription for perfect speech boundary detection
- **Smart Transitions**: Cross-fade transitions between viral segments for professional flow
- **Viral Scoring Algorithm**: Advanced scoring system that identifies the most engaging moments
- **Content Diversity Optimization**: Ensures varied content across different parts of the video

Unlike simple single-segment extraction, this endpoint creates true viral compilations that capture the best moments from the entire video, resulting in shorts with significantly higher engagement potential.

## 2. Endpoint

**URL:** `/v1/video/viral-shorts`
**Method:** `POST`

## 3. Request

### Headers

- `x-api-key`: Required. The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `video_input` (string, required): The video source for generating the viral short. Can be:
  - **YouTube URL**: Any YouTube video URL (youtube.com, youtu.be)
  - **Direct Video URL**: Direct link to video files (.mp4, .webm, .avi, .mov, .mkv, .flv, .wmv, .m4v)
  - **Examples**: `https://youtube.com/watch?v=...`, `https://example.com/video.mp4`
- `context` (string, optional): Additional context to help the AI generate better viral scripts. This can include information about the video topic, target audience, or specific viral angles to emphasize.
- `tts_voice` (string, optional): The voice to be used for the generated commentary voiceover. This determines both the voice and the language for script generation (e.g., "fr-CA-ThierryNeural" will generate French scripts). Defaults to "en-US-AvaNeural".
- `short_duration` (integer, optional): Duration of the viral short in seconds. Range: 15-180. Default: 60. The system will find the best segment from the source video.
- `video_format` (string, optional): Output video format and aspect ratio. Options: "portrait" (9:16), "landscape" (16:9), "square" (1:1). Default: "portrait".
- `add_captions` (boolean, optional): Whether to automatically add viral-style captions to the video. Default: true.
- `cookies_content` (string, optional): YouTube cookies content for authentication when downloading restricted videos.
- `cookies_url` (string, optional): URL to download YouTube cookies from for authentication.
- `auth_method` (string, optional): YouTube authentication method. Options: "auto", "oauth2", "cookies_content", "cookies_url", "cookies_file". Defaults to "auto".
- `webhook_url` (string, optional): A URL to receive a webhook notification when the viral short generation process is complete.
- `id` (string, optional): An identifier for the request.

### Example Requests

#### Example 1: Basic Viral Short Generation (YouTube)
```json
{
    "video_input": "https://www.youtube.com/watch?v=example"
}
```
This minimal request will download the video, analyze it visually with AI, generate a viral script, create commentary voiceover, and intelligently mix it with the original audio.

#### Example 2: Direct Video URL with Custom Duration and Format
```json
{
    "video_input": "https://example.com/interesting_content.mp4",
    "context": "This video shows an amazing life hack that everyone needs to know about",
    "tts_voice": "en-US-GuyNeural",
    "short_duration": 90,
    "video_format": "square"
}
```

#### Example 3: French Viral Short with Direct Video URL
```json
{
    "video_input": "https://example.com/french_content.mp4",
    "context": "Contenu viral français sur les nouvelles technologies",
    "tts_voice": "fr-CA-ThierryNeural",
    "short_duration": 60,
    "video_format": "portrait",
    "add_captions": true
}
```

#### Example 4: WebM Video with Landscape Format
```json
{
    "video_input": "https://example.com/tutorial.webm",
    "context": "Quick tutorial breakdown for viral content",
    "tts_voice": "en-US-AriaNeural",
    "short_duration": 45,
    "video_format": "landscape",
    "add_captions": false
}
```

#### Example 5: YouTube Video with Authentication
```json
{
    "video_input": "https://www.youtube.com/watch?v=restricted_video",
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
        "video_input": "https://example.com/trending_video.mp4",
        "context": "Breaking down this viral moment everyone is talking about",
        "tts_voice": "en-US-AriaNeural"
    }' \
    https://your-api-endpoint.com/v1/video/viral-shorts
```

## 4. Enhanced Multi-Segment Viral Compilation

### Revolutionary Compilation Technology 🔥
The enhanced viral shorts endpoint doesn't just find one good moment - it creates viral compilations by combining multiple engaging segments from throughout the entire video:

#### Multi-Segment Viral Detection
- **20+ Candidate Analysis**: Analyzes up to 20 potential viral moments throughout the video
- **Enhanced Viral Scoring**: Uses advanced algorithm combining audio energy, keywords, scene changes, and engagement indicators  
- **Optimal Duration Distribution**: Segments range from 5-15 seconds each for maximum impact
- **Viral Keyword Detection**: Scans for 70+ viral keywords including reactions, emotions, superlatives, and engagement triggers

#### AI-Powered Content Filtering
- **Duplicate Detection**: Automatically filters out repetitive or similar content (>50% overlap prevention)
- **Content Similarity Analysis**: Uses text analysis to prevent redundant segments  
- **Quality Threshold**: Only includes segments with viral potential score >0.3
- **Diversity Optimization**: Ensures segments are spread across different parts of the video

#### Precision Timestamp Cutting
- **SRT-Based Boundaries**: Uses transcription timestamps to cut at perfect speech boundaries
- **Word-Level Precision**: Avoids cutting mid-word or mid-sentence
- **Natural Flow**: Maintains conversational flow across segment transitions
- **Fallback Protection**: Gracefully handles missing transcription data

#### Smart Transition System
- **Cross-Fade Transitions**: Professional 0.5-second fade transitions between segments
- **Audio Continuity**: Seamless audio mixing across segment boundaries  
- **Visual Flow**: Smooth visual transitions that maintain viewer engagement
- **Dynamic Timing**: Transition timing calculated based on segment content

### Compilation Strategies
The system uses intelligent strategies to create optimal viral compilations:

#### Multi-Segment Strategy (Preferred)
- **3-8 Viral Moments**: Combines multiple high-scoring segments
- **Total Duration Matching**: Precisely matches requested duration (e.g., 60 seconds)
- **Engagement Distribution**: Spreads viral content throughout the compilation
- **Professional Transitions**: Cross-fade effects between segments

#### Single-Segment Fallback
- **High-Quality Single Moment**: Falls back to best single segment when needed
- **Optimal Duration**: Uses the most viral continuous segment
- **Quality Assurance**: Maintains high engagement even with single segment

#### Intelligent Scoring Metrics
- **Viral Score (0.0-1.0)**: Overall viral potential based on multiple factors
- **Diversity Score (0.0-1.0)**: How well content is distributed across video timeline  
- **Engagement Score (0.0-1.0)**: Combined metric predicting audience retention

### Video Format Conversion

#### Automatic Format Optimization
The endpoint converts videos to optimal formats for different platforms:

#### Portrait Format (9:16) - Default
- **Resolution**: 1080x1920 pixels
- **Optimized for**: TikTok, Instagram Reels, YouTube Shorts
- **Padding**: Adds black bars to maintain aspect ratio
- **Quality**: Preserves video quality during conversion

#### Landscape Format (16:9)
- **Resolution**: 1920x1080 pixels  
- **Optimized for**: YouTube, desktop viewing
- **Professional**: Standard broadcast format
- **Compatibility**: Works across all platforms

#### Square Format (1:1)
- **Resolution**: 1080x1080 pixels
- **Optimized for**: Instagram posts, social media
- **Versatile**: Works on both mobile and desktop
- **Consistent**: Uniform appearance across devices

### Automatic Captions System

#### Viral-Optimized Caption Style
- **Word-by-word highlighting**: Each word appears as spoken for maximum engagement
- **Bold, all-caps text**: High-impact visual style for viral content
- **Strong contrast**: White text with black outline for visibility
- **Bottom positioning**: Doesn't block important visual content

#### Caption Features
- **Automatic generation**: Created from TTS timing for perfect synchronization
- **Language matching**: Captions match the script language automatically
- **Mobile optimized**: Large, readable text for mobile viewing
- **Platform ready**: Style optimized for viral short-form platforms

## 5. Advanced AI Analysis Features

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

### Enhanced Success Response

#### Primary Response Fields
- `short_url` (string): The cloud URL of the generated viral short video file.
- `job_id` (string): A unique identifier for the job.
- `script_data` (object): The AI-generated script data with hook and main content.
- `segment_info` (object): Legacy field - single segment info (null for multi-segment compilations).
- `compilation_info` (object): **NEW** - Complete compilation information including all segments and metadata.
- `source_metadata` (object): Information about the processed video source.
- `video_format` (string): The output video format applied.
- `duration` (integer): The duration of the generated short in seconds.
- `language` (string): The language used for script generation.
- `enhanced_features` (object): **NEW** - Enhanced compilation features and metrics.
- `message` (string): Success confirmation with segment count.

#### Enhanced Multi-Segment Response Example:

```json
{
    "short_url": "https://cloud.example.com/viral-compilation-short.mp4",
    "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "script_data": {
        "hook": "This compilation shows the 5 most viral moments that broke the internet!",
        "script": "From the incredible opening sequence to the mind-blowing finale, these moments capture exactly why this content went viral and had millions of viewers rewatching again and again."
    },
    "segment_info": null,
    "compilation_info": {
        "segments": [
            {
                "start_time": 12.5,
                "end_time": 20.8,
                "score": 0.92,
                "viral_score": 0.95,
                "reason": "High energy moment with viral keywords",
                "precision_adjusted": true,
                "srt_segments": [
                    {
                        "index": 3,
                        "start_time": 12.5,
                        "end_time": 15.2,
                        "text": "This is absolutely incredible!"
                    }
                ]
            },
            {
                "start_time": 45.2,
                "end_time": 56.7,
                "score": 0.88,
                "viral_score": 0.91,
                "reason": "Scene change with emotional reaction",
                "precision_adjusted": true
            },
            {
                "start_time": 87.3,
                "end_time": 99.1,
                "score": 0.85,
                "viral_score": 0.89,
                "reason": "Climactic moment with engaging audio",
                "precision_adjusted": true
            }
        ],
        "metadata": {
            "viral_score": 0.91,
            "diversity_score": 0.83,
            "engagement_score": 0.89,
            "segment_count": 3,
            "compilation_strategy": "multi_segment_compilation_3_segments",
            "precision_timing_applied": true,
            "total_duration": 59.3,
            "transition_time": 1.0,
            "average_segment_duration": 9.77
        }
    },
    "source_metadata": {
        "source_type": "youtube_url",
        "original_url": "https://youtube.com/watch?v=example",
        "title": "Amazing Viral Moments Compilation"
    },
    "video_format": "portrait",
    "duration": 60,
    "language": "en",
    "enhanced_features": {
        "multi_segment_compilation": true,
        "viral_score": 0.91,
        "diversity_score": 0.83,
        "engagement_score": 0.89,
        "compilation_strategy": "multi_segment_compilation_3_segments",
        "precision_timing_applied": true
    },
    "message": "Enhanced viral short created successfully with 3 segment(s)"
}
```

#### Single-Segment Response Example (Fallback):

```json
{
    "short_url": "https://cloud.example.com/viral-single-short.mp4",
    "job_id": "b2c3d4e5-f6g7-8901-2345-678901bcdefg",
    "script_data": {
        "hook": "You won't believe what happens in this viral moment!",
        "script": "This single incredible sequence shows exactly why this content became an instant viral sensation."
    },
    "segment_info": {
        "start_time": 45.2,
        "end_time": 105.2,
        "score": 0.85,
        "reason": "High audio energy and engaging keywords"
    },
    "compilation_info": {
        "segments": [
            {
                "start_time": 45.2,
                "end_time": 105.2,
                "score": 0.85,
                "viral_score": 0.87,
                "reason": "High audio energy and engaging keywords"
            }
        ],
        "metadata": {
            "viral_score": 0.87,
            "diversity_score": 0.5,
            "engagement_score": 0.74,
            "segment_count": 1,
            "compilation_strategy": "single_segment_fallback",
            "precision_timing_applied": false
        }
    },
    "video_format": "portrait",
    "duration": 60,
    "language": "en",
    "enhanced_features": {
        "multi_segment_compilation": false,
        "viral_score": 0.87,
        "diversity_score": 0.5,
        "engagement_score": 0.74,
        "compilation_strategy": "single_segment_fallback",
        "precision_timing_applied": false
    },
    "message": "Enhanced viral short created successfully with 1 segment(s)"
}
```

### Error Responses

#### Missing or Invalid Parameters

**Status Code:** 400 Bad Request

```json
{
    "error": "Missing 'video_input' parameter"
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

### Example Configuration
```bash
# Required
API_KEY=your_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (with defaults shown)
LOCAL_STORAGE_PATH=/app/data/tmp
```

## 9. Revolutionary Enhancements vs. Standard Processing

### Multi-Segment Compilation Technology 🚀
- **True Viral Compilation**: Creates compilations with 3-8 viral moments instead of single segments
- **AI-Powered Segment Selection**: Analyzes 20+ candidates to find the most viral moments
- **Precision Timing**: Uses SRT transcription for word-perfect cutting boundaries
- **Smart Transitions**: Professional cross-fade transitions between viral segments
- **Duplicate Filtering**: Prevents repetitive content with advanced similarity detection

### Enhanced Viral Detection
- **70+ Viral Keywords**: Expanded keyword detection including emotions, reactions, and engagement triggers
- **Multi-Modal Scoring**: Combines audio energy, scene changes, transcription analysis, and viral keywords
- **Engagement Prediction**: Advanced metrics predict viral potential and audience retention
- **Content Diversity**: Ensures varied content across different parts of the source video

### Professional Compilation Features
- **Seamless Transitions**: Cross-fade effects with perfect timing calculations
- **Audio Continuity**: Intelligent mixing preserves audio flow across segment boundaries
- **Precision Boundaries**: SRT-based cutting ensures natural speech flow
- **Quality Thresholds**: Only includes segments with viral potential >0.3

### Enhanced Analytics & Insights
- **Viral Score (0.0-1.0)**: Predicts viral potential based on multiple engagement factors
- **Diversity Score (0.0-1.0)**: Measures content variety across video timeline
- **Engagement Score (0.0-1.0)**: Combined metric for audience retention prediction
- **Segment-Level Analytics**: Individual viral scores and reasons for each segment

### Backward Compatibility
- **Legacy Support**: Single-segment fallback maintains compatibility with existing workflows
- **Graceful Degradation**: Automatically falls back to single segments when compilation fails
- **Enhanced Responses**: New fields added without breaking existing integrations

## 10. Enhanced Usage Notes

### Video Input Requirements
- **Supported Formats**: YouTube URLs and direct video files (.mp4, .webm, .avi, .mov, .mkv, .flv, .wmv, .m4v)
- **Optimal Length**: 2+ minute videos provide more viral moments for compilation
- **Quality**: Higher quality source videos result in better viral segment detection

### Multi-Segment Compilation Behavior
- **Duration Targeting**: System intelligently combines segments to match requested duration (15-180s)
- **Automatic Fallback**: Falls back to single-segment if compilation analysis fails
- **Transition Handling**: 0.5s transitions automatically added between segments (accounted for in total duration)
- **Segment Distribution**: Prefers 5-15 second segments for optimal viral impact

### Enhanced Configuration
- **Precision Timing**: Enable with high-quality transcription for word-perfect boundaries
- **Viral Keywords**: System automatically scans for 70+ engagement indicators  
- **Content Filtering**: Duplicate segments filtered automatically (>50% overlap prevention)
- **Quality Thresholds**: Only segments with >0.3 viral score included in compilations

### AI Analysis Optimization
- **Gemini Visual Analysis**: Provides superior results for viral content detection
- **Transcription Enhancement**: SRT timestamps enable precision cutting and better segment analysis
- **Fallback Strategy**: Graceful degradation from visual → transcript → basic analysis
- **Multi-Modal Scoring**: Combines visual, audio, and text analysis for best results

### Response Interpretation
- **compilation_info**: Contains complete segment details and analytics
- **enhanced_features**: Provides viral scores and compilation metadata
- **segment_info**: Legacy field (null for multi-segment compilations)
- **Viral Scores**: >0.7 = High viral potential, >0.5 = Good potential, >0.3 = Acceptable

### Platform Optimization
- **Format Selection**: "portrait" for TikTok/Instagram, "landscape" for YouTube, "square" for social posts
- **Cross-Platform**: Multi-segment compilations work well across all platforms
- **Engagement Optimization**: System optimizes for each platform's viral characteristics

## 11. Common Issues

- Invalid `video_input` causing download failures.
- Missing `GEMINI_API_KEY` preventing AI analysis.
- Video upload to Gemini AI failing (automatically falls back to transcript analysis).
- Issues with the TTS service (e.g., invalid `tts_voice`).
- Audio mixing failures due to corrupted files or unsupported formats.
- Network issues during video upload or processing.

## 12. Enhanced Best Practices

### Video Selection for Optimal Compilation
- **Longer Videos (2+ minutes)**: Provide more viral moments for better compilations
- **High-Energy Content**: Videos with dynamic moments, reactions, and engagement work best
- **Clear Audio**: Good audio quality improves transcription and viral keyword detection
- **Varied Content**: Videos with different types of moments create better diversity scores

### Maximizing Viral Potential
- **Context Optimization**: Use descriptive context to guide AI toward specific viral angles
- **Platform-Specific**: Tailor context for target platform (TikTok vs YouTube vs Instagram)
- **Viral Keywords**: Include words like "amazing", "incredible", "unbelievable" in context
- **Trend Awareness**: Reference current trends and viral formats in context

### Technical Optimization
- **Voice Selection**: Choose voices matching target audience and language for better engagement
- **Duration Strategy**: 60-90 second compilations typically perform best for viral content
- **Format Selection**: Use "portrait" for mobile-first platforms, "landscape" for desktop
- **Webhook Integration**: Use webhooks for production to handle longer processing times

### Monitoring & Analytics
- **Viral Scores**: Target compilations with >0.7 viral scores for best performance
- **Diversity Scores**: Higher diversity (>0.6) typically leads to better engagement
- **Segment Analysis**: Review individual segment reasons to understand what works
- **Compilation Strategy**: Monitor which strategies (multi vs single) work best for your content

### Development Guidelines
- **Error Handling**: Monitor logs for compilation failures and fallback behaviors
- **Testing Strategy**: Test with various video types and lengths to understand capabilities
- **Response Parsing**: Use new `compilation_info` and `enhanced_features` fields for insights
- **Backward Compatibility**: Maintain support for legacy `segment_info` field if needed

### Content Strategy
- **Multi-Segment Benefits**: Emphasize multi-segment compilations for higher engagement
- **Transcription Quality**: Ensure good audio quality for precision timing features
- **Language Consistency**: Match TTS voice language with video content language
- **International Content**: Use native language voices for cultural authenticity

## 13. Performance Considerations

- Video upload to Gemini AI may take longer for large files but provides better analysis.
- Fallback to transcript analysis ensures reliable processing even with upload failures.
- Intelligent audio mixing adds processing time but significantly improves output quality.
- Cloud storage integration ensures scalable file handling for viral content distribution.
- Asynchronous processing via webhooks recommended for production applications.