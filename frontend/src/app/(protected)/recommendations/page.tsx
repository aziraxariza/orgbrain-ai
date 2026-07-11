"use client";

import { useEffect, useState } from "react";
import { orgApi } from "@/lib/api";
import { PageHeader, Card, Loading, EmptyState, Badge } from "@/components/ui";

export default function RecommendationsPage() {
  const [allocations, setAllocations] = useState<Awaited<ReturnType<typeof orgApi.allocationRecommendations>> | null>(null);
  const [decisionType, setDecisionType] = useState<"reorg" | "hire">("reorg");
  const [disruptionWeeks, setDisruptionWeeks] = useState(4);
  const [validation, setValidation] = useState<Awaited<ReturnType<typeof orgApi.validateDecision>> | null>(null);
  const [validating, setValidating] = useState(false);

  useEffect(() => {
    orgApi.allocationRecommendations().then(setAllocations).catch(() => setAllocations([]));
  }, []);

  async function runValidation() {
    setValidating(true);
    setValidation(null);
    try {
      setValidation(
        await orgApi.validateDecision({
          type: decisionType,
          affected_employee_ids: [],
          disruption_weeks: disruptionWeeks,
        })
      );
    } finally {
      setValidating(false);
    }
  }

  return (
    <div>
      <PageHeader eyebrow="FR-503 / FR-502 / FR-601" title="Recommendations" subtitle="Deterministic allocation suggestions and decision validation, explained in plain language." />
      <div className="p-8 space-y-6">
        <Card>
          <h2 className="font-display text-lg mb-4">Resource Allocation</h2>
          {!allocations ? (
            <Loading />
          ) : allocations.length === 0 ? (
            <EmptyState message="No overloaded/underutilized skill-matched pairs found right now." />
          ) : (
            <div className="space-y-2">
              {allocations.map((a, i) => (
                <div key={i} className="border hairline rounded p-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-ink-100">{a.action}</p>
                    <div className="flex gap-1.5 mt-1.5">
                      {a.shared_skills.map((s) => (
                        <Badge key={s} className="text-ink-500 border-ink-500/30">{s}</Badge>
                      ))}
                    </div>
                  </div>
                  <span className="font-mono text-xs text-ink-500 shrink-0 ml-4">{Math.round(a.confidence * 100)}% confidence</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <h2 className="font-display text-lg mb-4">Decision Validation</h2>
          <div className="flex items-end gap-4 mb-4">
            <label className="block">
              <span className="text-xs text-ink-500">Decision type</span>
              <select
                value={decisionType}
                onChange={(e) => setDecisionType(e.target.value as "reorg" | "hire")}
                className="mt-1 bg-graphite-800 border hairline rounded px-3 py-2 text-sm text-ink-100 outline-none focus:border-signal"
              >
                <option value="reorg">Reorg</option>
                <option value="hire">Hire</option>
              </select>
            </label>
            {decisionType === "reorg" && (
              <label className="block">
                <span className="text-xs text-ink-500">Disruption weeks</span>
                <input
                  type="number" min={1} max={12} value={disruptionWeeks}
                  onChange={(e) => setDisruptionWeeks(Number(e.target.value))}
                  className="mt-1 bg-graphite-800 border hairline rounded px-3 py-2 text-sm text-ink-100 outline-none focus:border-signal w-24"
                />
              </label>
            )}
            <button
              onClick={runValidation}
              disabled={validating}
              className="bg-signal text-graphite-950 font-medium text-sm px-4 py-2 rounded hover:opacity-90 disabled:opacity-50"
            >
              {validating ? "Validating…" : "Validate"}
            </button>
          </div>

          {validation && (
            <div className="border hairline rounded p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Badge className={validation.recommended ? "text-calm border-calm/40 bg-calm/10" : "text-severity-critical border-severity-critical/40 bg-severity-critical/10"}>
                  {validation.recommended ? "Recommended" : "Not recommended"}
                </Badge>
              </div>
              <p className="text-sm text-ink-300">{String(validation.rationale ?? "")}</p>
              <div className="border-t hairline pt-3">
                <p className="text-xs text-ink-500 uppercase tracking-wide mb-1.5">Explanation</p>
                <p className="text-sm text-ink-300">{validation.explanation}</p>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
