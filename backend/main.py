import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(level=logging.INFO)
from contextlib import asynccontextmanager
from routes.auth import router as auth_router
from routes.user import router as user_router
from routes.feed import router as feed_router
from routes.leaderboard import router as leaderboard_router
from routes.coordinator import router as coordinator_router
from routes.feedback import router as feedback_router
from routes.admin import router as admin_router
from routes.webhooks import router as webhooks_router
from routes.course import router as course_router
from routes.programme import router as programme_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    # The leaderboard is served straight from Postgres (services/leaderboard.py),
    # so there is no cache to seed at startup any more — and no "restart the
    # backend to fix the leaderboard" failure mode.
    yield



app = FastAPI(lifespan=lifespan)

# Excluding /metrics keeps http_request_* a measure of user traffic. Prometheus
# scrapes every 15s, so without this the endpoint contributes 240 requests/hour
# forever and drowns out real usage — it was 629 of 631 recorded requests. Scrape
# health is already covered by Prometheus's own up / scrape_duration_seconds.
Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app)

from prometheus_client import REGISTRY
from integrity_metrics import IntegrityCollector

REGISTRY.register(IntegrityCollector())
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(feed_router)
app.include_router(leaderboard_router)
app.include_router(coordinator_router)
app.include_router(feedback_router)
app.include_router(admin_router)
app.include_router(webhooks_router)
app.include_router(course_router)
app.include_router(programme_router)
