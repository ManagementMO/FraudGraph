import type {
  DashboardStats,
  GraphData,
  SampleTransaction,
  FraudVerdict,
  AnalyzeRequest,
} from "./types";

// ── Base URLs ───────────────────────────────────────────────────────

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/stream";

// ── Fetch Helpers ───────────────────────────────────────────────────

export async function fetchStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`);
  return res.json();
}

export async function fetchGraph(
  cardId: string,
  depth: number = 2,
  maxNodes: number = 50
): Promise<GraphData> {
  const res = await fetch(
    `${API_BASE}/graph/${cardId}?depth=${depth}&max_nodes=${maxNodes}`
  );
  if (!res.ok) throw new Error(`Failed to fetch graph: ${res.status}`);
  return res.json();
}

export async function fetchSampleTransactions(
  n?: number
): Promise<SampleTransaction[]> {
  const url = n
    ? `${API_BASE}/sample-transactions?n=${n}`
    : `${API_BASE}/sample-transactions`;
  const res = await fetch(url);
  if (!res.ok)
    throw new Error(`Failed to fetch sample transactions: ${res.status}`);
  return res.json();
}

export function getWebSocketUrl(): string {
  return WS_URL;
}

export async function fetchSampleCardIds(n: number = 20): Promise<string[]> {
  const res = await fetch(`${API_BASE}/sample-card-ids?n=${n}`);
  if (!res.ok) throw new Error(`Failed to fetch sample card IDs: ${res.status}`);
  return res.json();
}

export async function analyzeTransaction(
  req: AnalyzeRequest
): Promise<FraudVerdict> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Failed to analyze transaction: ${res.status}`);
  return res.json();
}

export function normalizeGraphData(raw: GraphData): GraphData {
  return {
    nodes: raw.nodes.map(n => ({ ...n, val: n.val ?? 5 })),
    links: raw.links,
  };
}
