"use client";

import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { fetchSampleCardIds } from "@/lib/api";
import { PRESET_TRANSACTIONS } from "@/lib/types";
import type { AnalyzeRequest } from "@/lib/types";

interface JudgeTestFormProps {
  onSubmit: (transaction: AnalyzeRequest) => void;
  isAnalyzing: boolean;
  initialValues?: Partial<AnalyzeRequest>;
}

const DEFAULT_VALUES: AnalyzeRequest = {
  amount: 500,
  card_id: "card_1662_visa_debit",
  merchant_id: "merchant_W_315",
  product_category: "W",
  hour_of_day: 14,
};

const CATEGORY_OPTIONS = [
  { value: "W", label: "W - General retail" },
  { value: "H", label: "H - Electronics" },
  { value: "C", label: "C - Services" },
  { value: "S", label: "S - Travel" },
  { value: "R", label: "R - Restaurants" },
];

export function JudgeTestForm({
  onSubmit,
  isAnalyzing,
  initialValues,
}: JudgeTestFormProps) {
  const [formValues, setFormValues] = useState<AnalyzeRequest>({
    ...DEFAULT_VALUES,
  });
  const [cardIds, setCardIds] = useState<string[]>([]);

  // Load sample card IDs
  useEffect(() => {
    fetchSampleCardIds(20)
      .then(setCardIds)
      .catch((err) => console.error("Failed to fetch card IDs:", err));
  }, []);

  // Apply initialValues when they change (from TransactionFeed click)
  useEffect(() => {
    if (initialValues) {
      setFormValues((prev) => ({ ...prev, ...initialValues }));
    }
  }, [initialValues]);

  const handlePreset = (data: Partial<AnalyzeRequest>) => {
    setFormValues({ ...DEFAULT_VALUES, ...data });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formValues);
  };

  return (
    <Card className="rounded-xl bg-card border-border shrink-0">
      <CardHeader className="pb-3 pt-4 px-4">
        <CardTitle className="text-xs uppercase tracking-wider text-muted-foreground">
          Transaction input
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-4 space-y-3">
        {/* Preset buttons */}
        <div className="flex flex-wrap gap-1.5">
          {PRESET_TRANSACTIONS.map((preset) => (
            <Button
              key={preset.label}
              type="button"
              variant="outline"
              size="sm"
              disabled={isAnalyzing}
              onClick={() => handlePreset(preset.data)}
              className="text-xs border-border hover:bg-secondary hover:text-foreground"
              title={preset.description}
            >
              {preset.label}
            </Button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {/* Amount */}
          <div>
            <label className="block text-xs text-muted-foreground mb-1">Amount</label>
            <Input
              type="number"
              required
              min={0}
              step="0.01"
              value={formValues.amount}
              onChange={(e) =>
                setFormValues((prev) => ({
                  ...prev,
                  amount: e.target.value === "" ? 0 : parseFloat(e.target.value),
                }))
              }
              disabled={isAnalyzing}
              className="font-mono bg-background border-border"
            />
          </div>

          {/* Card ID + Category row */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-muted-foreground mb-1">
                Card ID
              </label>
              <Select
                value={formValues.card_id}
                onValueChange={(val) =>
                  setFormValues((prev) => ({ ...prev, card_id: val ?? prev.card_id }))
                }
                disabled={isAnalyzing}
              >
                <SelectTrigger className="bg-background border-border font-mono text-xs">
                  <SelectValue placeholder="Select card" />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  {/* Always include current value */}
                  {!cardIds.includes(formValues.card_id) && (
                    <SelectItem
                      value={formValues.card_id}
                      className="font-mono text-xs"
                    >
                      {formValues.card_id}
                    </SelectItem>
                  )}
                  {cardIds.map((id) => (
                    <SelectItem key={id} value={id} className="font-mono text-xs">
                      {id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1">
                Category
              </label>
              <Select
                value={formValues.product_category ?? "W"}
                onValueChange={(val) =>
                  setFormValues((prev) => ({ ...prev, product_category: val ?? prev.product_category }))
                }
                disabled={isAnalyzing}
              >
                <SelectTrigger className="bg-background border-border text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  {CATEGORY_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="text-xs">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Hour slider */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs text-muted-foreground">Hour of day</label>
              <span className="text-xs font-mono text-muted-foreground tabular-nums">
                {Math.floor(formValues.hour_of_day)}:00
              </span>
            </div>
            <Slider
              min={0}
              max={23}
              step={1}
              value={[formValues.hour_of_day]}
              onValueChange={(val) => {
                const v = Array.isArray(val) ? val[0] : val;
                setFormValues((prev) => ({ ...prev, hour_of_day: v }));
              }}
              disabled={isAnalyzing}
              className="py-1"
            />
          </div>

          {/* Submit */}
          <Button
            type="submit"
            disabled={isAnalyzing}
            className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              "Analyze Transaction"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
