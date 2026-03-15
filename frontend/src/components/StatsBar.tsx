"use client";

import { useStats } from "@/hooks/useStats";

interface StatCardProps {
  label: string;
  value: string;
  loading: boolean;
}

function StatCard({ label, value, loading }: StatCardProps) {
  return (
    <div className="flex flex-col items-center p-2 rounded-md bg-bg-primary/50">
      {loading ? (
        <div className="bg-bg-primary animate-pulse h-6 w-16 rounded" />
      ) : (
        <span className="text-lg font-bold text-text-primary font-mono">
          {value}
        </span>
      )}
      <span className="text-xs text-text-secondary uppercase tracking-wide mt-0.5">
        {label}
      </span>
    </div>
  );
}

export function StatsBar() {
  const { stats, loading, error, refetch } = useStats();

  if (error) {
    return (
      <div className="bg-card-bg border border-border rounded-lg p-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-secondary">
            Failed to load stats
          </span>
          <button
            onClick={refetch}
            className="text-xs text-accent hover:text-text-primary border border-border rounded px-2 py-1 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const formatNumber = (n: number | undefined | null): string => {
    if (n == null) return "N/A";
    return n.toLocaleString();
  };

  return (
    <div className="bg-card-bg border border-border rounded-lg p-3">
      <div className="grid grid-cols-5 gap-3">
        <StatCard
          label="Transactions"
          value={formatNumber(stats?.total_transactions)}
          loading={loading}
        />
        <StatCard
          label="Fraud Rate"
          value={
            stats?.fraud_rate_pct != null
              ? stats.fraud_rate_pct.toFixed(2) + "%"
              : "N/A"
          }
          loading={loading}
        />
        <StatCard
          label="Graph Nodes"
          value={formatNumber(stats?.node_count)}
          loading={loading}
        />
        <StatCard
          label="Graph Edges"
          value={formatNumber(stats?.edge_count)}
          loading={loading}
        />
        <StatCard
          label="Communities"
          value={formatNumber(stats?.community_count)}
          loading={loading}
        />
      </div>
    </div>
  );
}
