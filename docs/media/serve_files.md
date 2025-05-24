# Serve Local Files

This endpoint provides HTTP access to files stored in the local storage directory for use by services like MoviePy video rendering.

## Endpoint

**GET** `/v1/media/files/{filename}`

## Description

Serves files from the local storage directory (`LOCAL_STORAGE_PATH`) via HTTP. This endpoint is primarily used to provide secure access to media files for browser-based rendering services that cannot access local file system paths directly.

## Parameters

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filename` | string | Yes | Relative path to the file within the local storage directory |

## Security Features

- **Directory Traversal Protection**: Prevents access to files outside the designated storage directory
- **Path Validation**: Rejects paths containing `..` or starting with `/`
- **File Existence Check**: Returns 404 if the requested file doesn't exist

## Response Headers

The endpoint automatically sets appropriate headers based on file type:

- **Content-Type**: Automatically detected based on file extension
- **Access-Control-Allow-Origin**: `*` (CORS enabled)
- **Cache-Control**: `no-cache`

### Supported MIME Types

| Extension | MIME Type |
|-----------|-----------|
| `.mp4` | `video/mp4` |
| `.mp3` | `audio/mpeg` |
| `.wav` | `audio/wav` |
| `.webm` | `video/webm` |
| Others | `application/octet-stream` |

## Example Usage

### Request
```http
GET /v1/media/files/background_video_12345.mp4
Host: localhost:8080
```

### Response
```http
HTTP/1.1 200 OK
Content-Type: video/mp4
Content-Length: 1048576
Access-Control-Allow-Origin: *
Cache-Control: no-cache

[Binary video data]
```

### Error Response (File Not Found)
```http
HTTP/1.1 404 NOT FOUND
Content-Type: text/plain

File not found
```

### Error Response (Invalid Path)
```http
HTTP/1.1 400 BAD REQUEST
Content-Type: text/plain

Invalid file path
```

## Use Cases

### MoviePy Video Rendering
This endpoint is primarily used by the MoviePy video rendering system to serve media files:

```python
# Convert local path to HTTP URL
def path_to_http_url(file_path):
    if file_path and os.path.exists(file_path):
        rel_path = os.path.relpath(file_path, LOCAL_STORAGE_PATH)
        return f"http://localhost:8080/v1/media/files/{rel_path}"
    return None

video_url = path_to_http_url("/tmp/storage/background_video.mp4")
# Returns: "http://localhost:8080/v1/media/files/background_video.mp4"
```

### Direct File Access
Access any file stored in the local storage directory:

```bash
curl http://localhost:8080/v1/media/files/audio/speech_output.mp3
```

## Configuration

The endpoint uses the `LOCAL_STORAGE_PATH` environment variable to determine the base directory for file serving:

```bash
LOCAL_STORAGE_PATH=/tmp/storage
```

## Security Considerations

1. **Limited Scope**: Only serves files from the designated storage directory
2. **No Authentication**: Currently public access - ensure sensitive files are not stored in the served directory
3. **CORS Enabled**: Allows cross-origin requests for browser-based applications
4. **Path Sanitization**: Prevents directory traversal attacks

## Related Endpoints

- [Short Video Creation](../video/short/short_video.md) - Uses this endpoint for media file access
- [Media Upload](upload.md) - Uploads files that can be served via this endpoint

## Error Handling

| Status Code | Description |
|-------------|-------------|
| 200 | File served successfully |
| 400 | Invalid file path (contains .. or starts with /) |
| 404 | File not found in storage directory |
| 500 | Internal server error during file serving |
