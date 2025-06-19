# Video Merge Debugging Guide

## Issue Analysis

Based on your error "FFmpeg failed to merge videos", here are the potential causes and solutions:

## 1. **Most Likely Issues**

### A. File Download Problems
The URLs you're using:
- `https://cdn.pixabay.com/video/2025/03/29/268528_large.mp4`
- `https://cdn.pixabay.com/video/2024/09/21/232538_large.mp4`
- `https://minio-oc0cgw4g48oogwsks8soc4wo.etugrand.com/dahopevi/background_music.mp3`

**Potential Issues:**
- Network connectivity to Pixabay or your Minio server
- File permissions or authentication requirements
- Large file sizes causing timeout

### B. FFmpeg Dependencies
- Ensure FFmpeg is properly installed in your Docker container
- Verify ffmpeg-python library is working correctly

### C. Audio Codec Issues
- Background music file format might not be compatible
- Audio mixing parameters might be incorrect

## 2. **Debugging Steps**

### Step 1: Test Without Background Music
Try this simplified request first:

```json
{
  "video_urls": [
    "https://cdn.pixabay.com/video/2025/03/29/268528_large.mp4",
    "https://cdn.pixabay.com/video/2024/09/21/232538_large.mp4"
  ],
  "id": "merge-test-simple"
}
```

### Step 2: Test Single Video
Try with just one video:

```json
{
  "video_urls": [
    "https://cdn.pixabay.com/video/2025/03/29/268528_large.mp4"
  ],
  "id": "merge-test-single"
}
```

### Step 3: Check File Accessibility
Test if the files are accessible from your server:

```bash
# From inside your container
curl -I "https://cdn.pixabay.com/video/2025/03/29/268528_large.mp4"
curl -I "https://cdn.pixabay.com/video/2024/09/21/232538_large.mp4"
curl -I "https://minio-oc0cgw4g48oogwsks8soc4wo.etugrand.com/dahopevi/background_music.mp3"
```

## 3. **Enhanced Error Reporting**

The current implementation should provide better error messages now. Look for:

1. **Download errors**: Check if video files are downloading successfully
2. **FFmpeg errors**: Look for specific FFmpeg error messages in logs
3. **File format issues**: Verify video and audio formats are supported

## 4. **Alternative Test Files**

If the Pixabay URLs are problematic, try with smaller, more reliable test files:

```json
{
  "video_urls": [
    "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
    "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4"
  ],
  "background_music_url": "https://sample-videos.com/zip/10/mp3/SampleAudio_0.4mb.mp3",
  "background_music_volume": 0.3,
  "id": "merge-test-samples"
}
```

## 5. **Code Improvements Made**

1. **Better Error Handling**: Added specific FFmpeg error capture
2. **Logging**: Enhanced logging throughout the process
3. **File Cleanup**: Proper cleanup of temporary files
4. **Pattern Match**: Used same pattern as working concatenate service

## 6. **Log Analysis**

Look for these log patterns:
- `"Starting video merge for X videos"`
- `"Background music file: ..."`
- `"Merging videos with/without background music"`
- `"FFmpeg error during merge: ..."`

## 7. **Container Verification**

Verify your container has:
```bash
# Check FFmpeg installation
ffmpeg -version
ffprobe -version

# Check Python packages
pip list | grep ffmpeg
```

## 8. **Next Steps**

1. Try the simplified requests above
2. Check your application logs for detailed error messages
3. Verify file accessibility
4. Test with smaller, simpler files first
5. If issues persist, check container resources (disk space, memory)

## 9. **Working Test Command**

Once basic functionality works, this should be your target:

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "video_urls": [
      "https://cdn.pixabay.com/video/2025/03/29/268528_large.mp4",
      "https://cdn.pixabay.com/video/2024/09/21/232538_large.mp4"
    ],
    "background_music_url": "https://minio-oc0cgw4g48oogwsks8soc4wo.etugrand.com/dahopevi/background_music.mp3",
    "background_music_volume": 0.3,
    "id": "merge-request-123"
  }' \
  https://api.dahopevi.com/v1/video/merge
```

The implementation should now work correctly with proper error reporting.