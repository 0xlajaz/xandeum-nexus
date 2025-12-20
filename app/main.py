import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.config import settings, logger
from app.routes import router
from app.bot import run_bot
from app.network import get_network_state # <--- IMPORT THIS

# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_TITLE,
    description="Local Heidelberg Analytics Platform",
    version=settings.VERSION
)

# --- MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# --- STATIC FILES & TEMPLATES ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- ROUTER REGISTRATION ---
app.include_router(router)

# --- BACKGROUND TASKS ---
async def warm_up_network():
    """Scans the network immediately so data is ready when user arrives."""
    logger.info("🔥 Warming up network cache...")
    try:
        nodes, _ = await get_network_state()
        logger.info(f"✅ Warm-up complete. Discovered {len(nodes)} nodes.")
    except Exception as e:
        logger.warning(f"⚠️ Warm-up failed: {e}")

# --- LIFECYCLE EVENTS ---
@app.on_event("startup")
async def startup_event():
    """
    Triggers when the server starts.
    1. Starts Sentinel Bot
    2. Warms up Network Cache
    """
    logger.info("🚀 Starting Xandeum Nexus Backend...")
    
    # 1. Start Bot
    if settings.TELEGRAM_TOKEN:
        asyncio.create_task(run_bot())
        logger.info("✅ Sentinel Bot Task Created")
    else:
        logger.warning("⚠️ No Telegram Token found. Bot functionality skipped.")

    # 2. Warm Up Cache (The Fix)
    asyncio.create_task(warm_up_network())

# --- ROOT ENDPOINT ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
