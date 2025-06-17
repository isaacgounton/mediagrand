# Text-to-Speech Service

The text-to-speech service provides speech synthesis by utilizing the Awesome-TTS API gateway. It supports multiple TTS providers including Kokoro ONNX, Chatterbox TTS, and OpenAI Edge TTS.

## Configuration

Set the Awesome-TTS server URL in your environment:
```env
TTS_SERVER_URL=https://tts.dahopevi.com
```

## Supported Providers

| Provider | Description | Features |
|----------|-------------|----------|
| `kokoro` | Kokoro ONNX | High-quality neural TTS with multi-language support |
| `chatterbox` | Chatterbox TTS | Voice cloning capabilities with reference audio |
| `openai-edge-tts` | OpenAI Edge TTS | Microsoft Edge TTS backend with extensive voice catalog |

## API Endpoints

### Generate Speech
`POST /v1/audio/speech`

Convert text to speech using the specified provider and parameters.

**Request Body:**
```json
{
    "text": "Text to convert to speech",
    "provider": "kokoro",
    "voice": "optional_voice_id",
    "speed": 1.0,
    "pitch": "optional_pitch_adjustment",
    "output_format": "mp3",
    "subtitle_format": "srt"
}
```

**Parameters:**
- `text` (required): The text to convert to speech
- `provider` (optional): TTS provider to use: `kokoro`, `chatterbox`, or `openai-edge-tts` (defaults to "kokoro")
- `tts` (optional): Alias for `provider` (for backward compatibility)
- `voice` (optional): Voice ID to use (provider-specific)
- `speed` (optional): Speech speed multiplier (0.5 - 2.0, default: 1.0)
- `rate` (optional): Speech rate adjustment (e.g., "+50%", "-20%") - converted to speed
- `pitch` (optional): Pitch adjustment (provider-dependent)
- `output_format` (optional): Audio output format (mp3, wav, default: mp3)
- `subtitle_format` (optional): Subtitle format (srt, vtt, default: srt)

**Response:**
```json
{
    "audio_url": "https://storage.example.com/path/to/audio.mp3",
    "subtitle_url": "https://storage.example.com/path/to/subtitles.srt",
    "engine": "kokoro",
    "provider": "kokoro",
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

### Generate Speech with Kokoro ONNX
```python
import requests

response = requests.post("http://your-server/v1/audio/speech", json={
    "text": "Hello, this is Awesome-TTS speaking!",
    "provider": "kokoro",
    "voice": "af_heart",
    "speed": 1.2,
    "output_format": "mp3"
})

if response.ok:
    result = response.json()
    print(f"Audio URL: {result['audio_url']}")
    print(f"Subtitle URL: {result['subtitle_url']}")
    print(f"Provider: {result['provider']}")
```

### Generate Speech with Chatterbox TTS
```python
response = requests.post("http://your-server/v1/audio/speech", json={
    "text": "This is voice cloning in action!",
    "provider": "chatterbox",
    "voice": "your_custom_voice",
    "speed": 1.0,
    "output_format": "wav"
})
```

### Generate Speech with OpenAI Edge TTS
```python
response = requests.post("http://your-server/v1/audio/speech", json={
    "text": "Microsoft Edge TTS has many voices!",
    "provider": "openai-edge-tts",
    "voice": "en-US-AriaNeural",
    "speed": 0.9,
    "output_format": "mp3"
})
```

### List Available Voices
```python
response = requests.get("http://your-server/v1/audio/speech/voices")
if response.ok:
    voices = response.json()['voices']
    for voice in voices:
        print(f"Voice: {voice.get('name', voice.get('id'))} (Provider: {voice.get('provider')})")
```

### List Available Providers
```python
response = requests.get("http://your-server/v1/audio/speech/engines")
if response.ok:
    engines = response.json()['engines']
    for engine in engines:
        print(f"Provider: {engine['id']} - {engine['name']}")
        print(f"Description: {engine['description']}")
```

### Check Service Health
```python
response = requests.get("http://your-server/v1/audio/speech/health")
if response.ok:
    health = response.json()
    print(f"Service Status: {'Available' if health.get('available') else 'Unavailable'}")
```
