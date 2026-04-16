import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { COLORS } from '../constants';

export const Scene03Reveal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  const fadeOut = interpolate(frame, [130, 150], [1, 0], { extrapolateLeft: 'clamp' });
  const opacity = Math.min(fadeIn, fadeOut);

  // "D" box reveal
  const boxScale = spring({
    frame: frame - 10,
    fps,
    config: { damping: 12, stiffness: 80, mass: 1.5 },
  });

  const boxOpacity = interpolate(frame, [10, 30], [0, 1], { extrapolateRight: 'clamp' });

  // Ring expansion
  const ring1Scale = spring({
    frame: frame - 20,
    fps,
    config: { damping: 8, stiffness: 40, mass: 2 },
  });
  const ring2Scale = spring({
    frame: frame - 35,
    fps,
    config: { damping: 8, stiffness: 35, mass: 2 },
  });

  // Text reveal
  const textY = spring({
    frame: frame - 50,
    fps,
    config: { damping: 16, stiffness: 100 },
  });
  const textOpacity = interpolate(frame, [50, 70], [0, 1], { extrapolateRight: 'clamp' });

  const taglineOpacity = interpolate(frame, [75, 95], [0, 1], { extrapolateRight: 'clamp' });
  const taglineY = spring({
    frame: frame - 75,
    fps,
    config: { damping: 16, stiffness: 100 },
  });

  const badgeOpacity = interpolate(frame, [100, 120], [0, 1], { extrapolateRight: 'clamp' });

  // Particle burst
  const burstParticles = Array.from({ length: 16 }, (_, i) => {
    const angle = (i / 16) * 360;
    const progress = spring({
      frame: frame - 15,
      fps,
      config: { damping: 25, stiffness: 60, mass: 1 },
    });
    const maxRadius = 280;
    const r = interpolate(progress, [0, 1], [0, maxRadius]);
    const x = Math.cos((angle * Math.PI) / 180) * r;
    const y = Math.sin((angle * Math.PI) / 180) * r;
    const pOpacity = interpolate(frame, [15, 30, 80, 100], [0, 0.8, 0.8, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    return { x, y, opacity: pOpacity, i };
  });

  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at center, #100000 0%, #000000 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        opacity,
        overflow: 'hidden',
      }}
    >
      {/* Large glow ring */}
      <div
        style={{
          position: 'absolute',
          width: 800,
          height: 800,
          borderRadius: '50%',
          border: `1px solid ${COLORS.primaryRed}22`,
          transform: `scale(${ring1Scale})`,
          opacity: interpolate(frame, [20, 40], [0, 1], { extrapolateRight: 'clamp' }),
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 600,
          height: 600,
          borderRadius: '50%',
          border: `1px solid ${COLORS.primaryRed}33`,
          transform: `scale(${ring2Scale})`,
          opacity: interpolate(frame, [35, 55], [0, 1], { extrapolateRight: 'clamp' }),
        }}
      />

      {/* Burst particles */}
      {burstParticles.map(({ x, y, opacity: pOp, i }) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            width: i % 4 === 0 ? 8 : 4,
            height: i % 4 === 0 ? 8 : 4,
            borderRadius: '50%',
            background: i % 3 === 0 ? COLORS.primaryRed : 'rgba(255,255,255,0.8)',
            transform: `translate(${x}px, ${y}px)`,
            opacity: pOp,
          }}
        />
      ))}

      {/* DENAI Logo Box */}
      <div
        style={{
          transform: `scale(${boxScale})`,
          opacity: boxOpacity,
          marginBottom: 48,
          position: 'relative',
        }}
      >
        <div
          style={{
            width: 140,
            height: 140,
            borderRadius: 28,
            background: `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed || '#db322f'})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: `0 0 80px ${COLORS.primaryRed}80, 0 0 160px ${COLORS.primaryRed}40`,
          }}
        >
          <span
            style={{
              color: '#fff',
              fontSize: 80,
              fontWeight: 900,
              fontFamily: 'Plus Jakarta Sans, sans-serif',
              lineHeight: 1,
            }}
          >
            D
          </span>
        </div>
      </div>

      {/* DENAI wordmark */}
      <div
        style={{
          opacity: textOpacity,
          transform: `translateY(${interpolate(textY, [0, 1], [30, 0])}px)`,
          textAlign: 'center',
        }}
      >
        <h1
          style={{
            color: '#fff',
            fontSize: 96,
            fontWeight: 900,
            fontFamily: 'Plus Jakarta Sans, sans-serif',
            margin: '0 0 16px 0',
            letterSpacing: '-0.02em',
            lineHeight: 1,
          }}
        >
          DENAI
        </h1>
      </div>

      {/* Tagline */}
      <p
        style={{
          opacity: taglineOpacity,
          transform: `translateY(${interpolate(taglineY, [0, 1], [20, 0])}px)`,
          color: 'rgba(255,255,255,0.6)',
          fontSize: 26,
          fontWeight: 400,
          fontFamily: 'Plus Jakarta Sans, sans-serif',
          margin: '0 0 40px 0',
          letterSpacing: '0.08em',
        }}
      >
        Asisten Pengetahuan Perusahaan
      </p>

      {/* Badge */}
      <div
        style={{
          opacity: badgeOpacity,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          background: 'rgba(255,255,255,0.06)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 999,
          padding: '12px 32px',
        }}
      >
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            background: `linear-gradient(135deg, ${COLORS.primaryRed}, #ff6b6b)`,
          }}
        />
        <span
          style={{
            color: 'rgba(255,255,255,0.7)',
            fontSize: 16,
            fontWeight: 600,
            fontFamily: 'Plus Jakarta Sans, sans-serif',
            letterSpacing: '0.1em',
          }}
        >
          Powered by Artificial Intelligence
        </span>
      </div>
    </AbsoluteFill>
  );
};
