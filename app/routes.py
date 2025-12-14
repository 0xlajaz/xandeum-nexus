import time
import statistics
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.network import get_network_state, calculate_heidelberg_score, GB_CONVERSION
from app.config import settings, logger
from app.storage import DataManager

# Initialize Router and Storage
router = APIRouter()
data_manager = DataManager(settings.HISTORY_FILE)

@router.get("/api/telemetry")
async def telemetry_endpoint():
    """
    Primary endpoint for fetching real-time network state.
    Aggregates data, calculates scores, and triggers background persistence.
    """
    try:
        raw_nodes = await get_network_state()
        
        # Fallback for empty network state
        if not raw_nodes:
            return JSONResponse({
                "timestamp": time.time(),
                "network": {
                    "total_nodes": 0, "total_storage_gb": 0, "avg_health": 0, 
                    "v7_adoption": 0, "avg_paging_efficiency": 0
                },
                "nodes": []
            })

        # Calculate aggregations for scoring context
        uptimes = [float(n.get('uptime') or 0) for n in raw_nodes]
        max_uptime = max(uptimes) if uptimes else 1
        
        processed_nodes = []
        for node in raw_nodes:
            score = calculate_heidelberg_score(node, {"max_uptime": max_uptime})
            
            processed_nodes.append({
                "pubkey": str(node.get('pubkey') or 'Unknown'),
                "short_id": str(node.get('pubkey') or 'Unknown')[:8] + "...",
                "ip": str(node.get('address') or 'Unknown'),
                "version": str(node.get('version') or 'Unknown'),
                "uptime_sec": float(node.get('uptime') or 0),
                "storage_used": float(node.get('storage_used') or 0),
                "storage_gb": round(float(node.get('storage_committed') or 0) / GB_CONVERSION, 4),
                "health_score": score['total'],
                "score_breakdown": score['breakdown'],
                "paging_metrics": score['metrics'],
                "latency_ms": node.get('_reporting_latency', 0)
            })

        # Network-wide KPIs
        net_stats = {
            "total_nodes": len(processed_nodes),
            "total_storage_gb": sum(n['storage_gb'] for n in processed_nodes),
            "avg_health": statistics.mean([n['health_score'] for n in processed_nodes]) if processed_nodes else 0,
            "v7_adoption": sum(1 for n in processed_nodes if ('0.7' in n['version'] or '0.8' in n['version'])),
            "avg_paging_efficiency": statistics.mean([n['paging_metrics']['hit_rate'] for n in processed_nodes]) if processed_nodes else 0
        }
        
        # Async persistence (Fire & Forget logic handled by storage manager)
        data_manager.save_history(net_stats)
        
        return JSONResponse({
            "timestamp": time.time(),
            "network": net_stats,
            "nodes": sorted(processed_nodes, key=lambda x: x['health_score'], reverse=True)
        })

    except Exception as e:
        logger.error(f"Endpoint Error (Telemetry): {e}", exc_info=True)
        return JSONResponse({"error": "Internal Server Error"}, status_code=500)

@router.get("/api/history/trend")
async def history_trend_endpoint():
    """Returns historical trend data for visualization charts."""
    rows = data_manager.get_history(100)
    
    if not rows:
        return JSONResponse({
            "timestamps": [], "node_counts": [], "health": [], "paging_efficiency": []
        })
        
    return JSONResponse({
        "timestamps": [r[0] for r in rows],
        "node_counts": [r[1] for r in rows],
        "health": [r[2] for r in rows],
        "paging_efficiency": [r[4] for r in rows]
    })