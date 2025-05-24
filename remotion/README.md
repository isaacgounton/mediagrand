# Video Composition with Remotion

This directory contains the Remotion components for creating professional-quality videos with dynamic captions, background videos, and music.

## Development

1. Install dependencies:
```bash
bash init.sh
```

2. Start the preview server:
```bash
npm run preview
```

3. Make changes to components in `src/components/`:
- `PortraitVideo.tsx` - Vertical video composition (9:16)
- `LandscapeVideo.tsx` - Horizontal video composition (16:9)

## Testing

1. Run the test render:
```bash
npm run test:render
```

This will create a test video with:
- Sample background video
- Test captions
- Audio track
- All visual elements

The test output will be saved as `test-output.mp4`.

## Architecture

### Components
- `PortraitVideo` - Vertical video composition (9:16)
- `LandscapeVideo` - Horizontal video composition (16:9)
- `Composition` - Main composition registration

### Script Files
- `render.js` - Main rendering script
- `test-render.js` - Test rendering script

### Configuration
- `tsconfig.json` - TypeScript configuration
- `.eslintrc.js` - ESLint rules
- `package.json` - Dependencies and scripts

## Integration with Main App

The Remotion components are called from:
- `services/v1/video/video_composition.py`
- `services/v1/video/short_video_create.py`

## Available Scripts

- `npm run preview` - Start preview server
- `npm run test:render` - Run test render
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run clean` - Clean build artifacts
- `npm run upgrade` - Upgrade Remotion packages

## Troubleshooting

1. If the render fails with memory issues:
   ```bash
   NODE_OPTIONS="--max-old-space-size=8192" npm run render
   ```

2. For Chromium issues:
   ```bash
   PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true npm install
   ```

3. For ESLint/TypeScript errors:
   ```bash
   npm run lint -- --fix
   ```

## Configuration Options

### Video Dimensions
- Portrait: 1080x1920 (9:16)
- Landscape: 1920x1080 (16:9)

### Caption Styles
- Position: top, center, bottom
- Background opacity: 50%
- Font: Inter (Google Fonts)
- Shadow: 2px offset, 50% opacity

### Audio
- Speech volume: 100%
- Music volume options:
  - High: 30%
  - Medium: 20%
  - Low: 10%
  - Muted: 0%

## Contributing

1. Create a new branch
2. Make changes
3. Test with `npm run test:render`
4. Submit PR

## License

See main project license
