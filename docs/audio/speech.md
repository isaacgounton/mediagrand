# Text-to-Speech Service

The text-to-speech service provides speech synthesis by utilizing a remote TTS API server. It supports multiple TTS engines, voices, and formats.

## Configuration

Set the TTS server URL in your environment:
```env
TTS_SERVER_URL=https://tts.dahopevi.com/api
```

## API Endpoints

### Generate Speech
`POST /v1/audio/speech`

Convert text to speech using the specified parameters.

**Request Body:**
```json
{
    "text": "Text to convert to speech",
    "voice": "optional_voice_id",
    "tts": "optional_engine_name",
    "rate": "optional_rate_adjustment",
    "volume": "optional_volume_adjustment",
    "pitch": "optional_pitch_adjustment",
    "output_format": "mp3",
    "subtitle_format": "srt"
}
```

**Parameters:**
- `text` (required): The text to convert to speech
- `voice` (optional): Voice ID to use
- `tts` (optional): TTS engine to use (defaults to "kokoro")
- `rate` (optional): Speech rate adjustment (e.g., "+50%", "-20%")
- `volume` (optional): Volume adjustment
- `pitch` (optional): Pitch adjustment
- `output_format` (optional): Audio output format (mp3, wav, ogg)
- `subtitle_format` (optional): Subtitle format (srt, vtt)

**Response:**
```json
{
    "audio_url": "https://storage.example.com/path/to/audio.mp3",
    "subtitle_url": "https://storage.example.com/path/to/subtitles.srt",
    "engine": "used_tts_engine",
    "voice": "used_voice",
    "format": "mp3"
}
```

### List Voices
`GET /v1/audio/speech/voices`

Get a list of available voices from the TTS server.

**Query Parameters:**
- `language` (optional): Filter voices by language code
- `engine` (optional): Filter voices by TTS engine

### List Engines
`GET /v1/audio/speech/engines`

Get a list of available TTS engines.

### Health Check
`GET /v1/audio/speech/health`

Check the health status of the TTS service.

## Examples

### Generate Speech
```python
import requests

response = requests.post("http://your-server/v1/audio/speech", json={
    "text": "Hello, world!",
    "voice": "en-US-neural",
    "output_format": "mp3"
})

if response.ok:
    result = response.json()
    print(f"Audio URL: {result['audio_url']}")
    print(f"Subtitle URL: {result['subtitle_url']}")
```

### List Available Voices
```python
response = requests.get("http://your-server/v1/audio/speech/voices")
if response.ok:
    voices = response.json()['voices']
    for voice in voices:
        print(f"Voice: {voice['name']} ({voice['id']})")
