import {Composition} from 'remotion';
import {PortraitVideo} from './components/PortraitVideo';
import {LandscapeVideo} from './components/LandscapeVideo';

export const RemotionVideo: React.FC = () => {
  return (
    <>
      <Composition
        id="PortraitVideo"
        component={PortraitVideo}
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
      <Composition
        id="LandscapeVideo"
        component={LandscapeVideo}
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
