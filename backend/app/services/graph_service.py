"""Builds the organizational graph: employees (reports-to), tasks (depends-on),
tasks->projects, teams->projects. This is the single source of truth every other
engine (workload, critical path, risk, simulation) reads from.

ADR-001: PostgreSQL + NetworkX for MVP. The graph is rebuilt in-memory per request
from relational rows rather than persisted as a native graph store — cheap at MVP
scale (hundreds of employees/tasks) and swappable for Neo4j post-MVP without
changing the algorithms below, since they only touch the networkx.DiGraph interface.
"""
import uuid

import networkx as nx
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.task import Task
from app.models.project import Project


def build_org_graph(db: Session, tenant_id: uuid.UUID) -> nx.DiGraph:
    """FR-101: Build Organization Graph from Entities.
    Node types: employee, task, project. Edge types: reports_to, assigned_to,
    depends_on, belongs_to.
    """
    g = nx.DiGraph()

    employees = db.query(Employee).filter(Employee.tenant_id == tenant_id).all()
    for e in employees:
        g.add_node(f"employee:{e.employee_id}", type="employee", name=e.name, role=e.role,
                    available_hours=e.available_hours_per_week, skills=e.skills)
        if e.manager_id:
            g.add_edge(f"employee:{e.manager_id}", f"employee:{e.employee_id}", type="reports_to")

    projects = db.query(Project).filter(Project.tenant_id == tenant_id).all()
    for p in projects:
        g.add_node(f"project:{p.project_id}", type="project", name=p.name, status=p.status.value)

    tasks = db.query(Task).filter(Task.tenant_id == tenant_id).all()
    for t in tasks:
        g.add_node(
            f"task:{t.task_id}", type="task", name=t.name,
            estimated_hours=t.estimated_hours, progress=t.progress_percent,
            priority=t.priority.value, status=t.status.value,
            deadline=t.deadline.isoformat() if t.deadline else None,
        )
        g.add_edge(f"task:{t.task_id}", f"project:{t.project_id}", type="belongs_to")
        if t.assigned_person_id:
            g.add_edge(f"employee:{t.assigned_person_id}", f"task:{t.task_id}", type="assigned_to")
        for dep in t.depends_on:
            # dependency points from the blocking task to the dependent task
            g.add_edge(f"task:{dep.task_id}", f"task:{t.task_id}", type="depends_on")

    return g


def identify_hierarchy(g: nx.DiGraph) -> dict:
    """FR-103: Identify Organizational Hierarchy. Returns depth per employee and
    detects cycles (which would indicate bad data — a manager cannot report to
    their own report)."""
    reports_edges = [(u, v) for u, v, d in g.edges(data=True) if d.get("type") == "reports_to"]
    hierarchy_graph = nx.DiGraph(reports_edges)

    roots = [n for n in hierarchy_graph.nodes if hierarchy_graph.in_degree(n) == 0]
    depths = {}
    for root in roots:
        for node, depth in nx.single_source_shortest_path_length(hierarchy_graph, root).items():
            depths[node] = min(depths.get(node, depth), depth)

    has_cycle = not nx.is_directed_acyclic_graph(hierarchy_graph)
    return {"depths": depths, "roots": roots, "has_cycle": has_cycle}
