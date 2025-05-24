export interface Caption {
  text: string;
  start: number;
  end: number;
}

export interface VideoConfig {
  captionPosition: 'top' | 'center' | 'bottom';
  captionBackgroundColor: string;
  musicVolume: 'low' | 'medium' | 'high' | 'muted';
  musicUrl?: string;
  orientation?: 'portrait' | 'landscape';
  duration?: number;
  paddingBack?: number;
}

export interface VideoProps {
  videoUrl: string;
  audioUrl: string;
  captions: Caption[];
  config: VideoConfig;
}
