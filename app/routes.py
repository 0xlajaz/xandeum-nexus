import time
import statistics
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.network import get_network_state, calculate_heidelberg_score, GB_CONVERSION
from app.config import settings, logger
from app.storage import DataManager
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from fastapi import Request

# Initialize Router and Storage
router = APIRouter()
data_manager = DataManager(settings.HISTORY_FILE)

CACHE_TTL = 30  # Seconds to hold data in RAM
_network_cache = {
    "timestamp": 0,
    "data": None
}

# --- RATE LIMITING ---
# Simple in-memory rate limiter (for production, use Redis)
request_tracker = defaultdict(list)
RATE_LIMIT_REQUESTS = 30  # Max requests per window
RATE_LIMIT_WINDOW = 60  # Time window in seconds

def check_rate_limit(client_ip: str) -> bool:
    """
    Simple rate limiting: 30 requests per minute per IP.
    Returns True if request is allowed, False if rate limit exceeded.
    """
    now = datetime.now()
    cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    
    # Clean old entries
    request_tracker[client_ip] = [
        req_time for req_time in request_tracker[client_ip] 
        if req_time > cutoff
    ]
    
    # Check limit
    if len(request_tracker[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    request_tracker[client_ip].append(now)
    return True

# --- HEALTH CHECK ENDPOINT ---
@router.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and Cloud Run.
    Returns 200 OK if the service is running.
    """
    return {
        "status": "healthy",
        "service": "Xandeum Nexus Intelligence",
        "version": settings.VERSION,
        "timestamp": time.time()
    }

@router.get("/api/telemetry")
async def telemetry_endpoint(request: Request = None): 
    """
    Primary endpoint for fetching real-time network state.
    Now includes caching to prevent IP Bans and Bankruptcy.
    """

    # 1. Rate Limiting Check
    client_ip = "unknown"
    if request:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif hasattr(request, 'client') and request.client:
            client_ip = request.client.host
    
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    # --- THE FIX: CHECK CACHE FIRST (The Anti-Ban Shield) ---
    global _network_cache
    current_time = time.time()
    
    # If cache is valid (less than 30s old), serve it immediately
    if _network_cache["data"] and (current_time - _network_cache["timestamp"] < CACHE_TTL):
        # logger.info(f"🚀 Serving telemetry from cache (Age: {int(current_time - _network_cache['timestamp'])}s)")
        return JSONResponse(_network_cache["data"])

    # 2. Cache Expired? Fetch Fresh Data
    try:
        raw_nodes, credits_map = await get_network_state()
        
        if not raw_nodes:
            logger.warning("No nodes returned from network state fetch")
            # Return empty structure (don't cache errors if possible, or cache briefly)
            return JSONResponse({
                "timestamp": current_time,
                "network": {"total_nodes": 0, "avg_health": 0}, 
                "nodes": [], 
                "warning": "Network offline"
            })

        # 3. Process the Nodes (Your existing logic)
        uptimes = [float(n.get('uptime') or 0) for n in raw_nodes]
        max_uptime = max(uptimes) if uptimes else 1
        
        processed_nodes = []
        location_stats = Counter()
        
        for node in raw_nodes:
            try:
                # ... (Keep your existing node processing logic exactly as is) ...
                score = calculate_heidelberg_score(node, {"max_uptime": max_uptime})
                pubkey = str(node.get('pubkey') or 'Unknown')
                official_credits = credits_map.get(pubkey, 0)
                
                geo = node.get('_geo', {})
                country = geo.get('countryCode', '??')
                city = geo.get('city', 'Unknown')
                loc_key = f"{country}|{city}" if (country != '??' and city != 'Unknown') else country
                location_stats[loc_key] += 1
                    
                processed_nodes.append({
                    "pubkey": pubkey,
                    "short_id": pubkey[:8] + "...",
                    "ip": str(node.get('address') or 'Unknown'),
                    "version": str(node.get('version') or 'Unknown'),
                    "uptime_sec": float(node.get('uptime') or 0),
                    "storage_used": float(node.get('storage_used') or 0),
                    "storage_gb": round(float(node.get('storage_committed') or 0) / GB_CONVERSION, 4),
                    "health_score": score['total'],
                    "reputation_credits": official_credits,
                    "score_breakdown": score['breakdown'],
                    "paging_metrics": score['metrics'],
                    "latency_ms": node.get('_reporting_latency', 0),
                    "visibility": node.get('_visibility', 1),
                    "geo": geo
                })
            except Exception as node_error:
                continue

        # 4. Calculate Stats
        net_stats = {
            "total_nodes": len(processed_nodes),
            "total_storage_gb": sum(n['storage_gb'] for n in processed_nodes),
            "avg_health": statistics.mean([n['health_score'] for n in processed_nodes]) if processed_nodes else 0,
            "v7_adoption": sum(1 for n in processed_nodes if '0.8' in n['version'] or '0.9' in n['version']),
            "avg_paging_efficiency": statistics.mean([n['paging_metrics']['hit_rate'] for n in processed_nodes]) if processed_nodes else 0,
            "geo_distribution": dict(location_stats.most_common(5)),
            "avg_visibility": statistics.mean([n['visibility'] for n in processed_nodes]) if processed_nodes else 0
        }
        
        # 5. Construct Response
        response_payload = {
            "timestamp": current_time,
            "network": net_stats,
            "nodes": sorted(processed_nodes, key=lambda x: x['health_score'], reverse=True)
        }

        # --- UPDATE CACHE ---
        _network_cache["timestamp"] = current_time
        _network_cache["data"] = response_payload

        # 6. Save History (Safe now due to storage.py throttle + cache)
        try:
            await data_manager.save_history_async(net_stats) 
        except Exception as storage_error:
            logger.error(f"Failed to save history: {storage_error}")
        
        return JSONResponse(response_payload)

    except Exception as e:
        logger.error(f"Critical error in telemetry endpoint: {e}", exc_info=True)
        return JSONResponse({"error": "Internal Server Error", "detail": str(e)}, status_code=500)

@router.get("/api/history/trend")
async def history_trend_endpoint():
    """
    Returns historical network metrics for charting.
    """
    try:
        rows = data_manager.get_history(100)
        
        if not rows:
            logger.info("No historical data available yet")
            return JSONResponse({
                "timestamps": [], 
                "node_counts": [], 
                "health": [], 
                "paging_efficiency": []
            })
        
        return JSONResponse({
            "timestamps": [r[0] for r in rows],
            "node_counts": [r[1] for r in rows],
            "health": [r[2] for r in rows],
            "paging_efficiency": [r[4] for r in rows]
        })
    
    except Exception as e:
        logger.error(f"Error fetching history: {e}", exc_info=True)
        return JSONResponse(
            {"error": "Failed to fetch history", "detail": str(e)}, 
            status_code=500
        )
