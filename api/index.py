from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import json

class MetricsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

app = FastAPI()

# Enable CORS for any origin (POST only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# === Load metrics.json once at startup ===
with open("q-vercel-latency.json") as f:
    all_data = json.load(f)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# === Endpoint ===
@app.post("/metrics")
async def compute_metrics(payload: MetricsRequest):
    regions = payload.regions
    threshold = payload.threshold_ms
    results = {}

    for region in regions:
        # Filter entries for this region
        region_entries = [entry for entry in all_data if entry["region"] == region]

        if not region_entries:
            results[region] = {"error": "No data found"}
            continue

        latencies = [entry["latency_ms"] for entry in region_entries]
        uptimes = [entry["uptime_pct"] for entry in region_entries]
        breaches = sum(1 for l in latencies if l > threshold)

        results[region] = {
            "avg_latency": round(np.mean(latencies), 2),
            "p95_latency": round(np.percentile(latencies, 95), 2),
            "avg_uptime": round(np.mean(uptimes), 3),
            "breaches": breaches
        }

    return results
