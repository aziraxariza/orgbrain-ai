"use client";

import { useEffect, useState } from "react";
import { orgApi, WorkloadEntry } from "@/lib/api";
import { PageHeader, Card, Loading, Badge } from "@/components/ui";
import { bandColor } from "@/lib/utils";

export default function EmployeesPage() {
  const [workload, setWorkload] = useState<WorkloadEntry[] | null>(null);
  const [bandFilter, setBandFilter] = useState<string>("all");

  useEffect(() => {
    orgApi.workload().then(setWorkload).catch(() => setWorkload([]));
  }, []);

  const filtered = workload?.filter((w) => bandFilter === "all" || w.band === bandFilter) ?? [];
  const bands = ["all", "overloaded", "at_capacity", "healthy", "underutilized"];

  return (
    <div>
      <PageHeader eyebrow="FR-102" title="Employees & Workload" subtitle="Remaining committed hours vs. available capacity, ranked by utilization." />
      <div className="p-8">
        <div className="flex gap-2 mb-5">
          {bands.map((b) => (
            <button
              key={b}
              onClick={() => setBandFilter(b)}
              className={`text-xs px-3 py-1.5 rounded border hairline capitalize ${
                bandFilter === b ? "bg-graphite-700 text-ink-100" : "text-ink-500 hover:text-ink-100"
              }`}
            >
              {b.replace("_", " ")}
            </button>
          ))}
        </div>

        <Card className="p-0 overflow-hidden">
          {!workload ? (
            <Loading />
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b hairline text-left text-ink-500 text-xs uppercase tracking-wide">
                  <th className="px-5 py-3 font-normal">Name</th>
                  <th className="px-5 py-3 font-normal">Utilization</th>
                  <th className="px-5 py-3 font-normal">Band</th>
                  <th className="px-5 py-3 font-normal">Committed Hrs</th>
                  <th className="px-5 py-3 font-normal">Available Hrs/wk</th>
                  <th className="px-5 py-3 font-normal">Active Tasks</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((w) => (
                  <tr key={w.employee_id} className="border-b hairline last:border-0 hover:bg-graphite-800/40">
                    <td className="px-5 py-3 text-ink-100">{w.name}</td>
                    <td className={`px-5 py-3 font-mono tabular ${bandColor(w.band)}`}>{Math.round(w.utilization_ratio * 100)}%</td>
                    <td className="px-5 py-3">
                      <Badge className={bandColor(w.band) + " border-current/30"}>{w.band.replace("_", " ")}</Badge>
                    </td>
                    <td className="px-5 py-3 font-mono tabular text-ink-300">{w.remaining_committed_hours}</td>
                    <td className="px-5 py-3 font-mono tabular text-ink-300">{w.available_hours_per_week}</td>
                    <td className="px-5 py-3 font-mono tabular text-ink-300">{w.active_task_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </div>
  );
}
