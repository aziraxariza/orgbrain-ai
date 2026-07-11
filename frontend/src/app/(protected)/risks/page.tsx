"use client";

import { useEffect, useState } from "react";
import { orgApi, RiskFinding } from "@/lib/api";
import { PageHeader, Card, Loading, Badge, EmptyState } from "@/components/ui";
import { severityColor } from "@/lib/utils";

const TYPE_LABEL: Record<string, string> = {
  execution_drift: "Execution Drift",
  bottleneck: "Bottleneck",
  dependency_concentration: "Dependency Concentration",
  capacity_violation: "Capacity Violation",
};

export default function RisksPage() {
  const [risks, setRisks] = useState<RiskFinding[] | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>("all");

  useEffect(() => {
    orgApi.risks().then(setRisks).catch(() => setRisks([]));
  }, []);

  const types = ["all", ...Object.keys(TYPE_LABEL)];
  const filtered = risks?.filter((r) => typeFilter === "all" || r.risk_type === typeFilter) ?? [];

  return (
    <div>
      <PageHeader eyebrow="FR-301 – FR-304" title="Risk Feed" subtitle="Every detector's output, ranked by severity score. Recomputed live from current state." />
      <div className="p-8">
        <div className="flex gap-2 mb-5 flex-wrap">
          {types.map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`text-xs px-3 py-1.5 rounded border hairline ${
                typeFilter === t ? "bg-graphite-700 text-ink-100" : "text-ink-500 hover:text-ink-100"
              }`}
            >
              {t === "all" ? "All" : TYPE_LABEL[t]}
            </button>
          ))}
        </div>

        {!risks ? (
          <Loading />
        ) : filtered.length === 0 ? (
          <EmptyState message="No risks matching this filter." />
        ) : (
          <div className="space-y-2">
            {filtered.map((r, i) => (
              <Card key={i} className="flex items-start gap-4">
                <Badge className={severityColor(r.severity) + " shrink-0"}>{r.severity}</Badge>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-ink-500 uppercase tracking-wide">{TYPE_LABEL[r.risk_type]}</span>
                    <span className="text-xs text-ink-500 font-mono">score {r.severity_score}</span>
                  </div>
                  <p className="text-sm text-ink-100">{r.description}</p>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
