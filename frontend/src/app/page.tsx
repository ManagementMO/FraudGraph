"use client";

import { useState, useCallback, useEffect } from "react";
import { Header } from "@/components/Header";
import { VerdictBanner } from "@/components/VerdictBanner";
import { JudgeTestForm } from "@/components/JudgeTestForm";
import { AgentReasoningPanel } from "@/components/AgentReasoningPanel";
import { GraphVisualization } from "@/components/GraphVisualization";
import { StatsBar } from "@/components/StatsBar";
import { useWebSocket } from "@/hooks/useWebSocket";
import { fetchGraph } from "@/lib/api";
import { WS_URL } from "@/lib/api";
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
  const [currentTransaction, setCurrentTransaction] =
    useState<AnalyzeRequest | null>(null);

  const { connect, send, disconnect, isConnected, onMessageRef } =
    useWebSocket(WS_URL);

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
      setCurrentTransaction(transaction);

      // Connect WebSocket if not already connected
      if (!isConnected) {
        connect();
      }

      // Fetch graph data in parallel
      try {
        const graph = await fetchGraph(transaction.card_id);
        setGraphData(graph);
      } catch (err) {
        console.error("Failed to fetch graph:", err);
      }

      // Send transaction for analysis via WebSocket
      // Small delay to ensure WebSocket is connected after connect() call
      setTimeout(() => {
        send(transaction);
      }, 100);
    },
    [isConnected, connect, send]
  );

  // Suppress unused variable warnings for currentTransaction and disconnect
  void currentTransaction;
  void disconnect;

  return (
    <div className="flex flex-col h-screen bg-bg-primary">
      <Header />
      <VerdictBanner verdict={verdict} isAnalyzing={isAnalyzing} />
      <main className="flex-1 grid grid-cols-[1fr_1.5fr] gap-4 p-4 min-h-0">
        {/* Left column */}
        <div className="flex flex-col gap-4 min-h-0">
          <JudgeTestForm onSubmit={handleSubmit} isAnalyzing={isAnalyzing} />
          <AgentReasoningPanel
            assessments={agentAssessments}
            isAnalyzing={isAnalyzing}
          />
        </div>
        {/* Right column (larger - hero graph) */}
        <div className="flex flex-col gap-4 min-h-0">
          <GraphVisualization
            data={graphData}
            assessments={agentAssessments}
          />
          <StatsBar />
        </div>
      </main>
    </div>
  );
}
