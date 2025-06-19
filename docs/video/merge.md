# Video Merge Endpoint

## 1. Overview

The `/v1/video/merge` endpoint is a part of the Video API and is responsible for merging multiple video files into a single video file, optionally adding a background audio track. This endpoint fits into the overall API structure as a part of the version 1 (v1) routes, specifically under the `/v1/video` namespace.

## 2. Endpoint

**URL Path:** `/v1/video/merge`
**HTTP Method:** `POST`

## 3. Request

### Headers

- `x-api-key` (required): The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `video_urls` (required, array of strings): An array of video URLs to be merged. Each element must be a valid URI string.
- `background_music_url` (optional, string, URI format): The URL of the background music file to be mixed with the merged video.
- `background_music_volume` (optional, number): Volume level for background music between 0.0 and 1.0 (default: 0.5).
- `webhook_url` (optional, string, URI format): The URL to which the response should be sent as a webhook.
- `id` (optional, string): An identifier for the request.

The `validate_payload` decorator in the routes file enforces the following JSON schema for the request body:

```json
{
    "type": "object",
    "properties": {
        "video_urls": {
            "type": "array",
            "items": {
                "type": "string",
                "format": "uri"
            },
            "minItems": 1,
            "description": "List of video URLs to merge"
        },
        "background_music_url": {
            "type": "string", 
            "format": "uri",
            "description": "Optional background music URL"
        },
        "background_music_volume": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "default": 0.5,
            "description": "Volume for background music (0.0 to 1.0)"
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_urls"],
    "additionalProperties": false
}
```

### Example Request

```json
{
    "video_urls": [
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4",
        "https://example.com/video3.mp4"
    ],
    "background_music_url": "https://example.com/background.mp3",
    "background_music_volume": 0.3,
    "webhook_url": "https://example.com/webhook",
    "id": "merge-request-123"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
        "video_urls": [
            "https://example.com/video1.mp4",
            "https://example.com/video2.mp4",
            "https://example.com/video3.mp4"
        ],
        "background_music_url": "https://example.com/background.mp3",
        "background_music_volume": 0.3,
        "webhook_url": "https://example.com/webhook",
        "id": "merge-request-123"
     }' \
     https://your-api-endpoint.com/v1/video/merge
```

## 4. Response

### Success Response

The success response follows the general response format defined in the `app.py` file. Here's an example:

```json
{
    "endpoint": "/v1/video/merge",
    "code": 200,
    "id": "merge-request-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "response": "https://cloud-storage.example.com/merged-video.mp4",
    "message": "success",
    "pid": 12345,
    "run_time": 15.234,
    "queue_time": 2.345,
    "total_time": 17.579,
    "queue_length": 0,
    "build_number": "1.0.0"
}
```

The `response` field contains the URL of the merged video file uploaded to cloud storage.

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
    "id": "merge-request-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "message": "MAX_QUEUE_LENGTH (100) reached",
    "pid": 12345,
    "queue_length": 100,
    "build_number": "1.0.0"
  }
  ```

- **500 Internal Server Error**: Returned when an unexpected error occurs during the video merge process.

  ```json
  {
    "code": 500,
    "message": "An error occurred during video merge"
  }
  ```

## 5. Error Handling

The endpoint handles the following common errors:

- **Missing or invalid request body**: If the request body is missing or does not conform to the expected JSON schema, a 400 Bad Request error is returned.
- **Missing or invalid API key**: If the `x-api-key` header is missing or invalid, a 401 Unauthorized error is returned.
- **Queue length exceeded**: If the maximum queue length is reached (determined by the `MAX_QUEUE_LENGTH` environment variable), a 429 Too Many Requests error is returned.
- **Unexpected errors during video merge**: If an unexpected error occurs during the video merge process, a 500 Internal Server Error is returned with the error message.

The main application context (`app.py`) also includes error handling for the task queue. If the queue length exceeds the `MAX_QUEUE_LENGTH` limit, the request is rejected with a 429 Too Many Requests error.

## 6. Usage Notes

- The video files to be merged must be accessible via the provided URLs.
- The order of the video files in the `video_urls` array determines the order in which they will be merged.
- All videos are normalized to match the dimensions and frame rate of the first video in the list.
- Background music is mixed with the original audio tracks at the specified volume level.
- If the `webhook_url` parameter is provided, the response will be sent as a webhook to the specified URL.
- The `id` parameter can be used to identify the request in the response.
- Processing time depends on the number and size of videos being merged.

## 7. Common Issues

- Providing invalid or inaccessible video URLs.
- Videos with incompatible formats that require significant re-encoding.
- Background music files that are too short or too long compared to the merged video duration.
- Exceeding the maximum queue length, which can lead to requests being rejected with a 429 Too Many Requests error.
- Encountering unexpected errors during the video merge process, which can result in a 500 Internal Server Error.

## 8. Best Practices

- Validate the video and audio URLs before sending the request to ensure they are accessible and in supported formats.
- Use videos with similar dimensions and frame rates to minimize processing time.
- Test background music volume levels to ensure optimal audio mixing.
- Monitor the queue length and adjust the `MAX_QUEUE_LENGTH` value accordingly to prevent requests from being rejected due to a full queue.
- Implement retry mechanisms for handling temporary errors or failures during the video merge process.
- Provide meaningful and descriptive `id` values to easily identify requests in the response.
- Consider the total file size of videos being merged as larger files require more processing time and storage.