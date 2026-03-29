import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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



@asynccontextmanager
async def lifespan(app: FastAPI):
    from leaderboard_cache import seed_from_db
    from database import SessionLocal
    async with SessionLocal() as db:
        await seed_from_db(db)
    yield



app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"],
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
