"use client";

import { useEffect, useRef, useState } from "react";
import { VERDICT_COLORS } from "@/lib/types";
import type { FraudVerdict } from "@/lib/types";

interface VerdictBannerProps {
  verdict: FraudVerdict | null;
  isAnalyzing: boolean;
}

/** Ease-out cubic: 1 - (1 - t)^3 */
function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

function useCountUp(target: number, duration: number = 1000) {
  const [displayValue, setDisplayValue] = useState(0);
  const rafRef = useRef<number | null>(null);
  const prevTarget = useRef<number | null>(null);

  useEffect(() => {
    // Only animate when target changes to a new non-zero value
    if (target === prevTarget.current) return;
    prevTarget.current = target;

    if (target === 0) {
      setDisplayValue(0);
      return;
    }

    const startTime = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeOutCubic(progress);
      setDisplayValue(easedProgress * target);

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [target, duration]);

  return displayValue;
}

export function VerdictBanner({ verdict, isAnalyzing }: VerdictBannerProps) {
  const [flash, setFlash] = useState(false);
  const prevVerdictId = useRef<string | null>(null);

  const animatedScore = useCountUp(verdict?.final_score ?? 0, 1000);

  // Trigger flash animation when a new verdict arrives
  useEffect(() => {
    if (!verdict) return;
    if (verdict.transaction_id === prevVerdictId.current) return;
    prevVerdictId.current = verdict.transaction_id;

    setFlash(true);
    const timer = setTimeout(() => setFlash(false), 600);
    return () => clearTimeout(timer);
  }, [verdict]);

  // No verdict and not analyzing: collapsed state
  if (!verdict && !isAnalyzing) {
    return (
      <div className="px-4 py-2 border-b border-border bg-card-bg text-text-secondary text-center text-sm">
        Submit a transaction to analyze
      </div>
    );
  }

  // Analyzing but no verdict yet: pulse state
  if (isAnalyzing && !verdict) {
    return (
      <div className="px-4 py-3 border-b border-border bg-card-bg text-text-primary text-center text-sm animate-pulse">
        Analyzing...
      </div>
    );
  }

  // Verdict display
  if (!verdict) return null;

  const verdictColor = VERDICT_COLORS[verdict.verdict];

  return (
    <div
      className="w-full px-4 py-3 border-b border-border transition-colors duration-500"
      style={{
        backgroundColor: flash
          ? `${verdictColor}33` // ~20% opacity flash
          : `${verdictColor}1a`, // ~10% opacity settled
      }}
    >
      {/* Main verdict row */}
      <div className="flex items-center justify-between">
        {/* Verdict text */}
        <div
          className="text-xl font-bold tracking-wide"
          style={{ color: verdictColor }}
        >
          {verdict.verdict}
        </div>

        {/* Score */}
        <div className="text-center">
          <div className="text-xs text-text-secondary uppercase tracking-wide">
            Risk Score
          </div>
          <div
            className="text-lg font-bold font-mono"
            style={{ color: verdictColor }}
          >
            {animatedScore.toFixed(1)}/100
          </div>
        </div>

        {/* Processing time */}
        <div className="text-right">
          <div className="text-xs text-text-secondary uppercase tracking-wide">
            Processing Time
          </div>
          <div className="text-sm font-mono text-text-secondary font-semibold">
            {verdict.processing_time_ms.toFixed(0)}ms
          </div>
        </div>
      </div>

      {/* Coordinator explanation */}
      {verdict.explanation && (
        <p className="text-xs text-text-secondary mt-1 line-clamp-2">
          {verdict.explanation}
        </p>
      )}
    </div>
  );
}
