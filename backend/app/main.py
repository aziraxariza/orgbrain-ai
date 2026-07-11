from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, entities, graph, simulation, risks, decisions

app = FastAPI(
    title="OrgBrain API",
    description="AI-powered Execution Intelligence Platform — deterministic simulation, "
                "risk detection, and explainable decision support.",
    version="0.1.0",
)

# CORS: open for local dev (Next.js on :3000). Tighten to explicit origins before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(entities.router)
app.include_router(graph.router)
app.include_router(simulation.router)
app.include_router(risks.router)
app.include_router(decisions.router)


@app.get("/health")
def health():
    return {"status": "ok"}
