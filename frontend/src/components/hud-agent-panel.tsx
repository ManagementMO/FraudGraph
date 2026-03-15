'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { AGENT_COLORS, CSS_COLORS, scoreToColor } from '@/lib/colors';
import type { AgentAssessment } from '@/lib/types';

interface HudAgentPanelProps {
  assessments: AgentAssessment[];
  isAnalyzing: boolean;
}

// Known agent ordering for skeleton placeholders
const AGENT_NAMES = ['Velocity Agent', 'Geolocation Agent', 'Graph Agent', 'Behavioral Agent'];

export function HudAgentPanel({ assessments, isAnalyzing }: HudAgentPanelProps) {
  const hasAny = assessments.length > 0 || isAnalyzing;

  return (
    <div className="hud-panel" style={{ padding: 14 }}>
      <div className="hud-label" style={{ marginBottom: 10 }}>
        AGENT REASONING
        {isAnalyzing && (
          <span className="typing-cursor" style={{ marginLeft: 6, color: CSS_COLORS.info }} />
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <AnimatePresence>
          {hasAny ? (
            <>
              {/* Render completed assessments */}
              {assessments.map((a, i) => (
                <AgentCard key={a.agent_name} assessment={a} index={i} />
              ))}
              {/* Render skeleton for in-progress agents */}
              {isAnalyzing && assessments.length < AGENT_NAMES.length && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  style={{
                    height: 56,
                    borderRadius: 3,
                    background: 'rgba(255,255,255,0.025)',
                    border: '1px solid rgba(255,255,255,0.06)',
                  }}
                  className="skeleton"
                />
              )}
            </>
          ) : (
            /* Idle state: 4 dim placeholder cards */
            AGENT_NAMES.map(name => (
              <IdleCard key={name} name={name} />
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function AgentCard({ assessment, index }: { assessment: AgentAssessment; index: number }) {
  const agentColor = AGENT_COLORS[assessment.agent_name] ?? CSS_COLORS.info;
  const scoreColor = scoreToColor(assessment.risk_score);

  return (
    <motion.div
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08, duration: 0.3, ease: 'easeOut' }}
      style={{
        borderLeft: `2px solid ${agentColor}`,
        padding: '8px 10px',
        background: 'rgba(255,255,255,0.025)',
        borderRadius: '0 3px 3px 0',
      }}
    >
      {/* Row 1: name + score */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
        <span style={{
          fontFamily: 'var(--font-ui)',
          fontSize: 10,
          fontWeight: 600,
          color: agentColor,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
        }}>
          {assessment.agent_name}
        </span>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: scoreColor,
        }}>
          {assessment.risk_score}
        </span>
      </div>

      {/* Row 2: score bar */}
      <div style={{
        height: 2,
        background: 'rgba(255,255,255,0.06)',
        borderRadius: 1,
        marginBottom: 5,
        overflow: 'hidden',
      }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${assessment.risk_score}%` }}
          transition={{ duration: 0.6, ease: 'easeOut', delay: 0.1 }}
          style={{ height: '100%', background: scoreColor, borderRadius: 1 }}
        />
      </div>

      {/* Row 3: signals */}
      {assessment.signals.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginBottom: 4 }}>
          {assessment.signals.slice(0, 3).map((signal, i) => (
            <span key={i} style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 9,
              padding: '1px 5px',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 2,
              color: CSS_COLORS.textDim,
              letterSpacing: '0.02em',
            }}>
              {signal}
            </span>
          ))}
        </div>
      )}

      {/* Row 4: explanation */}
      <p style={{
        fontFamily: 'var(--font-ui)',
        fontSize: 10,
        color: CSS_COLORS.textDim,
        lineHeight: 1.5,
        margin: 0,
      }}>
        {assessment.explanation}
      </p>
    </motion.div>
  );
}

function IdleCard({ name }: { name: string }) {
  const agentColor = AGENT_COLORS[name] ?? CSS_COLORS.info;
  return (
    <div style={{
      borderLeft: `2px solid rgba(255,255,255,0.08)`,
      padding: '8px 10px',
      background: 'rgba(255,255,255,0.015)',
      borderRadius: '0 3px 3px 0',
      opacity: 0.4,
    }}>
      <div style={{
        fontFamily: 'var(--font-ui)',
        fontSize: 10,
        fontWeight: 600,
        color: agentColor,
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
      }}>
        {name}
      </div>
      <div style={{ height: 2, background: 'rgba(255,255,255,0.04)', borderRadius: 1, marginTop: 6 }} />
    </div>
  );
}
