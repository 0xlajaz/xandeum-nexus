import os
import json
import time
from typing import List, Dict, Any
from app.config import logger

class DataManager:
    """
    Handles local data persistence using flat JSON files.
    Designed to replace cloud object storage for on-premise deployments.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Bootstrapping: Ensures the target directory exists before writing."""
        directory = os.path.dirname(self.file_path)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logger.info(f"FileSystem: Created data directory at {directory}")
            except OSError as e:
                logger.critical(f"FileSystem: Failed to create directory {directory}: {e}")

    def get_history(self, limit: int = 100) -> List[List[Any]]:
        """
        Retrieves historical metrics from disk.
        
        Args:
            limit (int): Number of recent entries to return.
        """
        if not os.path.exists(self.file_path):
            return []
        
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data[-limit:]
                return []
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"IO Error: Failed to read history file: {e}")
            return []

    def save_history(self, stats: Dict[str, Any]) -> None:
        """
        Persists network metrics to local storage.
        
        NOTE: Implements rate limiting (Debounce) to prevent excessive disk I/O.
        Only saves if the last entry is older than 5 minutes.
        """
        try:
            history = self.get_history(limit=1000)

            # Rate Limiting Check
            if history:
                try:
                    last_timestamp = history[-1][0]
                    # 300 seconds = 5 minutes
                    if time.time() - last_timestamp < 300: 
                        return 
                except IndexError:
                    pass

            # Construct new record structure
            new_entry = [
                time.time(),
                stats['total_nodes'],
                stats['avg_health'],
                stats['total_storage_gb'],
                stats.get('avg_paging_efficiency', 0)
            ]
            
            history.append(new_entry)
            
            # Pruning strategy: Keep file size manageable
            history = history[-1000:]

            # Atomic write operation
            with open(self.file_path, 'w') as f:
                json.dump(history, f, indent=2)
            
            logger.info("Persistence: Network history snapshot saved.")

        except Exception as e:
            logger.error(f"Persistence Error: Failed to save history: {e}")