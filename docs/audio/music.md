# Audio Music Generation Endpoint

## 1. Overview

The `/v1/audio/music` endpoint is a part of the Audio API and is responsible for generating music from text descriptions using Meta's MusicGen model. This endpoint fits into the overall API structure as a part of the version 1 (v1) routes, specifically under the `/v1/audio` namespace. It uses the Transformers library to provide AI-powered music generation with support for different model sizes and output formats.

## 2. Endpoint

**URL Path:** `/v1/audio/music`
**HTTP Method:** `POST`

## 3. Request

### Headers

- `x-api-key` (required): The API key for authentication.

### Body Parameters

The request body must be a JSON object with the following properties:

- `description` (required, string): Text description of the music to generate.
- `duration` (optional, number): Duration in seconds (1-30). Default: 8.
- `model_size` (optional, string): Model size to use. Options: "small", "medium", "large". Default: "small".
- `output_format` (optional, string): Audio output format. Options: "wav", "mp3". Default: "wav".
- `webhook_url` (optional, string, URI format): The URL to which the response should be sent as a webhook.
- `id` (optional, string): An identifier for the request.

### Example Request

**Basic Music Generation:**

```json
{
    "description": "lo-fi music with a soothing melody",
    "duration": 8,
    "model_size": "small",
    "output_format": "wav"
}
```

**Advanced Music Generation:**

```json
{
    "description": "upbeat electronic dance music with heavy bass",
    "duration": 15,
    "model_size": "medium",
    "output_format": "mp3",
    "webhook_url": "https://example.com/webhook",
    "id": "music-gen-123"
}
```

**Different Music Styles:**

```json
{
    "description": "classical piano piece in minor key",
    "duration": 20,
    "model_size": "large",
    "output_format": "wav"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
        "description": "lo-fi music with a soothing melody",
        "duration": 8,
        "model_size": "small",
        "output_format": "wav"
     }' \
     https://your-api-endpoint.com/v1/audio/music
```

## 4. Response

### Success Response

The success response follows the general response format defined in the `app.py` file. Here's an example:

```json
{
    "endpoint": "/v1/audio/music",
    "code": 200,
    "id": "music-gen-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "response": {
        "message": "Music generated successfully",
        "output_url": "https://cloud-storage.example.com/musicgen/generated-music.wav",
        "duration": 8.15,
        "model_used": "facebook/musicgen-small",
        "description": "lo-fi music with a soothing melody",
        "file_size": 1048576,
        "sampling_rate": 32000
    },
    "message": "success",
    "pid": 12345,
    "run_time": 15.678,
    "queue_time": 2.456,
    "total_time": 18.134,
    "queue_length": 0,
    "build_number": "1.0.0"
}
```

The `response` field contains an object with the generated music file URL and metadata.

### Error Responses

- **400 Bad Request**: Returned when the request body is missing or invalid.

  ```json
  {
    "code": 400,
    "message": "Missing required parameter: description"
  }
  ```

  ```json
  {
    "code": 400,
    "message": "Duration cannot exceed 30 seconds"
  }
  ```

  ```json
  {
    "code": 400,
    "message": "Invalid model_size. Must be 'small', 'medium', or 'large'"
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
    "id": "music-gen-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "message": "MAX_QUEUE_LENGTH (100) reached",
    "pid": 12345,
    "queue_length": 100,
    "build_number": "1.0.0"
  }
  ```

- **500 Internal Server Error**: Returned when an unexpected error occurs during the music generation process.

  ```json
  {
    "code": 500,
    "message": "Music generation failed",
    "error": "Model loading failed: Out of memory"
  }
  ```

## 5. Error Handling

The endpoint handles the following common errors:

- **Missing or invalid request body**: If the request body is missing or does not contain the required `description` parameter, a 400 Bad Request error is returned.
- **Invalid parameters**: If duration exceeds 30 seconds, model_size is not supported, or output_format is invalid, a 400 Bad Request error is returned.
- **Missing or invalid API key**: If the `x-api-key` header is missing or invalid, a 401 Unauthorized error is returned.
- **Queue length exceeded**: If the maximum queue length is reached (determined by the `MAX_QUEUE_LENGTH` environment variable), a 429 Too Many Requests error is returned.
- **Model loading failures**: If the MusicGen model fails to load due to memory constraints or other issues, a 500 Internal Server Error is returned.
- **Storage upload failures**: If the generated music file cannot be uploaded to cloud storage, a 500 Internal Server Error is returned.

## 6. Usage Notes

- The music generation process uses Meta's MusicGen model, which is a single stage auto-regressive Transformer model.
- Generated music is mono audio at 32kHz sampling rate.
- The `small` model (300M parameters) is fastest but may have lower quality than `medium` or `large` models.
- Text descriptions should be clear and descriptive (e.g., "jazz piano with soft drums" rather than just "music").
- Processing time varies significantly based on model size and duration (typically 10-60 seconds).
- The model performs best with music-related descriptions in English.
- Generated music may not include realistic vocals as the model is primarily trained on instrumental music.
- If the `webhook_url` parameter is provided, the response will be sent as a webhook to the specified URL.
- The `id` parameter can be used to identify the request in the response.

## 7. Common Issues

- **Model loading failures**: Large models may fail to load on systems with insufficient RAM. Consider using smaller models or increasing system memory.
- **Long generation times**: Complex descriptions or longer durations may result in extended processing times.
- **Quality variations**: Generated music quality can vary based on the specificity and clarity of the text description.
- **Storage upload failures**: Network issues or storage service outages can prevent successful file uploads.
- **Unsupported descriptions**: Very abstract or non-musical descriptions may produce unexpected results.
- **Memory constraints**: Running multiple concurrent requests may exceed available system memory.

## 8. Best Practices

- **Use descriptive text**: Provide clear, music-specific descriptions (e.g., "upbeat rock guitar with drums" vs. "happy song").
- **Start with small models**: Begin with the "small" model for faster testing before moving to larger models.
- **Limit duration**: Keep initial tests to 8-15 seconds to reduce processing time and resource usage.
- **Monitor system resources**: Music generation is memory-intensive; monitor RAM usage especially with larger models.
- **Cache results**: Store generated music files to avoid regenerating identical requests.
- **Implement retry logic**: Handle temporary failures gracefully with exponential backoff.
- **Use appropriate formats**: WAV for highest quality, MP3 for smaller file sizes.
- **Test descriptions**: Experiment with different text descriptions to find optimal prompts for your use case.

## 9. Related Endpoints

### Endpoint Information

**GET** `/v1/audio/music`

Returns detailed information about the music generation endpoint, including supported parameters and examples.

**Example Response:**
```json
{
    "endpoint": "/v1/audio/music",
    "method": "POST",
    "description": "Generate music from text descriptions using Meta's MusicGen model",
    "parameters": {
        "description": {
            "type": "string",
            "required": true,
            "description": "Text description of the music to generate"
        },
        "duration": {
            "type": "integer",
            "required": false,
            "default": 8,
            "max": 30,
            "description": "Duration in seconds (max 30)"
        },
        "model_size": {
            "type": "string",
            "required": false,
            "default": "small",
            "options": ["small", "medium", "large"],
            "description": "Model size to use"
        },
        "output_format": {
            "type": "string",
            "required": false,
            "default": "wav",
            "options": ["wav", "mp3"],
            "description": "Output audio format"
        }
    },
    "examples": [
        {
            "description": "lo-fi music with a soothing melody",
            "duration": 8,
            "model_size": "small"
        },
        {
            "description": "upbeat electronic dance music",
            "duration": 15,
            "model_size": "medium"
        }
    ]
}
```

### Health Check

**GET** `/health`

General API health check endpoint that includes system status and available resources.

## 10. Model Information

The endpoint uses Meta's MusicGen models with the following characteristics:

### Available Models

| Model Size | Parameters | Speed | Quality | Memory Usage |
|------------|------------|--------|---------|--------------|
| `small` | 300M | Fast | Good | ~2GB RAM |
| `medium` | 1.5B | Medium | Better | ~6GB RAM |
| `large` | 3.3B | Slow | Best | ~12GB RAM |

### Model Capabilities

- **Input**: Text descriptions in natural language
- **Output**: 32kHz mono audio waveform
- **Duration**: Up to 30 seconds (configurable)
- **Genres**: Wide variety of musical genres and styles
- **Language**: Primarily English descriptions, but supports some multilingual input
- **Limitations**: Cannot generate realistic vocals; primarily instrumental music

### Performance Characteristics

- **Processing Time**:
  - Small model: ~10-20 seconds for 8-second audio
  - Medium model: ~30-45 seconds for 8-second audio
  - Large model: ~60-90 seconds for 8-second audio
- **Memory Requirements**: Models are cached after first load
- **Concurrent Requests**: Limited by available system memory

## 11. Configuration

The endpoint supports the following optional environment variables:

```env
# Storage Configuration
LOCAL_STORAGE_PATH=/tmp
S3_ENDPOINT_URL=https://your-s3-endpoint.com
S3_BUCKET_NAME=your-bucket-name
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key

# Processing Configuration
MAX_QUEUE_LENGTH=100
GUNICORN_TIMEOUT=300
```

### Dependencies

The music generation endpoint requires the following Python packages:

```txt
transformers>=4.31.0
scipy>=1.9.0
torch>=2.0.0
numpy>=1.21.0
```

### System Requirements

- **Minimum RAM**: 4GB (for small model)
- **Recommended RAM**: 8GB+ (for medium/large models)
- **Storage**: At least 2GB free space for model caching
- **Network**: Stable internet connection for model downloads and file uploads

## 12. Example Use Cases

### Background Music Generation

```json
{
    "description": "ambient background music for relaxation",
    "duration": 30,
    "model_size": "medium",
    "output_format": "mp3"
}
```

### Game Audio

```json
{
    "description": "8-bit video game music with upbeat tempo",
    "duration": 10,
    "model_size": "small",
    "output_format": "wav"
}
```

### Podcast Intros

```json
{
    "description": "professional podcast intro music with electronic elements",
    "duration": 15,
    "model_size": "medium",
    "output_format": "mp3"
}
```

### Mood-Based Music

```json
{
    "description": "melancholic piano melody in minor key",
    "duration": 20,
    "model_size": "large",
    "output_format": "wav"
}
```
