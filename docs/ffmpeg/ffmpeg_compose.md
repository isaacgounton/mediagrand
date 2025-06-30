# FFmpeg Compose API Endpoint

## 1. Overview

The `/v1/ffmpeg/compose` endpoint is a flexible and powerful API that allows users to compose complex FFmpeg commands by providing input files, filters, and output options. This endpoint is part of the version 1.0 API structure, as shown in the `app.py` file. It is designed to handle various media processing tasks, such as video and audio manipulation, transcoding, and more.

## 2. Endpoint

**URL Path:** `/v1/ffmpeg/compose`
**HTTP Method:** `POST`

## 3. Request

### Headers

- `x-api-key` (required): The API key for authentication.

### Body Parameters

The request body should be a JSON object with the following properties:

- `inputs` (required, array): An array of input file objects, each containing:
  - `file_url` (required, string): The URL of the input file.
  - `options` (optional, array): An array of option objects, each containing:
    - `option` (required, string): The FFmpeg option.
    - `argument` (optional, string, number, or null): The argument for the option.
- `stream_mappings` (optional, array): An array of global stream mappings that apply to all outputs (e.g., ["0:v:0", "1:a:0"]).
- `filters` (optional, array): An array of filter objects, each containing:
  - `filter` (required, string): The FFmpeg filter.
  - `arguments` (optional, array): An array of filter arguments.
  - `input_labels` (optional, array): An array of input stream labels.
  - `output_label` (optional, string): Output label for this filter.
  - `type` (optional, string): Filter type - "video" or "audio" (used for simple filters).
- `use_simple_video_filter` (optional, boolean): Use `-vf` for video filters instead of complex filter graph.
- `use_simple_audio_filter` (optional, boolean): Use `-af` for audio filters instead of complex filter graph.
- `outputs` (required, array): An array of output option objects, each containing:
  - `options` (required, array): An array of option objects, each containing:
    - `option` (required, string): The FFmpeg option.
    - `argument` (optional, string, number, or null): The argument for the option.
  - `stream_mappings` (optional, array): An array of stream mappings specific to this output.
- `global_options` (optional, array): An array of global option objects, each containing:
  - `option` (required, string): The FFmpeg global option.
  - `argument` (optional, string, number, or null): The argument for the option.
- `metadata` (optional, object): An object specifying which metadata to include in the response, with the following properties:
  - `thumbnail` (optional, boolean): Whether to include a thumbnail for the output file.
  - `filesize` (optional, boolean): Whether to include the file size of the output file.
  - `duration` (optional, boolean): Whether to include the duration of the output file.
  - `bitrate` (optional, boolean): Whether to include the bitrate of the output file.
  - `encoder` (optional, boolean): Whether to include the encoder used for the output file.
- `webhook_url` (required, string): The URL to send the response webhook.
- `id` (required, string): A unique identifier for the request.

### Example Request

```json
{
  "inputs": [
    {
      "file_url": "https://example.com/video1.mp4",
      "options": [
        {
          "option": "-ss",
          "argument": 10
        },
        {
          "option": "-t",
          "argument": 20
        }
      ]
    },
    {
      "file_url": "https://example.com/video2.mp4"
    }
  ],
  "filters": [
    {
      "filter": "hflip"
    }
  ],
  "outputs": [
    {
      "options": [
        {
          "option": "-c:v",
          "argument": "libx264"
        },
        {
          "option": "-crf",
          "argument": 23
        }
      ]
    }
  ],
  "global_options": [
    {
      "option": "-y"
    }
  ],
  "metadata": {
    "thumbnail": true,
    "filesize": true,
    "duration": true,
    "bitrate": true,
    "encoder": true
  },
  "webhook_url": "https://example.com/webhook",
  "id": "unique-request-id"
}
```

### Stream Mapping Examples

#### Basic Stream Mapping
```json
{
  "inputs": [
    {"file_url": "https://example.com/video.mp4"},
    {"file_url": "https://example.com/audio.mp3"}
  ],
  "stream_mappings": ["0:v:0", "1:a:0"],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"}
      ]
    }
  ],
  "webhook_url": "https://example.com/webhook",
  "id": "stream-mapping-example"
}
```

#### Per-Output Stream Mapping
```json
{
  "inputs": [
    {"file_url": "https://example.com/video1.mp4"},
    {"file_url": "https://example.com/video2.mp4"}
  ],
  "outputs": [
    {
      "options": [{"option": "-c:v", "argument": "libx264"}],
      "stream_mappings": ["0:v:0", "0:a:0"]
    },
    {
      "options": [{"option": "-c:v", "argument": "libx265"}],
      "stream_mappings": ["1:v:0", "1:a:0"]
    }
  ],
  "webhook_url": "https://example.com/webhook",
  "id": "per-output-mapping"
}
```

#### Simple Filter Example
```json
{
  "inputs": [
    {"file_url": "https://example.com/input.mp4"}
  ],
  "filters": [
    {
      "filter": "scale",
      "arguments": ["1280", "720"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true,
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"}
      ]
    }
  ],
  "webhook_url": "https://example.com/webhook",
  "id": "simple-filter-example"
}
```

```bash
curl -X POST \
  https://api.example.com/v1/ffmpeg/compose \
  -H 'x-api-key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": [
      {
        "file_url": "https://example.com/video1.mp4",
        "options": [
          {
            "option": "-ss",
            "argument": 10
          },
          {
            "option": "-t",
            "argument": 20
          }
        ]
      },
      {
        "file_url": "https://example.com/video2.mp4"
      }
    ],
    "stream_mappings": [
      "0:v:0",
      "1:a:0"
    ],
    "filters": [
      {
        "filter": "scale",
        "arguments": ["1920", "1080"],
        "input_labels": ["0:v"],
        "output_label": "scaled",
        "type": "video"
      }
    ],
    "outputs": [
      {
        "options": [
          {
            "option": "-c:v",
            "argument": "libx264"
          },
          {
            "option": "-crf",
            "argument": 23
          }
        ],
        "stream_mappings": ["[scaled]", "0:a"]
      }
    ],
    "global_options": [
      {
        "option": "-y"
      }
    ],
    "metadata": {
      "thumbnail": true,
      "filesize": true,
      "duration": true,
      "bitrate": true,
      "encoder": true
    },
    "webhook_url": "https://example.com/webhook",
    "id": "unique-request-id"
  }'
```

## 4. Response

### Success Response

The response will be sent to the specified `webhook_url` as a JSON object with the following properties:

- `endpoint` (string): The endpoint URL (`/v1/ffmpeg/compose`).
- `code` (number): The HTTP status code (200 for success).
- `id` (string): The unique identifier for the request.
- `job_id` (string): The unique job ID assigned to the request.
- `response` (array): An array of output file objects, each containing:
  - `file_url` (string): The URL of the uploaded output file.
  - `thumbnail_url` (string, optional): The URL of the uploaded thumbnail, if requested.
  - `filesize` (number, optional): The file size of the output file, if requested.
  - `duration` (number, optional): The duration of the output file, if requested.
  - `bitrate` (number, optional): The bitrate of the output file, if requested.
  - `encoder` (string, optional): The encoder used for the output file, if requested.
- `message` (string): The success message ("success").
- `pid` (number): The process ID of the worker that processed the request.
- `queue_id` (number): The ID of the queue used for processing the request.
- `run_time` (number): The time taken to process the request (in seconds).
- `queue_time` (number): The time the request spent in the queue (in seconds).
- `total_time` (number): The total time taken to process the request, including queue time (in seconds).
- `queue_length` (number): The current length of the processing queue.
- `build_number` (string): The build number of the application.

### Error Responses

- **400 Bad Request**: The request payload is invalid or missing required parameters.
- **401 Unauthorized**: The provided API key is invalid or missing.
- **429 Too Many Requests**: The maximum queue length has been reached.
- **500 Internal Server Error**: An unexpected error occurred while processing the request.

Example error response:

```json
{
  "code": 400,
  "id": "unique-request-id",
  "job_id": "job-id",
  "message": "Invalid request payload: 'inputs' is a required property",
  "pid": 123,
  "queue_id": 456,
  "queue_length": 0,
  "build_number": "1.0.0"
}
```

## 5. Error Handling

The API handles various types of errors, including:

- **Missing or invalid parameters**: If the request payload is missing required parameters or contains invalid data types, a 400 Bad Request error will be returned.
- **Authentication failure**: If the provided API key is invalid or missing, a 401 Unauthorized error will be returned.
- **Queue limit reached**: If the maximum queue length is reached, a 429 Too Many Requests error will be returned.
- **Unexpected errors**: If an unexpected error occurs during request processing, a 500 Internal Server Error will be returned.

The main application context (`app.py`) includes error handling for the processing queue. If the maximum queue length is set and the queue size reaches that limit, new requests will be rejected with a 429 Too Many Requests error.

## 6. Usage Notes

- The `inputs` array must contain at least one input file object.
- The `outputs` array must contain at least one output option object.
- The `filters` array is optional and can be used to apply FFmpeg filters to the input files.
- The `global_options` array is optional and can be used to specify global FFmpeg options.
- The `stream_mappings` array is optional and provides global stream mapping for all outputs.
- Per-output `stream_mappings` override global mappings for specific outputs.
- Use `use_simple_video_filter` or `use_simple_audio_filter` flags to apply filters as `-vf` or `-af` instead of complex filter graphs.
- The `metadata` object is optional and can be used to request specific metadata for the output files.
- The `webhook_url` parameter is required and specifies the URL where the response should be sent.
- The `id` parameter is required and should be a unique identifier for the request.

### Stream Mapping Syntax

- `"0:v:0"` - First video stream from first input (input index 0)
- `"1:a:0"` - First audio stream from second input (input index 1)
- `"0:v"` - All video streams from first input
- `"0:a"` - All audio streams from first input
- `"[labelname]"` - Output from a filter with specific label

### New Features

#### Stream Mapping Support
- **Global Mappings**: Apply to all outputs using `stream_mappings` array
- **Per-Output Mappings**: Override global mappings for specific outputs using `stream_mappings` in output objects
- **Complex Stream Selection**: Support for `0:v:0`, `1:a:0`, `[label]` syntax

#### Simple Filter Support
- **Video Filters**: Use `-vf` for simple video filters when `use_simple_video_filter` is true
- **Audio Filters**: Use `-af` for simple audio filters when `use_simple_audio_filter` is true
- **Filter Types**: Specify `"type": "video"` or `"type": "audio"` on filter objects

#### Extended Format Support
- **Video Codecs**: h264, h265, hevc → libx264, libx265
- **Audio Codecs**: opus → libopus, m4a → aac
- **Modern Formats**: Support for latest codec standards

## 7. Common Issues

- Providing invalid or malformed input file URLs.
- Specifying invalid or unsupported FFmpeg options or filters.
- Reaching the maximum queue length, resulting in a 429 Too Many Requests error.
- Network or connectivity issues that prevent the response webhook from being delivered.

## 8. Best Practices

- Validate input file URLs and ensure they are accessible before sending the request.
- Test your FFmpeg command locally before using the API to ensure it works as expected.
- Monitor the queue length and adjust the maximum queue length as needed to prevent overloading the system.
- Implement retry mechanisms for handling failed webhook deliveries or other transient errors.
- Use unique and descriptive `id` values for each request to aid in troubleshooting and monitoring.
