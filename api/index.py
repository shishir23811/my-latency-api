import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI()


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


DATA = json.loads((Path(__file__).parent / "telemetry.json").read_text())


class Query(BaseModel):
    regions: list[str]
    threshold_ms: float


@app.post("/")
@app.post("/api")
@app.post("/api/latency")
def metrics(q: Query):
    result = {}
    for region in q.regions:
        rows = [r for r in DATA if r["region"] == region]
        if not rows:
            continue
        lat = np.array([r["latency_ms"] for r in rows], dtype=float)
        up = np.array([r["uptime_pct"] for r in rows], dtype=float)
        result[region] = {
            "avg_latency": float(lat.mean()),
            "p95_latency": float(np.percentile(lat, 95)),
            "avg_uptime": float(up.mean()),
            "breaches": int((lat > q.threshold_ms).sum()),
        }
    return {"regions": result}