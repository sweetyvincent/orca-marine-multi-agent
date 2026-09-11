# 🌊 ORCA — Marine Multi-Agent System

A multi-agent AI system for marine data analysis and Harmful Algal Bloom (HAB) risk assessment. Powered by LangGraph orchestration, real NOAA/NASA satellite data, and Claude AI.

## Architecture

```
User Question → Router Agent (Claude) → Specialist Agents → Synthesizer → Answer
                                          ├── 🌡️ SST Agent (NOAA OISST v2.1)
                                          ├── 🌿 Chlorophyll Agent (NASA MODIS Aqua)
                                          └── 🐟 Fisheries Agent (HAB heuristic)
```

## Quick Start

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your Anthropic API key

# Run the server
python main.py
```

Backend runs at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

### 3. Try These Demo Questions

1. **Single-agent SST**: "What's the current SST near Chennai coast?"
2. **Single-agent Chlorophyll**: "What are chlorophyll levels in the Gulf of Mexico?"
3. **Compound HAB query**: "Will conditions favour a harmful algal bloom near Florida Keys next week?"
4. **Three-agent**: "Is it safe to harvest shellfish from Chesapeake Bay?"

## Data Sources

| Agent | Source | Resolution | Auth |
|-------|--------|------------|------|
| SST | [NOAA OISST v2.1](https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.html) | 0.25° daily | None |
| Chlorophyll | [NASA MODIS Aqua](https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdMH1chla8day.html) | 4km 8-day | None |
| Fisheries | Rule-based HAB heuristic | N/A | N/A |

## Tech Stack

- **Orchestration**: LangGraph (Python)
- **LLM**: Claude API (Anthropic)
- **Data**: xarray + NOAA/NASA ERDDAP
- **Backend**: FastAPI with SSE streaming
- **Frontend**: React + Tailwind CSS

## Team

Built for VeoHack 2026.
