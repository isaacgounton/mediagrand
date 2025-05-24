const { bundle } = require('@remotion/bundler');
const { renderMedia, selectComposition } = require('@remotion/renderer');
const path = require('path');

// Bundle the video before rendering
async function bundleVideo() {
  const bundled = await bundle(path.join(__dirname, '../src/index.ts'), {
    port: 3000,
    publicPath: '/',
    enableCaching: false,
    logLevel: 'error',
    webpackOverride: (config) => {
      // Completely remove all plugins and add only essential ones
      const essentialPlugins = [];
      
      if (config.plugins) {
        config.plugins.forEach(plugin => {
          const name = plugin.constructor.name;
          // Keep only essential plugins, exclude all progress-related ones
          if (name !== 'ProgressPlugin' && 
              name !== 'webpack.ProgressPlugin' &&
              !name.includes('Progress')) {
            essentialPlugins.push(plugin);
          }
        });
      }
      
      config.plugins = essentialPlugins;
      
      // Disable all progress and logging
      config.stats = false;
      config.infrastructureLogging = { level: 'silent' };
      
      return config;
    },
    // Disable progress callback entirely
    onProgress: undefined,
    onBrowserLog: () => {},
    onDownload: () => {}
  });
  return bundled;
}

// Render the video with the provided props
async function renderVideo(props, output) {
  try {
    // Bundle the video first
    const bundled = await bundleVideo();

    // Get composition based on orientation
    const compositionId = props.config.orientation === 'portrait' ? 'PortraitVideo' : 'LandscapeVideo';
    const composition = await selectComposition({
      serveUrl: bundled.url,
      id: compositionId || 'PortraitVideo',
      inputProps: props
    });

    // Use provided duration or fallback to 30 seconds
    const duration = props.config?.duration || 30;
    const durationInFrames = Math.ceil(duration * composition.fps);

    // Start the rendering
    await renderMedia({
      codec: 'h264',
      composition,
      serveUrl: bundled.url,
      outputLocation: output,
      inputProps: props,
      durationInFrames,
      fps: composition.fps,
      chromiumOptions: {
        enableWebSecurity: false,
        disableHTTPCache: true,
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
