from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from src.api.routers import games, genres, publishers
from contextlib import asynccontextmanager
from src.api.dependencies import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Startup: checking database schema...", flush=True)
    try:
        db.create_schema() # create db schema if doesn't exist
        print("Schema created successfully!", flush=True)
    except Exception as e:
        print(f"ERROR creating schema: {e}", flush=True)
        raise
    yield
    print("Shutdown: cleaning up...", flush=True)


app = FastAPI(
    title="Game Insights API",
    lifespan=lifespan,
    description="Video game data API",
    version="1.0.0",
)

# start at games endpoint
@app.get("/")
def root():
    return RedirectResponse(url="/games/")


app.include_router(games.router)
app.include_router(genres.router)
app.include_router(publishers.router)
