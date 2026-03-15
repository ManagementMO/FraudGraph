"use client";

import type { GraphData, AgentAssessment } from "@/lib/types";

interface GraphVisualizationProps {
  data: GraphData | null;
  assessments: AgentAssessment[];
}

export function GraphVisualization({
  data,
  assessments,
}: GraphVisualizationProps) {
  void data;
  void assessments;
  return (
    <div className="flex-1 p-4 border border-border rounded-lg bg-card-bg text-text-primary min-h-0">
      GraphVisualization
    </div>
  );
}
