# Image Format Conversion Endpoint Documentation

## 1. Overview

The `/v1/image/format` endpoint is part of the Flask API application and is responsible for converting image files from one format to another. This endpoint supports both file uploads and URL-based image conversion, making it versatile for different use cases.

## 2. Endpoint

**URL Path:** `/v1/image/format`
**HTTP Method:** `POST`

## 3. Request Types

This endpoint supports two types of requests:

### 3.1 File Upload (multipart/form-data)

Convert an image file directly uploaded to the server.

#### Headers
- `x-api-key` (required): The API key for authentication.
- `Content-Type`: `multipart/form-data`

#### Form Parameters
- `image` (required, file): The image file to be converted.
- `format` (required, string): The desired output format. Supported formats: `jpg`, `jpeg`, `webp`, `png`.

#### Query Parameters
- `format` (alternative, string): Can also be provided as a query parameter instead of form data.

### 3.2 URL-based Conversion (application/json)

Convert an image from a publicly accessible URL.

#### Headers
- `x-api-key` (required): The API key for authentication.
- `Content-Type`: `application/json`

#### Body Parameters
- `image_url` (required, string): The URL of the image to be converted.
- `format` (required, string): The desired output format. Supported formats: `jpg`, `jpeg`, `webp`, `png`.
- `webhook_url` (optional, string): The URL to receive a webhook notification upon completion.
- `id` (optional, string): An optional identifier for the conversion request.

## 4. Example Requests

### 4.1 File Upload Example

```bash
curl -X POST \
  https://api.example.com/v1/image/format?format=webp \
  -H 'x-api-key: YOUR_API_KEY' \
  -F 'image=@input.jpg'
```

### 4.2 URL Conversion Example

```json
{
  "image_url": "https://example.com/image.jpg",
  "format": "webp",
  "webhook_url": "https://example.com/webhook",
  "id": "unique-request-id"
}
```

```bash
curl -X POST \
  https://api.example.com/v1/image/format \
  -H 'x-api-key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "format": "webp",
    "webhook_url": "https://example.com/webhook",
    "id": "unique-request-id"
  }'
```

## 5. Response

### Success Response

The success response will be a JSON object containing the URL of the converted image uploaded to cloud storage.

```json
{
  "code": 200,
  "id": "unique-request-id",
  "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
  "response": "https://cloud.example.com/converted-image.webp",
  "message": "success",
  "pid": 12345,
  "run_time": 2.134,
  "queue_time": 0.045,
  "total_time": 2.179,
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
  "message": "Unsupported format: gif. Supported formats: ['jpg', 'jpeg', 'webp', 'png']",
  "pid": 12345,
  "queue_length": 0,
  "build_number": "1.0.0"
}
```

## 6. Supported Formats

### Input Formats
- JPG/JPEG
- PNG
- WebP
- GIF (converted with transparency handling)
- Most standard image formats supported by PIL/Pillow

### Output Formats
- `jpg` / `jpeg`: JPEG format with white background for transparent images
- `webp`: WebP format with transparency support
- `png`: PNG format with transparency support

## 7. Image Processing Features

- **Automatic transparency handling**: When converting RGBA images to JPEG, a white background is automatically added
- **Quality optimization**: Images are saved with optimized quality settings
- **Format validation**: Both input and output formats are validated
- **Error handling**: Comprehensive error handling with detailed error messages

## 8. Usage Notes

- **File size limits**: Check your server configuration for maximum file upload limits
- **URL accessibility**: For URL-based conversion, the image URL must be publicly accessible
- **Transparency**: JPEG format doesn't support transparency; transparent areas will be filled with white background
- **Quality**: Converted images are optimized for web use with quality=95 for JPEG

## 9. Error Handling

The endpoint includes comprehensive error handling for:
- Invalid or unsupported image formats
- Network errors when downloading from URLs
- File processing errors
- Missing or invalid parameters
- Authentication failures

## 10. Best Practices

- Always validate file types on the client side before uploading
- Use appropriate image formats: WebP for web optimization, PNG for transparency, JPEG for photographs
- Implement proper error handling in your client applications
- Consider implementing client-side image compression for large files
- Use the `webhook_url` parameter for asynchronous processing notifications