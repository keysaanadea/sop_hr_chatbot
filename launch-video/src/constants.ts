// DENAI Brand Colors
export const COLORS = {
  primaryRed: '#b7131a',
  primaryDarkRed: '#db322f',
  secondaryBlue: '#4c56af',
  teal: '#006578',
  dark: '#191c1e',
  darkGray: '#5b403d',
  lightGray: '#9CA3AF',
  surfaceLight: '#f8f9fc',
  surfaceLower: '#f2f3f6',
  borderSoft: '#e7e8eb',
  borderWarm: '#e4beb9',
  white: '#ffffff',
  black: '#000000',
  success: '#16a34a',
};

export const GRADIENT_RED = `linear-gradient(135deg, ${COLORS.primaryRed}, ${COLORS.primaryDarkRed})`;
export const GRADIENT_DARK = `linear-gradient(135deg, #0f0f0f, #1a1a2e)`;

// Video config
export const FPS = 30;
export const VIDEO_WIDTH = 1920;
export const VIDEO_HEIGHT = 1080;
export const DURATION_IN_FRAMES = 1050; // 35 seconds

// Scene timings (in frames at 30fps)
export const SCENES = {
  opening: { start: 0, end: 90 },       // 0-3s
  problem: { start: 90, end: 210 },     // 3-7s
  reveal: { start: 210, end: 360 },     // 7-12s
  landing: { start: 360, end: 540 },    // 12-18s
  chat: { start: 540, end: 720 },       // 18-24s
  callMode: { start: 720, end: 870 },   // 24-29s
  closing: { start: 870, end: 1050 },   // 29-35s
};
