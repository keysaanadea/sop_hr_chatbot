import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { COLORS } from '../constants';

const transcriptLines = [
  { text: 'Halo DENAI, berapa hari lembur maksimal?', role: 'user', startFrame: 20 },
  { text: 'Lembur maksimal 3 jam per hari atau 14 jam per minggu...', role: 'bot', startFrame: 55 },
  { text: 'Kompensasi lemburnya berapa persen?', role: 'user', startFrame: 95 },
  { text: '150% untuk 1 jam pertama, 200% untuk jam berikutnya.', role: 'bot', startFrame: 120 },
];

const WaveformBar: React.FC<{ index: number; totalBars: number }> = ({ index, totalBars }) => {
  const frame = useCurrentFrame();

  const baseHeight = 8;
  const maxHeight = 60;
  const wave1 = Math.sin(frame * 0.18 + index * 0.5) * 0.5 + 0.5;
  const wave2 = Math.sin(frame * 0.12 + index * 0.8 + 2) * 0.3 + 0.7;
  const height = baseHeight + (maxHeight - baseHeight) * wave1 * wave2;

  const centerRatio = 1 - Math.abs(index / totalBars - 0.5) * 2;
  const colorR = Math.floor(183 + centerRatio * 50);
  const colorG = Math.floor(19 + centerRatio * 30);
  const color = `rgb(${colorR}, ${colorG}, 26)`;
  const opacity = 0.4 + centerRatio * 0.6;

  return (
    <div
      style={{
        width: 6,
        height,
        borderRadius: 3,
        background: color,
        opacity,
        transition: 'height 0.05s ease',
      }}
    />
  );
};

const TranscriptItem: React.FC<{ text: string; role: string; startFrame: number }> = ({
  text,
  role,
  startFrame,
}) => {
  const frame = useCurrentFrame();
  if (frame < startFrame) return null;

  const opacity = interpolate(frame - startFrame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const isBot = role === 'bot';

  return (
    <div
      style={{
        opacity,
        marginBottom: 12,
        display: 'flex',
        gap: 8,
        alignItems: 'flex-start',
      }}
    >
      <div
        style={{
          width: 24,
          height: 24,
          borderRadius: '50%',
          background: isBot
            ? `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed || '#db322f'})`
            : COLORS.dark,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginTop: 2,
        }}
      >
        <span style={{ color: '#fff', fontSize: 10, fontWeight: 700 }}>
          {isBot ? 'D' : 'U'}
        </span>
      </div>
      <p
        style={{
          margin: 0,
          fontSize: 13,
          color: isBot ? 'rgba(255,255,255,0.85)' : 'rgba(255,255,255,0.6)',
          fontFamily: 'Plus Jakarta Sans, sans-serif',
          fontWeight: isBot ? 500 : 400,
          lineHeight: 1.5,
        }}
      >
        {text}
      </p>
    </div>
  );
};

export const Scene06CallMode: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  const fadeOut = interpolate(frame, [130, 150], [1, 0], { extrapolateLeft: 'clamp' });
  const sceneOpacity = Math.min(fadeIn, fadeOut);

  const leftPanel = spring({
    frame: frame - 5,
    fps,
    config: { damping: 18, stiffness: 90 },
  });
  const rightPanel = spring({
    frame: frame - 20,
    fps,
    config: { damping: 18, stiffness: 90 },
  });

  const leftX = interpolate(leftPanel, [0, 1], [-60, 0]);
  const rightX = interpolate(rightPanel, [0, 1], [60, 0]);

  const labelOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  // Breathing animation for the microphone
  const breathe = Math.sin(frame * 0.08) * 0.08 + 1;

  const totalBars = 32;

  // Timer
  const seconds = Math.floor(frame / fps);
  const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
  const secs = (seconds % 60).toString().padStart(2, '0');

  // Status badge pulse
  const pulse = Math.sin(frame * 0.15) * 0.3 + 0.7;

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(135deg, #0a0a14 0%, #0f0010 50%, #0a0a14 100%)`,
        opacity: sceneOpacity,
        overflow: 'hidden',
      }}
    >
      {/* Feature label */}
      <div
        style={{
          position: 'absolute',
          top: 40,
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 10,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: `${COLORS.primaryRed}22`,
          border: `1px solid ${COLORS.primaryRed}44`,
          borderRadius: 999,
          padding: '8px 24px',
          opacity: labelOpacity,
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: COLORS.primaryRed,
            opacity: pulse,
          }}
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
          Mode Telepon
        </span>
      </div>

      <div style={{ display: 'flex', height: '100%', padding: '100px 80px 60px' }}>
        {/* Left Panel */}
        <div
          style={{
            flex: 2,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 32,
            transform: `translateX(${leftX}px)`,
            opacity: interpolate(frame, [5, 25], [0, 1], { extrapolateRight: 'clamp' }),
          }}
        >
          {/* Status pill */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              background: 'rgba(183,19,26,0.15)',
              border: '1px solid rgba(183,19,26,0.35)',
              borderRadius: 999,
              padding: '8px 20px',
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: COLORS.primaryRed,
                opacity: pulse,
                boxShadow: `0 0 8px ${COLORS.primaryRed}`,
              }}
            />
            <span
              style={{
                color: 'rgba(255,255,255,0.9)',
                fontSize: 14,
                fontWeight: 600,
                fontFamily: 'Plus Jakarta Sans, sans-serif',
              }}
            >
              Sedang Mendengarkan...
            </span>
          </div>

          {/* Last input card */}
          <div
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 16,
              padding: '16px 28px',
              maxWidth: 480,
              width: '100%',
              backdropFilter: 'blur(10px)',
            }}
          >
            <p
              style={{
                margin: 0,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: '0.1em',
                color: 'rgba(255,255,255,0.35)',
                fontFamily: 'Plus Jakarta Sans, sans-serif',
                marginBottom: 6,
                textTransform: 'uppercase',
              }}
            >
              Terakhir Diucapkan
            </p>
            <p
              style={{
                margin: 0,
                fontSize: 17,
                color: 'rgba(255,255,255,0.85)',
                fontFamily: 'Plus Jakarta Sans, sans-serif',
                fontWeight: 500,
                lineHeight: 1.5,
              }}
            >
              "Kompensasi lemburnya berapa persen?"
            </p>
          </div>

          {/* Waveform visualizer */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              height: 80,
            }}
          >
            {Array.from({ length: totalBars }, (_, i) => (
              <WaveformBar key={i} index={i} totalBars={totalBars} />
            ))}
          </div>

          {/* Mic pulsing circle + icon */}
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {/* Pulse rings */}
            <div
              style={{
                position: 'absolute',
                width: 120,
                height: 120,
                borderRadius: '50%',
                border: `2px solid ${COLORS.primaryRed}`,
                opacity: 0.15,
                transform: `scale(${breathe * 1.4})`,
              }}
            />
            <div
              style={{
                position: 'absolute',
                width: 100,
                height: 100,
                borderRadius: '50%',
                border: `1.5px solid ${COLORS.primaryRed}`,
                opacity: 0.25,
                transform: `scale(${breathe * 1.2})`,
              }}
            />
            {/* Mic button */}
            <div
              style={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                background: `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed || '#db322f'})`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: `0 0 40px ${COLORS.primaryRed}60`,
                transform: `scale(${breathe})`,
              }}
            >
              <span style={{ fontSize: 32 }}>🎤</span>
            </div>
          </div>

          {/* Timer */}
          <p
            style={{
              margin: 0,
              fontSize: 28,
              fontWeight: 700,
              color: 'rgba(255,255,255,0.6)',
              fontFamily: 'Plus Jakarta Sans, sans-serif',
              letterSpacing: '0.1em',
            }}
          >
            {mins}:{secs}
          </p>

          {/* Controls */}
          <div style={{ display: 'flex', gap: 20 }}>
            {/* Mute */}
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255,255,255,0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span style={{ fontSize: 22 }}>🔇</span>
            </div>
            {/* Skip */}
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255,255,255,0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span style={{ fontSize: 22 }}>⏭️</span>
            </div>
            {/* End Call */}
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                background: `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed || '#db322f'})`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: `0 4px 20px ${COLORS.primaryRed}50`,
              }}
            >
              <span style={{ fontSize: 22 }}>📵</span>
            </div>
          </div>
        </div>

        {/* Divider */}
        <div
          style={{
            width: 1,
            background: 'rgba(255,255,255,0.08)',
            margin: '0 48px',
            opacity: interpolate(frame, [20, 40], [0, 1], { extrapolateRight: 'clamp' }),
          }}
        />

        {/* Right Panel - Transcript */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            transform: `translateX(${rightX}px)`,
            opacity: interpolate(frame, [20, 40], [0, 1], { extrapolateRight: 'clamp' }),
          }}
        >
          {/* Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 24,
            }}
          >
            <p
              style={{
                margin: 0,
                fontSize: 16,
                fontWeight: 700,
                color: 'rgba(255,255,255,0.9)',
                fontFamily: 'Plus Jakarta Sans, sans-serif',
              }}
            >
              Transkrip Live
            </p>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                background: 'rgba(22,163,74,0.2)',
                border: '1px solid rgba(22,163,74,0.4)',
                borderRadius: 999,
                padding: '4px 12px',
              }}
            >
              <div
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: '#16a34a',
                  opacity: pulse,
                }}
              />
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  color: '#16a34a',
                  fontFamily: 'Plus Jakarta Sans, sans-serif',
                  letterSpacing: '0.08em',
                }}
              >
                LIVE
              </span>
            </div>
          </div>

          {/* Transcript items */}
          <div style={{ flex: 1, overflowY: 'hidden' }}>
            {transcriptLines.map(({ text, role, startFrame }) => (
              <TranscriptItem key={text} text={text} role={role} startFrame={startFrame} />
            ))}
          </div>

          {/* Disclaimer */}
          <p
            style={{
              margin: 0,
              fontSize: 11,
              color: 'rgba(255,255,255,0.25)',
              fontFamily: 'Plus Jakarta Sans, sans-serif',
              lineHeight: 1.5,
              borderTop: '1px solid rgba(255,255,255,0.06)',
              paddingTop: 12,
            }}
          >
            DENAI dapat memberikan estimasi. Verifikasi dengan sumber resmi.
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
};
