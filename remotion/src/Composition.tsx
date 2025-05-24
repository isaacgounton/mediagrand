import React from 'react';
import {Composition} from 'remotion';
import {PortraitVideo} from './components/PortraitVideo';
import {LandscapeVideo} from './components/LandscapeVideo';
import {VideoProps} from './types/video';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition<VideoProps>
        id="PortraitVideo"
        component={PortraitVideo as React.ComponentType<VideoProps>}
        durationInFrames={900} // 30s @ 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          videoUrl: '',
          audioUrl: '',
          captions: [],
          config: {
            captionPosition: 'bottom',
            captionBackgroundColor: '#000000',
            musicVolume: 'medium'
          }
        }}
      />
      <Composition<VideoProps>
        id="LandscapeVideo"
        component={LandscapeVideo as React.ComponentType<VideoProps>}
        durationInFrames={900}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          videoUrl: '',
          audioUrl: '',
          captions: [],
          config: {
            captionPosition: 'bottom',
            captionBackgroundColor: '#000000',
            musicVolume: 'medium'
          }
        }}
      />
    </>
  );
};
