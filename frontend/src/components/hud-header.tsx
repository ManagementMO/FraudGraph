'use client';

import { useState, useEffect } from 'react';
import { fetchStats } from '@/lib/api';
import { CSS_COLORS } from '@/lib/colors';
import type { DashboardStats } from '@/lib/types';

export function HudHeader() {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    const load = () => fetchStats().then(setStats).catch(console.error);
    load();
    const interval = setInterval(load, 30_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header
      className="hud-panel"
      style={{
        position: 'absolute',
        top: 0, left: 0, right: 0,
        height: 44,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        borderLeft: 'none',
        borderRight: 'none',
        borderTop: 'none',
        borderRadius: 0,
      }}
    >
      {/* Left: branding */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <svg width="18" height="18" viewBox="0 0 20 20">
          <polygon
            points="10,1 18,5.5 18,14.5 10,19 2,14.5 2,5.5"
            fill="none"
            stroke={CSS_COLORS.info}
            strokeWidth="1.5"
          />
          <circle cx="10" cy="10" r="2.5" fill={CSS_COLORS.info} />
        </svg>
        <span style={{
          fontFamily: 'var(--font-ui)',
          fontWeight: 700,
          fontSize: 15,
          letterSpacing: '0.08em',
          color: CSS_COLORS.text,
        }}>
          FRAUD<span style={{ color: CSS_COLORS.info }}>GRAPH</span>
        </span>
      </div>

      {/* Right: stats + online */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
        {stats ? (
          <>
            <StatReadout label="TRANSACTIONS" value={stats.total_transactions.toLocaleString()} />
            <StatReadout label="FRAUD RATE" value={`${(stats.fraud_rate_pct ?? 0).toFixed(1)}%`} color={CSS_COLORS.gold} />
            <StatReadout label="NODES" value={stats.node_count.toLocaleString()} />
            <StatReadout label="EDGES" value={stats.edge_count.toLocaleString()} />
          </>
        ) : (
          <span className="hud-label">CONNECTING...</span>
        )}

      </div>
    </header>
  );
}

function StatReadout({ label, value, color }: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div style={{ textAlign: 'right' }}>
      <div className="hud-label">{label}</div>
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 12,
        lineHeight: 1.2,
        color: color ?? CSS_COLORS.text,
        letterSpacing: '0.03em',
      }}>
        {value}
      </div>
    </div>
  );
}
