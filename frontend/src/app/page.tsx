"use client";

import { useState, useCallback, useEffect } from "react";
import { HeaderBar } from "@/components/HeaderBar";
import { JudgeTestForm } from "@/components/JudgeTestForm";
import { AgentReasoningPanel, VerdictCard } from "@/components/AgentReasoningPanel";
import { GraphVisualization } from "@/components/GraphVisualization";
import { TransactionFeed } from "@/components/TransactionFeed";
import { useWebSocket } from "@/hooks/useWebSocket";
import { fetchGraph, WS_URL } from "@/lib/api";
import type {
  AgentAssessment,
  FraudVerdict,
  GraphData,
  AnalyzeRequest,
} from "@/lib/types";

export default function Dashboard() {
  const [agentAssessments, setAgentAssessments] = useState<AgentAssessment[]>(
    []
  );
  const [verdict, setVerdict] = useState<FraudVerdict | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedTransaction, setSelectedTransaction] =
    useState<Partial<AnalyzeRequest> | undefined>(undefined);

  const { connect, send, isConnected, onMessageRef } = useWebSocket(WS_URL);

  // Wire up WebSocket message handler (avoids stale closures via ref)
  useEffect(() => {
    onMessageRef.current = (msg) => {
      switch (msg.type) {
        case "agent_assessment":
          setAgentAssessments((prev) => [...prev, msg.data]);
          break;
        case "final_verdict":
          setVerdict(msg.data);
          setIsAnalyzing(false);
          break;
        case "error":
          console.error("WebSocket error:", msg.data.message);
          setIsAnalyzing(false);
          break;
      }
    };
  }, [onMessageRef]);

  const handleSubmit = useCallback(
    async (transaction: AnalyzeRequest) => {
      // Reset state for new analysis
      setAgentAssessments([]);
      setVerdict(null);
      setGraphData(null);
      setIsAnalyzing(true);

      // Connect WebSocket and fetch graph in parallel
      try {
        const [graph] = await Promise.all([
          fetchGraph(transaction.card_id).catch((err) => {
            console.error("Failed to fetch graph:", err);
            return null;
          }),
          isConnected ? Promise.resolve() : connect(),
        ]);
        if (graph) setGraphData(graph);
      } catch (err) {
        console.error("WebSocket connection failed:", err);
        setIsAnalyzing(false);
        return;
      }

      // WebSocket is guaranteed open now — send transaction
      send(transaction);
    },
    [isConnected, connect, send]
  );

  const handleSelectTransaction = useCallback(
    (values: Partial<AnalyzeRequest>) => {
      setSelectedTransaction(values);
    },
    []
  );

  return (
    <div className="flex flex-col h-screen bg-background">
      <HeaderBar />
      <main className="flex-1 grid grid-rows-[1fr_auto] gap-4 p-6 min-h-0">
        {/* Top row: Graph | Form | Agents */}
        <div className="grid grid-cols-[1.4fr_0.8fr_1fr] gap-4 min-h-0">
          <GraphVisualization data={graphData} assessments={agentAssessments} />
          <JudgeTestForm
            onSubmit={handleSubmit}
            isAnalyzing={isAnalyzing}
            initialValues={selectedTransaction}
          />
          <AgentReasoningPanel
            assessments={agentAssessments}
            isAnalyzing={isAnalyzing}
            verdict={verdict}
          />
        </div>
        {/* Bottom row: Feed | Verdict */}
        <div className="grid grid-cols-[1.6fr_1fr] gap-4">
          <TransactionFeed onSelectTransaction={handleSelectTransaction} />
          {verdict ? (
            <VerdictCard verdict={verdict} />
          ) : (
            <div className="bg-card border border-border rounded-xl p-4 flex items-center justify-center">
              <p className="text-sm text-muted-foreground">
                Verdict will appear here after analysis
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
