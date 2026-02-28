from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes.auth import router as auth_router
from routes.user import router as user_router
from routes.feed import router as feed_router
from routes.leaderboard import router as leaderboard_router
from routes.coordinator import router as coordinator_router
from scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(feed_router)
app.include_router(leaderboard_router)
app.include_router(coordinator_router)
