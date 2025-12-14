import aiohttp
import asyncio
import time
from typing import List, Dict, Optional
from app.config import settings

# Constant for Byte to GB conversion
GB_CONVERSION = 1024**3

async def fetch_node_stats(session: aiohttp.ClientSession, ip: str) -> Optional[List[Dict]]:
    """
    Executes JSON-RPC call to a target node to retrieve pod statistics.
    Includes latency measurement.
    """
    url = f"http://{ip}:{settings.RPC_PORT}{settings.RPC_ENDPOINT}"
    payload = {"jsonrpc": "2.0", "method": "get-pods-with-stats", "id": 1}
    
    try:
        start_time = time.time()
        timeout = aiohttp.ClientTimeout(total=2.5) # Strict timeout to prevent hanging
        
        async with session.post(url, json=payload, timeout=timeout) as response:
            latency = (time.time() - start_time) * 1000 # ms
            
            if response.status == 200:
                data = await response.json()
                result = data.get('result', {})
                pods = result.get('pods', []) if isinstance(result, dict) else result
                
                # Metadata Injection
                for pod in pods:
                    pod['_reporting_latency'] = latency
                    pod['_source_node'] = ip
                return pods
    except Exception:
        # Silently fail for unreachable nodes (common in P2P networks)
        pass
    return None

async def get_network_state() -> List[Dict]:
    """
    Aggregates state from all seed nodes concurrently.
    Implements deduplication logic to handle multiple reports for the same pubkey.
    """
    async with aiohttp.ClientSession() as session:
        # Parallel execution
        tasks = [fetch_node_stats(session, ip) for ip in settings.seed_nodes]
        results = await asyncio.gather(*tasks)
        
        unique_nodes = {}
        
        for res in results:
            if not res: continue
            for pod in res:
                pubkey = pod.get('pubkey')
                if not pubkey: continue 
                
                # --- DEDUPLICATION STRATEGY ---
                if pubkey not in unique_nodes:
                    unique_nodes[pubkey] = pod
                else:
                    # Conflict resolution: Prefer newer version, then higher storage
                    curr = unique_nodes[pubkey]
                    new_ver = pod.get('version', '0.0.0') or '0.0.0'
                    curr_ver = curr.get('version', '0.0.0') or '0.0.0'
                    
                    if new_ver > curr_ver:
                        unique_nodes[pubkey] = pod
                    elif new_ver == curr_ver:
                        new_storage = float(pod.get('storage_committed') or 0)
                        curr_storage = float(curr.get('storage_committed') or 0)
                        if new_storage > curr_storage:
                            unique_nodes[pubkey] = pod

        return list(unique_nodes.values())

def calculate_heidelberg_score(node: Dict, net_stats: Dict) -> Dict:
    """
    Implements the 'Heidelberg Score' algorithm to quantify node health.
    
    Factors:
    1. Version Compliance (0.7/0.8+)
    2. Uptime Reliability (Relative to network max)
    3. Storage Commitment
    4. Paging Efficiency (Hit Rate)
    """
    # 1. Version Scoring
    version = str(node.get('version') or '0.0.0')
    is_valid_version = ('0.7' in version) or ('0.8' in version)
    score_version = 40 if is_valid_version else 10
    
    # 2. Uptime Scoring
    uptime = float(node.get('uptime') or 0)
    max_uptime = net_stats.get('max_uptime', 1)
    score_uptime = (uptime / max_uptime) * 30 if max_uptime > 0 else 0

    # 3. Storage Scoring
    storage_committed = float(node.get('storage_committed') or 0)
    target_gb = 0.1 # Baseline target
    storage_gb_committed = storage_committed / GB_CONVERSION
    score_storage = min((storage_gb_committed / target_gb) * 20, 20)
    
    # 4. Efficiency Scoring
    hit_rate = float(node.get('paging_hit_rate') or 0.95)
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