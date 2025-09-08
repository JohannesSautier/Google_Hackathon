# server.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI(title="Immigration Time Risk API")

class RunRequest(BaseModel):
    origin: str
    destination: str
    since_days: int = 5
    max_articles: int = 40
    use_llm: bool = True
    model: str = "gemini-1.5-flash"
    process_file: Optional[str] = None
    process_plan_inline: Optional[Dict[str, Dict[str, str]]] = None

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/run")
def run(req: RunRequest) -> Dict[str, Any]:
    try:
        # Lazy import here to avoid crash at startup
        from main import run_pipeline, load_process_plan  # or from immigration_time_risk_datapoints import ...
        process_plan = req.process_plan_inline if req.process_plan_inline else load_process_plan(req.process_file)
        result = run_pipeline(
            origin=req.origin,
            destination=req.destination,
            since_days=req.since_days,
            use_llm=req.use_llm,
            max_articles=req.max_articles,
            process_plan=process_plan,
            model=req.model,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
