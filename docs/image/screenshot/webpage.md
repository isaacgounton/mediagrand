# /v1/image/screenshot/webpage

Take a screenshot of a webpage using Playwright.

## Request

**Method:** `POST`  
**Endpoint:** `/v1/image/screenshot/webpage`  
**Content-Type:** `application/json`

### Headers

| Header | Value | Required |
|--------|-------|----------|
| `x-api-key` | Your API key | Yes |

### Request Body

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string (uri) | Yes* | - | URL of the webpage to screenshot |
| `html` | string | Yes* | - | HTML content to render (alternative to url) |
| `viewport_width` | integer | No | 1280 | Browser viewport width |
| `viewport_height` | integer | No | 720 | Browser viewport height |
| `full_page` | boolean | No | false | Whether to capture the full page |
| `format` | string | No | "png" | Image format ("png" or "jpeg") |
| `delay` | integer | No | 0 | Delay in milliseconds before taking screenshot |
| `device_scale_factor` | number | No | 1.0 | Device pixel ratio |
| `user_agent` | string | No | - | Custom user agent string |
| `cookies` | array | No | - | Array of cookie objects |
| `headers` | object | No | - | Additional HTTP headers |
| `quality` | integer | No | - | JPEG quality (1-100, only for JPEG format) |
| `clip` | object | No | - | Specific area to capture |
| `timeout` | integer | No | 30000 | Navigation timeout in milliseconds |
| `wait_until` | string | No | "load" | When to consider navigation complete |
| `wait_for_selector` | string | No | - | CSS selector to wait for |
| `emulate` | object | No | - | Media emulation options |
| `omit_background` | boolean | No | false | Make background transparent (PNG only) |
| `selector` | string | No | - | Take screenshot of specific element |
| `js` | string | No | - | JavaScript code to inject |
| `css` | string | No | - | CSS code to inject |
| `webhook_url` | string (uri) | No | - | Webhook URL for async processing |
| `id` | string | No | - | Custom job identifier |

*Either `url` or `html` is required, but not both.

### Cookie Object Structure

```json
{
  "name": "session_id",
  "value": "abc123",
  "domain": "example.com",
  "path": "/"
}
```

### Clip Object Structure

```json
{
  "x": 0,
  "y": 0,
  "width": 800,
  "height": 600
}
```

### Emulate Object Structure

```json
{
  "color_scheme": "dark"
}
```

## Response

### Success Response (200)

Returns the URL of the uploaded screenshot.

```json
"https://cloud-storage.example.com/screenshot_12345.png"
```

### Error Response (400)

```json
{
  "error": "The selector '.non-existent' was not found on the page. Please check your selector."
}
```

## Examples

### Basic Screenshot

```json
{
  "url": "https://example.com"
}
```

### Full Page Screenshot with Custom Viewport

```json
{
  "url": "https://example.com",
  "full_page": true,
  "viewport_width": 1920,
  "viewport_height": 1080
}
```

### Screenshot with Custom CSS and JavaScript

```json
{
  "url": "https://example.com",
  "css": "body { background-color: red !important; }",
  "js": "document.querySelector('h1').style.color = 'blue';"
}
```

### Screenshot with Authentication Cookies

```json
{
  "url": "https://private-site.com/dashboard",
  "cookies": [
    {
      "name": "session_token",
      "value": "your-token-here",
      "domain": "private-site.com",
      "path": "/"
    }
  ]
}
```

### Screenshot of HTML Content

```json
{
  "html": "<html><body><h1>Hello World</h1></body></html>",
  "viewport_width": 800,
  "viewport_height": 600
}
```

### Screenshot of Specific Element

```json
{
  "url": "https://example.com",
  "selector": ".main-content",
  "format": "jpeg",
  "quality": 90
}
```

## Error Handling

Common error messages:

- `"You must provide either a 'url' or 'html' field."` - Missing required parameter
- `"The selector '.example' was not found on the page."` - Invalid CSS selector
- `"'quality' is not supported for PNG format."` - Quality parameter only works with JPEG
- `"'omit_background' is only supported for PNG format."` - Background transparency only for PNG
- `"Clip dimensions must be positive and non-negative."` - Invalid clip coordinates

## Notes

- Playwright must be installed for this endpoint to work
- Screenshots are uploaded to your configured cloud storage
- The endpoint supports both synchronous and asynchronous processing via webhooks
- For performance, consider using smaller viewport sizes when full-page screenshots aren't needed
- JPEG format supports quality settings but not transparency
- PNG format supports transparency but not quality settings