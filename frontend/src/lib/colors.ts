import * as THREE from 'three';

// ── HDR Node Colors ───────────────────────────────────────────────────────────
// Values > 1.0 drive UnrealBloomPass. toneMapped: false MUST be set on all
// materials using these colors, or Three.js will clamp them to [0,1] range.

export function getNodeHDRColor(node: {
  is_fraud: boolean;
  is_target: boolean;
  type: string;
}): THREE.Color {
  if (node.is_target) return new THREE.Color(1.1, 0.78, 0.05); // gold
  if (node.is_fraud)  return new THREE.Color(1.3, 0.15, 0.15); // red

  switch (node.type) {
    case 'card':     return new THREE.Color(0.15, 0.38, 1.0);  // blue
    case 'merchant': return new THREE.Color(0.1,  0.7,  0.45); // teal
    case 'device':   return new THREE.Color(0.38, 0.26, 0.95); // violet
    case 'ip':       return new THREE.Color(0.7,  0.18, 0.55); // pink
    default:         return new THREE.Color(0.28, 0.33, 0.42); // gray
  }
}

// ── CSS Color Constants ───────────────────────────────────────────────────────

export const CSS_COLORS = {
  fraud:    '#ff4545',
  safe:     '#2dffc8',
  info:     '#4db8ff',
  gold:     '#f5c842',
  text:     '#c4d4e8',
  textDim:  'rgba(196, 212, 232, 0.55)',
  surface:  'rgba(4, 8, 20, 0.82)',
  border:   'rgba(255, 255, 255, 0.07)',
  borderHi: 'rgba(255, 255, 255, 0.13)',
} as const;

// ── Agent Identity Colors ─────────────────────────────────────────────────────

export const AGENT_COLORS: Record<string, string> = {
  'Velocity Agent':    '#4db8ff',
  'Geolocation Agent': '#4db8ff',
  'Graph Agent':       '#4db8ff',
  'Behavioral Agent':  '#4db8ff',
};

// ── Verdict Colors ────────────────────────────────────────────────────────────

export const VERDICT_COLORS = {
  APPROVE: '#2dffc8',
  FLAG:    '#f5c842',
  BLOCK:   '#ff4545',
} as const;

// ── Score to CSS Color ────────────────────────────────────────────────────────

export function scoreToColor(score: number): string {
  if (score <= 30) return CSS_COLORS.safe;
  if (score <= 65) return CSS_COLORS.gold;
  return CSS_COLORS.fraud;
}

// ── Link Colors ───────────────────────────────────────────────────────────────

export function getLinkColor(isFraud: boolean): string {
  return isFraud
    ? 'rgba(255, 69, 69, 0.2)'
    : 'rgba(196, 212, 232, 0.06)';
}
