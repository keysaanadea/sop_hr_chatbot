import React from 'react';
import { Composition, registerRoot } from 'remotion';
import { DENAILaunch } from './DENAILaunch';
import { FPS, VIDEO_WIDTH, VIDEO_HEIGHT, DURATION_IN_FRAMES } from './constants';

const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DENAILaunch"
        component={DENAILaunch}
        durationInFrames={DURATION_IN_FRAMES}
        fps={FPS}
        width={VIDEO_WIDTH}
        height={VIDEO_HEIGHT}
        defaultProps={{}}
      />
    </>
  );
};

registerRoot(RemotionRoot);
