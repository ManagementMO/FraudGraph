'use client';

import { useState, useCallback, useEffect } from 'react';
import { GraphVisualization } from '@/components/graph-visualization';
import { HudHeader } from '@/components/hud-header';
import { HudTestForm } from '@/components/hud-test-form';
import { HudAgentPanel } from '@/components/hud-agent-panel';
import { HudVerdict } from '@/components/hud-verdict';
import { HudFeed } from '@/components/hud-feed';
import { useWebSocket } from '@/hooks/useWebSocket';
import { fetchGraph, normalizeGraphData, WS_URL } from '@/lib/api';
import type { AgentAssessment, FraudVerdict, GraphData, AnalyzeRequest } from '@/lib/types';

export default function Dashboard() {
  const [agentAssessments, setAgentAssessments] = useState<AgentAssessment[]>([]);
  const [verdict, setVerdict] = useState<FraudVerdict | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<Partial<AnalyzeRequest> | undefined>();
  const [feedOpen, setFeedOpen] = useState(true);

  const { connect, send, isConnected, onMessageRef } = useWebSocket(WS_URL);

  // Wire up WebSocket message handler (avoids stale closures via ref)
  useEffect(() => {
    onMessageRef.current = (msg) => {
      switch (msg.type) {
        case 'agent_assessment':
          setAgentAssessments(prev => [...prev, msg.data]);
          break;
        case 'final_verdict':
          setVerdict(msg.data);
          setIsAnalyzing(false);
          break;
        case 'error':
          console.error('WebSocket error:', msg.data.message);
          setIsAnalyzing(false);
          break;
      }
    };
  }, [onMessageRef]);

  const handleSubmit = useCallback(async (transaction: AnalyzeRequest) => {
    setAgentAssessments([]);
    setVerdict(null);
    setGraphData(null);
    setIsAnalyzing(true);

    try {
      const [graph] = await Promise.all([
        fetchGraph(transaction.card_id).catch(err => {
          console.error('Failed to fetch graph:', err);
          return null;
        }),
        isConnected ? Promise.resolve() : connect(),
      ]);
      if (graph) setGraphData(normalizeGraphData(graph));
    } catch (err) {
      console.error('WebSocket connection failed:', err);
      setIsAnalyzing(false);
      return;
    }

    send(transaction);
  }, [isConnected, connect, send]);

  return (
    <>
      {/* Layer 0: 3D graph — full viewport WebGL canvas */}
      <GraphVisualization data={graphData} assessments={agentAssessments} />

      {/* Layer 1: HUD overlay
          pointer-events: none on wrapper so mouse events pass through to graph canvas.
          Individual panels restore pointer-events: auto. */}
      <div style={{
        position: 'fixed',
        inset: 0,
        zIndex: 10,
        pointerEvents: 'none',
      }}>
        {/* Header — full width */}
        <div style={{ pointerEvents: 'auto' }}>
          <HudHeader />
        </div>

        {/* Left panel: transaction form + verdict */}
        <div style={{
          position: 'absolute',
          top: 56,
          left: 16,
          width: 280,
          height: `calc(100vh - 56px - ${feedOpen ? 156 : 36}px - 16px)`,
          display: 'flex',
          flexDirection: 'column',
          pointerEvents: 'auto',
          transition: 'height 0.2s ease',
        }}>
          <HudTestForm
            onSubmit={handleSubmit}
            isAnalyzing={isAnalyzing}
            initialValues={selectedTransaction}
          />
          {verdict && (
            <div style={{ flex: 1, marginTop: 8, minHeight: 0, overflowY: 'auto' }} className="hud-scroll">
              <HudVerdict verdict={verdict} />
            </div>
          )}
        </div>

        {/* Right panel: agent cards (scrollable) */}
        <div style={{
          position: 'absolute',
          top: 56,
          right: 16,
          width: 288,
          maxHeight: `calc(100vh - 56px - ${feedOpen ? 156 : 36}px - 16px)`,
          overflowY: 'auto',
          pointerEvents: 'auto',
          transition: 'max-height 0.2s ease',
        }}
          className="hud-scroll"
        >
          <HudAgentPanel assessments={agentAssessments} isAnalyzing={isAnalyzing} />
        </div>

        {/* Bottom: transaction feed */}
        <div style={{ pointerEvents: 'auto' }}>
          <HudFeed
            onSelectTransaction={setSelectedTransaction}
            isOpen={feedOpen}
            onToggle={() => setFeedOpen(v => !v)}
          />
        </div>
      </div>
    </>
  );
}
