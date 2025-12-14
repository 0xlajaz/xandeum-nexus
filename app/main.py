from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes import router

# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_TITLE,
    description="Local Heidelberg Analytics Platform",
    version=settings.VERSION
)

# --- MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STATIC FILES & TEMPLATES ---
# Mounts the static directory to serve JS/CSS
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- ROUTER REGISTRATION ---
app.include_router(router)

# --- ROOT ENDPOINT ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serves the Single Page Application (SPA) entrypoint."""
    return templates.TemplateResponse("index.html", {"request": request})