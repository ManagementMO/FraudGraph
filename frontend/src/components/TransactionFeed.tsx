"use client";

import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchSampleTransactions } from "@/lib/api";
import type { SampleTransaction, AnalyzeRequest } from "@/lib/types";

interface TransactionFeedProps {
  onSelectTransaction: (values: Partial<AnalyzeRequest>) => void;
}

export function TransactionFeed({ onSelectTransaction }: TransactionFeedProps) {
  const [transactions, setTransactions] = useState<SampleTransaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSampleTransactions(20)
      .then(setTransactions)
      .catch((err) => console.error("Failed to fetch transactions:", err))
      .finally(() => setLoading(false));
  }, []);

  const handleClick = (txn: SampleTransaction) => {
    onSelectTransaction({
      transaction_id: txn.TransactionID,
      amount: txn.TransactionAmt ?? 0,
      card_id: txn.card_id,
      merchant_id: txn.merchant_id ?? undefined,
      product_category: txn.ProductCD ?? undefined,
      hour_of_day: txn.hour_of_day ?? 12,
    });
  };

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <h2 className="text-sm font-semibold text-foreground mb-0.5">
        Transaction Feed
      </h2>
      <p className="text-xs text-muted-foreground mb-2">Recent transactions</p>
      <div className="max-h-48 overflow-y-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-card z-10">
            <tr className="border-b border-border text-muted-foreground text-xs">
              <th className="text-left py-1.5 px-3 font-medium">ID</th>
              <th className="text-right py-1.5 px-3 font-medium">Amount</th>
              <th className="text-left py-1.5 px-3 font-medium">Category</th>
              <th className="text-left py-1.5 px-3 font-medium">Card</th>
              <th className="text-left py-1.5 px-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-b border-border/50">
                    <td className="py-1.5 px-3">
                      <Skeleton className="h-4 w-20" />
                    </td>
                    <td className="py-1.5 px-3 text-right">
                      <Skeleton className="h-4 w-14 ml-auto" />
                    </td>
                    <td className="py-1.5 px-3">
                      <Skeleton className="h-4 w-8" />
                    </td>
                    <td className="py-1.5 px-3">
                      <Skeleton className="h-4 w-24" />
                    </td>
                    <td className="py-1.5 px-3">
                      <Skeleton className="h-4 w-12" />
                    </td>
                  </tr>
                ))
              : transactions.map((txn) => (
                  <tr
                    key={txn.TransactionID}
                    onClick={() => handleClick(txn)}
                    className="border-b border-border/50 hover:bg-secondary/50 cursor-pointer transition-colors"
                  >
                    <td className="py-1.5 px-3 font-mono text-xs text-muted-foreground">
                      {txn.TransactionID}
                    </td>
                    <td className="py-1.5 px-3 text-right font-mono text-xs text-muted-foreground tabular-nums">
                      ${(txn.TransactionAmt ?? 0).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </td>
                    <td className="py-1.5 px-3">
                      <Badge
                        variant="secondary"
                        className="text-[10px] bg-secondary text-muted-foreground border-border"
                      >
                        {txn.ProductCD ?? "\u2014"}
                      </Badge>
                    </td>
                    <td className="py-1.5 px-3 font-mono text-xs text-muted-foreground max-w-[140px] truncate">
                      {txn.card_id}
                    </td>
                    <td className="py-1.5 px-3">
                      {txn.isFraud ? (
                        <Badge className="text-[10px] bg-red-500/10 text-red-400 border-red-500/30 hover:bg-red-500/10">
                          Fraud
                        </Badge>
                      ) : (
                        <Badge className="text-[10px] bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10">
                          Legit
                        </Badge>
                      )}
                    </td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
