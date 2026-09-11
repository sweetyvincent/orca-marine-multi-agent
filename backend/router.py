import json
import logging
from anthropic import AsyncAnthropic
from config import CLAUDE_MODEL, ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

ROUTER_PROMPT = """You are a routing agent for ORCA, a marine data assistant.
Given a user question about ocean conditions, decide which specialist agents to consult.

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "agents": ["sst", "chlorophyll", "fisheries"],
  "reasoning": "one sentence explaining why these agents are needed",
  "needs_synthesis": true
}}

Available agents:
- sst: Sea surface temperature — current values, anomalies vs climatology, warming/cooling trends. Use for questions about water temperature, marine heatwaves, thermal conditions.
- chlorophyll: Chlorophyll-a concentration — phytoplankton/algal biomass, ocean productivity. Use for questions about algal blooms, water quality, biological productivity.
- fisheries: Harmful algal bloom risk assessment, coastal advisories, fishing safety. Use when the question asks about HAB risk, shellfish safety, fishing advisories, or when BOTH sst and chlorophyll are needed (HAB assessment requires cross-referencing both).

Set needs_synthesis=true when multiple agents are needed and their outputs must be cross-referenced.

IMPORTANT: Always include at least one agent. For HAB/algal bloom questions, include all three: ["sst", "chlorophyll", "fisheries"].

Question: {question}
Location: {location_name}
"""

def heuristic_route(question: str) -> dict:
    """Heuristic routing when LLM API key is not present or API call fails."""
    q_lower = question.lower()
    
    is_hab = any(k in q_lower for k in ["bloom", "algal", "hab", "red tide", "toxin", "shellfish", "closure", "harvest", "fish"])
    is_sst = any(k in q_lower for k in ["temperature", "sst", "warm", "cool", "heatwave", "thermal", "degree"])
    is_chl = any(k in q_lower for k in ["chlorophyll", "plankton", "productivity", "green", "biomass", "algae", "chla"])

    if is_hab or (is_sst and is_chl):
        return {
            "agents": ["sst", "chlorophyll", "fisheries"],
            "reasoning": "Query involves bloom risk or multiple environmental factors; consulting SST, Chlorophyll, and Fisheries advisory specialists for synthesis.",
            "needs_synthesis": True
        }
    elif is_sst:
        return {
            "agents": ["sst"],
            "reasoning": "Query is specifically focused on sea surface temperature and thermal conditions.",
            "needs_synthesis": False
        }
    elif is_chl:
        return {
            "agents": ["chlorophyll"],
            "reasoning": "Query focuses on chlorophyll-a concentration and ocean biological productivity.",
            "needs_synthesis": False
        }
    else:
        return {
            "agents": ["sst", "chlorophyll", "fisheries"],
            "reasoning": "Broad marine inquiry; dispatching SST, Chlorophyll, and Fisheries specialists for comprehensive assessment.",
            "needs_synthesis": True
        }

async def route_question(question: str, location_name: str) -> dict:
    """Route a user question to the appropriate specialist agents."""
    if not ANTHROPIC_API_KEY:
        logger.info("No ANTHROPIC_API_KEY set; utilizing domain heuristic routing.")
        return heuristic_route(question)

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    
    try:
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=150,
            system="You are a JSON-only API. Respond strictly with JSON.",
            messages=[
                {"role": "user", "content": ROUTER_PROMPT.format(question=question, location_name=location_name)}
            ]
        )
        content = response.content[0].text.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        parsed = json.loads(content.strip())
        return {
            "agents": parsed.get("agents", ["sst", "chlorophyll"]),
            "reasoning": parsed.get("reasoning", "Dispatched to relevant marine observation agents."),
            "needs_synthesis": parsed.get("needs_synthesis", True)
        }
    except Exception as e:
        logger.warning(f"Claude router error ({e}); falling back to heuristic routing.")
        return heuristic_route(question)
