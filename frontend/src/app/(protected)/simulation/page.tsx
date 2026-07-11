"use client";

import { useEffect, useState } from "react";
import { orgApi, Project, Employee } from "@/lib/api";
import { PageHeader, Card, Loading, Stat } from "@/components/ui";

export default function SimulationPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [projectId, setProjectId] = useState<string>("");
  const [employeeId, setEmployeeId] = useState<string>("");
  const [extraHours, setExtraHours] = useState(10);
  const [result, setResult] = useState<Awaited<ReturnType<typeof orgApi.whatIf>> | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    orgApi.projects().then((ps) => {
      setProjects(ps);
      if (ps[0]) setProjectId(ps[0].project_id);
    });
    orgApi.employees().then((es) => {
      setEmployees(es);
      if (es[0]) setEmployeeId(es[0].employee_id);
    });
  }, []);

  async function run() {
    if (!projectId) return;
    setRunning(true);
    setResult(null);
    try {
      const addCapacity = employeeId ? [{ employee_id: employeeId, extra_hours_per_week: extraHours }] : [];
      setResult(await orgApi.whatIf(projectId, [], addCapacity));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <PageHeader eyebrow="FR-501" title='"What-If" Simulation' subtitle="Applied in a transaction that's always rolled back — nothing here touches real data." />
      <div className="p-8 grid grid-cols-2 gap-6">
        <Card>
          <h2 className="font-display text-lg mb-4">Scenario: Add Capacity</h2>
          <div className="space-y-4">
            <Field label="Project">
              <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className={selectClass}>
                {projects.map((p) => (
                  <option key={p.project_id} value={p.project_id}>{p.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Employee to add capacity to">
              <select value={employeeId} onChange={(e) => setEmployeeId(e.target.value)} className={selectClass}>
                {employees.map((e) => (
                  <option key={e.employee_id} value={e.employee_id}>{e.name}</option>
                ))}
              </select>
            </Field>
            <Field label={`Extra hours/week: ${extraHours}`}>
              <input
                type="range" min={0} max={40} value={extraHours}
                onChange={(e) => setExtraHours(Number(e.target.value))}
                className="w-full accent-signal"
              />
            </Field>
            <button
              onClick={run}
              disabled={running || !projectId}
              className="w-full bg-signal text-graphite-950 font-medium text-sm py-2 rounded hover:opacity-90 disabled:opacity-50"
            >
              {running ? "Simulating…" : "Run scenario"}
            </button>
          </div>
        </Card>

        <Card>
          <h2 className="font-display text-lg mb-4">Result</h2>
          {!result ? (
            <p className="text-sm text-ink-500">Run a scenario to see baseline vs. scenario delta.</p>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Stat label="Baseline Critical Path" value={`${result.baseline.critical_path_days ?? "—"}d`} />
                <Stat label="Scenario Critical Path" value={`${result.scenario.critical_path_days ?? "—"}d`} />
              </div>
              <Stat
                label="Delta"
                value={result.delta_critical_path_days != null ? `${result.delta_critical_path_days > 0 ? "+" : ""}${result.delta_critical_path_days}d` : "—"}
                tone={result.delta_critical_path_days != null && result.delta_critical_path_days < 0 ? "calm" : "signal"}
              />
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

const selectClass = "mt-1 w-full bg-graphite-800 border hairline rounded px-3 py-2 text-sm text-ink-100 focus:border-signal outline-none";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs text-ink-500">{label}</span>
      {children}
    </label>
  );
}
