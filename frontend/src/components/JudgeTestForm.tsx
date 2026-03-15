"use client";

import type { AnalyzeRequest } from "@/lib/types";

interface JudgeTestFormProps {
  onSubmit: (transaction: AnalyzeRequest) => void;
  isAnalyzing: boolean;
}

export function JudgeTestForm({ onSubmit, isAnalyzing }: JudgeTestFormProps) {
  void onSubmit;
  void isAnalyzing;
  return (
    <div className="p-4 border border-border rounded-lg bg-card-bg text-text-primary">
      JudgeTestForm
    </div>
  );
}
