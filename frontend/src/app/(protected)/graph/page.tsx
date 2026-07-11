"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import ReactFlow, {
  Background, Controls, MiniMap, Node, Edge, useNodesState, useEdgesState, MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import { orgApi, GraphNode as ApiNode, GraphEdge as ApiEdge } from "@/lib/api";
import { PageHeader, Loading } from "@/components/ui";

const TYPE_COLOR: Record<string, string> = {
  employee: "#5B8DEF",
  task: "#F2C94C",
  project: "#4FD1C5",
};

function layout(nodes: ApiNode[]): Node[] {
  // Simple deterministic radial-ish layout grouped by type — no heavy layout
  // library dependency needed for MVP; swap for dagre/elk post-MVP if the org
  // graph grows large enough that overlap becomes a real problem.
  const byType: Record<string, ApiNode[]> = { employee: [], task: [], project: [] };
  nodes.forEach((n) => byType[n.type]?.push(n));

  const positioned: Node[] = [];
  const columnX: Record<string, number> = { employee: 80, task: 480, project: 880 };

  (["employee", "task", "project"] as const).forEach((type) => {
    byType[type].forEach((n, i) => {
      positioned.push({
        id: n.id,
        position: { x: columnX[type], y: i * 70 },
        data: { label: n.name || n.id },
        style: {
          background: "#1A2029",
          border: `1px solid ${TYPE_COLOR[type]}66`,
          borderRadius: 6,
          color: "#EDEFF3",
          fontSize: 12,
          padding: 8,
          width: 200,
        },
      });
    });
  });
  return positioned;
}

export default function GraphPage() {
  const [raw, setRaw] = useState<{ nodes: ApiNode[]; edges: ApiEdge[] } | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [filter, setFilter] = useState<"all" | "employee" | "task" | "project">("all");

  useEffect(() => {
    orgApi.graph().then(setRaw).catch(() => setRaw({ nodes: [], edges: [] }));
  }, []);

  useEffect(() => {
    if (!raw) return;
    const filteredNodes = filter === "all" ? raw.nodes : raw.nodes.filter((n) => n.type === filter);
    const nodeIds = new Set(filteredNodes.map((n) => n.id));
    const filteredEdges: Edge[] = raw.edges
      .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
      .slice(0, 300) // cap for render performance on the full 300-employee org
      .map((e, i) => ({
        id: `e${i}`,
        source: e.source,
        target: e.target,
        style: { stroke: "#333C4B" },
        markerEnd: { type: MarkerType.ArrowClosed, color: "#333C4B" },
      }));
    setNodes(layout(filteredNodes));
    setEdges(filteredEdges);
  }, [raw, filter, setNodes, setEdges]);

  const counts = useMemo(() => {
    if (!raw) return { employee: 0, task: 0, project: 0 };
    return {
      employee: raw.nodes.filter((n) => n.type === "employee").length,
      task: raw.nodes.filter((n) => n.type === "task").length,
      project: raw.nodes.filter((n) => n.type === "project").length,
    };
  }, [raw]);

  return (
    <div className="h-screen flex flex-col">
      <PageHeader
        eyebrow="FR-101"
        title="Organization Graph"
        subtitle="Reports-to, assigned-to, depends-on, and belongs-to edges across the whole org."
      />
      <div className="px-8 py-3 flex gap-2 border-b hairline">
        {(["all", "employee", "task", "project"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`text-xs px-3 py-1.5 rounded border hairline capitalize ${
              filter === f ? "bg-graphite-700 text-ink-100" : "text-ink-500 hover:text-ink-100"
            }`}
          >
            {f === "all" ? "All" : `${f}s`}
            {f !== "all" && <span className="ml-1.5 font-mono text-ink-500">{counts[f]}</span>}
          </button>
        ))}
      </div>
      <div className="flex-1 min-h-0">
        {!raw ? (
          <Loading />
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#242B37" gap={20} />
            <Controls />
            <MiniMap
              nodeColor={(n) => {
                const t = (raw.nodes.find((rn) => rn.id === n.id)?.type ?? "task") as string;
                return TYPE_COLOR[t] ?? "#4A5568";
              }}
              maskColor="rgba(11,14,19,0.8)"
              style={{ background: "#12161E" }}
            />
          </ReactFlow>
        )}
      </div>
    </div>
  );
}
