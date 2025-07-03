from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# Routers
from app.api import events, categories, calendar

app = FastAPI(title="HomeBase Calendar")

# Frontend is now in the same directory as the app
frontend_dir = os.path.join(os.getcwd(), "frontend")
static_path = os.path.join(frontend_dir, "static")
templates_path = os.path.join(frontend_dir, "templates")

app.mount("/static", StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=templates_path)

# Include API routers
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])


# Serve Frontend
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/weekly", response_class=HTMLResponse)
async def read_weekly(request: Request):
    return templates.TemplateResponse("weekly.html", {"request": request})

@app.get("/monthly", response_class=HTMLResponse)
async def read_monthly(request: Request):
    return templates.TemplateResponse("monthly.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def read_settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request}) 