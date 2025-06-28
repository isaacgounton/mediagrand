# Video Clips Generation Endpoint (v1)

## 1. Overview

The `/v1/video/generate-clips` endpoint is designed for automatically generating multiple video clips from a single source video using intelligent segmentation analysis. This endpoint focuses specifically on clip extraction and processing, without adding voiceover or commentary. It uses advanced AI-powered video analysis to identify the most interesting segments and creates standalone clips with optional resizing, formatting, and quality optimization.

## 2. Endpoint

**URL:** `/v1/video/generate-clips`
**Method:** `POST`

## 3. Request

### Headers

- `x-api-key`: Required. The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `video_url` (string, required): The URL of the source video from which clips will be generated.
- `num_clips` (integer, optional): Number of clips to generate from the video. Range: 1-20. Default: 3.
- `clip_duration` (integer, optional): Duration of each clip in seconds. Range: 15-180. Default: 60.
- `segment_method` (string, optional): Method for identifying video segments. Options: "auto", "equal_parts", "highlights", "chapters". Default: "auto".
  - `"auto"`: Automatically chooses the best method based on video content and available transcription
  - `"highlights"`: Uses AI analysis to detect interesting segments based on audio energy, transcription keywords, and scene changes
  - `"equal_parts"`: Divides the video into equal time segments
  - `"chapters"`: Uses video chapter markers if available (falls back to equal_parts)
- `video_format` (string, optional): Output video orientation and aspect ratio. Options: "portrait" (9:16), "landscape" (16:9), "square" (1:1), "original". Default: "portrait".
- `resolution` (object, optional): Custom video resolution settings:
  - `width` (integer, 480-4096): Video width in pixels
  - `height` (integer, 480-4096): Video height in pixels
- `cookies_content` (string, optional): YouTube cookies content for authentication when downloading restricted videos.
- `cookies_url` (string, optional): URL to download YouTube cookies from for authentication.
- `auth_method` (string, optional): YouTube authentication method. Options: "auto", "oauth2", "cookies_content", "cookies_url", "cookies_file". Default: "auto".
- `webhook_url` (string, optional): A URL to receive a webhook notification when the clip generation process is complete.
- `id` (string, optional): An identifier for the request.

### Example Requests

#### Example 1: Basic Clip Generation
```json
{
    "video_url": "https://example.com/long_video.mp4"
}
```
This minimal request will generate 3 portrait clips of 60 seconds each using automatic segmentation.

#### Example 2: Multiple Landscape Clips with Highlights
```json
{
    "video_url": "https://www.youtube.com/watch?v=example",
    "num_clips": 5,
    "clip_duration": 45,
    "segment_method": "highlights",
    "video_format": "landscape"
}
```

#### Example 3: Square Clips with Custom Resolution
```json
{
    "video_url": "https://example.com/podcast.mp4",
    "num_clips": 4,
    "clip_duration": 30,
    "video_format": "square",
    "resolution": {
        "width": 1080,
        "height": 1080
    }
}
```

#### Example 4: Equal Parts Segmentation with Original Format
```json
{
    "video_url": "https://example.com/tutorial.mp4",
    "num_clips": 6,
    "clip_duration": 90,
    "segment_method": "equal_parts",
    "video_format": "original"
}
```

#### Example 5: Advanced Configuration with Authentication
```json
{
    "video_url": "https://www.youtube.com/watch?v=restricted_video",
    "num_clips": 3,
    "clip_duration": 60,
    "segment_method": "highlights",
    "video_format": "portrait",
    "cookies_content": "your_youtube_cookies_here",
    "auth_method": "cookies_content",
    "webhook_url": "https://my-app.com/clips-callback",
    "id": "clips-batch-001"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
        "video_url": "https://example.com/conference_talk.mp4",
        "num_clips": 4,
        "clip_duration": 75,
        "segment_method": "highlights",
        "video_format": "landscape"
    }' \
    https://your-api-endpoint.com/v1/video/generate-clips
```

## 4. Intelligent Video Segmentation

### AI-Powered Segment Detection
The clips generator uses advanced analysis to identify the most interesting parts of videos:

#### Audio Energy Analysis
- **RMS Energy Detection**: Analyzes audio energy levels to find exciting moments
- **Spectral Centroid Analysis**: Detects brightness and tonal changes in audio
- **Dynamic Range Scoring**: Identifies segments with high audio activity and engagement
- **Volume Variation**: Finds moments with significant audio changes indicating important content

#### Transcription-Based Intelligence
- **Keyword Detection**: Scans transcriptions for engaging words and phrases
- **Emotional Language**: Identifies excitement, surprise, controversy, and other engaging markers
- **Question and Answer Patterns**: Detects interactive content that performs well in clips
- **Topic Transitions**: Identifies natural break points and topic changes

#### Visual Scene Analysis
- **Scene Change Detection**: Uses computer vision to identify significant visual transitions
- **Frame Difference Analysis**: Calculates visual changes between frames
- **Content Variety Scoring**: Prioritizes segments with visual diversity and movement
- **Motion Analysis**: Detects high-motion segments that are typically more engaging

#### Combined Scoring Algorithm
- **Multi-factor Analysis**: Combines audio, transcription, and visual scores
- **Weighted Importance**: Balances different factors based on content type
- **Temporal Optimization**: Ensures segments meet target duration requirements
- **Overlap Resolution**: Intelligently merges overlapping high-scoring segments
- **Quality Ranking**: Sorts all potential segments by engagement score

### Segmentation Methods

#### Auto Method
- **Intelligent Selection**: Automatically chooses between highlights and equal_parts
- **Content Analysis**: Determines best approach based on available data
- **Fallback Strategy**: Uses equal_parts if AI analysis fails
- **Optimization**: Balances quality and reliability

#### Highlights Method
- **AI-Driven Selection**: Uses full analysis pipeline for optimal segments
- **Engagement Focus**: Prioritizes most interesting and engaging content
- **Score-Based Ranking**: Selects top-scoring segments across the video
- **Dynamic Duration**: Adjusts segment boundaries for optimal content

#### Equal Parts Method
- **Consistent Coverage**: Divides video into equal time segments
- **Reliable Distribution**: Ensures even coverage across entire video
- **Predictable Output**: Consistent results regardless of content type
- **Simple Processing**: Faster processing with guaranteed results

#### Chapters Method (Future Enhancement)
- **Metadata-Based**: Uses video chapter markers when available
- **Natural Boundaries**: Respects content creator's intended segments
- **Fallback Support**: Automatically switches to equal_parts if no chapters

## 5. Video Format and Resolution Control

### Format Options
The endpoint supports multiple video orientations optimized for different platforms:

#### Portrait Format (9:16)
- **Default Resolution**: 1080x1920 pixels
- **Platform Optimization**: Perfect for TikTok, Instagram Reels, YouTube Shorts
- **Mobile-First**: Optimized for vertical mobile viewing
- **Social Media Ready**: Ideal aspect ratio for modern social platforms

#### Landscape Format (16:9)
- **Default Resolution**: 1920x1080 pixels
- **Traditional Format**: Standard horizontal video format
- **Desktop Friendly**: Optimal for YouTube, Vimeo, and desktop viewing
- **Broadcast Standard**: Professional video production standard

#### Square Format (1:1)
- **Default Resolution**: 1080x1080 pixels
- **Social Media**: Perfect for Instagram posts and square video requirements
- **Uniform Display**: Consistent appearance across different devices
- **Versatile Use**: Works well for both mobile and desktop

#### Original Format
- **Unchanged Dimensions**: Preserves source video's original resolution
- **No Scaling**: Maintains exact pixel dimensions and aspect ratio
- **Quality Preservation**: No quality loss from resizing operations
- **Format Flexibility**: Supports any source video format

### Resolution Control
- **Custom Dimensions**: Override defaults with specific width and height
- **Aspect Ratio Handling**: Automatic scaling with black padding to maintain proportions
- **Quality Optimization**: Smart scaling ensures high-quality output
- **Size Validation**: Ensures output dimensions are within supported ranges (480-4096 pixels)

### Video Processing Pipeline
1. **Segment Extraction**: Uses FFmpeg to extract precise time segments
2. **Format Conversion**: Applies scaling and aspect ratio adjustments
3. **Quality Optimization**: Maintains video quality during processing
4. **Codec Optimization**: Uses efficient encoding for optimal file sizes

## 6. Response

### Success Response

- `clips` (array): Array of generated clip objects with metadata.
- `job_id` (string): A unique identifier for the job.
- `total_clips` (integer): Total number of clips successfully generated.
- `requested_clips` (integer): Number of clips originally requested.
- `clip_duration` (integer): Duration setting used for clip generation.
- `segment_method` (string): Segmentation method used.
- `video_format` (string): Output video format applied.
- `message` (string): Success confirmation message.

Each clip object contains:
- `clip_url` (string): The cloud URL of the generated clip file.
- `clip_index` (integer): The index of this clip (1-based).
- `start_time` (number): Start time in the original video (seconds).
- `end_time` (number): End time in the original video (seconds).
- `duration` (number): Actual duration of the clip (seconds).
- `score` (number): AI-generated engagement score (0.0-1.0).
- `reason` (string): Description of why this segment was selected.

Example:

```json
{
    "clips": [
        {
            "clip_url": "https://cloud.example.com/clip-1.mp4",
            "clip_index": 1,
            "start_time": 45.2,
            "end_time": 105.2,
            "duration": 60.0,
            "score": 0.85,
            "reason": "High audio energy and engaging keywords"
        },
        {
            "clip_url": "https://cloud.example.com/clip-2.mp4",
            "clip_index": 2,
            "start_time": 180.5,
            "end_time": 240.5,
            "duration": 60.0,
            "score": 0.78,
            "reason": "Scene change detected with keyword matches"
        },
        {
            "clip_url": "https://cloud.example.com/clip-3.mp4",
            "clip_index": 3,
            "start_time": 320.0,
            "end_time": 380.0,
            "duration": 60.0,
            "score": 0.72,
            "reason": "High motion content with audio variation"
        }
    ],
    "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "total_clips": 3,
    "requested_clips": 3,
    "clip_duration": 60,
    "segment_method": "highlights",
    "video_format": "portrait",
    "message": "Successfully generated 3 clips"
}
```

### Partial Success Response

When some clips fail to generate:

```json
{
    "clips": [
        {
            "clip_url": "https://cloud.example.com/clip-1.mp4",
            "clip_index": 1,
            "start_time": 45.2,
            "end_time": 105.2,
            "duration": 60.0,
            "score": 0.85,
            "reason": "High audio energy and engaging keywords"
        }
    ],
    "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "total_clips": 1,
    "requested_clips": 3,
    "clip_duration": 60,
    "segment_method": "highlights",
    "video_format": "portrait",
    "message": "Successfully generated 1 clips"
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

#### Video Processing Failure

**Status Code:** 500 Internal Server Error

```json
{
    "error": "Video segmentation failed: Unable to analyze video content"
}
```

#### No Clips Generated

**Status Code:** 500 Internal Server Error

```json
{
    "error": "No clips were successfully generated"
}
```

## 7. Environment Variables

### Required Variables
- `API_KEY`: Main API authentication key

### Optional Variables (with defaults)
- `LOCAL_STORAGE_PATH`: Path for temporary file storage (default: `/app/data/tmp`)

### Example Configuration
```bash
# Required
API_KEY=your_api_key_here

# Optional (with defaults shown)
LOCAL_STORAGE_PATH=/app/data/tmp
```

## 8. Usage Notes

- The `video_url` must be a valid and accessible URL pointing to a video file.
- Longer source videos provide more opportunities for intelligent segmentation.
- The `highlights` method requires sufficient audio/visual content for analysis.
- Custom resolution settings will override format defaults if specified.
- Clips are generated independently and uploaded to cloud storage.
- Processing time increases with the number of clips requested.
- Some clips may fail while others succeed - check `total_clips` vs `requested_clips`.

## 9. Common Issues

- Invalid `video_url` causing download failures.
- Source video too short for requested number of clips.
- Insufficient content variation for highlights method (automatically falls back to equal_parts).
- Custom resolution settings outside supported range (480-4096 pixels).
- Network issues during video download or upload.
- FFmpeg processing errors with corrupted or unsupported video files.

## 10. Best Practices

- Use `highlights` method for content with varied audio and visual elements.
- Use `equal_parts` for consistent results with unknown content types.
- Choose appropriate `video_format` based on target platform:
  - **TikTok/Instagram Reels**: Use "portrait"
  - **YouTube/Vimeo**: Use "landscape"
  - **Instagram Posts**: Use "square"
  - **Professional Use**: Use "original"
- Start with smaller `num_clips` for testing, then scale up.
- Monitor `score` values to understand content quality.
- Use webhooks for asynchronous processing of multiple clips.
- Validate source video quality and duration before processing.
- Consider target platform requirements when setting `clip_duration`.

## 11. Performance Considerations

- Processing time scales with number of clips and video duration.
- Intelligent segmentation (`highlights`) takes longer but provides better results.
- Custom resolution processing adds overhead but improves platform compatibility.
- Cloud storage integration ensures scalable distribution of generated clips.
- Parallel processing within the endpoint optimizes overall performance.
- Transcription generation may add initial processing time but improves segment quality.

## 12. Integration Examples

### Batch Processing Workflow
```python
import requests
import time

def generate_clips_batch(video_urls):
    results = []
    for url in video_urls:
        response = requests.post(
            'https://api.example.com/v1/video/generate-clips',
            headers={'x-api-key': 'your_api_key'},
            json={
                'video_url': url,
                'num_clips': 3,
                'segment_method': 'highlights',
                'video_format': 'portrait'
            }
        )
        results.append(response.json())
        time.sleep(1)  # Rate limiting
    return results
```

### Quality-Based Filtering
```python
def filter_high_quality_clips(clips_response):
    clips = clips_response.get('clips', [])
    high_quality_clips = [
        clip for clip in clips 
        if clip['score'] >= 0.7
    ]
    return high_quality_clips
```