import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { COLORS } from '../constants';

const quickActions = [
  { icon: '✈️', title: 'Perjalanan Dinas', desc: 'Kebijakan & prosedur' },
  { icon: '⏰', title: 'Kebijakan Lembur', desc: 'Aturan & kompensasi' },
  { icon: '🏠', title: 'Benefit Relokasi', desc: 'Fasilitas pindah' },
  { icon: '👔', title: 'Pakaian Kerja', desc: 'Seragam lapangan' },
];

const QuickActionCard: React.FC<{ icon: string; title: string; desc: string; delay: number }> = ({
  icon,
  title,
  desc,
  delay,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardSpring = spring({
    frame: frame - delay,
    fps,
    config: { damping: 16, stiffness: 100 },
  });

  const y = interpolate(cardSpring, [0, 1], [40, 0]);
  const opacity = interpolate(frame - delay, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        background: 'rgba(255,255,255,0.85)',
        border: `1px solid ${COLORS.borderSoft}`,
        borderRadius: 16,
        padding: '20px 20px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 8,
        transform: `translateY(${y}px)`,
        opacity,
        flex: 1,
        boxShadow: '0 4px 20px rgba(0,0,0,0.06)',
      }}
    >
      <span style={{ fontSize: 28 }}>{icon}</span>
      <p
        style={{
          margin: 0,
          fontSize: 14,
          fontWeight: 700,
          color: COLORS.dark,
          fontFamily: 'Plus Jakarta Sans, sans-serif',
          textAlign: 'center',
        }}
      >
        {title}
      </p>
      <p
        style={{
          margin: 0,
          fontSize: 12,
          fontWeight: 500,
          color: COLORS.lightGray,
          fontFamily: 'Plus Jakarta Sans, sans-serif',
          textAlign: 'center',
        }}
      >
        {desc}
      </p>
    </div>
  );
};

export const Scene04Landing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  const fadeOut = interpolate(frame, [160, 180], [1, 0], { extrapolateLeft: 'clamp' });
  const opacity = Math.min(fadeIn, fadeOut);

  // Camera zoom effect - subtle zoom in
  const cameraZoom = interpolate(frame, [0, 180], [1.05, 1], { extrapolateRight: 'clamp' });

  const labelOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  const heroY = spring({
    frame: frame - 10,
    fps,
    config: { damping: 18, stiffness: 90 },
  });

  const inputSpring = spring({
    frame: frame - 35,
    fps,
    config: { damping: 18, stiffness: 90 },
  });

  const inputY = interpolate(inputSpring, [0, 1], [30, 0]);
  const inputOpacity = interpolate(frame, [35, 55], [0, 1], { extrapolateRight: 'clamp' });

  // Typing animation for search input
  const fullText = 'Tanyakan kebijakan cuti tahunan untuk karyawan...';
  const typingProgress = interpolate(frame, [60, 110], [0, 1], { extrapolateRight: 'clamp' });
  const displayText = fullText.slice(0, Math.floor(typingProgress * fullText.length));

  const cursorVisible = Math.floor(frame / 8) % 2 === 0;

  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at 70% 20%, #fff1f1 0%, #f2f3f6 60%, #eef0f4 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        opacity,
        transform: `scale(${cameraZoom})`,
        overflow: 'hidden',
      }}
    >
      {/* Ambient decorations */}
      <div
        style={{
          position: 'absolute',
          top: -100,
          right: -100,
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${COLORS.primaryRed}15 0%, transparent 70%)`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: -150,
          left: -100,
          width: 450,
          height: 450,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${COLORS.secondaryBlue}10 0%, transparent 70%)`,
        }}
      />

      {/* Feature label */}
      <div
        style={{
          position: 'absolute',
          top: 60,
          left: 80,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: `${COLORS.primaryRed}18`,
          border: `1px solid ${COLORS.primaryRed}33`,
          borderRadius: 999,
          padding: '8px 20px',
          opacity: labelOpacity,
        }}
      >
        <div
          style={{ width: 8, height: 8, borderRadius: '50%', background: COLORS.primaryRed }}
        />
        <span
          style={{
            color: COLORS.primaryRed,
            fontSize: 14,
            fontWeight: 700,
            letterSpacing: '0.12em',
            fontFamily: 'Plus Jakarta Sans, sans-serif',
          }}
        >
          Landing Page
        </span>
      </div>

      {/* Main content */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          maxWidth: 860,
          width: '100%',
          padding: '0 40px',
        }}
      >
        {/* Hero Heading */}
        <div
          style={{
            transform: `translateY(${interpolate(heroY, [0, 1], [50, 0])}px)`,
            opacity: interpolate(frame, [10, 35], [0, 1], { extrapolateRight: 'clamp' }),
            textAlign: 'center',
            marginBottom: 48,
          }}
        >
          <h1
            style={{
              margin: 0,
              fontSize: 58,
              fontWeight: 800,
              color: COLORS.dark,
              fontFamily: 'Plus Jakarta Sans, sans-serif',
              lineHeight: 1.1,
              letterSpacing: '-0.02em',
            }}
          >
            Ada yang bisa{' '}
            <span
              style={{
                background: `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed || '#db322f'})`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontStyle: 'italic',
              }}
            >
              DENAI
            </span>{' '}
            bantu
            <br />
            untuk{' '}
            <span
              style={{
                fontStyle: 'italic',
                color: COLORS.primaryRed,
              }}
            >
              Anda?
            </span>
          </h1>
        </div>

        {/* Search Input */}
        <div
          style={{
            width: '100%',
            transform: `translateY(${inputY}px)`,
            opacity: inputOpacity,
            marginBottom: 40,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              background: 'rgba(255,255,255,0.9)',
              border: `1.5px solid ${COLORS.primaryRed}55`,
              borderRadius: 16,
              padding: '16px 20px',
              boxShadow: `0 0 0 4px ${COLORS.primaryRed}10, 0 8px 32px rgba(0,0,0,0.08)`,
              gap: 12,
            }}
          >
            <span style={{ fontSize: 22, opacity: 0.5 }}>🔍</span>
            <p
              style={{
                margin: 0,
                flex: 1,
                fontSize: 18,
                color: COLORS.dark,
                fontFamily: 'Plus Jakarta Sans, sans-serif',
                fontWeight: 400,
                minHeight: 28,
              }}
            >
              {displayText}
              {cursorVisible && typingProgress < 1 && (
                <span
                  style={{
                    display: 'inline-block',
                    width: 2,
                    height: 20,
                    background: COLORS.primaryRed,
                    marginLeft: 2,
                    verticalAlign: 'middle',
                  }}
                />
              )}
              {typingProgress === 0 && (
                <span style={{ color: COLORS.lightGray }}>
                  Tanyakan kebijakan HR, lembur, cuti...
                </span>
              )}
            </p>
            {/* Send Button */}
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                background: `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed || '#db322f'})`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <span style={{ color: '#fff', fontSize: 18 }}>→</span>
            </div>
          </div>
        </div>

        {/* Quick Action Cards */}
        <div
          style={{
            display: 'flex',
            gap: 16,
            width: '100%',
          }}
        >
          {quickActions.map(({ icon, title, desc }, i) => (
            <QuickActionCard
              key={title}
              icon={icon}
              title={title}
              desc={desc}
              delay={75 + i * 12}
            />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
