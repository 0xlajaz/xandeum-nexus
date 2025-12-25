import aiohttp
import asyncio
import time
import re
import json
import os
from collections import defaultdict
from typing import List, Dict, Optional, Tuple
from app.config import settings, logger
import geoip2.database

# Constant for Byte to GB conversion
GB_CONVERSION = 1024**3
CREDITS_API_URL = "https://podcredits.xandeum.network/api/pods-credits"

class GeoResolver:
    """
    Handles IP-to-Country resolution using local MaxMind GeoLite2 DB.
    Zero-latency, privacy-preserving, and offline-capable.
    """
    def __init__(self, db_path="data/GeoLite2-City.mmdb"):
        self.db_path = db_path
        self.reader = None
        self._load_reader()

    def _load_reader(self):
        """Initializes the MMDB reader securely."""
        try:
            if os.path.exists(self.db_path):
                self.reader = geoip2.database.Reader(self.db_path)
                logger.info(f"✅ Loaded GeoIP Database: {self.db_path}")
            else:
                logger.warning(f"⚠️ GeoIP Database missing at {self.db_path}. Geo-resolution disabled.")
        except Exception as e:
            logger.error(f"❌ Failed to load GeoIP Database: {e}")

    async def resolve_batch(self, ips: List[str]):
        """
        Compatibility method. 
        With local DB, 'batching' is unnecessary as lookups are instant.
        We keep this to avoid breaking existing calls in get_network_state.
        """
        # No-op: Local lookups are done on-demand in get_geo
        pass 

    def get_geo(self, ip: str) -> Dict:
        """
        Instant local lookup. No caching needed (MMDB is optimized for speed).
        """
        if not self.reader:
            return {'country': 'Unknown', 'countryCode': '??'}

        # Filter out local IPs to avoid errors
        if ip in ["127.0.0.1", "localhost", "::1"]:
             return {'country': 'Localhost', 'countryCode': 'LH'}

        try:
            # Perform Lookup
            response = self.reader.city(ip)
            
            return {
                'country': response.country.name or 'Unknown',
                'countryCode': response.country.iso_code or '??',
                'region': response.subdivisions.most_specific.name or '',
                'city': response.city.name or '',
                'isp': 'Unknown' # MMDB City version doesn't include ISP data
            }
        except geoip2.errors.AddressNotFoundError:
            # IP not in database
            return {'country': 'Unknown', 'countryCode': '??'}
        except Exception as e:
            logger.debug(f"Geo lookup error for {ip}: {e}")
            return {'country': 'Unknown', 'countryCode': '??'}

    def close(self):
        """Clean up file handle on shutdown."""
        if self.reader:
            self.reader.close()

# Initialize global resolver
geo_resolver = GeoResolver()

def parse_version(version_str: str) -> Tuple[int, int, int]:
    """
    Safely parse version string to tuple for comparison.
    Examples: "0.7.0" -> (0, 7, 0), "v0.8.1" -> (0, 8, 1)
    Returns (0, 0, 0) if parsing fails.
    """
    try:
        # Remove common prefixes and extract numbers
        clean_version = re.sub(r'^v', '', version_str.strip())
        parts = re.findall(r'\d+', clean_version)
        
        if len(parts) >= 3:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        elif len(parts) == 2:
            return (int(parts[0]), int(parts[1]), 0)
        elif len(parts) == 1:
            return (int(parts[0]), 0, 0)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse version '{version_str}': {e}")
    
    return (0, 0, 0)

async def fetch_pod_credits(session: aiohttp.ClientSession) -> Dict[str, int]:
    """
    Fetches official Reputation Credits from Xandeum API.
    Returns a dictionary mapping pod_id (pubkey) -> credits.
    """
    try:
        async with session.get(CREDITS_API_URL, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status == 200:
                data = await response.json()
                credits_map = {}
                
                for item in data.get('pods_credits', []):
                    pid = item.get('pod_id')
                    c = item.get('credits', 0)
                    if pid:
                        credits_map[pid] = c
                
                logger.info(f"Successfully fetched credits for {len(credits_map)} pods")
                return credits_map
            else:
                logger.warning(f"Credits API returned status {response.status}")
                
    except asyncio.TimeoutError:
        logger.error("Timeout fetching pod credits - API took longer than 5 seconds")
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching pod credits: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching pod credits: {e}", exc_info=True)
    
    return {}

async def fetch_node_stats(session: aiohttp.ClientSession, ip: str) -> Optional[List[Dict]]:
    """
    Executes JSON-RPC call to a target node to retrieve pod statistics.
    Includes latency measurement and improved error handling.
    """
    url = f"http://{ip}:{settings.RPC_PORT}{settings.RPC_ENDPOINT}"
    payload = {"jsonrpc": "2.0", "method": "get-pods-with-stats", "id": 1}
    
    try:
        start_time = time.time()
        timeout = aiohttp.ClientTimeout(total=2.5)
        
        async with session.post(url, json=payload, timeout=timeout) as response:
            latency = (time.time() - start_time) * 1000  # ms
            
            if response.status == 200:
                data = await response.json()
                result = data.get('result', {})
                pods = result.get('pods', []) if isinstance(result, dict) else result
                
                if not pods:
                    logger.debug(f"Node {ip} returned empty pod list")
                
                # Metadata Injection
                for pod in pods:
                    pod['_reporting_latency'] = latency
                    pod['_source_node'] = ip
                
                logger.debug(f"Successfully fetched {len(pods)} pods from {ip} (latency: {latency:.2f}ms)")
                return pods
            else:
                logger.warning(f"Node {ip} returned HTTP {response.status}")
                
    except asyncio.TimeoutError:
        logger.warning(f"Timeout connecting to node {ip} (>2.5s)")
    except aiohttp.ClientError as e:
        logger.warning(f"Network error connecting to {ip}: {type(e).__name__}")
    except Exception as e:
        logger.error(f"Unexpected error fetching stats from {ip}: {e}", exc_info=True)
    
    return None

async def get_network_state() -> Tuple[List[Dict], Dict[str, int]]:
    """
    Aggregates state from all seed nodes AND fetches official credits concurrently.
    Returns: (nodes_list, credits_map)
    """
    logger.info(f"Fetching network state from {len(settings.seed_nodes)} seed nodes")
    
    async with aiohttp.ClientSession() as session:
        # Parallel execution: Fetch RPC stats AND Pod Credits at the same time
        tasks = [fetch_node_stats(session, ip) for ip in settings.seed_nodes]
        credits_task = fetch_pod_credits(session)
        
        # Unpack results
        results = await asyncio.gather(*tasks, credits_task, return_exceptions=True)
        
        # Separate RPC results from credits
        rpc_results = results[:-1]
        credits_result = results[-1]
        
        # Handle credits result
        if isinstance(credits_result, Exception):
            logger.error(f"Credits fetch failed with exception: {credits_result}")
            credits_map = {}
        else:
            credits_map = credits_result
        
        unique_nodes = {}
        total_pods_found = 0
        
        for idx, res in enumerate(rpc_results):
            # Handle exceptions from individual node fetches
            if isinstance(res, Exception):
                logger.error(f"Seed node {settings.seed_nodes[idx]} failed: {res}")
                continue
            
            if not res:
                continue
            
            total_pods_found += len(res)
            
            for pod in res:
                pubkey = pod.get('pubkey')
                if not pubkey:
                    logger.warning(f"Pod without pubkey from {pod.get('_source_node', 'unknown')}")
                    continue 
                
                # --- IMPROVED DEDUPLICATION STRATEGY ---
                if pubkey not in unique_nodes:
                    unique_nodes[pubkey] = pod
                else:
                    curr = unique_nodes[pubkey]
                    
                    # Parse versions for proper comparison
                    new_ver = parse_version(pod.get('version', '0.0.0') or '0.0.0')
                    curr_ver = parse_version(curr.get('version', '0.0.0') or '0.0.0')
                    
                    # Prioritize newer version
                    if new_ver > curr_ver:
                        unique_nodes[pubkey] = pod
                        logger.debug(f"Updated node {pubkey[:8]} to newer version {new_ver}")
                    elif new_ver == curr_ver:
                        # If same version, prioritize higher storage
                        try:
                            new_storage = float(pod.get('storage_committed') or 0)
                            curr_storage = float(curr.get('storage_committed') or 0)
                            if new_storage > curr_storage:
                                unique_nodes[pubkey] = pod
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid storage value for node {pubkey[:8]}: {e}")

        logger.info(f"Discovered {len(unique_nodes)} unique nodes from {total_pods_found} total pod entries")
        return list(unique_nodes.values()), credits_map

async def get_network_state() -> Tuple[List[Dict], Dict[str, int]]:
    """
    Aggregates state with INSIGHT 2 (Visibility) and INSIGHT 3 (Geo)
    """
    logger.info(f"Fetching network state from {len(settings.seed_nodes)} seed nodes")
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_node_stats(session, ip) for ip in settings.seed_nodes]
        credits_task = fetch_pod_credits(session)
        results = await asyncio.gather(*tasks, credits_task, return_exceptions=True)
        
        rpc_results = results[:-1]
        credits_result = results[-1]
        credits_map = credits_result if not isinstance(credits_result, Exception) else {}
        
        unique_nodes = {}
        # 🟢 INSIGHT 2: Track Visibility (Witness Count)
        visibility_counts = defaultdict(int) 
        
        total_pods_found = 0
        all_ips = set()
        
        for idx, res in enumerate(rpc_results):
            if isinstance(res, Exception) or not res: continue
            
            total_pods_found += len(res)
            
            for pod in res:
                pubkey = pod.get('pubkey')
                if not pubkey: continue
                
                # 🟢 INSIGHT 2: Increment witness count
                visibility_counts[pubkey] += 1
                
                # Collect IP for Geo Resolution
                ip_address = pod.get('address', '').split(':')[0]
                if ip_address: all_ips.add(ip_address)

                # Deduplication Logic
                if pubkey not in unique_nodes:
                    unique_nodes[pubkey] = pod
                else:
                    curr = unique_nodes[pubkey]
                    new_ver = parse_version(pod.get('version', '0.0.0'))
                    curr_ver = parse_version(curr.get('version', '0.0.0'))
                    
                    if new_ver > curr_ver:
                        unique_nodes[pubkey] = pod
                    elif new_ver == curr_ver:
                        try:
                            if float(pod.get('storage_committed') or 0) > float(curr.get('storage_committed') or 0):
                                unique_nodes[pubkey] = pod
                        except: pass

        # 🌍 INSIGHT 3: Trigger Background Geo Resolution
        # We don't await this blocking the main request - we fire and forget (or await if fast)
        # For first run, it might be slow, so we just trigger it.
        asyncio.create_task(geo_resolver.resolve_batch(list(all_ips)))

        # Final Data Injection
        final_nodes = []
        for pubkey, node in unique_nodes.items():
            # Inject Visibility
            node['_visibility'] = visibility_counts[pubkey]
            
            # Inject Geo Data (from cache)
            ip = node.get('address', '').split(':')[0]
            node['_geo'] = geo_resolver.get_geo(ip)
            
            final_nodes.append(node)

        logger.info(f"Discovered {len(final_nodes)} unique nodes. Max visibility: {max(visibility_counts.values()) if visibility_counts else 0}")
        return final_nodes, credits_map

def calculate_heidelberg_score(node: Dict, net_stats: Dict) -> Dict:
    try:
        # 1. Version (Keep as is) - 40 pts
        version = str(node.get('version') or '0.0.0')
        is_valid_version = bool(re.search(r'0\.[89]', version))
        score_version = 40 if is_valid_version else 10
        
        # 2. Uptime (CHANGE THIS) - 30 pts
        # Don't compare to "Max Uptime". Compare to a fixed "24 Hour" target.
        uptime = float(node.get('uptime') or 0)
        target_uptime = 86400 * 7  # Target: 7 Days (604800 seconds)
        # Cap it at 1.0 so you don't get >30 points
        uptime_ratio = min(uptime / target_uptime, 1.0)
        score_uptime = uptime_ratio * 30

        # 3. Storage (Keep as is) - 20 pts
        storage_committed = float(node.get('storage_committed') or 0)
        target_gb = 0.1
        score_storage = min(((storage_committed / GB_CONVERSION) / target_gb) * 20, 20)
        
        # 4. Paging / Performance - 10 pts
        # Combine Hit Rate + Latency to create "Jitter" (movement) in the chart
        hit_rate = float(node.get('paging_hit_rate') or 0.95)
        
        # New: Latency Penalty
        latency = node.get('_reporting_latency', 0)
        latency_penalty = 0
        if latency > 500: latency_penalty = 2
        if latency > 1000: latency_penalty = 5
        
        score_paging = max((hit_rate * 10) - latency_penalty, 0)
        
        total = score_version + score_uptime + score_storage + score_paging
        
        return {
            "total": int(total), # It will now fluctuate based on latency/uptime growth
            "breakdown": {
                "v0.7_compliance": int(score_version),
                "uptime_reliability": int(score_uptime),
                "storage_weight": int(score_storage),
                "paging_efficiency": int(score_paging)
            },
            "metrics": {
                "hit_rate": hit_rate,
                "latency": latency
            }
        }
    except:
        return {"total": 0, "breakdown": {}, "metrics": {}}
