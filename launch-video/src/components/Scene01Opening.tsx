import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Img,
  staticFile,
} from 'remotion';
import { COLORS } from '../constants';

export const Scene01Opening: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoScale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 120, mass: 1 },
    delay: 10,
  });

  const logoOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  const textOpacity = interpolate(frame, [30, 55], [0, 1], { extrapolateRight: 'clamp' });
  const subtextOpacity = interpolate(frame, [50, 75], [0, 1], { extrapolateRight: 'clamp' });
  const overlayOpacity = interpolate(frame, [75, 90], [0, 1], { extrapolateRight: 'clamp' });

  const particleCount = 12;
  const particles = Array.from({ length: particleCount }, (_, i) => {
    const angle = (i / particleCount) * 360;
    const radius = 300 + Math.sin(frame * 0.05 + i) * 20;
    const x = Math.cos((angle * Math.PI) / 180) * radius;
    const y = Math.sin((angle * Math.PI) / 180) * radius;
    const particleOpacity = interpolate(frame, [15, 40], [0, 0.3], { extrapolateRight: 'clamp' });
    return { x, y, opacity: particleOpacity, angle, i };
  });

  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at center, #1a0505 0%, #0a0a0a 60%, #000000 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Ambient glow */}
      <div
        style={{
          position: 'absolute',
          width: 800,
          height: 800,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${COLORS.primaryRed}33 0%, transparent 70%)`,
          opacity: interpolate(frame, [0, 60], [0, 1], { extrapolateRight: 'clamp' }),
        }}
      />

      {/* Orbit particles */}
      {particles.map(({ x, y, opacity, i }) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            width: i % 3 === 0 ? 6 : 4,
            height: i % 3 === 0 ? 6 : 4,
            borderRadius: '50%',
            background: i % 2 === 0 ? COLORS.primaryRed : COLORS.white,
            transform: `translate(${x}px, ${y}px)`,
            opacity,
          }}
        />
      ))}

      {/* HC Hub Logo */}
      <div
        style={{
          opacity: logoOpacity,
          transform: `scale(${logoScale})`,
          marginBottom: 48,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 24,
        }}
      >
        {/* Logo container */}
        <div
          style={{
            background: 'rgba(255,255,255,0.08)',
            border: '1px solid rgba(255,255,255,0.12)',
            borderRadius: 24,
            padding: '32px 48px',
            backdropFilter: 'blur(20px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Img
            src={staticFile('hchub-logo.png')}
            style={{ height: 80, objectFit: 'contain' }}
          />
        </div>

        {/* Divider line */}
        <div
          style={{
            width: interpolate(frame, [25, 60], [0, 200], { extrapolateRight: 'clamp' }),
            height: 1,
            background: `linear-gradient(90deg, transparent, ${COLORS.primaryRed}, transparent)`,
          }}
        />

        <p
          style={{
            opacity: textOpacity,
            color: 'rgba(255,255,255,0.5)',
            fontSize: 18,
            letterSpacing: '0.3em',
            textTransform: 'uppercase',
            fontFamily: 'Plus Jakarta Sans, sans-serif',
            fontWeight: 600,
            margin: 0,
          }}
        >
          PT. Semen Indonesia (Persero) Tbk.
        </p>
      </div>

      {/* "Mempersembahkan" */}
      <p
        style={{
          opacity: subtextOpacity,
          color: 'rgba(255,255,255,0.35)',
          fontSize: 22,
          letterSpacing: '0.25em',
          textTransform: 'uppercase',
          fontFamily: 'Plus Jakarta Sans, sans-serif',
          fontWeight: 400,
          margin: 0,
        }}
      >
        mempersembahkan
      </p>

      {/* Fade to next scene */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: '#000',
          opacity: overlayOpacity,
        }}
      />
    </AbsoluteFill>
  );
};
