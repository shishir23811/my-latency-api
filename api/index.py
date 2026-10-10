import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

app = FastAPI()

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
    "X-Version": "v4",
}


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        return Response(status_code=200, headers=CORS)
    try:
        response = await call_next(request)
    except Exception as e:
        response = JSONResponse({"error": str(e)}, status_code=500)
    for k, v in CORS.items():
        response.headers[k] = v
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
    return {**result, "regions": result}