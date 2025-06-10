# Docker Deployment for AI Research Feature

## Overview

This guide covers deploying the AI Research to Video feature in a Docker environment, specifically for Coolify server deployment.

## Environment Variables

Add these environment variables to your Docker deployment:

```bash
# Required for AI Research Feature
PERPLEXITY_API_KEY=your-perplexity-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key

# Google Custom Search (Excellent fallback/alternative)
GOOGLE_SEARCH_API_KEY=your-google-search-api-key
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id
```

## Docker Implementation

### 1. Update Dockerfile

The research feature uses standard HTTP requests and doesn't require additional Docker dependencies. The existing Node.js environment is sufficient.

### 2. API Integration

Since MCP servers are typically local desktop applications, the Docker implementation uses direct API calls:

- **Perplexity API**: Direct HTTP requests to Perplexity's API
- **DeepSeek API**: Direct HTTP requests for scene generation
- **Fallback**: Comprehensive mock implementations for development

### 3. Service Configuration

The `ResearchService` automatically detects the environment:

- **With API Keys**: Uses real API services
- **Without API Keys**: Falls back to sophisticated mock implementations
- **Error Handling**: Graceful degradation with detailed logging

## Production Configuration

### Environment Setup

In your Coolify deployment, configure these environment variables:

```bash
# Core API Keys
PERPLEXITY_API_KEY=pplx-xxx...
DEEPSEEK_API_KEY=sk-xxx...

# Optional Configuration
NODE_ENV=production
LOG_LEVEL=info
```

### API Endpoints

The feature adds these new endpoints to your existing API:

- `POST /api/research-topic` - Research any topic
- `POST /api/generate-scenes` - Generate video scenes from research

### Integration Flow

1. **User Input**: Topic search in `/research` frontend
2. **Research Phase**: Calls Perplexity API for comprehensive research
3. **Scene Generation**: Uses DeepSeek API to create video scenes
4. **Video Creation**: Integrates with existing video pipeline

## Architecture for Docker

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │  External APIs  │
│   /research     │───▶│  ResearchService │───▶│  Perplexity API │
│                 │    │                  │    │  DeepSeek API   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Video Pipeline │
                       │   (Existing)     │
                       └──────────────────┘
```

## API Implementation Details

### Perplexity Integration

```typescript
// Direct API call instead of MCP
const response = await fetch('https://api.perplexity.ai/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.PERPLEXITY_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'llama-3.1-sonar-small-128k-online',
    messages: [{
      role: 'user',
      content: `Research this topic in detail: ${searchTerm}`
    }]
  })
});
```

### DeepSeek Integration

```typescript
// Scene generation using DeepSeek API
const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.DEEPSEEK_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'deepseek-chat',
    messages: [{
      role: 'system',
      content: 'You are an expert video content creator. Generate JSON only.'
    }, {
      role: 'user',
      content: sceneGenerationPrompt
    }],
    temperature: 0.7
  })
});
```

## Testing in Docker

### Local Testing

```bash
# Build and run locally
cd short-video-maker
docker build -t video-maker .
docker run -p 3000:3000 \
  -e PERPLEXITY_API_KEY=your-key \
  -e DEEPSEEK_API_KEY=your-key \
  video-maker
```

### Mock Mode Testing

Without API keys, the service provides realistic mock responses:

```bash
# Test without API keys (mock mode)
docker run -p 3000:3000 video-maker
```

## Coolify Deployment

### 1. Environment Variables

In Coolify dashboard, add:

- `PERPLEXITY_API_KEY`
- `DEEPSEEK_API_KEY`

### 2. Deploy

The research feature will be automatically available at:
- Frontend: `https://your-domain.com/research`
- API: `https://your-domain.com/api/research-topic`

### 3. Verification

Test the deployment:

```bash
# Test research endpoint
curl -X POST https://your-domain.com/api/research-topic \
  -H "Content-Type: application/json" \
  -d '{"searchTerm": "artificial intelligence", "targetLanguage": "en"}'

# Test scene generation
curl -X POST https://your-domain.com/api/generate-scenes \
  -H "Content-Type: application/json" \
  -d '{"title": "AI Guide", "content": "AI research content...", "targetLanguage": "en"}'
```

## Monitoring and Logs

### API Usage Monitoring

The service logs all API calls:

```json
{
  "level": "info",
  "message": "Research request",
  "searchTerm": "artificial intelligence",
  "targetLanguage": "en",
  "timestamp": "2025-01-06T10:30:00Z"
}
```

### Error Handling

Graceful fallbacks ensure the service always responds:

1. **API Failure**: Falls back to mock implementation
2. **Rate Limits**: Implements retry logic with exponential backoff
3. **Invalid Responses**: Returns structured error messages

## Performance Considerations

### Caching

- Research results cached for 1 hour
- Scene generation cached for 24 hours
- Reduces API costs and improves response times

### Rate Limiting

- Implements request throttling
- Prevents API quota exhaustion
- User-friendly error messages for rate limits

## Security

### API Key Management

- Environment variables only
- No hardcoded keys in source code
- Secure key rotation support

### Input Validation

- Sanitize all user inputs
- Validate API responses
- XSS and injection protection

## Troubleshooting

### Common Issues

1. **API Keys Not Working**
   - Verify environment variables in Coolify
   - Check API key validity and quotas
   - Review Docker logs for authentication errors

2. **Service Unavailable**
   - Check external API status
   - Verify network connectivity from container
   - Review fallback mode logs

3. **Slow Responses**
   - Monitor API response times
   - Check cache hit rates
   - Consider regional API endpoints

### Debug Mode

Enable detailed logging:

```bash
# In Coolify environment variables
DEBUG=research:*
LOG_LEVEL=debug
```

This provides comprehensive request/response logging for troubleshooting.
