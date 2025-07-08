# Media Transcription API Documentation

## Overview
The Media Transcription endpoint is part of the v1 API suite, providing enhanced audio/video transcription and translation capabilities. This endpoint leverages a queuing system for handling long-running transcription tasks, with webhook support for asynchronous processing. It's integrated into the main Flask application as a Blueprint and supports both direct response and cloud storage options for the transcription results.

### 🚀 Enhanced Features
- **Chunked Processing with Voice Activity Detection (VAD)**: Intelligently detects speech segments and skips silence for better efficiency
- **Real-time Progress Tracking**: Monitor transcription progress via dedicated API endpoints
- **Enhanced Audio Processing**: FFmpeg preprocessing with volume normalization and noise filtering
- **Robust Error Handling**: Specific error types with graceful fallbacks
- **Batch Processing**: Rate limiting to avoid API limits and improve reliability
- **Backwards Compatibility**: All existing API calls continue to work seamlessly

## Endpoints

### Main Transcription Endpoint
- **URL**: `/v1/media/transcribe`
- **Method**: `POST`
- **Blueprint**: `v1_media_transcribe_bp`

### Progress Tracking Endpoints
- **URL**: `/v1/media/transcribe/progress/<job_id>`
- **Method**: `GET`
- **Description**: Get real-time progress of a specific transcription job

- **URL**: `/v1/media/transcribe/status`
- **Method**: `GET`
- **Description**: Get status of all transcription jobs

## Request

The endpoint supports two types of requests:
1. **JSON Request**: Provide a `media_url` to transcribe media from a URL
2. **Multipart Form Request**: Upload a media file directly

### Option 1: JSON Request (URL-based)

#### Headers
- `x-api-key`: Required. Authentication key for API access.
- `Content-Type`: Required. Must be `application/json`.

#### Body Parameters

##### Required Parameters
- `media_url` (string)
  - Format: URI
  - Description: URL of the media file to be transcribed

### Option 2: Multipart Form Request (File Upload)

#### Headers
- `x-api-key`: Required. Authentication key for API access.
- `Content-Type`: Required. Must be `multipart/form-data`.

#### Form Parameters

##### Required Parameters
- `file` (file)
  - Description: Media file to be transcribed (audio or video)
  - Supported formats: MP3, MP4, WAV, M4A, and other common audio/video formats

## Common Optional Parameters

The following optional parameters are available for both JSON and multipart form requests:

- `task` (string)
  - Allowed values: `"transcribe"`, `"translate"`
  - Default: `"transcribe"`
  - Description: Specifies whether to transcribe or translate the audio
  
- `include_text` (boolean)
  - Default: `true`
  - Description: Include plain text transcription in the response
  
- `include_srt` (boolean)
  - Default: `false`
  - Description: Include SRT format subtitles in the response
  
- `include_segments` (boolean)
  - Default: `false`
  - Description: Include timestamped segments in the response
  
- `word_timestamps` (boolean)
  - Default: `false`
  - Description: Include timestamps for individual words
  
- `response_type` (string)
  - Allowed values: `"direct"`, `"cloud"`
  - Default: `"direct"`
  - Description: Whether to return results directly or as cloud storage URLs
  
- `language` (string)
  - Optional
  - Description: Source language code for transcription
  
- `webhook_url` (string)
  - Format: URI
  - Description: URL to receive the transcription results asynchronously
  
- `id` (string)
  - Description: Custom identifier for the transcription job

- `words_per_line` (integer)
  - Minimum: 1
  - Description: Controls the maximum number of words per line in the SRT file. When specified, each segment's text will be split into multiple lines with at most the specified number of words per line.

- `use_chunked` (boolean)
  - Default: `true`
  - Description: Enable enhanced chunked processing with Voice Activity Detection (VAD). When enabled, uses intelligent speech detection to process only speech segments, improving efficiency and reducing processing time for long videos with silence periods.

**Note**: For multipart form requests, boolean parameters should be sent as strings (`"true"` or `"false"`).

### Example Requests

#### JSON Request (URL-based)

```bash
curl -X POST "https://api.example.com/v1/media/transcribe" \
  -H "x-api-key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "media_url": "https://example.com/media/file.mp3",
    "task": "transcribe",
    "include_text": true,
    "include_srt": true,
    "include_segments": true,
    "response_type": "cloud",
    "webhook_url": "https://your-webhook.com/callback",
    "id": "custom-job-123",
    "words_per_line": 5,
    "use_chunked": true
  }'
```

#### Multipart Form Request (File Upload)

```bash
curl -X POST "https://api.example.com/v1/media/transcribe" \
  -H "x-api-key: your_api_key" \
  -F "file=@/path/to/your/audio.mp3" \
  -F "task=transcribe" \
  -F "include_text=true" \
  -F "include_srt=true" \
  -F "include_segments=true" \
  -F "response_type=cloud" \
  -F "webhook_url=https://your-webhook.com/callback" \
  -F "id=custom-job-123" \
  -F "words_per_line=5" \
  -F "use_chunked=true"
```

## Progress Tracking

### Get Job Progress

#### Request
```bash
curl -X GET "https://api.example.com/v1/media/transcribe/progress/{job_id}" \
  -H "x-api-key: your_api_key"
```

#### Response
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "progress": {
    "stage": "processing_segment",
    "message": "Processing segment 3/15",
    "current_segment": 3,
    "total_segments": 15,
    "percent": 20
  },
  "timestamp": 1642680000.123,
  "started_at": 1642679950.456,
  "completed_at": null,
  "error": null
}
```

### Get All Jobs Status

#### Request
```bash
curl -X GET "https://api.example.com/v1/media/transcribe/status" \
  -H "x-api-key: your_api_key"
```

#### Response
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "progress": {
        "stage": "complete",
        "message": "Transcription completed successfully",
        "percent": 100
      },
      "timestamp": 1642680000.123,
      "started_at": 1642679950.456,
      "completed_at": 1642680055.789
    }
  ],
  "total_jobs": 1
}
```

## Response

### Immediate Response (202 Accepted)
When a webhook URL is provided, the API returns an immediate acknowledgment:

```json
{
  "code": 202,
  "id": "custom-job-123",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "processing",
  "pid": 12345,
  "queue_id": 67890,
  "max_queue_length": "unlimited",
  "queue_length": 1,
  "build_number": "1.0.0"
}
```

### Success Response (via Webhook)
For direct response_type:

```json
{
  "endpoint": "/v1/transcribe/media",
  "code": 200,
  "id": "custom-job-123",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": {
    "text": "Transcribed text content...",
    "srt": "SRT formatted content...",
    "segments": [...],
    "text_url": null,
    "srt_url": null,
    "segments_url": null
  },
  "message": "success",
  "pid": 12345,
  "queue_id": 67890,
  "run_time": 5.234,
  "queue_time": 0.123,
  "total_time": 5.357,
  "queue_length": 0,
  "build_number": "1.0.0"
}
```

For cloud response_type:

```json
{
  "endpoint": "/v1/transcribe/media",
  "code": 200,
  "id": "custom-job-123",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": {
    "text": null,
    "srt": null,
    "segments": null,
    "text_url": "https://storage.example.com/text.txt",
    "srt_url": "https://storage.example.com/subtitles.srt",
    "segments_url": "https://storage.example.com/segments.json"
  },
  "message": "success",
  "pid": 12345,
  "queue_id": 67890,
  "run_time": 5.234,
  "queue_time": 0.123,
  "total_time": 5.357,
  "queue_length": 0,
  "build_number": "1.0.0"
}
```

### Error Responses

#### Queue Full (429 Too Many Requests)
```json
{
  "code": 429,
  "id": "custom-job-123",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "MAX_QUEUE_LENGTH (100) reached",
  "pid": 12345,
  "queue_id": 67890,
  "queue_length": 100,
  "build_number": "1.0.0"
}
```

#### Server Error (500 Internal Server Error)
```json
{
  "endpoint": "/v1/transcribe/media",
  "code": 500,
  "id": "custom-job-123",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": null,
  "message": "Error message details",
  "pid": 12345,
  "queue_id": 67890,
  "run_time": 0.123,
  "queue_time": 0.056,
  "total_time": 0.179,
  "queue_length": 1,
  "build_number": "1.0.0"
}
```

## Error Handling

### Enhanced Error Types
The enhanced transcription service provides specific error types for better debugging:

- **TranscriptionError**: General transcription failures
- **AudioProcessingError**: Issues with audio preprocessing or FFmpeg
- **SpeechDetectionError**: Problems with Voice Activity Detection
- **ModelLoadError**: Whisper model loading failures
- **SegmentExtractionError**: Audio segment extraction issues

### Common Errors
- **Invalid API Key**: 401 Unauthorized
- **Invalid JSON Payload**: 400 Bad Request
- **Missing Required Fields**: 400 Bad Request
- **Invalid media_url**: 400 Bad Request
- **Queue Full**: 429 Too Many Requests
- **Processing Error**: 500 Internal Server Error
- **FFmpeg Not Available**: 500 Internal Server Error (when FFmpeg is not installed)
- **Speech Detection Failed**: 500 Internal Server Error (when no speech segments are detected)

### Validation Errors
The endpoint performs strict validation of the request payload using JSON Schema. Common validation errors include:
- Invalid URI format for media_url or webhook_url
- Invalid task value (must be "transcribe" or "translate")
- Invalid response_type value (must be "direct" or "cloud")
- Invalid use_chunked value (must be boolean)
- Unknown properties in the request body
- Invalid words_per_line value (must be positive integer)

## Usage Notes

1. **Enhanced Processing**
   - **Chunked Processing**: When `use_chunked` is enabled (default), the system uses Voice Activity Detection to identify speech segments
   - **Automatic Fallback**: If chunked processing fails, the system automatically falls back to standard processing
   - **Progress Tracking**: Use the progress endpoints to monitor long-running transcription jobs
   - **Audio Enhancement**: FFmpeg preprocessing improves audio quality before transcription

2. **Webhook Processing**
   - When a webhook_url is provided, the request is processed asynchronously
   - The API returns an immediate 202 response with a job_id
   - Final results are sent to the webhook_url when processing completes
   - Progress updates are available via the progress tracking endpoints

3. **Queue Management**
   - Requests with webhook_url are queued for processing
   - MAX_QUEUE_LENGTH environment variable controls queue size
   - Set MAX_QUEUE_LENGTH to 0 for unlimited queue size
   - Batch processing prevents API rate limit issues

4. **File Management**
   - For cloud response_type, temporary files are automatically cleaned up
   - Results are uploaded to cloud storage before deletion
   - URLs in the response provide access to the stored files
   - Enhanced cleanup ensures no temporary files are left behind

5. **SRT Formatting**
   - The `words_per_line` parameter allows control over the maximum number of words per line in the SRT file
   - When specified, each segment's text will be split into multiple lines with at most the specified number of words per line
   - This is useful for creating more readable subtitles with consistent line lengths

## Common Issues

1. **Media Access**
   - Ensure media_url is publicly accessible
   - Verify media file format is supported
   - Check for media file corruption
   - For chunked processing, ensure the audio contains detectable speech

2. **Enhanced Processing Issues**
   - **FFmpeg Not Available**: Ensure FFmpeg is installed and in system PATH
   - **No Speech Detected**: The system will automatically fall back to standard processing
   - **Audio Quality**: Poor audio quality may affect Voice Activity Detection accuracy
   - **Long Videos**: Use progress tracking endpoints to monitor processing of long videos

3. **Webhook Delivery**
   - Ensure webhook_url is publicly accessible
   - Implement webhook endpoint retry logic
   - Monitor webhook endpoint availability
   - Check progress endpoints if webhook delivery fails

4. **Resource Usage**
   - Large media files may take significant processing time
   - Monitor queue length for production deployments
   - Consider implementing request size limits
   - Chunked processing reduces memory usage for long videos

## Best Practices

1. **Enhanced Processing**
   - **Enable Chunked Processing**: Use `use_chunked: true` for better performance on long videos
   - **Monitor Progress**: Use progress tracking endpoints for long-running jobs
   - **Audio Quality**: Ensure good audio quality for optimal Voice Activity Detection
   - **Language Specification**: Specify the `language` parameter for better accuracy on non-English content

2. **Request Handling**
   - Always provide a unique id for job tracking
   - Implement webhook retry logic
   - Store job_id for result correlation
   - Use progress endpoints to check job status

3. **Resource Management**
   - Monitor queue length in production
   - Implement appropriate timeout handling
   - Use cloud response_type for large files
   - Leverage chunked processing for memory efficiency

4. **Error Handling**
   - Implement comprehensive webhook error handling
   - Log job_id with all related operations
   - Monitor processing times and error rates
   - Handle specific error types (TranscriptionError, AudioProcessingError, etc.)
   - Implement fallback logic for when enhanced processing fails

5. **Security**
   - Use HTTPS for media_url and webhook_url
   - Implement webhook authentication
   - Validate media file types before processing
   - Ensure FFmpeg is properly secured in production environments

## Performance Optimization

1. **Chunked Processing Benefits**
   - Reduces processing time by skipping silence
   - Better memory management for long videos
   - Improved accuracy through segment-based processing
   - Automatic rate limiting prevents API throttling

2. **Monitoring and Debugging**
   - Use progress endpoints to track processing stages
   - Monitor error types for system health
   - Track processing times for performance optimization
   - Set up alerts for specific error patterns

3. **Scaling Considerations**
   - Enhanced processing is more resource-efficient
   - Progress tracking reduces client polling overhead
   - Batch processing improves overall system throughput
   - Graceful fallbacks ensure high availability