import networkx as nx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.tenancy import get_current_user, CurrentUser
from app.services.graph_service import build_org_graph, identify_hierarchy

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


@router.get("")
def get_org_graph(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """GET /api/v1/orgs/{org_id}/graph — returns nodes/edges shaped for React Flow."""
    g = build_org_graph(db, current_user.tenant_id)

    nodes = [{"id": n, **{k: v for k, v in d.items() if k != "id"}} for n, d in g.nodes(data=True)]
    edges = [{"source": u, "target": v, "type": d.get("type")} for u, v, d in g.edges(data=True)]

    return {"nodes": nodes, "edges": edges, "node_count": g.number_of_nodes(), "edge_count": g.number_of_edges()}


@router.get("/hierarchy")
def get_hierarchy(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    g = build_org_graph(db, current_user.tenant_id)
    result = identify_hierarchy(g)
    return {
        "has_cycle": result["has_cycle"],
        "root_count": len(result["roots"]),
        "depths": result["depths"],
    }
