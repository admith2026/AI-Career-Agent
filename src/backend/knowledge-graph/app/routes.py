"""Knowledge Graph API routes."""

from fastapi import APIRouter
from app.graph import GraphManager

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])

graph = GraphManager()


@router.get("/company/{company_name}")
async def get_company_network(company_name: str):
    return await graph.get_company_network(company_name)


@router.get("/company/{company_name}/decision-makers")
async def get_decision_makers(company_name: str):
    return await graph.find_decision_makers(company_name)


@router.get("/hotspots")
async def hiring_hotspots(limit: int = 20):
    return await graph.get_hiring_hotspots(limit)


@router.get("/technology-demand")
async def technology_demand(limit: int = 20):
    return await graph.get_technology_demand(limit)


@router.get("/stats")
async def graph_stats():
    return await graph.get_graph_stats()


@router.post("/company")
async def upsert_company(body: dict):
    name = body.get("name", "")
    if not name:
        return {"error": "name required"}
    props = {k: v for k, v in body.items() if k != "name"}
    await graph.upsert_company(name, props)
    return {"status": "ok", "company": name}


@router.post("/recruiter")
async def upsert_recruiter(body: dict):
    email = body.get("email", "")
    name = body.get("name", "")
    if not email or not name:
        return {"error": "email and name required"}
    await graph.upsert_recruiter(email, name, body.get("company"), body)
    return {"status": "ok", "recruiter": email}


# ─── Recruiter Intelligence ─────────────────────────────────────────────────

@router.post("/recruiter/{email}/interaction")
async def track_recruiter_interaction(email: str, body: dict):
    """Track an interaction with a recruiter to build relationship strength."""
    interaction_type = body.get("type", "message")
    sentiment = float(body.get("sentiment", 0.5))
    notes = body.get("notes", "")
    await graph.track_interaction(email, interaction_type, sentiment, notes)
    return {"status": "ok", "recruiter": email, "interaction_type": interaction_type}


@router.get("/recruiter-rankings")
async def recruiter_rankings(limit: int = 20):
    """Get recruiters ranked by relationship strength and interaction history."""
    return await graph.get_recruiter_rankings(limit)


@router.get("/company/{company_name}/recruiters")
async def company_recruiters(company_name: str):
    """Get all recruiters for a company with relationship scores."""
    return await graph.get_company_recruiter_map(company_name)
