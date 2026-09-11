from typing import TypedDict, Annotated
import operator
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer

from router import route_question
from synthesizer import compute_hab_risk, synthesize_answer
from geocoding import resolve_location, extract_location_from_text
from agents import run_sst_agent, run_chlorophyll_agent, run_fisheries_agent

logger = logging.getLogger(__name__)

class OrcaState(TypedDict):
    question: str
    location_name: str
    lat: float
    lon: float
    agents_needed: list[str]
    routing_reasoning: str
    needs_synthesis: bool
    agent_results: Annotated[list[dict], operator.add]
    risk_level: str
    final_answer: str
    citations: list[str]
    error: str

async def geocode_node(state: OrcaState):
    """Resolve location name to lat/lon coordinates, extracting from question if present."""
    writer = get_stream_writer()
    
    # Priority: If question mentions a specific location (e.g. "Gulf of Mexico"), prefer that
    extracted = extract_location_from_text(state.get("question", ""))
    target_location = extracted if extracted else state.get("location_name", "Chennai")
    
    writer({"type": "geocode", "status": "running", "data": {"location": target_location}})
    try:
        result = await resolve_location(target_location)
        lat = result["lat"]
        lon = result["lon"]
        resolved_name = result["name"]
        writer({"type": "geocode", "status": "complete", "data": {"lat": lat, "lon": lon, "name": resolved_name}})
        return {"lat": lat, "lon": lon, "location_name": resolved_name}
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        writer({"type": "geocode", "status": "error", "data": {"error": str(e)}})
        return {"error": f"Could not resolve location '{target_location}': {str(e)}"}

async def router_node(state: OrcaState):
    """Decide which specialist agents to consult."""
    writer = get_stream_writer()
    writer({"type": "router", "status": "running", "data": {}})
    route_data = await route_question(state["question"], state.get("location_name", ""))
    writer({"type": "router", "status": "complete", "data": route_data})
    return {
        "agents_needed": route_data["agents"],
        "routing_reasoning": route_data["reasoning"],
        "needs_synthesis": route_data["needs_synthesis"]
    }

async def sst_node(state: OrcaState):
    """Run the SST specialist agent."""
    if "sst" not in state.get("agents_needed", []):
        return {}
    writer = get_stream_writer()
    writer({"type": "sst", "status": "running", "data": {}})
    res = await run_sst_agent(state["lat"], state["lon"], state.get("location_name", "Unknown"))
    writer({"type": "sst", "status": "complete", "data": res})
    return {"agent_results": [res]}

async def chlorophyll_node(state: OrcaState):
    """Run the Chlorophyll specialist agent."""
    if "chlorophyll" not in state.get("agents_needed", []):
        return {}
    writer = get_stream_writer()
    writer({"type": "chlorophyll", "status": "running", "data": {}})
    res = await run_chlorophyll_agent(state["lat"], state["lon"], state.get("location_name", "Unknown"))
    writer({"type": "chlorophyll", "status": "complete", "data": res})
    return {"agent_results": [res]}

async def fisheries_node(state: OrcaState):
    """Run the Fisheries/HAB advisory specialist agent using SST & Chlorophyll findings."""
    if "fisheries" not in state.get("agents_needed", []):
        return {}
    writer = get_stream_writer()
    writer({"type": "fisheries", "status": "running", "data": {}})
    
    sst_result = None
    chl_result = None
    for r in state.get("agent_results", []):
        if r.get("agent") == "sst":
            sst_result = r
        elif r.get("agent") == "chlorophyll":
            chl_result = r
    
    res = await run_fisheries_agent(
        state["lat"], state["lon"], 
        state.get("location_name", "Unknown"),
        sst_result=sst_result, 
        chl_result=chl_result
    )
    writer({"type": "fisheries", "status": "complete", "data": res})
    return {"agent_results": [res]}

async def synthesizer_node(state: OrcaState):
    """Combine all agent outputs into a final grounded answer."""
    writer = get_stream_writer()
    writer({"type": "synthesizer", "status": "running", "data": {}})
    
    if state.get("error"):
        final_answer = f"I couldn't process your request: {state['error']}"
        risk_level = "unknown"
    else:
        agent_results = state.get("agent_results", [])
        risk_level, factors = compute_hab_risk(agent_results)
        final_answer = await synthesize_answer(
            state["question"], 
            state.get("location_name", "Unknown"), 
            agent_results,
            risk_level,
            factors
        )
        
    writer({"type": "synthesizer", "status": "complete", "data": {
        "final_answer": final_answer, 
        "risk_level": risk_level
    }})
    return {"final_answer": final_answer, "risk_level": risk_level}

builder = StateGraph(OrcaState)
builder.add_node("geocode_node", geocode_node)
builder.add_node("router_node", router_node)
builder.add_node("sst_node", sst_node)
builder.add_node("chlorophyll_node", chlorophyll_node)
builder.add_node("fisheries_node", fisheries_node)
builder.add_node("synthesizer_node", synthesizer_node)

builder.add_edge(START, "geocode_node")
builder.add_edge("geocode_node", "router_node")
builder.add_edge("router_node", "sst_node")
builder.add_edge("sst_node", "chlorophyll_node")
builder.add_edge("chlorophyll_node", "fisheries_node")
builder.add_edge("fisheries_node", "synthesizer_node")
builder.add_edge("synthesizer_node", END)

orca_graph = builder.compile()
