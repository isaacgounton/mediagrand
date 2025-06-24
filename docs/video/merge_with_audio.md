# Video Merge with Audio Endpoint

## 1. Overview

The `/v1/video/merge_with_audio` endpoint merges multiple video files into a single video, overlays a speech audio track, and repeats the last video segment until the audio ends. The merged video will always match or slightly exceed the audio duration.

## 2. Endpoint

**URL Path:** `/v1/video/merge_with_audio`  
**HTTP Method:** `POST`

## 3. Request

### Headers

- `x-api-key` (required): The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `video_urls` (required, array of strings): An array of video URLs to be merged. Each element must be a valid URI string.
- `audio_url` (required, string, URI format): The URL of the speech audio file to overlay on the merged video.
- `webhook_url` (optional, string, URI format): The URL to which the response should be sent as a webhook.
- `id` (optional, string): An identifier for the request.

#### Example Request

```json
{
    "video_urls": [
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4"
    ],
    "audio_url": "https://example.com/speech.mp3",
    "webhook_url": "https://example.com/webhook",
    "id": "merge-audio-request-001"
}
```

## 4. Behavior

- The endpoint merges all provided videos in order.
- If the combined video duration is shorter than the audio duration, the last video segment is repeated as many times as needed, and trimmed to match the audio length (with a small buffer).
- The output video ends only after the audio finishes.
- The speech audio is used as the main audio track.

## 5. Response

### Success Response

```json
{
    "endpoint": "/v1/video/merge_with_audio",
    "code": 200,
    "id": "merge-audio-request-001",
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
- **401 Unauthorized**: Returned when the `x-api-key` header is missing or invalid.
- **429 Too Many Requests**: Returned when the maximum queue length is reached.
- **500 Internal Server Error**: Returned when an unexpected error occurs during the video merge process.

## 6. Usage Notes

- The video files and audio file must be accessible via the provided URLs.
- The order of the video files in the `video_urls` array determines the order in which they will be merged.
- The merged video will always match or slightly exceed the audio duration.
- The endpoint is asynchronous; use the `job_id` to track status or provide a `webhook_url` for notification.