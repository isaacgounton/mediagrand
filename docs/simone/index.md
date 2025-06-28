# Simone Integration: Video to Blog Post

This endpoint allows you to convert a YouTube video into a blog post with context-aware screenshots using the integrated Simone functionality.

## Endpoint

`POST /v1/simone/process_video`

## Request Body

| Parameter     | Type   | Description                                   | Required |
| :------------ | :----- | :-------------------------------------------- | :------- |
| `video_url`   | `string` | The URL of the YouTube video to process.      | Yes      |
| `platform`    | `string` | Optional. The social media platform for which to generate content. Supported: `linkedin`, `facebook`, `instagram`, `x`. | No      |

## Response

The response will be a JSON object containing the generated blog post content and the paths to the saved screenshots.

```json
{
  "blog_post_content": "...",
  "blog_post_url": "...",
  "screenshots": [
    "/path/to/screenshot_0.png",
    "/path/to/screenshot_1.png",
    "...etc"
  ],
  "social_media_post_content": "..."
}
```

## Social Media Content Generation

In addition to the blog post, you can generate content tailored for various social media platforms by providing the `platform` parameter in the request.

Supported platforms include:
*   `linkedin`: Generates a professional post suitable for LinkedIn.
*   `facebook`: Generates a conversational and engaging post for Facebook.
*   `instagram`: Generates a concise and visually appealing caption for Instagram.
*   `x`: Generates a concise and impactful tweet (X post).

If no `platform` is specified, only the blog post and screenshots will be generated.

## Example Usage

```bash
curl -X POST \
  http://localhost:8080/v1/simone/process_video \
  -H 'Content-Type: application/json' \
  -d '{
    "video_url": "YOUR_YOUTUBE_VIDEO_URL_HERE",
    "platform": "linkedin"
  }'
```

## Environment Variables

The `OPENAI_API_KEY` environment variable must be set for this endpoint to function correctly. This key is used to access the OpenAI-compatible API (like OpenRouter.ai) for generating keywords and blog post content.

```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=google/gemma-3-12b-it:free
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

## Dependencies

This functionality relies on the following external dependencies installed on the system:

*   **FFmpeg**: For video processing and screenshot extraction.
*   **Tesseract OCR Engine**: For text recognition in screenshots.
