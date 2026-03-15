"use client";

import { useState } from "react";
import { PRESET_TRANSACTIONS } from "@/lib/types";
import type { AnalyzeRequest } from "@/lib/types";

interface JudgeTestFormProps {
  onSubmit: (transaction: AnalyzeRequest) => void;
  isAnalyzing: boolean;
}

const DEFAULT_VALUES: AnalyzeRequest = {
  amount: 500,
  card_id: "card_1_visa_debit",
  merchant_id: "merchant_W_300",
  product_category: "W",
  hour_of_day: 14,
};

export function JudgeTestForm({ onSubmit, isAnalyzing }: JudgeTestFormProps) {
  const [formValues, setFormValues] = useState<AnalyzeRequest>({
    ...DEFAULT_VALUES,
  });

  const handlePreset = (data: Partial<AnalyzeRequest>) => {
    setFormValues({ ...DEFAULT_VALUES, ...data });
  };

  const handleChange = (field: keyof AnalyzeRequest, value: string) => {
    setFormValues((prev) => ({
      ...prev,
      [field]:
        field === "amount" || field === "hour_of_day"
          ? value === ""
            ? 0
            : parseFloat(value)
          : value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formValues);
  };

  return (
    <div className="bg-card-bg border border-border rounded-lg p-4">
      <h2 className="text-sm font-semibold text-text-primary mb-3">
        Transaction Input
      </h2>

      {/* Preset Buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        {PRESET_TRANSACTIONS.map((preset) => (
          <button
            key={preset.label}
            type="button"
            disabled={isAnalyzing}
            onClick={() => handlePreset(preset.data)}
            className="px-3 py-1.5 text-sm rounded-md border border-border bg-card-bg hover:bg-accent/20 text-text-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title={preset.description}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Form Fields */}
      <form onSubmit={handleSubmit}>
        {/* Amount - full width */}
        <div className="mb-3">
          <label className="block text-xs font-medium text-text-secondary uppercase tracking-wide mb-1">
            Amount
          </label>
          <input
            type="number"
            required
            min={0}
            step="0.01"
            value={formValues.amount}
            onChange={(e) => handleChange("amount", e.target.value)}
            disabled={isAnalyzing}
            className="w-full px-3 py-2 rounded-md bg-bg-primary border border-border text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50"
          />
        </div>

        {/* Grid layout for remaining fields */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="block text-xs font-medium text-text-secondary uppercase tracking-wide mb-1">
              Card ID
            </label>
            <input
              type="text"
              required
              value={formValues.card_id}
              onChange={(e) => handleChange("card_id", e.target.value)}
              disabled={isAnalyzing}
              className="w-full px-3 py-2 rounded-md bg-bg-primary border border-border text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-secondary uppercase tracking-wide mb-1">
              Merchant ID
            </label>
            <input
              type="text"
              value={formValues.merchant_id ?? ""}
              onChange={(e) => handleChange("merchant_id", e.target.value)}
              disabled={isAnalyzing}
              className="w-full px-3 py-2 rounded-md bg-bg-primary border border-border text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-secondary uppercase tracking-wide mb-1">
              Product Category
            </label>
            <input
              type="text"
              value={formValues.product_category ?? ""}
              onChange={(e) => handleChange("product_category", e.target.value)}
              disabled={isAnalyzing}
              className="w-full px-3 py-2 rounded-md bg-bg-primary border border-border text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-secondary uppercase tracking-wide mb-1">
              Hour of Day
            </label>
            <input
              type="number"
              min={0}
              max={23.99}
              step={0.5}
              value={formValues.hour_of_day}
              onChange={(e) => handleChange("hour_of_day", e.target.value)}
              disabled={isAnalyzing}
              className="w-full px-3 py-2 rounded-md bg-bg-primary border border-border text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50"
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isAnalyzing}
          className="w-full py-2.5 rounded-md bg-accent text-white font-medium text-sm transition-colors hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isAnalyzing ? "Analyzing..." : "Analyze Transaction"}
        </button>
      </form>
    </div>
  );
}
