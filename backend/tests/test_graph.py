import networkx as nx

from app.services.graph_service import build_org_graph, identify_hierarchy


def test_graph_has_expected_node_types(db, seeded_org):
    g = build_org_graph(db, seeded_org.organization_id)
    node_types = {d["type"] for _, d in g.nodes(data=True)}
    assert node_types == {"employee", "task", "project"}
    assert g.number_of_nodes() > 0


def test_hierarchy_has_no_cycles_in_synthetic_data(db, seeded_org):
    g = build_org_graph(db, seeded_org.organization_id)
    result = identify_hierarchy(g)
    assert result["has_cycle"] is False
    assert len(result["roots"]) >= 1


def test_task_depends_on_edges_exist(db, seeded_org):
    g = build_org_graph(db, seeded_org.organization_id)
    dep_edges = [e for e in g.edges(data=True) if e[2].get("type") == "depends_on"]
    assert len(dep_edges) > 0
