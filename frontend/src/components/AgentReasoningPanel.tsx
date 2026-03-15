"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { AgentAssessment, FraudVerdict } from "@/lib/types";
import { AGENT_COLORS, VERDICT_COLORS } from "@/lib/types";

interface AgentReasoningPanelProps {
  assessments: AgentAssessment[];
  isAnalyzing: boolean;
  verdict: FraudVerdict | null;
}

function getScoreColor(score: number): string {
  if (score <= 30) return "#22c55e";
  if (score <= 60) return "#f59e0b";
  return "#ef4444";
}

function getAgentColor(name: string): string {
  return AGENT_COLORS[name] ?? "#71717a";
}

function AgentCard({
  assessment,
  index,
}: {
  assessment: AgentAssessment;
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const color = getAgentColor(assessment.agent_name);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.15, duration: 0.3 }}
      className="border border-border rounded-lg p-3 bg-background/50"
    >
      {/* Agent header */}
      <div className="flex items-center gap-2 mb-2">
        <span
          className="w-2 h-2 rounded-full shrink-0"
          style={{ backgroundColor: color }}
        />
        <span className="text-sm font-medium text-foreground/80">
          {assessment.agent_name}
        </span>
        <span className="ml-auto text-xs font-mono text-muted-foreground tabular-nums">
          {(assessment.confidence * 100).toFixed(0)}%
        </span>
      </div>

      {/* Risk score bar */}
      <div className="flex items-center gap-2 mb-2">
        <div className="bg-secondary rounded-full h-1.5 w-full flex-1">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${assessment.risk_score}%` }}
            transition={{ duration: 0.7, ease: "easeOut" }}
            className="h-1.5 rounded-full"
            style={{ backgroundColor: getScoreColor(assessment.risk_score) }}
          />
        </div>
        <span className="text-xs text-muted-foreground font-mono whitespace-nowrap tabular-nums">
          {assessment.risk_score}/100
        </span>
      </div>

      {/* Signals */}
      {assessment.signals.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {assessment.signals.map((signal, i) => (
            <Badge
              key={i}
              variant="secondary"
              className="text-[10px] font-mono bg-secondary text-muted-foreground border-border hover:bg-secondary"
            >
              {signal}
            </Badge>
          ))}
        </div>
      )}

      {/* Explanation */}
      {assessment.explanation && (
        <div>
          <p
            className={`text-xs text-muted-foreground leading-relaxed ${
              !expanded ? "line-clamp-2" : ""
            }`}
          >
            {assessment.explanation}
          </p>
          {assessment.explanation.length > 120 && (
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-primary hover:text-primary/80 mt-0.5"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>
      )}
    </motion.div>
  );
}

export function VerdictCard({ verdict }: { verdict: FraudVerdict }) {
  const borderColor = VERDICT_COLORS[verdict.verdict];

  return (
    <motion.div
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="bg-card border border-border rounded-xl p-4 flex flex-col"
    >
      <h2 className="text-xs uppercase tracking-wider text-muted-foreground mb-3">
        Verdict
      </h2>
      <div className="flex-1 flex flex-col items-center justify-center">
        <span
          className="text-5xl font-bold font-mono tracking-wider mb-4"
          style={{
            color: borderColor,
            textShadow: `0 0 20px ${borderColor}40`,
          }}
        >
          {verdict.verdict}
        </span>
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed mb-2">
        {verdict.explanation}
      </p>
      <span className="text-[10px] font-mono text-muted-foreground/50 tabular-nums">
        Score: {verdict.final_score}/100 &middot; {verdict.processing_time_ms}ms
      </span>
    </motion.div>
  );
}

function SkeletonCards() {
  return (
    <div className="grid grid-cols-2 gap-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="border border-border rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <Skeleton className="w-2 h-2 rounded-full" />
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-3 w-8 ml-auto" />
          </div>
          <Skeleton className="h-1.5 w-full rounded-full mb-2" />
          <div className="flex gap-1">
            <Skeleton className="h-4 w-16 rounded" />
            <Skeleton className="h-4 w-20 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function AgentReasoningPanel({
  assessments,
  isAnalyzing,
  verdict,
}: AgentReasoningPanelProps) {
  return (
    <div className="bg-card border border-border rounded-xl p-4 flex-1 min-h-0 overflow-y-auto">
      {/* Title */}
      <div className="flex items-center gap-2 mb-3">
        <h2 className="text-xs uppercase tracking-wider text-muted-foreground">
          Agent analysis
        </h2>
        {isAnalyzing && (
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
          </span>
        )}
      </div>

      {/* Waiting skeleton state */}
      {isAnalyzing && assessments.length === 0 && <SkeletonCards />}

      {/* No analysis yet */}
      {!isAnalyzing && assessments.length === 0 && !verdict && (
        <div className="text-sm text-muted-foreground">
          Submit a transaction to see agent reasoning
        </div>
      )}

      {/* Agent assessment cards */}
      <AnimatePresence>
        <div className="grid grid-cols-2 gap-2">
          {assessments.map((assessment, index) => (
            <AgentCard
              key={assessment.agent_name}
              assessment={assessment}
              index={index}
            />
          ))}
        </div>
      </AnimatePresence>

      {/* Analyzing indicator after cards */}
      {isAnalyzing && assessments.length > 0 && assessments.length < 4 && (
        <div className="text-xs text-muted-foreground font-mono mt-2">
          <span className="typing-cursor">Waiting for more agents...</span>
        </div>
      )}
    </div>
  );
}
