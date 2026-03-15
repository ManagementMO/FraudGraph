"use client";

import { useState, useEffect } from "react";
import { Shield } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchStats } from "@/lib/api";
import type { DashboardStats } from "@/lib/types";

export function HeaderBar() {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch((err) => console.error("Failed to fetch stats:", err));
  }, []);

  return (
    <header className="h-16 px-6 border-b border-border bg-background flex items-center justify-between shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5">
        <Shield className="h-5 w-5 text-primary" />
        <span className="font-bold text-lg text-foreground tracking-tight">
          FraudGraph
        </span>
      </div>

      {/* Stat pills */}
      <div className="flex items-center gap-3">
        {stats ? (
          <>
            <StatPill
              value={stats.total_transactions.toLocaleString()}
              label="transactions"
            />
            <StatPill
              value={`${stats.fraud_rate_pct ?? 0}%`}
              label="fraud rate"
              color="amber"
            />
            <StatPill
              value={stats.node_count.toLocaleString()}
              label="nodes"
            />
          </>
        ) : (
          <>
            <Skeleton className="h-8 w-28 rounded-full" />
            <Skeleton className="h-8 w-24 rounded-full" />
            <Skeleton className="h-8 w-24 rounded-full" />
          </>
        )}

        {/* Online indicator */}
        <div className="flex items-center gap-2 text-sm border border-emerald-400/30 rounded-full px-4 py-1.5">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="text-emerald-400">Agent status: ONLINE</span>
        </div>
      </div>
    </header>
  );
}

function StatPill({
  value,
  label,
  color,
}: {
  value: string;
  label: string;
  color?: "amber" | "emerald";
}) {
  const borderClass =
    color === "amber"
      ? "border-amber-400/30"
      : color === "emerald"
        ? "border-emerald-400/30"
        : "border-border";
  const valueClass =
    color === "amber"
      ? "text-amber-400"
      : color === "emerald"
        ? "text-emerald-400"
        : "text-foreground";

  return (
    <div
      className={`flex items-center gap-1.5 text-sm border ${borderClass} rounded-full px-4 py-1.5`}
    >
      <span className={`font-mono tabular-nums ${valueClass}`}>{value}</span>
      <span className="text-muted-foreground">{label}</span>
    </div>
  );
}
