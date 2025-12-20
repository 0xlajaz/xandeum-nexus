import os
import logging
from typing import List
from dotenv import load_dotenv

load_dotenv()  

# --- LOGGING CONFIGURATION ---
# 1. Define the format
log_format = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"

# 2. Configure the Root Logger
logging.basicConfig(level=logging.INFO, format=log_format)

# 3. SILENCE THE NOISY LIBRARIES (The Fix)
# This stops httpx (Telegram) and apscheduler (Job Queue) from spamming "INFO" logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)

logger = logging.getLogger("xandeum_nexus")

class Config:
    """
    Centralized configuration management.
    """
    
    # Project Metadata
    PROJECT_TITLE: str = os.getenv("PROJECT_TITLE", "Xandeum Nexus Intelligence")
    VERSION: str = os.getenv("PROJECT_VERSION", "1.1.0-SENTINEL")
    
    # Server Settings
    PORT: int = int(os.getenv("PORT", 8080))
    RPC_PORT: str = os.getenv("RPC_PORT", "6000")
    RPC_ENDPOINT: str = os.getenv("RPC_ENDPOINT", "/rpc")
    
    # Storage Settings
    DATA_DIR: str = "data"
    HISTORY_FILE: str = os.path.join(DATA_DIR, "network_history.json")
    
    # Sentinel Bot Configuration
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", "")
    
    # Network Settings
    DEFAULT_SEEDS: List[str] = [
        "173.212.203.145", "173.212.220.65", "161.97.97.41",
        "192.190.136.36", "192.190.136.37", "192.190.136.38",
        "192.190.136.28", "192.190.136.29", "207.244.255.1"
    ]

    @property
    def seed_nodes(self) -> List[str]:
        env_seeds = os.getenv("SEED_NODES")
        return env_seeds.split(",") if env_seeds else self.DEFAULT_SEEDS

settings = Config()
