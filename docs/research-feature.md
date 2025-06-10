# AI Research to Video Feature

## Overview

The AI Research to Video feature allows users to:
1. Enter a search term or topic
2. Automatically research the topic using AI
3. Generate video scenes from the research
4. Customize and create the video

## Architecture

### Frontend Components

- **VideoResearcher.tsx**: Main research interface at `/research`
- **Layout.tsx**: Updated with navigation to research feature
- **App.tsx**: Added route for research page

### Backend API Endpoints

- `POST /api/research-topic`: Research a topic using AI
- `POST /api/generate-scenes`: Generate video scenes from research content

### Integration Points

#### 1. Perplexity MCP Integration

**Current State**: Mock implementation for development
**Production Setup**: Configure Perplexity MCP server

```bash
# Install Perplexity MCP
npm install -g @perplexity/mcp-server

# Configure in your MCP setup
# Add to mcp-config.json:
{
  "servers": {
    "perplexity": {
      "command": "npx",
      "args": ["@perplexity/mcp-server"],
      "env": {
        "PERPLEXITY_API_KEY": "your-api-key"
      }
    }
  }
}
```

**API Usage**:
```typescript
// In production, replace the mock with:
const result = await mcpClient.callTool('search', {
  query: searchTerm,
  detail_level: 'detailed'
});
```

#### 2. AI Scene Generation (DeepSeek Integration)

**Current State**: Mock implementation with realistic scene generation
**Production Setup**: Add DEEPSEEK_API_KEY to environment

```bash
# Add to .env
DEEPSEEK_API_KEY=your-deepseek-api-key
```

**Implementation**:
```typescript
// Replace mock in callAIForSceneGeneration method:
const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.DEEPSEEK_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'deepseek-chat',
    messages: [{ role: 'user', content: prompt }]
  })
});
```

## Workflow

### 1. Research Phase
- User enters topic (e.g., "Climate change effects")
- System calls Perplexity MCP or Google Custom Search
- Returns comprehensive research with sources

### 2. Scene Generation Phase
- Research content is sent to AI (DeepSeek)
- AI generates 3-6 video scenes with:
  - Narration text optimized for TTS
  - Search terms for background videos
  - Appropriate voice selection based on language

### 3. Customization Phase
- User can edit generated scenes
- Modify video configuration (voice, music, orientation)
- Preview and adjust before creation

### 4. Video Creation
- Uses existing video creation pipeline
- Same as manual video creation but with AI-generated content

## Features

### Multi-language Support
- Supports 9 languages (English, French, Spanish, German, Italian, Portuguese, Japanese, Chinese, Arabic)
- Automatic voice selection based on target language
- Content generation in target language

### Smart Configuration
- AI selects appropriate voices based on language
- Suggests optimal video settings
- Generates relevant search terms for background videos

### User Control
- Full editing capabilities for generated content
- Advanced settings for video customization
- Fallback to manual creation if needed

## File Structure

```
short-video-maker/src/
├── ui/
│   ├── pages/
│   │   └── VideoResearcher.tsx     # Main research interface
│   ├── components/
│   │   └── Layout.tsx              # Updated navigation
│   └── App.tsx                     # Added route
├── server/routers/
│   └── rest.ts                     # Added API endpoints
└── types/
    └── shorts.ts                   # Existing types (reused)
```

## Configuration for Production

### Environment Variables
```bash
# Required for real research functionality
PERPLEXITY_API_KEY=your-perplexity-key
DEEPSEEK_API_KEY=your-deepseek-key

# Optional: Google Custom Search (alternative to Perplexity)
GOOGLE_SEARCH_API_KEY=your-google-key
GOOGLE_SEARCH_ENGINE_ID=your-engine-id
```

### MCP Server Configuration
Update your MCP configuration to include research services:

```json
{
  "servers": {
    "perplexity": {
      "command": "node",
      "args": ["/path/to/perplexity-mcp-server/dist/index.js"],
      "env": {
        "PERPLEXITY_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Usage Examples

### Research Topics
- "Climate change effects on agriculture"
- "History of artificial intelligence"
- "Benefits of renewable energy"
- "Space exploration timeline"
- "Blockchain technology applications"

### Generated Content Examples
The AI generates educational content with:
- Introduction and overview
- Key concepts and principles
- Historical context
- Current applications
- Future implications
- Challenges and considerations

## Development vs Production

### Development Mode (Current)
- Mock implementations for research and AI
- Realistic but static content generation
- Full UI functionality for testing

### Production Mode (With API Keys)
- Real Perplexity research integration
- Live AI scene generation
- Dynamic content based on actual research

## Integration with Existing System

The research feature integrates seamlessly with your existing video creation system:
- Uses same video types and configuration
- Leverages existing TTS engines and voices
- Utilizes current music and background video systems
- Maintains existing queue and processing pipeline

## Future Enhancements

1. **Real-time Research Updates**: Live content updates as research progresses
2. **Source Citation**: Include clickable sources in video descriptions
3. **Topic Suggestions**: AI-powered topic recommendations
4. **Content Templates**: Pre-built templates for different content types
5. **Collaborative Editing**: Multi-user scene editing and review
