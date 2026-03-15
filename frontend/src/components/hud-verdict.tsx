'use client';

import { motion } from 'framer-motion';
import { VERDICT_COLORS, CSS_COLORS } from '@/lib/colors';
import type { FraudVerdict } from '@/lib/types';

interface HudVerdictProps {
  verdict: FraudVerdict;
}

export function HudVerdict({ verdict }: HudVerdictProps) {
  const color = VERDICT_COLORS[verdict.verdict];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 8 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="hud-panel"
      style={{
        padding: 14,
        marginTop: 0,
        height: '100%',
        boxSizing: 'border-box',
        borderColor: `${color}40`,
      }}
    >
      <div className="hud-label" style={{ marginBottom: 8 }}>FINAL VERDICT</div>

      {/* Verdict badge */}
      <div style={{ textAlign: 'center', padding: '10px 0 12px' }}>
        <div style={{
          fontFamily: 'var(--font-ui)',
          fontWeight: 700,
          fontSize: 28,
          letterSpacing: '0.2em',
          color,
          textShadow: `0 0 28px ${color}80`,
        }}>
          {verdict.verdict}
        </div>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: CSS_COLORS.textDim,
          marginTop: 4,
          letterSpacing: '0.06em',
        }}>
          SCORE: {verdict.final_score.toFixed(0)}/100
        </div>
      </div>

      {/* Score bar */}
      <div style={{
        height: 2,
        background: 'rgba(255,255,255,0.06)',
        borderRadius: 1,
        marginBottom: 10,
        overflow: 'hidden',
      }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${verdict.final_score}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          style={{ height: '100%', background: color, borderRadius: 1 }}
        />
      </div>

      {/* Explanation */}
      <p style={{
        fontFamily: 'var(--font-ui)',
        fontSize: 10,
        color: CSS_COLORS.textDim,
        lineHeight: 1.6,
        margin: 0,
        marginBottom: 8,
      }}>
        {verdict.explanation}
      </p>

      {/* Footer */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        fontFamily: 'var(--font-mono)',
        fontSize: 9,
        color: 'rgba(196,212,232,0.25)',
        letterSpacing: '0.04em',
      }}>
        <span>{verdict.processing_time_ms}ms</span>
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 150, whiteSpace: 'nowrap' }}>
          {verdict.transaction_id}
        </span>
      </div>
    </motion.div>
  );
}
