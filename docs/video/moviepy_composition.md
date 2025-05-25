# MoviePy Composition System

## Overview

This module provides two ways to use MoviePy for video creation:

1. **Standard MoviePy Renderer** (`MoviePyRenderer` class)
   - Simplified API for common video creation needs
   - Support for optional captions/subtitles
   - Person image overlays
   - Background music

2. **Flexible MoviePy Composer** (`MoviePyComposer` class)
   - Fully customizable video composition
   - Similar to FFmpeg compose but using MoviePy's capabilities
   - Support for complex layouts and animations

## Making Captions Optional

The standard renderer now supports optional captions. To disable captions, include `"show_captions": false` in the config object:

```json
{
  "config": {
    "caption_position": "bottom",
    "caption_background_color": "#000000",
    "show_captions": false,
    "orientation": "portrait"
  }
}
```

Even if captions are provided in the API call, they will be ignored if `show_captions` is set to `false`.

## MoviePy Composer API

The new `/v1/video/moviepy/compose` endpoint allows for creating custom video compositions with MoviePy. This provides similar flexibility to the FFmpeg compose endpoint but using MoviePy's capabilities.

### Request Format

```json
{
  "composition": {
    "type": "composite",
    "orientation": "landscape",
    "clips": [
      {
        "type": "video",
        "path": "https://example.com/video.mp4",
        "position": "center"
      },
      {
        "type": "text",
        "text": "Hello World",
        "font_size": 36,
        "position": ["center", "bottom"]
      }
    ],
    "audio": {
      "path": "https://example.com/audio.mp3",
      "volume": 0.8
    },
    "fps": 30,
    "codec": "libx264"
  }
}
```

### Clip Types

The composer supports the following clip types:

1. **Video Clips**
   ```json
   {
     "type": "video",
     "path": "https://example.com/video.mp4",
     "start_time": 10,
     "end_time": 20,
     "position": "center"
   }
   ```

2. **Audio Clips**
   ```json
   {
     "type": "audio",
     "path": "https://example.com/audio.mp3",
     "volume": 0.8,
     "start_time": 0,
     "end_time": 30
   }
   ```

3. **Text Clips**
   ```json
   {
     "type": "text",
     "text": "Hello World",
     "font_size": 36,
     "color": "white",
     "stroke_color": "black",
     "stroke_width": 2,
     "bg_color": "rgba(0,0,0,0.5)",
     "position": ["center", "bottom"],
     "start_time": 1,
     "end_time": 5
   }
   ```

4. **Image Clips**
   ```json
   {
     "type": "image",
     "path": "https://example.com/image.jpg",
     "position": "center",
     "duration": 5,
     "width": 640,
     "height": 360
   }
   ```

5. **Color Clips**
   ```json
   {
     "type": "color",
     "color": "black",
     "width": 1920,
     "height": 1080,
     "duration": 10
   }
   ```

6. **Composite Clips** (for complex compositions)
   ```json
   {
     "type": "composite",
     "orientation": "landscape",
     "clips": [
       { "type": "video", "path": "..." },
       { "type": "text", "text": "..." }
     ]
   }
   ```

### Common Clip Properties

These properties can be applied to most clip types:

- `position`: Position in the video frame (e.g., "center", "top", [x, y])
- `duration`: Duration in seconds
- `start_time`/`end_time`: Start and end times for subclips
- `width`/`height`: Dimensions for resizing
- `opacity`: Transparency (0.0 to 1.0)
- `rotation`: Rotation angle in degrees

### Example Use Cases

1. **Picture-in-Picture**
   ```json
   {
     "type": "composite",
     "orientation": "landscape",
     "clips": [
       {
         "type": "video",
         "path": "https://example.com/background.mp4"
       },
       {
         "type": "video",
         "path": "https://example.com/overlay.mp4",
         "width": 480,
         "height": 270,
         "position": [20, 20]
       }
     ]
   }
   ```

2. **Slideshow**
   ```json
   {
     "type": "composite",
     "orientation": "landscape",
     "clips": [
       {
         "type": "color",
         "color": "black",
         "duration": 15
       },
       {
         "type": "image",
         "path": "https://example.com/image1.jpg",
         "position": "center",
         "duration": 5,
         "start_time": 0
       },
       {
         "type": "image",
         "path": "https://example.com/image2.jpg",
         "position": "center",
         "duration": 5,
         "start_time": 5
       },
       {
         "type": "image",
         "path": "https://example.com/image3.jpg",
         "position": "center",
         "duration": 5,
         "start_time": 10
       }
     ],
     "audio": {
       "path": "https://example.com/music.mp3",
       "volume": 0.7
     }
   }
   ```

## Getting Example Compositions

You can retrieve example compositions by sending a GET request to:

```
GET /v1/video/moviepy/compose/examples
```

This will return a set of example compositions that you can use as starting points for your own compositions.