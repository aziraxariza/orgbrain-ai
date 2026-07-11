"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { orgApi, Project } from "@/lib/api";
import { PageHeader, Card, Loading, Badge } from "@/components/ui";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[] | null>(null);

  useEffect(() => {
    orgApi.projects().then(setProjects).catch(() => setProjects([]));
  }, []);

  return (
    <div>
      <PageHeader title="Projects" subtitle="Click into a project for critical path, Monte Carlo forecast, and delivery prediction." />
      <div className="p-8">
        {!projects ? (
          <Loading />
        ) : (
          <div className="grid grid-cols-3 gap-4">
            {projects.map((p) => (
              <Link key={p.project_id} href={`/projects/${p.project_id}`}>
                <Card className="hover:border-signal/50 transition-colors h-full">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-ink-100 font-medium leading-snug">{p.name}</h3>
                  </div>
                  <Badge className={statusColor(p.status)}>{p.status.replace("_", " ")}</Badge>
                  <p className="text-xs text-ink-500 mt-3 line-clamp-2">{p.description}</p>
                  <div className="text-xs text-ink-500 mt-3 font-mono">
                    {p.start_date} → {p.target_end_date ?? "no target"}
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function statusColor(status: string) {
  if (status === "at_risk" || status === "blocked") return "text-severity-critical border-severity-critical/40 bg-severity-critical/10";
  if (status === "active") return "text-calm border-calm/40 bg-calm/10";
  return "text-ink-500 border-ink-500/30 bg-transparent";
}
