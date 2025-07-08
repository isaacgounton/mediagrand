# Simone Integration: Video Processing Service

Simone is a comprehensive video processing service that converts videos into multiple content formats including blog posts, social media content, transcriptions, and viral content packages. It offers two processing modes to meet different content creation needs.

## Overview

Simone processes videos through an AI-powered pipeline that:
- Downloads and transcribes video content
- Generates blog posts and social media content
- Extracts context-aware screenshots using OCR
- Identifies viral topics and creates engagement-optimized content
- Provides time-stamped content mapping

## Available Endpoints

### 1. Standard Processing
`POST /v1/simone/process_video`

### 2. Enhanced Processing (Recommended)
`POST /v1/simone/process_video_enhanced`

### 3. Topic Generation
`POST /v1/simone/generate_topics`

### 4. X/Twitter Thread Generation
`POST /v1/simone/generate_x_thread`

---

## Standard Video Processing

### Endpoint
`POST /v1/simone/process_video`

### Request Body
| Parameter        | Type     | Description                                   | Required |
| :--------------- | :------- | :-------------------------------------------- | :------- |
| `video_url`      | `string` | The URL of the video to process               | Yes      |
| `platform`       | `string` | Social media platform for content generation | No       |
| `cookies_content`| `string` | Cookie content for private videos             | No       |
| `cookies_url`    | `string` | Cookie URL for authentication                 | No       |

### Response
```json
{
  "blog_post_content": "Generated blog post text...",
  "blog_post_url": "/public/simone_outputs/uuid/generated_blogpost.txt",
  "screenshots": [
    "/public/simone_outputs/uuid/screenshot_0.png",
    "/public/simone_outputs/uuid/screenshot_1.png"
  ],
  "social_media_post_content": "Platform-specific social media post...",
  "transcription_content": "Raw video transcription text...",
  "transcription_url": "/public/simone_outputs/uuid/transcription.txt"
}
```

---

## Enhanced Video Processing (Recommended)

### Endpoint
`POST /v1/simone/process_video_enhanced`

### Request Body
| Parameter        | Type      | Description                                   | Required | Default |
| :--------------- | :-------- | :-------------------------------------------- | :------- | :------ |
| `video_url`      | `string`  | The URL of the video to process               | Yes      | -       |
| `include_topics` | `boolean` | Generate viral topic identification           | No       | `true`  |
| `include_x_thread`| `boolean`| Generate X/Twitter thread                    | No       | `true`  |
| `platforms`      | `array`   | Social media platforms to generate content for| No      | `["x", "linkedin", "instagram"]` |
| `thread_config`  | `object`  | Configuration for thread generation           | No       | See below |
| `topic_config`   | `object`  | Configuration for topic identification        | No       | See below |
| `cookies_content`| `string`  | Cookie content for private videos             | No       | -       |
| `cookies_url`    | `string`  | Cookie URL for authentication                 | No       | -       |

#### Thread Configuration
```json
{
  "max_posts": 8,           // 2-15 posts
  "character_limit": 280,   // 100-500 characters
  "thread_style": "viral"   // "viral", "educational", "storytelling", "professional", "conversational"
}
```

#### Topic Configuration
```json
{
  "min_topics": 3,          // 1-5 topics
  "max_topics": 8           // 3-15 topics
}
```

### Response
```json
{
  "blog_post_content": "Generated blog post text...",
  "blog_post_url": "/public/simone_outputs/uuid/generated_blogpost.txt",
  "screenshots": [
    "/public/simone_outputs/uuid/screenshot_0.png"
  ],
  "viral_content_package": {
    "generated_at": "2024-01-01T00:00:00.000Z",
    "source": "transcription",
    "content": {
      "topics": {
        "topics": [
          {
            "topic": "AI Revolution in Content Creation",
            "description": "How AI is transforming content creation workflows",
            "confidence": 0.92,
            "viral_potential": 0.85,
            "category": "educational",
            "target_audience": "content creators",
            "hook_angle": "The secret to 10x content productivity",
            "timestamp_ranges": [{"start": "00:01:30", "end": "00:03:45"}],
            "hashtags": ["#AI", "#ContentCreation", "#Productivity"]
          }
        ],
        "summary": "Content focuses on AI-powered productivity tools"
      },
      "x_thread": {
        "thread": [
          {
            "post_number": 1,
            "content": "1/8 🧵 The AI content revolution is here, and it's changing everything about how we create...",
            "character_count": 95,
            "start_time": "00:01:30",
            "end_time": "00:02:15",
            "engagement_elements": ["hook", "emoji", "thread_indicator"]
          }
        ],
        "thread_summary": "AI revolution in content creation",
        "viral_elements": ["strong_hook", "data_points", "actionable_tips"],
        "target_metrics": {
          "expected_engagement": "high",
          "shareability_score": 0.8
        }
      },
      "posts": {
        "linkedin": "Professional LinkedIn post content...",
        "instagram": "Instagram caption with hashtags..."
      }
    }
  },
  "content_package_url": "/public/simone_outputs/uuid/viral_content_package.json",
  "transcription_content": "Raw video transcription text...",
  "transcription_url": "/public/simone_outputs/uuid/transcription.txt",
  "enhanced_features": {
    "topics_included": true,
    "x_thread_included": true,
    "platforms_processed": ["x", "linkedin", "instagram"],
    "thread_config": {
      "max_posts": 8,
      "character_limit": 280,
      "thread_style": "viral"
    }
  },
  "processing_summary": {
    "total_topics": 5,
    "thread_posts": 8,
    "platforms_generated": ["linkedin", "instagram"],
    "screenshots_count": 3
  }
}
```

---

## Topic Generation

### Endpoint
`POST /v1/simone/generate_topics`

### Request Body
| Parameter            | Type      | Description                           | Required |
| :------------------- | :-------- | :------------------------------------ | :------- |
| `transcription_text` | `string`  | Raw transcription text                | Yes*     |
| `transcription_file_url` | `string` | URL to transcription file          | Yes*     |
| `min_topics`         | `integer` | Minimum topics to generate (1-5)      | No       |
| `max_topics`         | `integer` | Maximum topics to generate (3-15)     | No       |
| `include_timestamps` | `boolean` | Include timestamp mapping             | No       |

*Either `transcription_text` or `transcription_file_url` is required.

---

## X/Twitter Thread Generation

### Endpoint
`POST /v1/simone/generate_x_thread`

### Request Body
| Parameter            | Type      | Description                           | Required |
| :------------------- | :-------- | :------------------------------------ | :------- |
| `transcription_text` | `string`  | Raw transcription text                | Yes*     |
| `transcription_file_url` | `string` | URL to transcription file          | Yes*     |
| `max_posts`          | `integer` | Maximum posts in thread (2-15)       | No       |
| `character_limit`    | `integer` | Character limit per post (100-500)   | No       |
| `thread_style`       | `string`  | Thread style (see options above)     | No       |
| `topic_focus`        | `string`  | Specific topic to focus on            | No       |
| `include_timestamps` | `boolean` | Include timestamp mapping             | No       |

*Either `transcription_text` or `transcription_file_url` is required.

---

## Supported Platforms

### Standard Social Media Platforms
- **LinkedIn**: Professional content with industry insights
- **Facebook**: Conversational and engaging posts
- **Instagram**: Concise captions with strategic hashtags
- **X (Twitter)**: Impactful posts optimized for engagement

### Enhanced Features
- **Topic Identification**: AI-powered viral topic extraction
- **Thread Generation**: Multi-post X/Twitter threads with engagement optimization
- **Time-stamped Mapping**: Content mapped back to video timestamps
- **Viral Scoring**: Confidence and viral potential scoring

---

## Example Usage

### Standard Processing
```bash
curl -X POST \
  http://localhost:8080/v1/simone/process_video \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "platform": "linkedin"
  }'
```

### Enhanced Processing
```bash
curl -X POST \
  http://localhost:8080/v1/simone/process_video_enhanced \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "include_topics": true,
    "include_x_thread": true,
    "platforms": ["x", "linkedin", "instagram"],
    "thread_config": {
      "max_posts": 10,
      "character_limit": 280,
      "thread_style": "viral"
    }
  }'
```

### Topic Generation Only
```bash
curl -X POST \
  http://localhost:8080/v1/simone/generate_topics \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -d '{
    "transcription_text": "Your video transcription text here...",
    "min_topics": 3,
    "max_topics": 8,
    "include_timestamps": true
  }'
```

---

## Environment Variables

### Required
```bash
OPENAI_API_KEY=your_openai_api_key_here
API_KEY=your_dahopevi_api_key_here
```

### Optional Configuration
```bash
OPENAI_MODEL=google/gemma-3-12b-it:free
OPENAI_BASE_URL=https://openrouter.ai/api/v1
TESSERACT_CMD_PATH=/usr/bin/tesseract
```

### Storage Configuration
```bash
# S3 Storage (Optional)
SIMONE_UPLOAD_TO_S3=true
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket_name
S3_REGION=us-east-1
```

---

## Dependencies

### System Requirements
- **FFmpeg**: Video processing and audio extraction
- **Tesseract OCR Engine**: Text recognition in screenshots
- **Python 3.8+**: Runtime environment

### Python Dependencies
- **OpenAI**: AI content generation
- **yt-dlp**: Video downloading
- **Whisper**: Audio transcription
- **Pillow**: Image processing
- **requests**: HTTP client

---

## Features

### Core Features
- ✅ Video download and processing
- ✅ AI-powered transcription
- ✅ Blog post generation
- ✅ Context-aware screenshot extraction
- ✅ Multi-platform social media content
- ✅ Raw transcription access
- ✅ S3 and local storage support

### Enhanced Features
- ✅ Viral topic identification with scoring
- ✅ X/Twitter thread generation
- ✅ Time-stamped content mapping
- ✅ Engagement optimization
- ✅ Multi-platform content packages
- ✅ Confidence scoring
- ✅ Viral potential assessment

### Quality Assurance
- ✅ Error handling and graceful fallbacks
- ✅ Authentication and authorization
- ✅ Queue-based processing
- ✅ Progress tracking
- ✅ Comprehensive logging

---

## Error Handling

Simone includes comprehensive error handling:
- Graceful fallbacks for missing files
- S3 to local storage fallback
- API error handling with detailed messages
- Timeout handling for long videos
- Memory management for large files

---

## Performance Considerations

- **Processing Time**: 2-10 minutes depending on video length
- **Memory Usage**: Scales with video length and quality
- **Storage**: Outputs stored temporarily, then moved to permanent storage
- **Rate Limits**: Respects OpenAI API rate limits
- **Concurrent Processing**: Queue-based system handles multiple requests

---

## Changelog

### Latest Updates
- ✅ Added transcription content to response
- ✅ Enhanced viral content package generation
- ✅ Improved topic identification with confidence scoring
- ✅ Added X/Twitter thread generation
- ✅ Time-stamped content mapping
- ✅ Multi-platform content optimization