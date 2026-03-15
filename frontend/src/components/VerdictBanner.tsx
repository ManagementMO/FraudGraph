"use client";

import type { FraudVerdict } from "@/lib/types";

interface VerdictBannerProps {
  verdict: FraudVerdict | null;
  isAnalyzing: boolean;
}

export function VerdictBanner({ verdict, isAnalyzing }: VerdictBannerProps) {
  return (
    <div className="px-4 py-2 border-b border-border bg-card-bg text-text-primary text-center text-sm">
      {isAnalyzing
        ? "Analyzing..."
        : verdict
          ? `${verdict.verdict} - Score: ${verdict.final_score.toFixed(1)} (${verdict.processing_time_ms.toFixed(0)}ms)`
          : "Submit a transaction to analyze"}
    </div>
  );
}
