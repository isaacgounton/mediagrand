# Simone Integration: Video to Blog Post

This endpoint allows you to convert a YouTube video into a blog post with context-aware screenshots using the integrated Simone functionality.

## Endpoint

`POST /v1/simone/process_video`

## Request Body

| Parameter     | Type   | Description                                   | Required |
| :------------ | :----- | :-------------------------------------------- | :------- |
| `video_url`   | `string` | The URL of the YouTube video to process.      | Yes      |

## Response

The response will be a JSON object containing the generated blog post content and the paths to the saved screenshots.

```json
{
  "blog_post": "...",
  "screenshots": [
    "/path/to/screenshot_0.png",
    "/path/to/screenshot_1.png",
    "...etc"
  ]
}
```

## Example Usage

```bash
curl -X POST \
  http://localhost:8080/v1/simone/process_video \
  -H 'Content-Type: application/json' \
  -d '{
    "video_url": "YOUR_YOUTUBE_VIDEO_URL_HERE"
  }'
```

## Environment Variables

The `GEMMA_API_KEY` environment variable must be set for this endpoint to function correctly. This key is used to access the OpenRouter.ai API for generating keywords and blog post content.

```
GEMMA_API_KEY=your_gemma_api_key_here
```

## Dependencies

This functionality relies on the following external dependencies installed on the system:

*   **FFmpeg**: For video processing and screenshot extraction.
*   **Tesseract OCR Engine**: For text recognition in screenshots.
