"use client";

import { useState } from "react";
import type { AgentAssessment } from "@/lib/types";

interface AgentReasoningPanelProps {
  assessments: AgentAssessment[];
  isAnalyzing: boolean;
}

/** Map agent names to colors for the consensus mini-bar */
const AGENT_COLORS = [
  "#60a5fa", // blue
  "#a78bfa", // purple
  "#f472b6", // pink
  "#34d399", // emerald
];

function getScoreColor(score: number): string {
  if (score <= 30) return "#22c55e";
  if (score <= 60) return "#f59e0b";
  return "#ef4444";
}

function AgentCard({ assessment, index }: { assessment: AgentAssessment; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="border border-border rounded-md p-3 mb-3 bg-bg-primary/50"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      {/* Agent name header */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-accent font-bold font-mono text-sm">
          {">"} {assessment.agent_name}
        </span>
        <span className="ml-auto text-xs px-2 py-0.5 rounded-full border border-border text-text-secondary">
          {(assessment.confidence * 100).toFixed(0)}% confident
        </span>
      </div>

      {/* Risk score bar */}
      <div className="flex items-center gap-2 mb-2">
        <div className="bg-bg-primary rounded-full h-2.5 w-full flex-1">
          <div
            className="h-2.5 rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${assessment.risk_score}%`,
              backgroundColor: getScoreColor(assessment.risk_score),
            }}
          />
        </div>
        <span className="text-xs text-text-secondary font-mono whitespace-nowrap">
          {assessment.risk_score}/100
        </span>
      </div>

      {/* Signals */}
      {assessment.signals.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {assessment.signals.map((signal, i) => (
            <span
              key={i}
              className="text-xs font-mono text-text-secondary bg-bg-primary px-1.5 py-0.5 rounded border border-border"
            >
              {signal}
            </span>
          ))}
        </div>
      )}

      {/* Explanation */}
      {assessment.explanation && (
        <div>
          <p
            className={`text-xs text-text-secondary font-mono ${
              !expanded ? "line-clamp-2" : ""
            }`}
          >
            {assessment.explanation}
          </p>
          {assessment.explanation.length > 120 && (
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-accent hover:underline mt-0.5"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function ConsensusBar({ assessments }: { assessments: AgentAssessment[] }) {
  if (assessments.length < 2) return null;

  const scores = assessments.map((a) => a.risk_score);
  const maxScore = Math.max(...scores);
  const minScore = Math.min(...scores);
  const spread = maxScore - minScore;

  return (
    <div className="mt-3 pt-3 border-t border-border">
      {/* Disagreement warning */}
      {spread > 30 && (
        <div className="text-warning bg-warning/10 border border-warning/30 rounded px-3 py-1.5 text-xs font-medium mb-2">
          Agents Disagree (spread: {spread.toFixed(0)} pts)
        </div>
      )}

      {/* Mini summary bar */}
      <div className="text-xs text-text-secondary mb-1 font-medium">
        Score Distribution
      </div>
      <div className="relative bg-bg-primary rounded-full h-3 w-full border border-border">
        {assessments.map((a, i) => (
          <div
            key={a.agent_name}
            className="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full border border-bg-primary"
            style={{
              left: `calc(${a.risk_score}% - 5px)`,
              backgroundColor: AGENT_COLORS[i % AGENT_COLORS.length],
            }}
            title={`${a.agent_name}: ${a.risk_score}`}
          />
        ))}
      </div>
      {/* Legend */}
      <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1.5">
        {assessments.map((a, i) => (
          <div key={a.agent_name} className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-full inline-block"
              style={{
                backgroundColor: AGENT_COLORS[i % AGENT_COLORS.length],
              }}
            />
            <span className="text-xs text-text-secondary font-mono">
              {a.agent_name.replace(" Agent", "")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AgentReasoningPanel({
  assessments,
  isAnalyzing,
}: AgentReasoningPanelProps) {
  return (
    <div className="bg-card-bg border border-border rounded-lg p-4 flex-1 min-h-0 overflow-y-auto">
      {/* Title */}
      <div className="flex items-center gap-2 mb-3">
        <h2 className="text-sm font-semibold text-text-primary">
          Agent Analysis
        </h2>
        {isAnalyzing && (
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-accent" />
          </span>
        )}
      </div>

      {/* Waiting state */}
      {isAnalyzing && assessments.length === 0 && (
        <div className="text-sm text-text-secondary font-mono">
          <span className="typing-cursor">Waiting for agents...</span>
        </div>
      )}

      {/* No analysis yet */}
      {!isAnalyzing && assessments.length === 0 && (
        <div className="text-sm text-text-secondary">
          Submit a transaction to see agent reasoning
        </div>
      )}

      {/* Agent assessment cards */}
      {assessments.map((assessment, index) => (
        <AgentCard key={assessment.agent_name} assessment={assessment} index={index} />
      ))}

      {/* Analyzing indicator after cards */}
      {isAnalyzing && assessments.length > 0 && (
        <div className="text-xs text-text-secondary font-mono mt-1">
          <span className="typing-cursor">Waiting for more agents...</span>
        </div>
      )}

      {/* Consensus / Disagreement Visualization */}
      <ConsensusBar assessments={assessments} />
    </div>
  );
}
