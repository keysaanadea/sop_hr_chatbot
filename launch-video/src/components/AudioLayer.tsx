import React from 'react';
import { Audio, staticFile, useCurrentFrame, interpolate } from 'remotion';
import { FPS, SCENES } from '../constants';

// Volume envelope helper — smooth fade between keyframes
const volumeAt = (frame: number): number => {
  return interpolate(
    frame,
    [
      0,                          // cold start
      15,                         // fade in
      SCENES.reveal.start,        // build up at reveal
      SCENES.reveal.start + 30,   // full volume
      SCENES.closing.end - 45,    // start fade out
      SCENES.closing.end - 5,     // nearly silent
    ],
    [
      0,    // silence
      0.25, // soft intro
      0.35, // slightly louder
      0.55, // full presence
      0.55, // hold
      0,    // fade out
    ],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );
};

export const AudioLayer: React.FC = () => {
  const frame = useCurrentFrame();
  const vol = volumeAt(frame);

  return (
    <>
      {/* ── Background Music ──────────────────────────────────────────
          Letakkan file musik di:  launch-video/public/music.mp3
          Rekomendasi: Pixabay "corporate inspiring" / "product launch epic"
          atau Mixkit "Inspiring corporate"
      ──────────────────────────────────────────────────────────────── */}
      <Audio
        src={staticFile('music.mp3')}
        volume={vol}
        loop
        playbackRate={1}
      />

      {/* ── SFX: Logo reveal boom (Scene 3, frame ~15) ───────────────
          File: public/sfx-boom.mp3  (Mixkit: "cinematic impact boom")
      ──────────────────────────────────────────────────────────────── */}
      <Audio
        src={staticFile('sfx-boom.mp3')}
        startFrom={0}
        endAt={45}
        volume={interpolate(
          frame - SCENES.reveal.start,
          [12, 16, 30, 45],
          [0, 0.7, 0.7, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        )}
      />

      {/* ── SFX: Scene whoosh transitions ────────────────────────────
          File: public/sfx-whoosh.mp3  (Mixkit: "fast small sweep whoosh")
          Plays at every scene boundary
      ──────────────────────────────────────────────────────────────── */}
      {[
        SCENES.problem.start,
        SCENES.reveal.start,
        SCENES.landing.start,
        SCENES.chat.start,
        SCENES.callMode.start,
        SCENES.closing.start,
      ].map((sceneStart) => (
        <Audio
          key={sceneStart}
          src={staticFile('sfx-whoosh.mp3')}
          startFrom={sceneStart}
          endAt={sceneStart + 20}
          volume={interpolate(
            frame - sceneStart,
            [0, 3, 15, 20],
            [0, 0.45, 0.45, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          )}
        />
      ))}

      {/* ── SFX: Typing tick (Scene 4 — Landing, search input) ───────
          File: public/sfx-typing.mp3  (Mixkit: "typewriter clack")
          Plays during typing animation (frame 60-110 of scene 4)
      ──────────────────────────────────────────────────────────────── */}
      <Audio
        src={staticFile('sfx-typing.mp3')}
        startFrom={SCENES.landing.start + 60}
        endAt={SCENES.landing.start + 110}
        volume={interpolate(
          frame - (SCENES.landing.start + 60),
          [0, 5, 45, 50],
          [0, 0.3, 0.3, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        )}
      />

      {/* ── SFX: Notification ping (Scene 5 — Chat, each bot message) ─
          File: public/sfx-ping.mp3  (Mixkit: "correct answer tone")
      ──────────────────────────────────────────────────────────────── */}
      {[50, 135].map((msgFrame) => (
        <Audio
          key={msgFrame}
          src={staticFile('sfx-ping.mp3')}
          startFrom={SCENES.chat.start + msgFrame}
          endAt={SCENES.chat.start + msgFrame + 15}
          volume={interpolate(
            frame - (SCENES.chat.start + msgFrame),
            [0, 2, 10, 15],
            [0, 0.4, 0.4, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          )}
        />
      ))}

      {/* ── SFX: Mic pop / call start (Scene 6 — Call Mode) ──────────
          File: public/sfx-mic.mp3  (Mixkit: "interface hint notification")
      ──────────────────────────────────────────────────────────────── */}
      <Audio
        src={staticFile('sfx-mic.mp3')}
        startFrom={SCENES.callMode.start + 5}
        endAt={SCENES.callMode.start + 25}
        volume={interpolate(
          frame - (SCENES.callMode.start + 5),
          [0, 3, 15, 20],
          [0, 0.5, 0.5, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        )}
      />
    </>
  );
};
