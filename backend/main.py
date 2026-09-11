import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from graph import orca_graph
from geocoding import PRESET_LOCATIONS

app = FastAPI(title="ORCA - Marine Multi-Agent System")

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str
    location: str = "Chennai"

async def stream_orca_response(question: str, location: str):
    """Stream LangGraph execution events as SSE."""
    initial_state = {
        "question": question,
        "location_name": location,
        "lat": 0.0,
        "lon": 0.0,
        "agents_needed": [],
        "routing_reasoning": "",
        "needs_synthesis": False,
        "agent_results": [],
        "risk_level": "",
        "final_answer": "",
        "citations": [],
        "error": ""
    }
    
    try:
        async for event in orca_graph.astream(
            initial_state, 
            stream_mode=["updates", "custom"]
        ):
            if isinstance(event, tuple) and len(event) == 2:
                mode, data = event
            else:
                continue
            
            if mode == "custom":
                event_type = data.get("type", "unknown")
                status = data.get("status", "unknown")
                event_data = data.get("data", {})
                
                if status == "complete":
                    if event_type == "router":
                        sse_type = "router"
                    elif event_type in ["sst", "chlorophyll", "fisheries"]:
                        sse_type = "agent_result"
                        event_data = {"agent": event_type, **event_data}
                    elif event_type == "synthesizer":
                        sse_type = "synthesis"
                    elif event_type == "geocode":
                        sse_type = "geocode"
                    else:
                        sse_type = event_type
                    
                    yield f"event: {sse_type}\ndata: {json.dumps(event_data, default=str)}\n\n"
                elif status == "running":
                    yield f"event: status\ndata: {json.dumps({'agent': event_type, 'status': 'running'})}\n\n"
                    
            elif mode == "updates":
                pass
                    
        yield f"event: done\ndata: {json.dumps({'status': 'completed'})}\n\n"
    except Exception as e:
        logger.error(f"Error in stream_orca_response: {e}", exc_info=True)
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

@app.post("/ask")
async def ask(request: AskRequest):
    """Process a marine science question and stream agent results via SSE."""
    return StreamingResponse(
        stream_orca_response(request.question, request.location),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@app.get("/health")
def health():
    return {"status": "ok", "service": "orca"}

@app.get("/locations")
def locations():
    """Return preset coastal locations for the frontend picker."""
    location_list = [
        {"name": name.title(), "lat": coords["lat"], "lon": coords["lon"]}
        for name, coords in PRESET_LOCATIONS.items()
    ]
    return {"locations": location_list}

# Serve frontend build artifacts if present (for single-service deployment on Render, Railway, etc.)
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static_assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
