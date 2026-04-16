import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { COLORS } from '../constants';

const problems = [
  { icon: '📋', text: 'Cari kebijakan HR di dokumen fisik...', delay: 0 },
  { icon: '📞', text: 'Hubungi bagian HC untuk tanya-jawab...', delay: 18 },
  { icon: '⏰', text: 'Tunggu jawaban berjam-jam...', delay: 36 },
];

const ProblemItem: React.FC<{ icon: string; text: string; delay: number }> = ({
  icon,
  text,
  delay,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const itemProgress = spring({
    frame: frame - delay,
    fps,
    config: { damping: 18, stiffness: 100 },
  });

  const opacity = interpolate(frame - delay, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const x = interpolate(itemProgress, [0, 1], [-80, 0]);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 24,
        opacity,
        transform: `translateX(${x}px)`,
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 16,
        padding: '20px 32px',
        marginBottom: 16,
        backdropFilter: 'blur(10px)',
      }}
    >
      <span style={{ fontSize: 36 }}>{icon}</span>
      <p
        style={{
          color: 'rgba(255,255,255,0.75)',
          fontSize: 26,
          fontFamily: 'Plus Jakarta Sans, sans-serif',
          fontWeight: 500,
          margin: 0,
        }}
      >
        {text}
      </p>
    </div>
  );
};

export const Scene02Problem: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });
  const fadeOut = interpolate(frame, [100, 120], [1, 0], { extrapolateLeft: 'clamp' });
  const opacity = Math.min(fadeIn, fadeOut);

  const titleY = spring({
    frame,
    fps,
    config: { damping: 16, stiffness: 110 },
  });

  const xTitle = interpolate(titleY, [0, 1], [0, 0]);
  const yTitle = interpolate(titleY, [0, 1], [40, 0]);

  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at 30% 50%, #0d0d1a 0%, #050505 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        padding: '0 160px',
        opacity,
      }}
    >
      {/* Background grid lines */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(183,19,26,0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(183,19,26,0.04) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      <div style={{ position: 'relative', width: '100%', maxWidth: 900 }}>
        {/* Tag */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            background: `${COLORS.primaryRed}22`,
            border: `1px solid ${COLORS.primaryRed}44`,
            borderRadius: 999,
            padding: '6px 20px',
            marginBottom: 32,
            opacity: interpolate(frame, [5, 20], [0, 1], { extrapolateRight: 'clamp' }),
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: COLORS.primaryRed,
            }}
          />
          <span
            style={{
              color: COLORS.primaryRed,
              fontSize: 14,
              fontWeight: 700,
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              fontFamily: 'Plus Jakarta Sans, sans-serif',
            }}
          >
            Tantangan Nyata
          </span>
        </div>

        {/* Title */}
        <h1
          style={{
            color: '#ffffff',
            fontSize: 52,
            fontWeight: 800,
            fontFamily: 'Plus Jakarta Sans, sans-serif',
            margin: '0 0 48px 0',
            lineHeight: 1.2,
            transform: `translate(${xTitle}px, ${yTitle}px)`,
            opacity: interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' }),
          }}
        >
          Karyawan menghabiskan waktu{' '}
          <span style={{ color: COLORS.primaryRed }}>berharga</span> hanya untuk
          mencari informasi HR
        </h1>

        {/* Problem items */}
        <div>
          {problems.map(({ icon, text, delay }) => (
            <ProblemItem key={text} icon={icon} text={text} delay={delay + 25} />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
