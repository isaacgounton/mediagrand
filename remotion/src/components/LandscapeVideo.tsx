import {Sequence, useVideoConfig, Audio, Video} from 'remotion';
import React from 'react';
import {VideoProps} from '../types/video';

export const LandscapeVideo: React.FC<VideoProps> = ({
  videoUrl,
  audioUrl,
  captions,
  config,
}) => {
  const {width, height} = useVideoConfig();
  const captionHeight = 100;
  const captionY = config.captionPosition === 'top' 
    ? 40
    : config.captionPosition === 'center' 
      ? (height - captionHeight) / 2
      : height - captionHeight - 40;

  return (
    <>
      <Video src={videoUrl} style={{width, height}} />
      {/* Speech audio */}
      <Audio src={audioUrl} volume={1} />
      
      {/* Background music */}
      {config.musicUrl && (
        <Audio 
          src={config.musicUrl} 
          volume={
            config.musicVolume === 'high' ? 0.3 :
            config.musicVolume === 'medium' ? 0.2 :
            config.musicVolume === 'low' ? 0.1 : 
            0
          }
        />
      )}
      {captions.map((caption, index) => (
        <Sequence
          key={index}
          from={Math.floor(caption.start * 30)}
          durationInFrames={Math.floor((caption.end - caption.start) * 30)}
        >
          <div
            style={{
              position: 'absolute',
              width: '100%',
              height: captionHeight,
              top: captionY,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              backgroundColor: `${config.captionBackgroundColor}88`,
              padding: '10px 20px',
              boxSizing: 'border-box',
            }}
          >
            <p
              style={{
                fontSize: '2.2em',
                color: 'white',
                margin: 0,
                fontFamily: 'Helvetica, Arial, sans-serif',
                textShadow: '2px 2px 4px rgba(0,0,0,0.5)',
              }}
            >
              {caption.text}
            </p>
          </div>
        </Sequence>
      ))}
    </>
  );
};
