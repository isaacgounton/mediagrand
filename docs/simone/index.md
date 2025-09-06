# Simone Video Processing

The Simone service converts videos into various content formats including transcriptions, blog posts, topics, and social media threads using AI-powered processing.

## Authentication

Authentication token required in the request header:
```
x-api-key: your-api-key-here
```

## Endpoints

### 1. Video Processing
```
POST /v1/simone/process_video
```

### 2. Topic Generation
```
POST /v1/simone/generate_topics
```

### 3. X/Twitter Thread Generation
```
POST /v1/simone/generate_x_thread
```

### 4. Topic Generation (Direct)
```
POST /v1/generate_topics
```

---

## Video Processing

The main endpoint for processing videos into various content formats.

### Request Body (JSON)

```json
{
    "video_url": "https://youtube.com/watch?v=example",
    "platform": "youtube",
    "include_transcription": true,
    "include_blog": true,
    "include_topics": true,
    "include_x_thread": false,
    "platforms": ["x", "linkedin", "instagram"],
    "thread_config": {
        "max_posts": 8,
        "character_limit": 280,
        "thread_style": "viral"
    },
    "topic_config": {
        "min_topics": 3,
        "max_topics": 8
    },
    "cookies_content": "sessionid=abc123; csrftoken=def456",
    "cookies_url": "https://example.com/cookies.txt"
}
```

### Parameters

- `video_url` (required): URL of the video to process
- `platform` (optional): Platform type (e.g., "youtube", "vimeo")
- `include_transcription` (optional): Generate transcription. Defaults to `true`
- `include_blog` (optional): Generate blog post. Defaults to `true`
- `include_topics` (optional): Generate topics. Defaults to `true`
- `include_x_thread` (optional): Generate X/Twitter thread. Defaults to `false`
- `platforms` (optional): Social media platforms for content generation. Defaults to `["x", "linkedin", "instagram"]`
- `thread_config` (optional): Thread generation configuration
  - `max_posts` (2-15): Maximum posts in thread. Defaults to `8`
  - `character_limit` (100-500): Character limit per post. Defaults to `280`
  - `thread_style` ("viral", "educational", "storytelling", "professional", "conversational"): Thread style. Defaults to `"viral"`
- `topic_config` (optional): Topic generation configuration
  - `min_topics` (1-5): Minimum topics to generate. Defaults to `3`
  - `max_topics` (3-15): Maximum topics to generate. Defaults to `8`
- `cookies_content` (optional): Raw cookie content for authentication
- `cookies_url` (optional): URL to download cookies from

### Response

#### Success Response

```json
{
    "code": 200,
    "job_id": "unique-job-id",
    "response": {
        "transcription_content": "Video transcription text...",
        "transcription_url": "/public/simone_outputs/uuid/transcription.txt",
        "blog_post_content": "Generated blog post content...",
        "blog_post_url": "/public/simone_outputs/uuid/generated_blogpost.txt",
        "screenshots": [
            "/public/simone_outputs/uuid/screenshot_0.png",
            "/public/simone_outputs/uuid/screenshot_1.png"
        ],
        "viral_content_package": {
            "topics": [
                {
                    "topic": "AI Revolution in Content Creation",
                    "description": "How AI is transforming content creation workflows",
                    "confidence": 0.92,
                    "viral_potential": 0.85,
                    "category": "educational",
                    "hashtags": ["#AI", "#ContentCreation", "#Productivity"]
                }
            ],
            "x_thread": [
                {
                    "post_number": 1,
                    "content": "1/8 🧵 The AI content revolution is here...",
                    "character_count": 95
                }
            ],
            "social_posts": {
                "linkedin": "Professional LinkedIn post content...",
                "instagram": "Instagram caption with hashtags..."
            }
        }
    },
    "message": "success"
}
```

#### For Queued Jobs

```json
{
    "code": 202,
    "job_id": "unique-job-id",
    "message": "processing"
}
```

#### Error Response

```json
{
    "code": 400,
    "message": "Error message here"
}
```

---

## Topic Generation

Generate viral topics from transcription text or file. This endpoint is available at both `/v1/simone/generate_topics` and `/v1/generate_topics` (direct access).

### Request Body (JSON)

```json
{
    "transcription_text": "Your video transcription text here...",
    "transcription_file_url": "https://example.com/transcription.txt",
    "min_topics": 3,
    "max_topics": 8,
    "include_timestamps": true,
    "cookies_content": "auth_token=xyz789; session=abc123"
}
```

### Parameters

- `transcription_text` (required*): Raw transcription text
- `transcription_file_url` (required*): URL to transcription file
- `min_topics` (optional): Minimum topics to generate (1-5). Defaults to `3`
- `max_topics` (optional): Maximum topics to generate (3-15). Defaults to `8`
- `include_timestamps` (optional): Include timestamp mapping. Defaults to `false`
- `cookies_content` (optional): Raw cookie content for downloading transcription files

*Either `transcription_text` or `transcription_file_url` is required.

### Response

```json
{
    "code": 200,
    "job_id": "unique-job-id",
    "response": {
        "topics": [
            {
                "topic": "AI Revolution in Content Creation",
                "description": "How AI is transforming content creation workflows",
                "confidence": 0.92,
                "viral_potential": 0.85,
                "category": "educational",
                "hashtags": ["#AI", "#ContentCreation", "#Productivity"]
            }
        ],
        "parameters": {
            "min_topics": 3,
            "max_topics": 8,
            "include_timestamps": true
        }
    },
    "message": "success"
}
```

---

## X/Twitter Thread Generation

Generate X/Twitter threads from transcription text or file.

### Request Body (JSON)

```json
{
    "transcription_text": "Your video transcription text here...",
    "transcription_file_url": "https://example.com/transcription.txt",
    "max_posts": 8,
    "character_limit": 280,
    "thread_style": "viral",
    "topic_focus": "AI and productivity",
    "include_timestamps": false,
    "cookies_content": "auth_token=xyz789; session=abc123"
}
```

### Parameters

- `transcription_text` (required*): Raw transcription text
- `transcription_file_url` (required*): URL to transcription file
- `max_posts` (optional): Maximum posts in thread (2-15). Defaults to `8`
- `character_limit` (optional): Character limit per post (100-500). Defaults to `280`
- `thread_style` (optional): Thread style ("viral", "educational", "storytelling", "professional", "conversational"). Defaults to `"viral"`
- `topic_focus` (optional): Specific topic to focus on
- `include_timestamps` (optional): Include timestamp mapping. Defaults to `false`
- `cookies_content` (optional): Raw cookie content for downloading transcription files

*Either `transcription_text` or `transcription_file_url` is required.

### Response

```json
{
    "code": 200,
    "job_id": "unique-job-id",
    "response": {
        "thread": [
            {
                "post_number": 1,
                "content": "1/8 🧵 The AI content revolution is here...",
                "character_count": 95,
                "start_time": "00:01:30",
                "end_time": "00:02:15"
            }
        ],
        "parameters": {
            "max_posts": 8,
            "character_limit": 280,
            "thread_style": "viral",
            "topic_focus": "AI and productivity",
            "include_timestamps": false
        }
    },
    "message": "success"
}
```

---

## Examples

### Basic Video Processing

```bash
curl -X POST https://api.example.com/v1/simone/process_video \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://youtube.com/watch?v=example"
  }'
```

### Video Processing with X Thread

```bash
curl -X POST https://api.example.com/v1/simone/process_video \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://youtube.com/watch?v=example",
    "include_x_thread": true,
    "thread_config": {
      "max_posts": 10,
      "thread_style": "educational"
    }
  }'
```

### Video Processing with Cookies

```bash
curl -X POST https://api.example.com/v1/simone/process_video \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://youtube.com/watch?v=example",
    "cookies_content": "sessionid=abc123; csrftoken=def456"
  }'
```

### Topic Generation

```bash
curl -X POST https://api.example.com/v1/simone/generate_topics \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "transcription_text": "Your video transcription text here...",
    "min_topics": 5,
    "max_topics": 10,
    "include_timestamps": true
  }'
```

### X Thread Generation

```bash
curl -X POST https://api.example.com/v1/simone/generate_x_thread \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "transcription_file_url": "https://example.com/transcription.txt",
    "max_posts": 12,
    "thread_style": "storytelling",
    "cookies_content": "auth_token=xyz789"
  }'
```

## Environment Variables

### Required
```bash
API_KEY=your_mediagrand_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Optional
```bash
OPENAI_MODEL=google/gemma-3-12b-it:free
OPENAI_BASE_URL=https://openrouter.ai/api/v1
TESSERACT_CMD_PATH=/usr/bin/tesseract
```

### Storage Configuration
```bash
SIMONE_UPLOAD_TO_S3=true
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket_name
S3_REGION=us-east-1
```