"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { orgApi } from "@/lib/api";
import { PageHeader, Card, Loading, Stat } from "@/components/ui";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();

  const [criticalPath, setCriticalPath] = useState<Awaited<ReturnType<typeof orgApi.criticalPath>> | null>(null);
  const [forecast, setForecast] = useState<Awaited<ReturnType<typeof orgApi.timelineForecast>> | null>(null);
  const [prediction, setPrediction] = useState<Awaited<ReturnType<typeof orgApi.prediction>> | null>(null);
  const [monteCarlo, setMonteCarlo] = useState<Awaited<ReturnType<typeof orgApi.monteCarlo>> | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!id) return;
    orgApi.criticalPath(id).then(setCriticalPath).catch(() => null);
    orgApi.timelineForecast(id).then(setForecast).catch(() => null);
    orgApi.prediction(id).then(setPrediction).catch(() => null);
  }, [id]);

  async function runMonteCarlo() {
    setRunning(true);
    try {
      setMonteCarlo(await orgApi.monteCarlo(id, 1000));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <PageHeader eyebrow="FR-201 / FR-401" title="Project Detail" subtitle="Deterministic critical path plus probabilistic delivery forecast." />
      <div className="p-8 space-y-6">
        <div className="grid grid-cols-3 gap-4">
          <Card>
            <Stat
              label="Delivery Success Probability"
              value={prediction?.success_probability != null ? `${Math.round(prediction.success_probability * 100)}%` : "—"}
              tone={prediction?.success_probability != null && prediction.success_probability < 0.5 ? "signal" : "calm"}
            />
          </Card>
          <Card>
            <Stat label="Critical Path Duration" value={criticalPath?.total_duration_days != null ? `${criticalPath.total_duration_days}d` : "—"} />
          </Card>
          <Card>
            <Stat
              label="Schedule Buffer"
              value={forecast?.buffer_days != null ? `${forecast.buffer_days}d` : "—"}
              tone={forecast?.at_risk ? "signal" : "default"}
            />
          </Card>
        </div>

        <Card>
          <h2 className="font-display text-lg mb-4">Critical Path</h2>
          {!criticalPath ? (
            <Loading />
          ) : criticalPath.error || criticalPath.critical_path.length === 0 ? (
            <p className="text-sm text-ink-500">{criticalPath.error === "dependency_cycle_detected" ? "Dependency cycle detected in task graph." : "No tasks with dependencies found for this project."}</p>
          ) : (
            <ol className="space-y-2">
              {criticalPath.critical_path.map((t, i) => (
                <li key={t.task_id} className="flex items-center gap-3 text-sm">
                  <span className="font-mono text-ink-500 w-6">{i + 1}.</span>
                  <span className="text-ink-100 flex-1">{t.name}</span>
                  <span className="font-mono text-ink-500">{t.duration_days}d</span>
                </li>
              ))}
            </ol>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-lg">Monte Carlo Forecast</h2>
            <button
              onClick={runMonteCarlo}
              disabled={running}
              className="text-xs bg-signal text-graphite-950 font-medium px-3 py-1.5 rounded hover:opacity-90 disabled:opacity-50"
            >
              {running ? "Running 1000 iterations…" : "Run simulation"}
            </button>
          </div>
          {monteCarlo && !monteCarlo.error ? (
            <div className="grid grid-cols-5 gap-4">
              <Stat label="P50" value={`${monteCarlo.p50_days}d`} />
              <Stat label="P80" value={`${monteCarlo.p80_days}d`} />
              <Stat label="P95" value={`${monteCarlo.p95_days}d`} tone="signal" />
              <Stat label="Min" value={`${monteCarlo.min_days}d`} />
              <Stat label="Max" value={`${monteCarlo.max_days}d`} />
            </div>
          ) : (
            <p className="text-sm text-ink-500">Run the simulation to see the completion-time distribution across 1000 resampled scenarios.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
