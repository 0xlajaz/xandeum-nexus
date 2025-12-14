import uvicorn
import os
from app.config import settings

if __name__ == "__main__":
    print(f"🚀 Starting {settings.PROJECT_TITLE} v{settings.VERSION}")
    print(f"📂 Local Data Directory: {os.path.abspath(settings.DATA_DIR)}")
    print(f"👉 Access Dashboard: http://localhost:{settings.PORT}")
    
    # Launch Uvicorn Server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True  # Auto-reload on code changes (Dev Mode)
    )