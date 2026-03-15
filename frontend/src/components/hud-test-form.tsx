'use client';

import { useState, useEffect } from 'react';
import { fetchSampleCardIds } from '@/lib/api';
import { PRESET_TRANSACTIONS } from '@/lib/types';
import { CSS_COLORS } from '@/lib/colors';
import type { AnalyzeRequest } from '@/lib/types';

interface HudTestFormProps {
  onSubmit: (transaction: AnalyzeRequest) => void;
  isAnalyzing: boolean;
  initialValues?: Partial<AnalyzeRequest>;
}

const DEFAULT_VALUES: AnalyzeRequest = {
  amount: 500,
  card_id: 'card_1662_visa_debit',
  merchant_id: 'merchant_W_315',
  product_category: 'W',
  hour_of_day: 14,
};

const CATEGORY_OPTIONS = [
  { value: 'W', label: 'W — General retail' },
  { value: 'H', label: 'H — Electronics' },
  { value: 'C', label: 'C — Services' },
  { value: 'S', label: 'S — Travel' },
  { value: 'R', label: 'R — Restaurants' },
];

const inputStyle: React.CSSProperties = {
  width: '100%',
  background: 'transparent',
  border: 'none',
  borderBottom: '1px solid rgba(255,255,255,0.1)',
  color: CSS_COLORS.text,
  fontFamily: 'var(--font-mono)',
  fontSize: 11,
  padding: '5px 0',
  outline: 'none',
  letterSpacing: '0.03em',
};

const selectStyle: React.CSSProperties = {
  width: '100%',
  background: 'rgba(4, 8, 20, 0.7)',
  border: '1px solid rgba(255,255,255,0.1)',
  color: CSS_COLORS.text,
  fontFamily: 'var(--font-mono)',
  fontSize: 11,
  padding: '5px 8px',
  borderRadius: 3,
  outline: 'none',
  cursor: 'pointer',
};

export function HudTestForm({ onSubmit, isAnalyzing, initialValues }: HudTestFormProps) {
  const [formValues, setFormValues] = useState<AnalyzeRequest>({ ...DEFAULT_VALUES });
  const [cardIds, setCardIds] = useState<string[]>([]);

  useEffect(() => {
    fetchSampleCardIds(20).then(setCardIds).catch(console.error);
  }, []);

  useEffect(() => {
    if (initialValues) {
      setFormValues(prev => ({ ...prev, ...initialValues }));
    }
  }, [initialValues]);

  const handlePreset = (data: Partial<AnalyzeRequest>) => {
    setFormValues({ ...DEFAULT_VALUES, ...data });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAnalyzing) onSubmit(formValues);
  };

  const hourDisplay = `${String(Math.floor(formValues.hour_of_day)).padStart(2, '0')}:00`;

  return (
    <div className="hud-panel" style={{ padding: 14 }}>
      <div className="hud-label" style={{ marginBottom: 10 }}>
        TRANSACTION INPUT
      </div>

      {/* Preset chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 12 }}>
        {PRESET_TRANSACTIONS.map(preset => (
          <button
            key={preset.label}
            type="button"
            disabled={isAnalyzing}
            onClick={() => handlePreset(preset.data)}
            title={preset.description}
            style={{
              padding: '3px 8px',
              fontSize: 9,
              fontFamily: 'var(--font-ui)',
              fontWeight: 600,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: CSS_COLORS.textDim,
              borderRadius: 2,
              cursor: isAnalyzing ? 'not-allowed' : 'pointer',
            }}
          >
            {preset.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {/* Amount */}
        <div>
          <label className="hud-label" style={{ display: 'block', marginBottom: 4 }}>AMOUNT (USD)</label>
          <input
            type="number"
            required
            min={0}
            step="0.01"
            value={formValues.amount}
            onChange={e => setFormValues(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
            disabled={isAnalyzing}
            style={inputStyle}
            placeholder="0.00"
          />
        </div>

        {/* Card ID */}
        <div>
          <label className="hud-label" style={{ display: 'block', marginBottom: 4 }}>CARD ID</label>
          <select
            value={formValues.card_id}
            onChange={e => setFormValues(prev => ({ ...prev, card_id: e.target.value }))}
            disabled={isAnalyzing}
            style={selectStyle}
          >
            {!cardIds.includes(formValues.card_id) && (
              <option value={formValues.card_id}>{formValues.card_id}</option>
            )}
            {cardIds.map(id => (
              <option key={id} value={id}>{id}</option>
            ))}
          </select>
        </div>

        {/* Category */}
        <div>
          <label className="hud-label" style={{ display: 'block', marginBottom: 4 }}>CATEGORY</label>
          <select
            value={formValues.product_category ?? 'W'}
            onChange={e => setFormValues(prev => ({ ...prev, product_category: e.target.value }))}
            disabled={isAnalyzing}
            style={selectStyle}
          >
            {CATEGORY_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Hour slider */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <label className="hud-label">HOUR OF DAY</label>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: CSS_COLORS.info }}>
              {hourDisplay}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={23}
            step={1}
            value={formValues.hour_of_day}
            onChange={e => setFormValues(prev => ({ ...prev, hour_of_day: parseInt(e.target.value) }))}
            disabled={isAnalyzing}
            className="hud-slider"
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isAnalyzing}
          style={{
            marginTop: 2,
            padding: '8px',
            fontFamily: 'var(--font-ui)',
            fontWeight: 700,
            fontSize: 11,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            background: isAnalyzing ? 'rgba(77,184,255,0.05)' : 'rgba(77,184,255,0.12)',
            border: `1px solid ${isAnalyzing ? 'rgba(255,255,255,0.07)' : CSS_COLORS.info}`,
            color: isAnalyzing ? CSS_COLORS.textDim : CSS_COLORS.info,
            borderRadius: 3,
            cursor: isAnalyzing ? 'not-allowed' : 'pointer',
            boxShadow: isAnalyzing ? 'none' : '0 0 14px rgba(77,184,255,0.15)',
            transition: 'all 0.2s ease',
          }}
        >
          {isAnalyzing ? 'ANALYZING...' : 'ANALYZE TRANSACTION'}
        </button>
      </form>
    </div>
  );
}
