'use client';

import { useState, useEffect } from 'react';
import { fetchSampleTransactions } from '@/lib/api';
import { CSS_COLORS } from '@/lib/colors';
import type { SampleTransaction, AnalyzeRequest } from '@/lib/types';

interface HudFeedProps {
  onSelectTransaction: (values: Partial<AnalyzeRequest>) => void;
  isOpen: boolean;
  onToggle: () => void;
}

export function HudFeed({ onSelectTransaction, isOpen, onToggle }: HudFeedProps) {
  const [transactions, setTransactions] = useState<SampleTransaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSampleTransactions(30)
      .then(setTransactions)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleClick = (txn: SampleTransaction) => {
    onSelectTransaction({
      amount: txn.TransactionAmt ?? 100,
      card_id: txn.card_id,
      merchant_id: txn.merchant_id ?? undefined,
      product_category: txn.ProductCD ?? 'W',
      hour_of_day: txn.hour_of_day ?? 12,
    });
  };

  return (
    <div
      className="hud-panel"
      style={{
        position: 'absolute',
        bottom: 0, left: 0, right: 0,
        height: isOpen ? 156 : 36,
        borderLeft: 'none',
        borderRight: 'none',
        borderBottom: 'none',
        borderRadius: 0,
        borderTop: isOpen
          ? `1px solid ${CSS_COLORS.borderHi}`
          : `1px solid ${CSS_COLORS.border}`,
        padding: isOpen ? '10px 0 10px 16px' : '0 0 0 16px',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        transition: 'height 0.2s ease, border-color 0.2s ease',
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingRight: 16,
          height: isOpen ? 'auto' : '100%',
          marginBottom: isOpen ? 8 : 0,
          flexShrink: 0,
        }}
      >
        <span className="hud-label">TRANSACTION FEED</span>
        <button
          onClick={onToggle}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            padding: '3px 6px',
            color: isOpen ? CSS_COLORS.info : CSS_COLORS.textDim,
            fontSize: 10,
            lineHeight: 1,
            display: 'flex',
            alignItems: 'center',
            transition: 'color 0.15s',
          }}
          title={isOpen ? 'Collapse feed' : 'Expand feed'}
        >
          <svg
            width="12"
            height="8"
            viewBox="0 0 12 8"
            fill="none"
            style={{
              transition: 'transform 0.2s ease',
              transform: isOpen ? 'rotate(0deg)' : 'rotate(180deg)',
            }}
          >
            <path
              d="M1 7L6 2L11 7"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>

      {/* Scrollable cards */}
      {isOpen && (
        <div
          className="hud-scroll"
          style={{
            flex: 1,
            overflowX: 'auto',
            overflowY: 'hidden',
            paddingBottom: 2,
          }}
        >
          <div style={{
            display: 'flex',
            gap: 6,
            height: '100%',
            paddingRight: 16,
          }}>
            {loading
              ? Array.from({ length: 10 }).map((_, i) => (
                  <div key={i} style={{
                    width: 160,
                    flexShrink: 0,
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    borderRadius: 3,
                  }} />
                ))
              : transactions.map(txn => (
                  <TxnCard key={txn.TransactionID} txn={txn} onClick={() => handleClick(txn)} />
                ))
            }
          </div>
        </div>
      )}
    </div>
  );
}

function TxnCard({ txn, onClick }: { txn: SampleTransaction; onClick: () => void }) {
  const isFraud = txn.isFraud === 1;
  const statusColor = isFraud ? CSS_COLORS.fraud : CSS_COLORS.safe;
  const amount = txn.TransactionAmt;

  const categoryColors: Record<string, string> = {
    W: CSS_COLORS.textDim,
    H: CSS_COLORS.info,
    C: '#c084fc',
    S: CSS_COLORS.gold,
    R: CSS_COLORS.safe,
  };

  return (
    <div
      onClick={onClick}
      style={{
        width: 160,
        flexShrink: 0,
        padding: '8px 10px',
        background: 'rgba(255,255,255,0.025)',
        border: `1px solid ${isFraud ? 'rgba(255,69,69,0.2)' : 'rgba(255,255,255,0.06)'}`,
        borderTop: `2px solid ${statusColor}`,
        borderRadius: 3,
        cursor: 'pointer',
        transition: 'background 0.15s',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
      onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.04)')}
      onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.025)')}
    >
      {/* ID */}
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 9,
        color: CSS_COLORS.textDim,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        marginBottom: 4,
      }}>
        {txn.TransactionID}
      </div>

      {/* Amount */}
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 15,
        fontWeight: 600,
        color: CSS_COLORS.text,
        marginBottom: 3,
        letterSpacing: '-0.01em',
      }}>
        {amount != null ? `$${amount.toFixed(0)}` : '—'}
      </div>

      {/* Status + category row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 9,
          color: statusColor,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
        }}>
          {isFraud ? 'FRAUD' : 'CLEAN'}
        </span>
        {txn.ProductCD && (
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 9,
            padding: '1px 5px',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 2,
            color: categoryColors[txn.ProductCD] ?? CSS_COLORS.textDim,
          }}>
            {txn.ProductCD}
          </span>
        )}
      </div>

      {/* Card ID */}
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 9,
        color: 'rgba(196,212,232,0.3)',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
      }}>
        {txn.card_id}
      </div>
    </div>
  );
}
