"use client";

import type { AgentAssessment } from "@/lib/types";

interface AgentReasoningPanelProps {
  assessments: AgentAssessment[];
  isAnalyzing: boolean;
}

export function AgentReasoningPanel({
  assessments,
  isAnalyzing,
}: AgentReasoningPanelProps) {
  void assessments;
  void isAnalyzing;
  return (
    <div className="flex-1 p-4 border border-border rounded-lg bg-card-bg text-text-primary overflow-auto min-h-0">
      AgentReasoningPanel
    </div>
  );
}
