# Text Overlay on Video Endpoint (v1)

## 1. Overview

The `/v1/text/add-text-overlay` endpoint is responsible for adding dynamic text overlays to videos. It supports various customization options for text appearance and positioning, as well as a system of predefined presets for common overlay styles. The processing is handled locally by executing FFmpeg commands directly, ensuring efficient and flexible video manipulation.

## 2. Endpoints

### Add Text Overlay
**URL:** `/v1/text/add-text-overlay`
**Method:** `POST`

### Get Available Presets
**URL:** `/v1/text/presets`
**Method:** `GET`

### Add Text Overlay Using Preset
**URL:** `/v1/text/add-text-overlay/preset/<preset_name>`
**Method:** `POST`

## 3. Request

### Headers

- `Content-Type`: `application/json`

### Body Parameters (`/v1/text/add-text-overlay` and `/v1/text/add-text-overlay/preset/<preset_name>`)

The request body must be a JSON object with the following properties:

- `video_url` (string, required): The URL of the source video to which the text overlay will be added.
- `text` (string, required): The text content to be overlaid on the video.
- `webhook_url` (string, required): A URL to receive a webhook notification when the text overlay process is complete.
- `options` (object, optional): An object containing various styling and positioning options for the text overlay. These options can be overridden when using a preset.
  - `duration` (integer, optional): How long the text overlay should be visible in seconds. Default: `3`.
  - `font_size` (integer, optional): The size of the font. Default: `60`.
  - `font_color` (string, optional): The color of the font (e.g., "black", "white", "red"). Default: `black`.
  - `box_color` (string, optional): The color of the background box behind the text. Default: `white`.
  - `box_opacity` (number, optional): The opacity of the background box (0.0-1.0). Default: `0.85`.
  - `position` (string, optional): The position of the text overlay on the video. Options: `top-left`, `top-center`, `top-right`, `center-left`, `center`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right`. Default: `top-center`.
  - `y_offset` (integer, optional): Vertical offset from the chosen position in pixels. Default: `100`.
  - `auto_wrap` (boolean, optional): Whether to automatically wrap long text. Default: `true`.

## 4. Response

### Success Response

#### For `/v1/text/add-text-overlay` and `/v1/text/add-text-overlay/preset/<preset_name>`

**Status Code:** 200 OK

```json
{
    "success": true,
    "message": "Video overlay processing started",
    "request_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "webhook_url": "https://your-webhook.com/callback",
    "ffmpeg_api_response": {
        "output_file_path": "/app/data/tmp/output_file.mp4",
        "message": "FFmpeg process completed successfully locally."
    }
}
```

#### For `/v1/text/presets`

**Status Code:** 200 OK

```json
{
    "title_overlay": {
        "description": "Large title text at the top",
        "options": {
            "duration": 5,
            "font_size": 80,
            "font_color": "white",
            "box_color": "black",
            "box_opacity": 0.7,
            "position": "top-center",
            "y_offset": 50
        }
    },
    "subtitle": {
        "description": "Subtitle text at the bottom",
        "options": {
            "duration": 10,
            "font_size": 40,
            "font_color": "white",
            "box_color": "black",
            "box_opacity": 0.8,
            "position": "bottom-center",
            "y_offset": 100
        }
    },
    "watermark": {
        "description": "Small watermark text",
        "options": {
            "duration": 999999,
            "font_size": 24,
            "font_color": "white",
            "box_color": "black",
            "box_opacity": 0.5,
            "position": "bottom-right",
            "y_offset": 30
        }
    },
    "alert": {
        "description": "Alert/notification style overlay",
        "options": {
            "duration": 3,
            "font_size": 50,
            "font_color": "red",
            "box_color": "yellow",
            "box_opacity": 0.9,
            "position": "center",
            "y_offset": 0
        }
    }
}
```

## 5. Error Handling

The endpoint handles the following common errors:

- **Missing or Invalid Parameters**: If any required parameters are missing or invalid, a 400 Bad Request error is returned with a descriptive error message.
- **Preset Not Found**: If an invalid `preset_name` is provided to the preset endpoint, a 404 Not Found error is returned.
- **FFmpeg Processing Failure**: If the underlying FFmpeg command fails, a 500 Internal Server Error is returned with details from the FFmpeg process.
- **Internal Server Error**: Any other unexpected errors will result in a 500 Internal Server Error.

## 6. Environment Variables

No specific environment variables are required for this feature beyond a working FFmpeg installation accessible in the system's PATH. The application executes FFmpeg commands directly via `subprocess.run`.

## 7. Usage Examples:

### Basic overlay:
```bash
curl -X POST http://localhost:8080/v1/text/add-text-overlay \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "text": "Hello World!",
    "webhook_url": "https://your-webhook.com/callback"
  }'
```

### Advanced overlay with custom options:
```bash
curl -X POST http://localhost:8080/v1/text/add-text-overlay \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "text": "Custom Overlay Text",
    "webhook_url": "https://your-webhook.com/callback",
    "options": {
      "duration": 5,
      "font_size": 80,
      "font_color": "white",
      "box_color": "red",
      "box_opacity": 0.8,
      "position": "center",
      "y_offset": 0,
      "auto_wrap": true
    }
  }'
```

### Using a preset:
```bash
curl -X POST http://localhost:8080/v1/text/add-text-overlay/preset/title_overlay \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "text": "Video Title",
    "webhook_url": "https://your-webhook.com/callback"
  }'
```

### Getting available presets:
```bash
curl -X GET http://localhost:8080/v1/text/presets
```

## 8. Common Issues

- **FFmpeg Not Found**: Ensure FFmpeg is installed and its executable is in the system's PATH.
- **Invalid Video URL**: The `video_url` must be a valid and accessible URL.
- **Webhook Failure**: Ensure the `webhook_url` is reachable and can receive POST requests.
- **Font File Not Found**: The default font file `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` must be present on the system. If not, FFmpeg will fail.

## 9. Best Practices

- **Test FFmpeg Installation**: Before using the API, verify that FFmpeg is correctly installed and accessible from the command line.
- **Use Webhooks**: For asynchronous processing, always provide a `webhook_url` to receive notifications upon job completion or failure.
- **Validate Inputs**: Ensure all required parameters are provided and `options` are within expected ranges.
- **Manage Fonts**: If using custom fonts, ensure they are available to the FFmpeg process.
- **Monitor Logs**: Check application logs for detailed error information if processing fails.
