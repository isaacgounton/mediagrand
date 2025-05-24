# API Documentation

Welcome to the Video Creation API documentation. This guide provides comprehensive information about using our APIs to create professional short-form videos and manage background music.

## Table of Contents

1. [Short Video Creation](#short-video-creation)
2. [Music Management](#music-management)
3. [Common Topics](#common-topics)

## Short Video Creation

The [Short Video Creation API](short_video_endpoints.md) allows you to create professional short-form videos suitable for social media platforms.

Key features:
- Text-to-speech with multiple voice options
- Background video search and selection
- Customizable captions
- Background music integration
- Multiple output formats

[View Short Video API Documentation →](short_video_endpoints.md)

## Music Management

The [Music Management API](music_endpoints.md) provides endpoints for managing the background music library.

Key features:
- Mood-based music selection
- Custom music uploads
- Music library management
- Volume control options

[View Music Management API Documentation →](music_endpoints.md)

## Common Topics

### Authentication

All API requests require an API key passed in the header:
```http
Authorization: Bearer your-api-key-here
```

### Rate Limiting

- API requests are limited per endpoint
- Usage tracked by API key
- Headers indicate remaining limits:
  ```http
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1621436800
  ```

### Response Formats

Standard response format:
```json
{
  "status": "success|error",
  "data": {},
  "error": null
}
```

Error response format:
```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `202` - Accepted (async job started)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Server Error

### Webhooks

Endpoints supporting webhooks will:
- Accept a `webhook_url` parameter
- POST updates to the provided URL
- Include job status and results
- Sign requests with `X-Webhook-Signature`

### API Versioning

Current version: `v1`

Version is specified in the URL path:
```
https://api.example.com/v1/...
```

Major versions may include breaking changes.

## Support

- [API Status Page](https://status.example.com)
- [Developer Discord](https://discord.gg/example)
- Email: api-support@example.com

## SDK Libraries

- [Python SDK](https://github.com/example/python-sdk)
- [Node.js SDK](https://github.com/example/node-sdk)
- [PHP SDK](https://github.com/example/php-sdk)

## Legal

- [Terms of Service](https://example.com/terms)
- [API License](https://example.com/api-license)
- [Privacy Policy](https://example.com/privacy)
