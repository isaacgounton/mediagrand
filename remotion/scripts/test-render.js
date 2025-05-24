const path = require('path');
const { renderVideo } = require('./render');

// Test video properties
const testProps = {
  videoUrl: 'https://player.vimeo.com/external/291648067.hd.mp4?s=94bb1e4c0536247eb02a3475c76e7bfab8d27bf8&profile_id=175&oauth2_token_id=57447761',
  audioUrl: 'https://www2.cs.uic.edu/~i101/SoundFiles/gettysburg.wav',
  captions: [
    {
      text: 'This is a test caption',
      start: 0,
      end: 3,
    },
    {
      text: 'With multiple scenes',
      start: 3,
      end: 6,
    },
    {
      text: 'To verify our setup',
      start: 6,
      end: 9,
    },
  ],
  config: {
    captionPosition: 'bottom',
    captionBackgroundColor: '#000000',
    musicVolume: 'medium',
    duration: 10,
    orientation: 'portrait',
  },
};

// Output path for the test video
const outputPath = path.join(__dirname, '../test-output.mp4');

console.log('Starting test render...');
console.log('Props:', JSON.stringify(testProps, null, 2));
console.log('Output:', outputPath);

// Render test video
renderVideo(testProps, outputPath)
  .then(() => {
    console.log('✅ Test render completed successfully!');
    console.log('Output video:', outputPath);
  })
  .catch((error) => {
    console.error('❌ Test render failed:', error);
    process.exit(1);
  });
