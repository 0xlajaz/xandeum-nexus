import os
import json
import time
import asyncio
from functools import partial
from typing import List, Dict, Any
from app.config import logger

class DataManager:
    """
    Handles local data persistence using flat JSON files.
    Includes Async IO wrapper to prevent Dashboard lag.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    # --- ASYNC WRAPPERS (PREVENTS LAG) ---
    async def save_history_async(self, stats: Dict[str, Any]) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self.save_history, stats))

    # --- WATCHLIST (BOT) ---
    @property
    def watchlist_file(self) -> str:
        return os.path.join(os.path.dirname(self.file_path), "watchlist.json")

    @property
    def ignores_file(self) -> str:
        return os.path.join(os.path.dirname(self.file_path), "ignores.json")

    def get_watchlist(self) -> Dict[str, List[str]]:
        return self._load_json(self.watchlist_file)

    def add_watch(self, chat_id: str, node_id: str) -> bool:
        data = self.get_watchlist()
        if chat_id not in data: data[chat_id] = []
        if node_id not in data[chat_id]:
            data[chat_id].append(node_id)
            return self._save_json(self.watchlist_file, data)
        return True

    def remove_watch(self, chat_id: str, node_id: str) -> bool:
        data = self.get_watchlist()
        if chat_id in data and node_id in data[chat_id]:
            data[chat_id].remove(node_id)
            if not data[chat_id]: del data[chat_id]
            return self._save_json(self.watchlist_file, data)
        return False

    # --- IGNORES (BOT PREFERENCES) ---
    def get_ignores(self) -> Dict[str, float]:
        return self._load_json(self.ignores_file)

    def save_ignores(self, data: Dict[str, float]) -> bool:
        return self._save_json(self.ignores_file, data)

    # --- HISTORY (DASHBOARD) ---
    def get_history(self, limit: int = 100) -> List[List[Any]]:
        data = self._load_json(self.file_path)
        return data[-limit:] if isinstance(data, list) else []

    def save_history(self, stats: Dict[str, Any]) -> bool:
        try:
            required = ['total_nodes', 'avg_health', 'total_storage_gb', 'avg_paging_efficiency']
            if any(k not in stats for k in required): return False
            
            history = self.get_history(limit=1000)
            if history and (time.time() - history[-1][0]) < 300: return False # 5 min limit

            new_entry = [
                time.time(), int(stats['total_nodes']), float(stats['avg_health']),
                float(stats['total_storage_gb']), float(stats.get('avg_paging_efficiency', 0))
            ]
            history.append(new_entry)
            if len(history) > 1000: history = history[-1000:]
            
            return self._save_json(self.file_path, history)
        except Exception as e:
            logger.error(f"Save history failed: {e}")
            return False

    # --- INTERNAL HELPERS ---
    def _load_json(self, path: str) -> Any:
        if not os.path.exists(path): return {} if "history" not in path else []
        try:
            with open(path, 'r') as f: return json.load(f)
        except: return {} if "history" not in path else []

    def _save_json(self, path: str, data: Any) -> bool:
        try:
            temp = f"{path}.tmp"
            with open(temp, 'w') as f: json.dump(data, f, indent=2)
            os.replace(temp, path)
            return True
        except Exception as e:
            logger.error(f"JSON Save failed for {path}: {e}")
            return False
