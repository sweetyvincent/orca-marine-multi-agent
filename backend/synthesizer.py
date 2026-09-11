import json
import logging
from anthropic import AsyncAnthropic
from config import (
    CLAUDE_MODEL, 
    ANTHROPIC_API_KEY, 
    CHL_ELEVATED_THRESHOLD, 
    CHL_HIGH_THRESHOLD, 
    SST_ANOMALY_WARM_THRESHOLD, 
    SST_ANOMALY_HOT_THRESHOLD
)

logger = logging.getLogger(__name__)

def compute_hab_risk(agent_results: list[dict]) -> tuple[str, list[str]]:
    """Apply HAB risk heuristic across all agent results.
    Returns (risk_level, contributing_factors)."""
    
    sst_anom = 0.0
    chl = 0.0
    has_sst = False
    has_chl = False
    
    for res in agent_results:
        if res.get("agent") == "sst" and "error" not in res:
            sst_anom = float(res.get("anomaly_c", 0))
            has_sst = True
        if res.get("agent") == "chlorophyll" and "error" not in res:
            chl = float(res.get("mean_chl_mg_m3", 0))
            has_chl = True
            
    contributing_factors = []
    
    if chl > CHL_HIGH_THRESHOLD:
        risk_level = "high"
        contributing_factors.append(f"Chlorophyll extremely high ({chl} mg/m³ > {CHL_HIGH_THRESHOLD})")
    elif chl > CHL_ELEVATED_THRESHOLD and sst_anom > SST_ANOMALY_WARM_THRESHOLD:
        risk_level = "elevated"
        contributing_factors.append(f"Elevated chlorophyll ({chl} mg/m³) with warm SST anomaly (+{sst_anom}°C)")
    elif chl > CHL_ELEVATED_THRESHOLD or sst_anom > SST_ANOMALY_HOT_THRESHOLD:
        risk_level = "moderate"
        if chl > CHL_ELEVATED_THRESHOLD:
            contributing_factors.append(f"Elevated chlorophyll ({chl} mg/m³)")
        if sst_anom > SST_ANOMALY_HOT_THRESHOLD:
            contributing_factors.append(f"Hot SST anomaly (+{sst_anom}°C)")
    else:
        risk_level = "low"
        contributing_factors.append("All observation parameters within normal baseline levels")
        
    return risk_level, contributing_factors

def format_domain_synthesis(location_name: str, agent_results: list[dict], risk_level: str, contributing_factors: list[str]) -> str:
    """Produces a clean, highly structured marine report even when offline or without external LLM keys."""
    sst_info = next((r for r in agent_results if r.get("agent") == "sst" and "error" not in r), None)
    chl_info = next((r for r in agent_results if r.get("agent") == "chlorophyll" and "error" not in r), None)
    fish_info = next((r for r in agent_results if r.get("agent") == "fisheries" and "error" not in r), None)

    paragraphs = []
    
    # 1. Primary findings
    obs_summary = []
    if sst_info:
        obs_summary.append(
            f"The Sea Surface Temperature (SST) near {location_name} is currently **{sst_info.get('current_sst_c')}°C**, "
            f"reflecting an anomaly of **{'+' if sst_info.get('anomaly_c', 0) >= 0 else ''}{sst_info.get('anomaly_c')}°C** "
            f"against climatological normal (7-day trend: *{sst_info.get('trend_direction')}*, {sst_info.get('trend_7day_c_per_week')}°C/week; source: {sst_info.get('data_source')})."
        )
    if chl_info:
        obs_summary.append(
            f"Satellite ocean color registers mean chlorophyll-a concentration at **{chl_info.get('mean_chl_mg_m3')} mg/m³** "
            f"(classification: *{chl_info.get('classification')}*, peak reading: {chl_info.get('max_chl_mg_m3')} mg/m³; source: {chl_info.get('data_source')})."
        )
    
    if obs_summary:
        paragraphs.append(" ".join(obs_summary))

    # 2. Risk verdict & Advisory
    if fish_info or (sst_info and chl_info):
        badge = risk_level.upper()
        adv_text = fish_info.get('advisory') if fish_info else "Conditions do not indicate immediate bloom progression."
        paragraphs.append(
            f"### Assessment: **{badge} RISK**\n"
            f"{adv_text}\n\n"
            f"**Key Indicators:** {', '.join(contributing_factors)}."
        )

    if not paragraphs:
        return f"Insufficient environmental observations retrieved for {location_name} to generate a grounded synthesis."

    return "\n\n".join(paragraphs)

async def synthesize_answer(
    question: str, 
    location_name: str, 
    agent_results: list[dict], 
    risk_level: str, 
    contributing_factors: list[str]
) -> str:
    """Generate a grounded natural-language answer using Claude, with robust domain template fallback."""
    if not ANTHROPIC_API_KEY:
        logger.info("No ANTHROPIC_API_KEY set; using grounded domain synthesis engine.")
        return format_domain_synthesis(location_name, agent_results, risk_level, contributing_factors)

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    results_str = json.dumps(agent_results, indent=2, default=str)
    
    prompt = f"""You are ORCA, a marine science communicator. Given the following data from 
specialist agents, write a clear, grounded answer to the user's question.

RULES:
- Cite specific numbers from the agent data (e.g., "SST is 29.4°C, +1.8°C above normal")
- Name the data source for each fact (e.g., "according to NOAA OISST v2.1")
- If this is a HAB risk assessment, clearly state the risk level and which factors drive it
- Be honest about limitations (e.g., "based on the most recent satellite composite, not a real-time forecast")
- Keep it conversational but precise — 2-3 paragraphs max
- Do NOT invent or hallucinate numbers — only use what's in the agent data below

User question: {question}
Location: {location_name}
Risk level: {risk_level}
Contributing factors: {', '.join(contributing_factors)}

Agent data:
{results_str}
"""
    
    try:
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        logger.warning(f"Synthesizer LLM invocation failed ({e}); formatting grounded domain synthesis.")
        return format_domain_synthesis(location_name, agent_results, risk_level, contributing_factors)
