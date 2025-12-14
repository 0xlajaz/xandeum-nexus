import os
import logging
from typing import List

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("xandeum_nexus")

class Config:
    """
    Centralized configuration management.
    Loads values from environment variables or falls back to defaults.
    """
    
    # Project Metadata
    PROJECT_TITLE: str = os.getenv("PROJECT_TITLE", "Xandeum Nexus Intelligence")
    VERSION: str = os.getenv("PROJECT_VERSION", "1.0.0-MODULAR")
    
    # Server Settings
    PORT: int = int(os.getenv("PORT", 8080))
    RPC_PORT: str = os.getenv("RPC_PORT", "6000")
    RPC_ENDPOINT: str = os.getenv("RPC_ENDPOINT", "/rpc")
    
    # Storage Settings
    DATA_DIR: str = "data"
    HISTORY_FILE: str = os.path.join(DATA_DIR, "network_history.json")
    
    # Network Settings
    # NOTE: Default public seeds provided by Xandeum documentation
    DEFAULT_SEEDS: List[str] = [
        "173.212.203.145", "173.212.220.65", "161.97.97.41",
        "192.190.136.36", "192.190.136.37", "192.190.136.38",
        "192.190.136.28", "192.190.136.29", "207.244.255.1"
    ]

    @property
    def seed_nodes(self) -> List[str]:
        """Parses seed nodes from ENV or returns default."""
        env_seeds = os.getenv("SEED_NODES")
        return env_seeds.split(",") if env_seeds else self.DEFAULT_SEEDS

settings = Config()