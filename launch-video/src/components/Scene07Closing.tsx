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

const features = [
  { icon: '💬', label: 'Chat Cerdas' },
  { icon: '🎤', label: 'Suara Real-time' },
  { icon: '📊', label: 'Analitik HR' },
  { icon: '🔐', label: 'Akses Berbasis Peran' },
];

export const Scene07Closing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: 'clamp' });

  // Background glow pulse
  const glowPulse = Math.sin(frame * 0.04) * 0.2 + 0.8;

  // Logo box
  const logoScale = spring({
    frame: frame - 15,
    fps,
    config: { damping: 12, stiffness: 80, mass: 1.2 },
  });
  const logoOpacity = interpolate(frame, [15, 35], [0, 1], { extrapolateRight: 'clamp' });

  // DENAI title
  const titleY = spring({
    frame: frame - 40,
    fps,
    config: { damping: 16, stiffness: 100 },
  });
  const titleOpacity = interpolate(frame, [40, 60], [0, 1], { extrapolateRight: 'clamp' });

  // Tagline
  const taglineOpacity = interpolate(frame, [65, 85], [0, 1], { extrapolateRight: 'clamp' });

  // Feature pills
  const featuresOpacity = interpolate(frame, [85, 105], [0, 1], { extrapolateRight: 'clamp' });

  // Divider line grow
  const dividerWidth = interpolate(frame, [70, 100], [0, 400], { extrapolateRight: 'clamp' });

  // Bottom brand
  const bottomOpacity = interpolate(frame, [110, 130], [0, 1], { extrapolateRight: 'clamp' });

  // Particle field
  const particles = Array.from({ length: 24 }, (_, i) => {
    const angle = (i / 24) * 360 + frame * 0.3;
    const r = 380 + Math.sin(frame * 0.04 + i * 1.3) * 30;
    const x = Math.cos((angle * Math.PI) / 180) * r;
    const y = Math.sin((angle * Math.PI) / 180) * r;
    const pOpacity = interpolate(frame, [20, 50], [0, 0.25], { extrapolateRight: 'clamp' });
    return { x, y, opacity: pOpacity, i };
  });

  // Shooting stars
  const stars = Array.from({ length: 6 }, (_, i) => {
    const startDelay = i * 25;
    const progress = interpolate(frame - startDelay, [0, 60], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    const startX = -600 + i * 150;
    const x = startX + progress * 1400;
    const y = 200 + i * 100;
    const opacity = interpolate(progress, [0, 0.1, 0.8, 1], [0, 0.6, 0.6, 0]);
    return { x, y, opacity, i };
  });

  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at center, #120000 0%, #050005 50%, #000000 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        opacity: fadeIn,
        overflow: 'hidden',
      }}
    >
      {/* Ambient background glow */}
      <div
        style={{
          position: 'absolute',
          width: 900,
          height: 900,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${COLORS.primaryRed}1a 0%, transparent 70%)`,
          opacity: glowPulse,
        }}
      />

      {/* Rotating orbit rings */}
      <div
        style={{
          position: 'absolute',
          width: 700,
          height: 700,
          borderRadius: '50%',
          border: `1px solid ${COLORS.primaryRed}18`,
          transform: `rotate(${frame * 0.2}deg)`,
          opacity: interpolate(frame, [20, 50], [0, 1], { extrapolateRight: 'clamp' }),
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 550,
          height: 550,
          borderRadius: '50%',
          border: `1px solid ${COLORS.primaryRed}10`,
          transform: `rotate(${-frame * 0.15}deg)`,
          opacity: interpolate(frame, [30, 60], [0, 1], { extrapolateRight: 'clamp' }),
        }}
      />

      {/* Shooting stars */}
      {stars.map(({ x, y, opacity, i }) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            transform: `translate(${x}px, ${y}px)`,
            opacity,
          }}
        >
          <div
            style={{
              width: 60,
              height: 1.5,
              background: `linear-gradient(90deg, transparent, ${COLORS.primaryRed}, rgba(255,255,255,0.8))`,
              borderRadius: 999,
            }}
          />
        </div>
      ))}

      {/* Orbit particles */}
      {particles.map(({ x, y, opacity: pOp, i }) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            width: i % 5 === 0 ? 5 : 3,
            height: i % 5 === 0 ? 5 : 3,
            borderRadius: '50%',
            background: i % 3 === 0 ? COLORS.primaryRed : 'rgba(255,255,255,0.6)',
            transform: `translate(${x}px, ${y}px)`,
            opacity: pOp,
          }}
        />
      ))}

      {/* DENAI Logo Box */}
      <div
        style={{
          transform: `scale(${logoScale})`,
          opacity: logoOpacity,
          marginBottom: 40,
          position: 'relative',
        }}
      >
        <div
          style={{
            width: 110,
            height: 110,
            borderRadius: 24,
            background: `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed || '#db322f'})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: `0 0 60px ${COLORS.primaryRed}70, 0 0 120px ${COLORS.primaryRed}30`,
          }}
        >
          <span
            style={{
              color: '#fff',
              fontSize: 64,
              fontWeight: 900,
              fontFamily: 'Plus Jakarta Sans, sans-serif',
              lineHeight: 1,
            }}
          >
            D
          </span>
        </div>
      </div>

      {/* DENAI Title */}
      <h1
        style={{
          margin: '0 0 8px 0',
          fontSize: 88,
          fontWeight: 900,
          color: '#ffffff',
          fontFamily: 'Plus Jakarta Sans, sans-serif',
          letterSpacing: '-0.02em',
          transform: `translateY(${interpolate(titleY, [0, 1], [30, 0])}px)`,
          opacity: titleOpacity,
          lineHeight: 1,
        }}
      >
        DENAI
      </h1>

      {/* Divider */}
      <div
        style={{
          width: dividerWidth,
          height: 1,
          background: `linear-gradient(90deg, transparent, ${COLORS.primaryRed}, transparent)`,
          marginBottom: 20,
        }}
      />

      {/* Tagline */}
      <p
        style={{
          opacity: taglineOpacity,
          color: 'rgba(255,255,255,0.65)',
          fontSize: 24,
          fontWeight: 400,
          fontFamily: 'Plus Jakarta Sans, sans-serif',
          margin: '0 0 48px 0',
          letterSpacing: '0.1em',
          textAlign: 'center',
        }}
      >
        Asisten Pengetahuan Perusahaan
      </p>

      {/* Feature pills */}
      <div
        style={{
          display: 'flex',
          gap: 12,
          opacity: featuresOpacity,
          marginBottom: 72,
          flexWrap: 'wrap',
          justifyContent: 'center',
        }}
      >
        {features.map(({ icon, label }, i) => {
          const pillSpring = spring({
            frame: frame - 85 - i * 10,
            fps,
            config: { damping: 16, stiffness: 120 },
          });
          const pillY = interpolate(pillSpring, [0, 1], [20, 0]);
          const pillOp = interpolate(frame - 85 - i * 10, [0, 12], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return (
            <div
              key={label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(255,255,255,0.10)',
                borderRadius: 999,
                padding: '10px 20px',
                transform: `translateY(${pillY}px)`,
                opacity: pillOp,
              }}
            >
              <span style={{ fontSize: 18 }}>{icon}</span>
              <span
                style={{
                  color: 'rgba(255,255,255,0.8)',
                  fontSize: 14,
                  fontWeight: 600,
                  fontFamily: 'Plus Jakarta Sans, sans-serif',
                }}
              >
                {label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Bottom — HC Hub branding */}
      <div
        style={{
          opacity: bottomOpacity,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
        }}
      >
        <p
          style={{
            margin: 0,
            fontSize: 12,
            color: 'rgba(255,255,255,0.3)',
            fontFamily: 'Plus Jakarta Sans, sans-serif',
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
          }}
        >
          Powered by
        </p>
        <div
          style={{
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 16,
            padding: '16px 36px',
            backdropFilter: 'blur(10px)',
          }}
        >
          <Img
            src={staticFile('hchub-logo.png')}
            style={{ height: 48, objectFit: 'contain', filter: 'brightness(0) invert(1)', opacity: 0.8 }}
          />
        </div>
        <p
          style={{
            margin: 0,
            fontSize: 14,
            color: 'rgba(255,255,255,0.4)',
            fontFamily: 'Plus Jakarta Sans, sans-serif',
            letterSpacing: '0.15em',
          }}
        >
          PT. Semen Indonesia (Persero) Tbk.
        </p>
      </div>
    </AbsoluteFill>
  );
};
