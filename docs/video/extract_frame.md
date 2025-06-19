# Video Extract Frame Endpoint

## 1. Overview

The `/v1/video/extract-frame` endpoint is a part of the Video API and is responsible for extracting a single image frame from a video file at a specified time. This endpoint fits into the overall API structure as a part of the version 1 (v1) routes, specifically under the `/v1/video` namespace.

## 2. Endpoint

**URL Path:** `/v1/video/extract-frame`
**HTTP Method:** `POST`

## 3. Request

### Headers

- `x-api-key` (required): The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `video_url` (required, string, URI format): The URL of the video file from which to extract the frame.
- `seconds` (optional, number): The time in seconds at which to extract the frame (default: 0, minimum: 0).
- `webhook_url` (optional, string, URI format): The URL to which the response should be sent as a webhook.
- `id` (optional, string): An identifier for the request.

The `validate_payload` decorator in the routes file enforces the following JSON schema for the request body:

```json
{
    "type": "object",
    "properties": {
        "video_url": {
            "type": "string",
            "format": "uri",
            "description": "URL of the video to extract frame from"
        },
        "seconds": {
            "type": "number",
            "minimum": 0,
            "default": 0,
            "description": "Time in seconds to extract the frame from (default: 0)"
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url"],
    "additionalProperties": false
}
```

### Example Request

```json
{
    "video_url": "https://example.com/sample-video.mp4",
    "seconds": 30.5,
    "webhook_url": "https://example.com/webhook",
    "id": "extract-frame-123"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
        "video_url": "https://example.com/sample-video.mp4",
        "seconds": 30.5,
        "webhook_url": "https://example.com/webhook",
        "id": "extract-frame-123"
     }' \
     https://your-api-endpoint.com/v1/video/extract-frame
```

## 4. Response

### Success Response

The success response follows the general response format defined in the `app.py` file. Here's an example:

```json
{
    "endpoint": "/v1/video/extract-frame",
    "code": 200,
    "id": "extract-frame-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "response": "https://cloud-storage.example.com/extracted-frame.jpg",
    "message": "success",
    "pid": 12345,
    "run_time": 3.234,
    "queue_time": 1.345,
    "total_time": 4.579,
    "queue_length": 0,
    "build_number": "1.0.0"
}
```

The `response` field contains the URL of the extracted frame image uploaded to cloud storage.

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
    "id": "extract-frame-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "message": "MAX_QUEUE_LENGTH (100) reached",
    "pid": 12345,
    "queue_length": 100,
    "build_number": "1.0.0"
  }
  ```

- **500 Internal Server Error**: Returned when an unexpected error occurs during the frame extraction process.

  ```json
  {
    "code": 500,
    "message": "An error occurred during frame extraction"
  }
  ```

## 5. Error Handling

The endpoint handles the following common errors:

- **Missing or invalid request body**: If the request body is missing or does not conform to the expected JSON schema, a 400 Bad Request error is returned.
- **Missing or invalid API key**: If the `x-api-key` header is missing or invalid, a 401 Unauthorized error is returned.
- **Queue length exceeded**: If the maximum queue length is reached (determined by the `MAX_QUEUE_LENGTH` environment variable), a 429 Too Many Requests error is returned.
- **Unexpected errors during frame extraction**: If an unexpected error occurs during the frame extraction process, a 500 Internal Server Error is returned with the error message.

The main application context (`app.py`) also includes error handling for the task queue. If the queue length exceeds the `MAX_QUEUE_LENGTH` limit, the request is rejected with a 429 Too Many Requests error.

## 6. Usage Notes

- The video file must be accessible via the provided URL.
- The extracted frame is saved as a high-quality JPEG image.
- If the specified time (`seconds`) exceeds the video duration, the frame will be extracted from the last available frame.
- Fractional seconds are supported for precise frame extraction (e.g., 30.5 seconds).
- If the `webhook_url` parameter is provided, the response will be sent as a webhook to the specified URL.
- The `id` parameter can be used to identify the request in the response.
- Processing time is typically very fast as only a single frame needs to be extracted.

## 7. Common Issues

- Providing invalid or inaccessible video URLs.
- Specifying a negative time value (not allowed by validation).
- Video files that are corrupted or in unsupported formats.
- Exceeding the maximum queue length, which can lead to requests being rejected with a 429 Too Many Requests error.
- Encountering unexpected errors during the frame extraction process, which can result in a 500 Internal Server Error.

## 8. Best Practices

- Validate the video URL before sending the request to ensure it is accessible and in a supported format.
- Use reasonable time values that are within the duration of the video.
- Consider extracting frames from key moments in the video for thumbnail generation.
- Monitor the queue length and adjust the `MAX_QUEUE_LENGTH` value accordingly to prevent requests from being rejected due to a full queue.
- Implement retry mechanisms for handling temporary errors or failures during the frame extraction process.
- Provide meaningful and descriptive `id` values to easily identify requests in the response.
- Cache extracted frames when possible to avoid repeated processing of the same video at the same time point.

## 9. Use Cases

- **Thumbnail Generation**: Extract representative frames for video thumbnails.
- **Content Analysis**: Extract frames for visual analysis or content moderation.
- **Preview Images**: Generate preview images for video galleries or catalogs.
- **Keyframe Extraction**: Extract frames at specific timestamps for video indexing.
- **Quality Assessment**: Extract frames to check video quality at different points.