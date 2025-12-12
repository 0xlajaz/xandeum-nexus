import uvicorn
import asyncio
import aiohttp
import time
import sqlite3
import json
import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import statistics

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("xandeum_nexus")

app = FastAPI(
    title="Xandeum Nexus Intelligence",
    description="v0.7 Heidelberg Analytics Platform",
    version="0.7.2-PRO"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# Known entrypoints
SEED_NODES = [
    "173.212.203.145", "173.212.220.65", "161.97.97.41",
    "192.190.136.36", "192.190.136.37", "192.190.136.38"
]
RPC_PORT = "6000"
RPC_ENDPOINT = "/rpc"
GB_CONVERSION = 1024**3

# --- PERSISTENCE LAYER (SQLite) ---
DB_PATH = "/tmp/nexus_history.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS network_history
                     (timestamp REAL, total_nodes INTEGER, avg_health REAL, 
                      total_storage REAL, avg_hit_rate REAL)''')
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to init DB: {e}")

# Initialize on startup
init_db()

def save_history(stats: Dict):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO network_history VALUES (?,?,?,?,?)",
                  (time.time(), stats['total_nodes'], stats['avg_health'], 
                   stats['total_storage_gb'], stats.get('avg_paging_efficiency', 0)))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Write Error: {e}")

def get_history_data(limit=50):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM network_history ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return list(reversed(rows))
    except Exception as e:
        logger.error(f"DB Read Error: {e}")
        return []

# --- CORE LOGIC ---
async def fetch_node_stats(session: aiohttp.ClientSession, ip: str) -> Optional[List[Dict]]:
    url = f"http://{ip}:{RPC_PORT}{RPC_ENDPOINT}"
    payload = {"jsonrpc": "2.0", "method": "get-pods-with-stats", "id": 1}
    try:
        start = time.time()
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=2)) as response:
            latency = (time.time() - start) * 1000 # ms
            if response.status == 200:
                data = await response.json()
                result = data.get('result', {})
                pods = result.get('pods', []) if isinstance(result, dict) else result
                
                for pod in pods:
                    pod['_reporting_latency'] = latency
                    pod['_source_node'] = ip
                return pods
    except Exception:
        pass
    return None

async def get_network_state():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_node_stats(session, ip) for ip in SEED_NODES]
        results = await asyncio.gather(*tasks)
        
        unique_nodes = {}
        for res in results:
            if not res: continue
            for pod in res:
                pubkey = pod.get('pubkey')
                if not pubkey: continue
                
                if pubkey not in unique_nodes:
                    unique_nodes[pubkey] = pod
                else:
                    curr = unique_nodes[pubkey]
                    if pod.get('version', '') > curr.get('version', ''):
                        unique_nodes[pubkey] = pod

        return list(unique_nodes.values())

def calculate_heidelberg_score(node: Dict, net_stats: Dict) -> Dict:
    version = node.get('version', '0.0.0')
    is_v7 = '0.7' in version
    score_version = 40 if is_v7 else 10
    
    uptime = float(node.get('uptime', 0))
    max_uptime = net_stats.get('max_uptime', 1)
    score_uptime = (uptime / max_uptime) * 30 if max_uptime > 0 else 0
    
    storage = float(node.get('storage_used', 0))
    score_storage = min((storage / (100 * 1024**3)) * 20, 20)
    
    hit_rate = node.get('paging_hit_rate', 0.95)
    score_paging = hit_rate * 10
    
    total = min(score_version + score_uptime + score_storage + score_paging, 100)
    
    return {
        "total": int(total),
        "breakdown": {
            "v0.7_compliance": score_version,
            "uptime_reliability": int(score_uptime),
            "storage_weight": int(score_storage),
            "paging_efficiency": int(score_paging)
        },
        "metrics": {
            "hit_rate": hit_rate,
            "replication_health": node.get('replication_factor', 3)
        }
    }

@app.get("/api/telemetry")
async def telemetry():
    try:
        raw_nodes = await get_network_state()
        
        if not raw_nodes:
            # Return empty state instead of error to keep UI alive
            return JSONResponse({
                "timestamp": time.time(),
                "network": {
                    "total_nodes": 0, "total_storage_gb": 0, "avg_health": 0, 
                    "v7_adoption": 0, "avg_paging_efficiency": 0
                },
                "nodes": []
            })

        uptimes = [float(n.get('uptime', 0)) for n in raw_nodes]
        max_uptime = max(uptimes) if uptimes else 1
        
        processed_nodes = []
        for node in raw_nodes:
            score = calculate_heidelberg_score(node, {"max_uptime": max_uptime})
            processed_nodes.append({
                "pubkey": node.get('pubkey'),
                "short_id": node.get('pubkey')[:8] + "...",
                "ip": node.get('address', 'Unknown'),
                "version": node.get('version', 'Unknown'),
                "uptime_sec": float(node.get('uptime', 0)),
                "storage_used": float(node.get('storage_used', 0)),
                "storage_gb": round(float(node.get('storage_used', 0)) / GB_CONVERSION, 4),
                "health_score": score['total'],
                "score_breakdown": score['breakdown'],
                "paging_metrics": score['metrics'],
                "latency_ms": node.get('_reporting_latency', 0)
            })

        net_stats = {
            "total_nodes": len(processed_nodes),
            "total_storage_gb": sum(n['storage_gb'] for n in processed_nodes),
            "avg_health": statistics.mean([n['health_score'] for n in processed_nodes]) if processed_nodes else 0,
            "v7_adoption": sum(1 for n in processed_nodes if '0.7' in n['version']),
            "avg_paging_efficiency": statistics.mean([n['paging_metrics']['hit_rate'] for n in processed_nodes]) if processed_nodes else 0
        }
        
        save_history(net_stats)
        
        return JSONResponse({
            "timestamp": time.time(),
            "network": net_stats,
            "nodes": sorted(processed_nodes, key=lambda x: x['health_score'], reverse=True)
        })
    except Exception as e:
        logger.error(f"Telemetry Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/history/trend")
async def history_trend():
    rows = get_history_data(100)
    return JSONResponse({
        "timestamps": [r[0] for r in rows],
        "node_counts": [r[1] for r in rows],
        "health": [r[2] for r in rows],
        "paging_efficiency": [r[4] for r in rows]
    })

@app.get("/", response_class=HTMLResponse)
async def serve_app(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))