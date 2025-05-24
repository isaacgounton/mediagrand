# MoviePy Video Creation Service

## Overview
MoviePy is a Python library for video editing that allows you to create videos programmatically. This service replaces the previous Remotion-based video composition with a pure Python solution using MoviePy.

## Key Features

### 1. Core Video Rendering
- **Python-based composition** - No Node.js dependencies
- **Multiple video codecs** - H.264, H.265, WebM formats
- **Professional quality** - High-quality video output with FFmpeg
- **Memory efficient** - Optimized for server environments

### 2. Available Video Formats

MoviePy supports multiple output formats:

- **MP4 (H.264)** - Most common video format
- **MP4 (H.265)** - High efficiency video codec
- **WebM** - Web-optimized format
- **AVI** - Uncompressed format
- **MOV** - QuickTime format
- **GIF** - Animated GIF
- **Audio formats** - MP3, AAC, WAV

### 3. Video Creation Process

#### Step 1: Initialize MoviePy Renderer
```python
from services.v1.video.moviepy_composition import MoviePyRenderer

renderer = MoviePyRenderer()
```

#### Step 2: Prepare Video Assets
```python
# Background video, audio, and captions
video_path = "/path/to/background.mp4"
audio_path = "/path/to/speech.wav"
captions = [
    {"text": "Hello World", "start": 0.0, "end": 3.0},
    {"text": "Welcome to MoviePy", "start": 3.0, "end": 6.0}
]
```

#### Step 3: Configure and Render
```python
config = {
    "caption_position": "bottom",
    "caption_background_color": "#000000",
    "music_volume": "medium",
    "orientation": "portrait",
    "duration": 30,
    "music_url": "/path/to/music.mp3"
}

output_path = renderer.render_video(
    video_url=video_path,
    audio_url=audio_path,
    captions=captions,
    config=config,
    output_path="/path/to/output.mp4",
    orientation="portrait"
)
```

## MoviePy vs Remotion Comparison

| Feature | Remotion | MoviePy |
|---------|----------|---------|
| **Language** | JavaScript/React | Python |
| **Dependencies** | Node.js, Chrome | Python, FFmpeg |
| **Learning Curve** | React knowledge required | Python knowledge sufficient |
| **Server Resources** | High (Chrome headless) | Medium (Python + FFmpeg) |
| **Performance** | Good for complex animations | Excellent for programmatic editing |
| **Text Rendering** | HTML/CSS based | Font-based with styling |
| **Programmatic Control** | Full React API | Full Python API |
| **Memory Usage** | High | Medium |

## Migration Benefits

✅ **Advantages of MoviePy:**
- **Simplified deployment** - No Node.js or Chrome dependencies
- **Better server compatibility** - Pure Python stack
- **Lower memory usage** - More efficient for batch processing
- **Direct file access** - No need for HTTP serving during rendering
- **Familiar Python ecosystem** - Easier to debug and maintain
- **Built-in optimizations** - Efficient video processing

## Configuration Options

### Video Dimensions
- **Portrait**: 1080x1920 (9:16)
- **Landscape**: 1920x1080 (16:9)

### Caption Styles
- **Position**: top, center, bottom
- **Background**: Configurable color with transparency
- **Font**: Roboto, Arial, DejaVu Sans (with fallbacks)
- **Styling**: White text with black stroke for readability

### Audio
- **Speech volume**: 100% (primary audio)
- **Music volume options**:
  - High: 30%
  - Medium: 20%
  - Low: 10%
  - Muted: 0%

### Video Processing
- **Automatic cropping** - Maintains aspect ratio
- **Video looping** - Extends short videos to match audio duration
- **Quality optimization** - 30 FPS, H.264 codec
- **Audio sync** - Precise synchronization with captions

## API Integration

### Basic Usage
```python
from services.v1.video.moviepy_composition import MoviePyRenderer

def create_video(scenes, config, job_id):
    renderer = MoviePyRenderer()
    
    for scene in scenes:
        output_path = f"/tmp/output_{job_id}.mp4"
        
        renderer.render_video(
            video_url=scene["background_video"],
            audio_url=scene["audio_path"],
            captions=scene["captions"],
            config=config,
            output_path=output_path,
            orientation=config.get("orientation", "portrait")
        )
    
    return output_path
```

### Error Handling
```python
try:
    output_path = renderer.render_video(...)
    print(f"Video rendered successfully: {output_path}")
except Exception as e:
    print(f"Rendering failed: {str(e)}")
```

## Performance Optimization

### 1. Memory Management
```python
# MoviePy automatically handles memory cleanup
# Clips are closed after rendering to free resources
```

### 2. Processing Speed
```python
# Use appropriate video quality settings
renderer.render_video(
    ...,
    # Optimized settings applied automatically:
    # - 30 FPS for social media compatibility
    # - H.264 codec for best compression/quality ratio
    # - AAC audio codec for compatibility
)
```

### 3. Resource Usage
- **CPU**: Single-threaded video processing
- **Memory**: Efficient clip management
- **Disk**: Temporary files cleaned automatically

## Best Practices

### 1. File Management
- Use absolute file paths
- Ensure sufficient disk space for temporary files
- Clean up input files after successful rendering

### 2. Error Recovery
- Validate input files before processing
- Handle missing fonts gracefully
- Provide meaningful error messages

### 3. Quality Control
- Test with various video formats and durations
- Verify caption timing and positioning
- Check audio synchronization

## Troubleshooting

### Common Issues

1. **Font not found**
   ```
   Solution: Ensure font files exist in /workspaces/dahopevi/fonts/
   ```

2. **Video codec errors**
   ```
   Solution: Verify FFmpeg installation and codec support
   ```

3. **Memory errors with large videos**
   ```
   Solution: Process videos in smaller segments or reduce resolution
   ```

4. **Audio sync issues**
   ```
   Solution: Check audio file format and sample rate
   ```

## Migration Notes

The migration from Remotion to MoviePy includes:

- ✅ **Removed**: Node.js dependencies, Remotion packages, Chrome headless
- ✅ **Added**: MoviePy library, direct file processing
- ✅ **Maintained**: All video features (captions, music, orientation)
- ✅ **Improved**: Deployment simplicity, resource usage, debugging

## Conclusion

MoviePy provides a robust, Python-native solution for video composition that maintains all the features of the previous Remotion-based system while offering:

- **Simplified deployment** with fewer dependencies
- **Better resource efficiency** for server environments
- **Easier maintenance** within the existing Python codebase
- **Direct file processing** without HTTP serving overhead

The migration preserves all existing API functionality while improving the overall system architecture and maintainability.
