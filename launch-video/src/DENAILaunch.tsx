import React from 'react';
import { AbsoluteFill, Sequence } from 'remotion';
import { Scene01Opening } from './components/Scene01Opening';
import { Scene02Problem } from './components/Scene02Problem';
import { Scene03Reveal } from './components/Scene03Reveal';
import { Scene04Landing } from './components/Scene04Landing';
import { Scene05Chat } from './components/Scene05Chat';
import { Scene06CallMode } from './components/Scene06CallMode';
import { Scene07Closing } from './components/Scene07Closing';
import { AudioLayer } from './components/AudioLayer';
import { SCENES } from './constants';

export const DENAILaunch: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: '#000', fontFamily: 'Plus Jakarta Sans, sans-serif' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&display=swap');
        * { box-sizing: border-box; }
      `}</style>

      {/* Audio — background music + SFX */}
      <AudioLayer />

      {/* Scene 1: Opening — 0s to 3s */}
      <Sequence
        from={SCENES.opening.start}
        durationInFrames={SCENES.opening.end - SCENES.opening.start}
      >
        <Scene01Opening />
      </Sequence>

      {/* Scene 2: Problem — 3s to 7s */}
      <Sequence
        from={SCENES.problem.start}
        durationInFrames={SCENES.problem.end - SCENES.problem.start}
      >
        <Scene02Problem />
      </Sequence>

      {/* Scene 3: Reveal — 7s to 12s */}
      <Sequence
        from={SCENES.reveal.start}
        durationInFrames={SCENES.reveal.end - SCENES.reveal.start}
      >
        <Scene03Reveal />
      </Sequence>

      {/* Scene 4: Landing Page — 12s to 18s */}
      <Sequence
        from={SCENES.landing.start}
        durationInFrames={SCENES.landing.end - SCENES.landing.start}
      >
        <Scene04Landing />
      </Sequence>

      {/* Scene 5: Chat Mode — 18s to 24s */}
      <Sequence
        from={SCENES.chat.start}
        durationInFrames={SCENES.chat.end - SCENES.chat.start}
      >
        <Scene05Chat />
      </Sequence>

      {/* Scene 6: Call Mode — 24s to 29s */}
      <Sequence
        from={SCENES.callMode.start}
        durationInFrames={SCENES.callMode.end - SCENES.callMode.start}
      >
        <Scene06CallMode />
      </Sequence>

      {/* Scene 7: Closing — 29s to 35s */}
      <Sequence
        from={SCENES.closing.start}
        durationInFrames={SCENES.closing.end - SCENES.closing.start}
      >
        <Scene07Closing />
      </Sequence>
    </AbsoluteFill>
  );
};
