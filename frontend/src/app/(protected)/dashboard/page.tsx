"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { orgApi, RiskFinding, Project } from "@/lib/api";
import { PageHeader, Card, Stat, Badge, Loading } from "@/components/ui";
import { severityColor } from "@/lib/utils";

export default function DashboardPage() {
  const [risks, setRisks] = useState<RiskFinding[] | null>(null);
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [imbalance, setImbalance] = useState<Awaited<ReturnType<typeof orgApi.workloadImbalances>> | null>(null);

  useEffect(() => {
    orgApi.risks().then(setRisks).catch(() => setRisks([]));
    orgApi.projects().then(setProjects).catch(() => setProjects([]));
    orgApi.workloadImbalances().then(setImbalance).catch(() => null);
  }, []);

  const critical = risks?.filter((r) => r.severity === "critical").length ?? 0;
  const high = risks?.filter((r) => r.severity === "high").length ?? 0;
  const atRiskProjects = projects?.filter((p) => p.status === "at_risk" || p.status === "blocked").length ?? 0;

  return (
    <div>
      <PageHeader
        eyebrow="Live Read"
        title="Execution Dashboard"
        subtitle="What's actually happening across the org right now, computed fresh from current data."
      />

      <div className="p-8 space-y-8">
        <div className="grid grid-cols-4 gap-4">
          <Card><Stat label="Critical Risks" value={risks ? critical : "—"} tone={critical > 0 ? "signal" : "default"} /></Card>
          <Card><Stat label="High-Severity Risks" value={risks ? high : "—"} /></Card>
          <Card><Stat label="Projects At Risk" value={projects ? atRiskProjects : "—"} /></Card>
          <Card><Stat label="Org Avg Utilization" value={imbalance ? `${Math.round(imbalance.org_avg_utilization * 100)}%` : "—"} /></Card>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-lg">Top Risks</h2>
              <Link href="/risks" className="text-xs text-signal hover:underline">View all →</Link>
            </div>
            {!risks ? (
              <Loading />
            ) : risks.length === 0 ? (
              <p className="text-sm text-ink-500">No risks detected — org is running clean.</p>
            ) : (
              <ul className="space-y-2.5">
                {risks.slice(0, 5).map((r, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <Badge className={severityColor(r.severity)}>{r.severity}</Badge>
                    <p className="text-sm text-ink-300 leading-snug">{r.description}</p>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-lg">Workload Imbalance</h2>
              <Link href="/employees" className="text-xs text-signal hover:underline">View all →</Link>
            </div>
            {!imbalance ? (
              <Loading />
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-ink-300">
                  <span className="text-severity-critical font-mono">{imbalance.overloaded_count}</span> overloaded,{" "}
                  <span className="text-calm font-mono">{imbalance.underutilized_count}</span> underutilized
                </p>
                <ul className="space-y-2">
                  {imbalance.overloaded.slice(0, 4).map((w) => (
                    <li key={w.employee_id} className="flex items-center justify-between text-sm">
                      <span className="text-ink-300">{w.name}</span>
                      <span className="font-mono text-severity-critical">{Math.round(w.utilization_ratio * 100)}%</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>
        </div>

        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-lg">Projects</h2>
            <Link href="/projects" className="text-xs text-signal hover:underline">View all →</Link>
          </div>
          {!projects ? (
            <Loading />
          ) : (
            <div className="grid grid-cols-3 gap-3">
              {projects.slice(0, 6).map((p) => (
                <Link
                  key={p.project_id}
                  href={`/projects/${p.project_id}`}
                  className="border hairline rounded p-3 hover:border-signal/50 transition-colors"
                >
                  <div className="text-sm text-ink-100 truncate">{p.name}</div>
                  <Badge className={statusColor(p.status) + " mt-2"}>{p.status.replace("_", " ")}</Badge>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

function statusColor(status: string) {
  if (status === "at_risk" || status === "blocked") return "text-severity-critical border-severity-critical/40 bg-severity-critical/10";
  if (status === "active") return "text-calm border-calm/40 bg-calm/10";
  return "text-ink-500 border-ink-500/30 bg-transparent";
}
