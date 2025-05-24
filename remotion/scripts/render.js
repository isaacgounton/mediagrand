const { bundle } = require('@remotion/bundler');
const { renderMedia, selectComposition } = require('@remotion/renderer');
const path = require('path');

// Global bundled URL cache
let bundledUrl = null;

// Bundle the video once and reuse
async function getBundledUrl() {
  if (!bundledUrl) {
    console.log('Bundling Remotion code...');
    const bundled = await bundle({
      entryPoint: path.join(__dirname, '../src/index.ts')
    });
    bundledUrl = bundled;
    console.log('Bundling completed successfully');
  }
  return bundledUrl;
}

// Render the video with the provided props
async function renderVideo(props, output) {
  try {
    // Get the bundled URL (will bundle on first call, reuse afterwards)
    const bundledUrl = await getBundledUrl();

    // Get composition based on orientation
    const compositionId = props.config.orientation === 'portrait' ? 'PortraitVideo' : 'LandscapeVideo';
    const composition = await selectComposition({
      serveUrl: bundledUrl,
      id: compositionId || 'PortraitVideo',
      inputProps: props
    });

    // Use provided duration or fallback to 30 seconds
    const duration = props.config?.duration || 30;
    const durationInFrames = Math.ceil(duration * composition.fps);

    // Start the rendering with proper progress callback
    await renderMedia({
      codec: 'h264',
      composition,
      serveUrl: bundledUrl,
      outputLocation: output,
      inputProps: props,
      durationInFrames,
      fps: composition.fps,
      onProgress: ({ progress }) => {
        console.log(`Rendering progress: ${Math.floor(progress * 100)}%`);
      },
      chromiumOptions: {
        enableWebSecurity: false,
        disableHTTPCache: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu',
          '--disable-background-timer-throttling',
          '--disable-backgrounding-occluded-windows',
          '--disable-renderer-backgrounding',
          '--allow-file-access-from-files',
          '--disable-web-security',
          '--allow-running-insecure-content'
        ]
      },
    });

    console.log('Rendering completed successfully');
    return { success: true };
  } catch (error) {
    console.error('Error rendering video:', error);
    throw error;
  }
}

// Handle command line arguments
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error('Usage: node render.js <props_file> <output_path>');
    process.exit(1);
  }

  const propsFile = args[0];
  const outputPath = args[1];

  // Read props from file
  const props = require(propsFile);

  // Start rendering
  renderVideo(props, outputPath)
    .then(() => {
      console.log('Video rendering completed');
      process.exit(0);
    })
    .catch((error) => {
      console.error('Video rendering failed:', error);
      process.exit(1);
    });
} else {
  module.exports = { renderVideo };
}
