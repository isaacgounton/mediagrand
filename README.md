![DahoPevi Logo](https://github.com/user-attachments/assets/75173cf4-2502-4710-998b-6b81740ae1bd)

# DahoPevi API

A powerful media processing API built with Python and Flask, designed for seamless audio, video, and image manipulation.

## Core Features

🎬 **Media Processing**
- Convert between audio/video formats
- Add captions to videos
- Extract audio from video
- Generate video from images
- Trim and concatenate media files

🗣️ **AI Features**
- Transcribe audio/video content
- Translate content between languages
- Process media with customizable parameters

☁️ **Cloud Integration**
- Google Drive
- Amazon S3
- Google Cloud Storage
- Dropbox

## Quick Start Guide

### 1. Build the Docker Image
```bash
docker build -t isaacgounton/dahopevi .
```

### 2. Run the Container
```bash
docker run -d -p 8080:8080 \
  -e API_KEY=your_api_key \
  -e GCP_SA_CREDENTIALS='{"your":"service_account_json"}' \
  -e GCP_BUCKET_NAME=your_bucket_name \
  isaacgounton/dahopevi
```

### 3. Test the API
Install the [Postman Template](https://bit.ly/49Gkhl) and configure:
- `base_url`: Your API endpoint
- `x-api-key`: Your API key

## API Reference

### Video Operations

```http
POST /v1/video/caption
POST /v1/video/cut
POST /v1/video/trim
POST /v1/video/concatenate
POST /v1/video/split
GET  /v1/video/thumbnail
```

### Audio Operations

```http
POST /v1/audio/concatenate
POST /v1/audio/speech
POST /v1/media/silence
POST /v1/media/convert/mp3
```

### Image Operations

```http
POST /v1/image/convert/video
```

### Cloud Storage

```http
POST /v1/s3/upload
```

## Deployment Options

### 🌟 Google Cloud Run (Recommended)
Best for:
- Scalable deployments
- Pay-per-use pricing
- Automatic scaling
- Built-in monitoring

[View GCP Setup Guide](https://github.com/isaacgounton/dahopevi/blob/main/docs/cloud-installation/gcp.md)

### 🌊 Digital Ocean
Best for:
- Predictable workloads
- Simplified deployment
- Consistent pricing

[View DO Setup Guide](https://github.com/isaacgounton/dahopevi/blob/main/docs/cloud-installation/do.md)

### 🐳 Docker (Self-hosted)
Best for:
- Full control
- Custom infrastructure
- Local development

[View Docker Guide](https://github.com/isaacgounton/dahopevi/blob/main/docker-compose.md)

## Configuration

### Essential Environment Variables

```bash
# Required
API_KEY=your_api_key

# Cloud Storage (Choose one)
GCP_SA_CREDENTIALS='{credentials_json}'
GCP_BUCKET_NAME=bucket_name

# OR

S3_ENDPOINT_URL=https://your-endpoint
S3_ACCESS_KEY=access_key
S3_SECRET_KEY=secret_key
S3_BUCKET_NAME=bucket_name
S3_REGION=region
```

### Performance Tuning

```bash
MAX_QUEUE_LENGTH=10        # Concurrent tasks (default: unlimited)
GUNICORN_WORKERS=4         # Worker processes (default: CPU cores + 1)
GUNICORN_TIMEOUT=300      # Process timeout in seconds (default: 30)
```

## Support and Community

Get dedicated support and connect with other developers:

- [DahoPevi Community](https://www.skool.com/no-code-architects)
- [Documentation](https://github.com/isaacgounton/dahopevi/docs)
- [API GPT Assistant](https://bit.ly/4feDDk4)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

Licensed under [GNU General Public License v2.0 (GPL-2.0)](LICENSE)
