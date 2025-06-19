# Audio Convert Endpoint Documentation

## 1. Overview

The `/v1/audio/convert` endpoint is part of the Flask API application and is responsible for converting audio files from one format to another. This endpoint supports both file uploads and URL-based audio conversion, making it versatile for different use cases.

## 2. Endpoint

**URL Path:** `/v1/audio/convert`
**HTTP Method:** `POST`

## 3. Request Types

This endpoint supports two types of requests:

### 3.1 File Upload (multipart/form-data)

Convert an audio file directly uploaded to the server.

#### Headers
- `x-api-key` (required): The API key for authentication.
- `Content-Type`: `multipart/form-data`

#### Form Parameters
- `audio` (required, file): The audio file to be converted.
- `format` (required, string): The desired output format. Supported formats: `mp3`, `ogg`, `oga`.

#### Query Parameters
- `format` (alternative, string): Can also be provided as a query parameter instead of form data.

### 3.2 URL-based Conversion (application/json)

Convert an audio file from a publicly accessible URL.

#### Headers
- `x-api-key` (required): The API key for authentication.
- `Content-Type`: `application/json`

#### Body Parameters
- `audio_url` (required, string): The URL of the audio file to be converted.
- `format` (required, string): The desired output format. Supported formats: `mp3`, `ogg`, `oga`.
- `webhook_url` (optional, string): The URL to receive a webhook notification upon completion.
- `id` (optional, string): An optional identifier for the conversion request.

## 4. Example Requests

### 4.1 File Upload Example

```bash
curl -X POST \
  https://api.example.com/v1/audio/convert?format=mp3 \
  -H 'x-api-key: YOUR_API_KEY' \
  -F 'audio=@input.ogg'
```

### 4.2 URL Conversion Example

```json
{
  "audio_url": "https://example.com/audio.ogg",
  "format": "mp3",
  "webhook_url": "https://example.com/webhook",
  "id": "unique-request-id"
}
```

```bash
curl -X POST \
  https://api.example.com/v1/audio/convert \
  -H 'x-api-key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "audio_url": "https://example.com/audio.ogg",
    "format": "mp3",
    "webhook_url": "https://example.com/webhook",
    "id": "unique-request-id"
  }'
```

## 5. Response

### Success Response

The success response will be a JSON object containing the URL of the converted audio file uploaded to cloud storage.

```json
{
  "code": 200,
  "id": "unique-request-id",
  "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
  "response": "https://cloud.example.com/converted-audio.mp3",
  "message": "success",
  "pid": 12345,
  "run_time": 5.234,
  "queue_time": 0.067,
  "total_time": 5.301,
  "queue_length": 0,
  "build_number": "1.0.0"
}
```

### Error Responses

- **400 Bad Request**: Returned when the request payload is missing or invalid.
- **401 Unauthorized**: Returned when the `x-api-key` header is missing or invalid.
- **500 Internal Server Error**: Returned when an unexpected error occurs during the conversion process.

Example error response:

```json
{
  "code": 400,
  "id": "unique-request-id",
  "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
  "message": "Source and target formats are the same",
  "pid": 12345,
  "queue_length": 0,
  "build_number": "1.0.0"
}
```

## 6. Supported Formats

### Input Formats
- MP3
- OGG
- OGA
- M4A (for input only)
- WAV
- FLAC
- Most audio formats supported by FFmpeg

### Output Formats
- `mp3`: MP3 format with libmp3lame encoder, 128k bitrate
- `ogg`: OGG Vorbis format with libvorbis encoder, 128k bitrate
- `oga`: OGA Vorbis format with libvorbis encoder, 128k bitrate

## 7. Audio Processing Features

- **High-quality encoding**: Uses industry-standard encoders (libmp3lame, libvorbis)
- **Consistent bitrate**: 128k bitrate for optimal quality/size balance
- **Format validation**: Both input and output formats are validated
- **Error handling**: Comprehensive error handling with detailed FFmpeg error messages
- **Automatic codec selection**: Optimal codec selection based on output format

## 8. Technical Details

### Encoding Settings
- **MP3**: libmp3lame encoder, 128k bitrate
- **OGG/OGA**: libvorbis encoder, 128k bitrate
- **Quality**: Optimized for good quality with reasonable file sizes

### Processing Pipeline
1. File upload or URL download
2. Format validation
3. FFmpeg processing with appropriate codecs
4. Cloud storage upload
5. Cleanup of temporary files

## 9. Usage Notes

- **File size limits**: Check your server configuration for maximum file upload limits
- **URL accessibility**: For URL-based conversion, the audio URL must be publicly accessible
- **Same format detection**: The system prevents conversion when source and target formats are identical
- **Processing time**: Conversion time depends on file size and complexity

## 10. Error Handling

The endpoint includes comprehensive error handling for:
- Invalid or unsupported audio formats
- Network errors when downloading from URLs
- FFmpeg processing errors
- Missing or invalid parameters
- Authentication failures
- Same source/target format detection

Common error scenarios:
- **"Source and target formats are the same"**: When trying to convert a file to the same format
- **"Unsupported format"**: When using formats not in the supported list
- **"No audio file uploaded"**: When the audio file is missing from the request
- **"Empty file uploaded"**: When the uploaded file has no content

## 11. Best Practices

- Always validate file types on the client side before uploading
- Use MP3 for maximum compatibility, OGG for open-source applications
- Implement proper error handling in your client applications
- Consider implementing client-side file size validation
- Use the `webhook_url` parameter for asynchronous processing notifications
- Test with various audio formats to ensure compatibility

## 12. Common Use Cases

- **Format standardization**: Convert various audio formats to MP3 for consistent playback
- **Open-source compliance**: Convert to OGG for applications requiring open formats
- **Web optimization**: Convert to efficient formats for web streaming
- **Cross-platform compatibility**: Ensure audio files work across different devices and platforms