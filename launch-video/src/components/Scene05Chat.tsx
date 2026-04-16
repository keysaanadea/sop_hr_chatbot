import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { COLORS } from '../constants';

const sessions = [
  { title: 'Kebijakan Cuti Tahunan', time: '10:32', active: false },
  { title: 'Lembur & Kompensasi', time: '09:15', active: true },
  { title: 'Benefit Karyawan 2024', time: 'Kemarin', active: false },
];

const chatMessages = [
  {
    role: 'user',
    text: 'Berapa hari cuti tahunan yang saya dapat?',
    startFrame: 25,
  },
  {
    role: 'bot',
    text: 'Berdasarkan kebijakan perusahaan, karyawan berhak mendapatkan 12 hari cuti tahunan setelah masa kerja 1 tahun. Cuti dapat diambil secara bertahap atau sekaligus.',
    startFrame: 50,
  },
  {
    role: 'user',
    text: 'Bagaimana prosedur pengajuannya?',
    startFrame: 110,
  },
  {
    role: 'bot',
    text: 'Pengajuan cuti dilakukan melalui sistem HRIS minimal 3 hari kerja sebelum tanggal cuti. Persetujuan atasan langsung diperlukan sebelum cuti dapat diaktivasi. 📋',
    startFrame: 135,
  },
];

const ChatMessage: React.FC<{
  role: string;
  text: string;
  startFrame: number;
}> = ({ role, text, startFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const msgSpring = spring({
    frame: frame - startFrame,
    fps,
    config: { damping: 18, stiffness: 120 },
  });

  const opacity = interpolate(frame - startFrame, [0, 12], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const y = interpolate(msgSpring, [0, 1], [20, 0]);

  // Typing effect for bot messages
  const isBot = role === 'bot';
  const displayText =
    isBot
      ? text.slice(
          0,
          Math.floor(
            interpolate(frame - startFrame - 5, [0, 40], [0, text.length], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })
          )
        )
      : text;

  if (frame < startFrame) return null;

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isBot ? 'flex-start' : 'flex-end',
        alignItems: 'flex-end',
        gap: 10,
        opacity,
        transform: `translateY(${y}px)`,
        marginBottom: 14,
      }}
    >
      {isBot && (
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            background: `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed || '#db322f'})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <span style={{ color: '#fff', fontSize: 16, fontWeight: 700 }}>D</span>
        </div>
      )}
      <div
        style={{
          maxWidth: '72%',
          background: isBot ? '#ffffff' : `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed || '#db322f'})`,
          borderRadius: isBot ? '4px 16px 16px 16px' : '16px 16px 4px 16px',
          padding: '12px 18px',
          boxShadow: isBot
            ? '0 2px 10px rgba(0,0,0,0.06)'
            : `0 4px 16px ${COLORS.primaryRed}40`,
        }}
      >
        <p
          style={{
            margin: 0,
            fontSize: 15,
            color: isBot ? COLORS.dark : '#ffffff',
            fontFamily: 'Plus Jakarta Sans, sans-serif',
            fontWeight: isBot ? 400 : 500,
            lineHeight: 1.6,
          }}
        >
          {displayText}
        </p>
      </div>
      {!isBot && (
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            background: COLORS.dark,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <span style={{ color: '#fff', fontSize: 14, fontWeight: 700 }}>BS</span>
        </div>
      )}
    </div>
  );
};

export const Scene05Chat: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  const fadeOut = interpolate(frame, [160, 180], [1, 0], { extrapolateLeft: 'clamp' });
  const opacity = Math.min(fadeIn, fadeOut);

  const sidebarSlide = spring({
    frame: frame - 5,
    fps,
    config: { damping: 18, stiffness: 100 },
  });
  const sidebarX = interpolate(sidebarSlide, [0, 1], [-280, 0]);

  const mainSlide = spring({
    frame: frame - 15,
    fps,
    config: { damping: 18, stiffness: 100 },
  });
  const mainOpacity = interpolate(frame, [15, 35], [0, 1], { extrapolateRight: 'clamp' });

  const labelOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        background: COLORS.surfaceLight,
        opacity,
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
          background: `${COLORS.primaryRed}18`,
          border: `1px solid ${COLORS.primaryRed}33`,
          borderRadius: 999,
          padding: '8px 24px',
          opacity: labelOpacity,
        }}
      >
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: COLORS.primaryRed }} />
        <span
          style={{
            color: COLORS.primaryRed,
            fontSize: 14,
            fontWeight: 700,
            letterSpacing: '0.12em',
            fontFamily: 'Plus Jakarta Sans, sans-serif',
          }}
        >
          Mode Chat
        </span>
      </div>

      <div style={{ display: 'flex', height: '100%' }}>
        {/* Sidebar */}
        <div
          style={{
            width: 280,
            background: '#ffffff',
            borderRight: `1px solid ${COLORS.borderSoft}`,
            display: 'flex',
            flexDirection: 'column',
            transform: `translateX(${sidebarX}px)`,
            flexShrink: 0,
            boxShadow: '2px 0 20px rgba(0,0,0,0.04)',
          }}
        >
          {/* Brand */}
          <div
            style={{
              padding: '100px 24px 24px 24px',
              borderBottom: `1px solid ${COLORS.borderSoft}`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: 10,
                  background: `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed || '#db322f'})`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <span style={{ color: '#fff', fontSize: 22, fontWeight: 900 }}>D</span>
              </div>
              <div>
                <p
                  style={{
                    margin: 0,
                    fontSize: 18,
                    fontWeight: 800,
                    color: COLORS.dark,
                    fontFamily: 'Plus Jakarta Sans, sans-serif',
                  }}
                >
                  DENAI
                </p>
                <p
                  style={{
                    margin: 0,
                    fontSize: 11,
                    fontWeight: 600,
                    color: COLORS.lightGray,
                    fontFamily: 'Plus Jakarta Sans, sans-serif',
                    letterSpacing: '0.08em',
                  }}
                >
                  HC Hub
                </p>
              </div>
            </div>

            {/* New Chat Button */}
            <div
              style={{
                marginTop: 16,
                background: COLORS.dark,
                borderRadius: 10,
                padding: '10px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span style={{ color: '#fff', fontSize: 16 }}>+</span>
              <span
                style={{
                  color: '#fff',
                  fontSize: 14,
                  fontWeight: 600,
                  fontFamily: 'Plus Jakarta Sans, sans-serif',
                }}
              >
                Chat Baru
              </span>
            </div>
          </div>

          {/* Session list */}
          <div style={{ padding: '16px 12px', flex: 1 }}>
            <p
              style={{
                margin: '0 0 8px 12px',
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: '0.12em',
                color: COLORS.lightGray,
                fontFamily: 'Plus Jakarta Sans, sans-serif',
                textTransform: 'uppercase',
              }}
            >
              Riwayat Chat
            </p>
            {sessions.map(({ title, time, active }) => (
              <div
                key={title}
                style={{
                  padding: '10px 12px',
                  borderRadius: 10,
                  background: active ? `${COLORS.primaryRed}10` : 'transparent',
                  borderLeft: active ? `3px solid ${COLORS.primaryRed}` : '3px solid transparent',
                  marginBottom: 4,
                }}
              >
                <p
                  style={{
                    margin: 0,
                    fontSize: 13,
                    fontWeight: active ? 600 : 400,
                    color: active ? COLORS.dark : COLORS.darkGray,
                    fontFamily: 'Plus Jakarta Sans, sans-serif',
                  }}
                >
                  {title}
                </p>
                <p
                  style={{
                    margin: 0,
                    fontSize: 11,
                    color: COLORS.lightGray,
                    fontFamily: 'Plus Jakarta Sans, sans-serif',
                  }}
                >
                  {time}
                </p>
              </div>
            ))}
          </div>

          {/* User chip */}
          <div
            style={{
              padding: '16px 20px',
              borderTop: `1px solid ${COLORS.borderSoft}`,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: '50%',
                background: COLORS.dark,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span style={{ color: '#fff', fontSize: 13, fontWeight: 700 }}>BS</span>
            </div>
            <div>
              <p
                style={{
                  margin: 0,
                  fontSize: 13,
                  fontWeight: 600,
                  color: COLORS.dark,
                  fontFamily: 'Plus Jakarta Sans, sans-serif',
                }}
              >
                Budi Santoso
              </p>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  background: '#dbeafe',
                  borderRadius: 999,
                  padding: '2px 8px',
                  marginTop: 2,
                }}
              >
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    color: '#2563eb',
                    fontFamily: 'Plus Jakarta Sans, sans-serif',
                  }}
                >
                  Karyawan
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Main chat area */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            opacity: mainOpacity,
          }}
        >
          {/* Chat header */}
          <div
            style={{
              padding: '100px 32px 20px 32px',
              borderBottom: `1px solid ${COLORS.borderSoft}`,
              background: '#fff',
            }}
          >
            <p
              style={{
                margin: 0,
                fontSize: 16,
                fontWeight: 700,
                color: COLORS.dark,
                fontFamily: 'Plus Jakarta Sans, sans-serif',
              }}
            >
              Lembur & Kompensasi
            </p>
            <p
              style={{
                margin: 0,
                fontSize: 12,
                color: COLORS.lightGray,
                fontFamily: 'Plus Jakarta Sans, sans-serif',
              }}
            >
              DENAI siap membantu
            </p>
          </div>

          {/* Messages */}
          <div
            style={{
              flex: 1,
              padding: '24px 32px',
              overflowY: 'hidden',
            }}
          >
            {chatMessages.map(({ role, text, startFrame }) => (
              <ChatMessage key={text} role={role} text={text} startFrame={startFrame} />
            ))}
          </div>

          {/* Input */}
          <div
            style={{
              padding: '16px 32px 24px',
              background: 'rgba(248,249,252,0.8)',
              backdropFilter: 'blur(10px)',
              borderTop: `1px solid ${COLORS.borderSoft}`,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                background: '#fff',
                border: `1.5px solid ${COLORS.borderSoft}`,
                borderRadius: 14,
                padding: '12px 16px',
                gap: 10,
                boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
              }}
            >
              <span style={{ fontSize: 20, opacity: 0.4 }}>🎤</span>
              <p
                style={{
                  margin: 0,
                  flex: 1,
                  fontSize: 14,
                  color: COLORS.lightGray,
                  fontFamily: 'Plus Jakarta Sans, sans-serif',
                }}
              >
                Ketik pertanyaan Anda...
              </p>
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  background: `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed || '#db322f'})`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <span style={{ color: '#fff', fontSize: 16 }}>→</span>
              </div>
            </div>
            <p
              style={{
                margin: '8px 0 0',
                fontSize: 11,
                textAlign: 'center',
                color: COLORS.lightGray,
                fontFamily: 'Plus Jakarta Sans, sans-serif',
              }}
            >
              DENAI dapat memberikan estimasi. Verifikasi dengan sumber resmi.
            </p>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
