import type * as d3 from "d3";

// ── Backend Schema Mirrors ──────────────────────────────────────────

export interface AgentAssessment {
  agent_name: string;
  risk_score: number; // 0-100
  confidence: number; // 0.0-1.0
  signals: string[];
  explanation: string;
}

export interface FraudVerdict {
  transaction_id: string;
  final_score: number; // 0-100
  verdict: "APPROVE" | "FLAG" | "BLOCK";
  agent_assessments: AgentAssessment[];
  explanation: string;
  processing_time_ms: number;
}

export interface AnalyzeRequest {
  transaction_id?: string;
  amount: number;
  card_id: string;
  merchant_id?: string;
  product_category?: string;
  hour_of_day: number;
  timestamp?: number;
  addr1?: number | null;
  addr2?: number | null;
  device_type?: string | null;
}

// ── WebSocket Message Types ─────────────────────────────────────────

export type WSMessage =
  | { type: "agent_assessment"; data: AgentAssessment }
  | { type: "final_verdict"; data: FraudVerdict }
  | { type: "error"; data: { message: string } };

// ── Graph Types (D3-compatible) ─────────────────────────────────────

export interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  type: "card" | "merchant" | "device" | "unknown";
  is_fraud: boolean;
  is_target: boolean;
}

export interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode;
  target: string | GraphNode;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// ── Dashboard Stats ─────────────────────────────────────────────────

export interface DashboardStats {
  node_count: number;
  edge_count: number;
  community_count: number;
  train_size: number;
  test_size: number;
  card_profile_count: number;
  fraud_rate_train: number | null;
  fraud_rate_test: number | null;
  total_transactions: number;
  fraud_rate_pct: number | null;
}

// ── Sample Transactions ─────────────────────────────────────────────

export interface SampleTransaction {
  TransactionID: string;
  TransactionAmt: number | null;
  card_id: string;
  ProductCD: string | null;
  isFraud: number;
  merchant_id: string | null;
  hour_of_day: number | null;
  [key: string]: unknown;
}

// ── Color Constants ─────────────────────────────────────────────────

export const NODE_COLORS = {
  card: "#3b82f6",
  merchant: "#22c55e",
  device: "#6b7280",
  fraud: "#ef4444",
  unknown: "#6b7280",
} as const;

export const TARGET_BORDER = "#fbbf24";
export const FRAUD_GLOW_COLOR = "#ef4444";

export const VERDICT_COLORS = {
  APPROVE: "#22c55e",
  FLAG: "#f59e0b",
  BLOCK: "#ef4444",
} as const;

// ── Preset Transactions ─────────────────────────────────────────────

export const PRESET_TRANSACTIONS: Array<{
  label: string;
  description: string;
  data: Partial<AnalyzeRequest>;
}> = [
  {
    label: "Suspicious $5K",
    description: "Large electronics purchase at 3 AM",
    data: {
      transaction_id: "demo_suspicious",
      amount: 5000,
      card_id: "card_13926_discover_credit",
      merchant_id: "merchant_H_999",
      product_category: "H",
      hour_of_day: 3,
    },
  },
  {
    label: "Normal $25",
    description: "Small grocery purchase during the day",
    data: {
      transaction_id: "demo_normal",
      amount: 25.50,
      card_id: "card_1662_visa_debit",
      merchant_id: "merchant_W_300",
      product_category: "W",
      hour_of_day: 14,
    },
  },
  {
    label: "Fraud Ring Card",
    description: "Card linked to known fraud network",
    data: {
      transaction_id: "demo_fraud_ring",
      amount: 1200,
      card_id: "card_12695_visa_debit",
      product_category: "W",
      hour_of_day: 22,
    },
  },
  {
    label: "Night Transaction",
    description: "Late-night high-value purchase",
    data: {
      transaction_id: "demo_night",
      amount: 800,
      card_id: "card_13926_discover_credit",
      merchant_id: "merchant_C_500",
      product_category: "C",
      hour_of_day: 2.5,
    },
  },
];
