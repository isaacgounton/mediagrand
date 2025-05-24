# Remotion Video Creation API

## Overview
Remotion is a framework for creating videos programmatically using React. Unlike traditional video editing tools, Remotion allows you to create videos using code, making it perfect for automated video generation, dynamic content creation, and scalable video production.

## Key Remotion Endpoints for Video Creation

### 1. Core Video Rendering Endpoint

The primary endpoint for creating any kind of video using Remotion is the `renderMedia()` function from `@remotion/renderer`:

```javascript
import { renderMedia } from '@remotion/renderer';

await renderMedia({
  composition,
  serveUrl,
  codec: 'h264',
  outputLocation,
  inputProps,
});
```

### 2. Available Video Codecs

Remotion supports multiple output formats:

- **h264** - Most common video format (MP4)
- **h265** - High efficiency video codec
- **vp8** / **vp9** - WebM formats
- **prores** - Professional video format
- **h264-mkv** - H264 in MKV container
- **gif** - Animated GIF
- **mp3** / **aac** / **wav** - Audio-only formats

### 3. Video Creation Process

#### Step 1: Bundle Your Remotion Project
```javascript
import { bundle } from '@remotion/bundler';

const bundleLocation = await bundle({
  entryPoint: './src/index.ts',
  webpackOverride: (config) => config,
});
```

#### Step 2: Get Available Compositions
```javascript
import { getCompositions } from '@remotion/renderer';

const compositions = await getCompositions(bundleLocation, {
  inputProps: {},
});
```

#### Step 3: Select and Render Composition
```javascript
import { selectComposition, renderMedia } from '@remotion/renderer';

const composition = await selectComposition({
  serveUrl: bundleLocation,
  id: 'MyVideo',
  inputProps: {},
});

await renderMedia({
  composition,
  serveUrl: bundleLocation,
  codec: 'h264',
  outputLocation: './output/video.mp4',
  inputProps: {
    title: 'My Dynamic Video',
    duration: 30,
  },
});
```

## Remotion vs FFmpeg Compose

### Can you use Remotion like FFmpeg compose?

**Yes and No** - Here's the comparison:

### FFmpeg Compose Approach
```bash
# Traditional FFmpeg compose
ffmpeg -i input1.mp4 -i input2.mp4 -filter_complex "[0:v][1:v]hstack" output.mp4
```

### Remotion Approach
```jsx
// Remotion composition (React-based)
export const MyComposition = () => {
  return (
    <AbsoluteFill>
      <Video src="input1.mp4" />
      <Video src="input2.mp4" style={{left: '50%'}} />
    </AbsoluteFill>
  );
};
```

### Key Differences

| Feature | FFmpeg | Remotion |
|---------|--------|----------|
| **Approach** | Command-line filters | React components |
| **Learning Curve** | Complex filter syntax | React/JavaScript knowledge |
| **Dynamic Content** | Limited | Excellent (data-driven) |
| **Animations** | Basic | Advanced (CSS, JS animations) |
| **Text Rendering** | Basic | Rich (HTML/CSS) |
| **Programmatic Control** | Shell commands | Full JavaScript API |
| **Performance** | Very fast | Good (depends on complexity) |

### When to Use Remotion Instead of FFmpeg

✅ **Use Remotion when:**
- Creating data-driven videos
- Need complex animations
- Want rich text rendering
- Building video generation APIs
- Need programmatic control
- Creating templates with variables

❌ **Use FFmpeg when:**
- Simple video processing
- Maximum performance needed
- Working with existing video files
- Basic concatenation/trimming
- Server resources are limited

## Remotion API Integration Examples

### 1. Basic Video Generation Endpoint

```javascript
// Express.js endpoint example
app.post('/api/v1/video/remotion/render', async (req, res) => {
  try {
    const { template, inputProps } = req.body;
    
    // Bundle the Remotion project
    const bundleLocation = await bundle({
      entryPoint: './remotion/src/index.ts',
    });
    
    // Get composition
    const composition = await selectComposition({
      serveUrl: bundleLocation,
      id: template,
      inputProps,
    });
    
    // Render video
    const outputPath = `./output/${Date.now()}.mp4`;
    await renderMedia({
      composition,
      serveUrl: bundleLocation,
      codec: 'h264',
      outputLocation: outputPath,
      inputProps,
    });
    
    res.json({
      success: true,
      videoPath: outputPath,
      duration: composition.durationInFrames / composition.fps,
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

### 2. Template-Based Video Creation

```javascript
// Create different video types
const templates = {
  'social-media': {
    width: 1080,
    height: 1080,
    fps: 30,
    durationInFrames: 900, // 30 seconds
  },
  'youtube-intro': {
    width: 1920,
    height: 1080,
    fps: 60,
    durationInFrames: 300, // 5 seconds
  },
  'story': {
    width: 1080,
    height: 1920,
    fps: 30,
    durationInFrames: 450, // 15 seconds
  }
};
```

### 3. Dynamic Content Integration

```jsx
// Remotion composition with dynamic data
export const DataDrivenVideo = ({data}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  
  return (
    <AbsoluteFill>
      {data.scenes.map((scene, index) => (
        <Sequence
          key={index}
          from={scene.startFrame}
          durationInFrames={scene.duration}
        >
          <div style={{
            fontSize: interpolate(frame, [0, 30], [20, 40]),
            opacity: interpolate(frame, [0, 10, 20, 30], [0, 1, 1, 0]),
          }}>
            {scene.text}
          </div>
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
```

## Advanced Remotion Features

### 1. Server-Side Rendering
- Full Node.js API support
- No browser required in production
- Scalable video generation

### 2. Cloud Rendering
- AWS Lambda integration (`@remotion/lambda`)
- Google Cloud Run support (`@remotion/cloudrun`)
- Automatic scaling

### 3. Real-time Preview
- Remotion Studio for development
- Live preview while coding
- Hot reload support

## Best Practices

### 1. Performance Optimization
```javascript
// Use concurrency for faster rendering
await renderMedia({
  composition,
  serveUrl,
  codec: 'h264',
  outputLocation,
  concurrency: '50%', // Use 50% of CPU cores
});
```

### 2. Memory Management
```javascript
// For large projects, use frame ranges
await renderMedia({
  composition,
  serveUrl,
  codec: 'h264',
  outputLocation,
  frameRange: [0, 300], // Render first 10 seconds only
});
```

### 3. Quality Control
```javascript
// Control video quality
await renderMedia({
  composition,
  serveUrl,
  codec: 'h264',
  outputLocation,
  crf: 18, // Lower = higher quality
  videoBitrate: '2M', // 2 Mbps
});
```

## Conclusion

Remotion provides a powerful alternative to traditional FFmpeg compose workflows, especially when you need:

- **Programmatic video generation**
- **Dynamic content integration**
- **Complex animations and effects**
- **Data-driven video creation**
- **Scalable video production APIs**

While FFmpeg excels at raw performance and simple operations, Remotion shines in scenarios requiring rich, dynamic, and programmatically controlled video content.

For your API, you can use Remotion's `renderMedia()` as the primary endpoint for creating any kind of video, with different compositions serving as templates for various video types.
