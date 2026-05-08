from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from src.api.routers import games, genres, publishers
from contextlib import asynccontextmanager
from src.api.dependencies import db
from src.db.ingest import seed_from_url
from src.cli.cli import CORGIS_URL  # Import your default URL constant
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Startup: checking database schema...", flush=True)
    try:
        db.create_schema()
        print("Schema ready!", flush=True)

        # Safely read the environment flag for auto seeding
        auto_seed_env = os.getenv("AUTO_SEED", "false")
        should_auto_seed = auto_seed_env.lower() in ("true", "1", "yes")

        if should_auto_seed and db.get_table_count("games") == 0:
            print(
                "Fresh database & auto-seed enabled - seeding from CORGIS...",
                flush=True,
            )

            seed_from_url(db, CORGIS_URL)
            print("Auto-seed complete!", flush=True)
        else:
            print("Auto-seed skipped (Disabled or data already exists).", flush=True)

    except Exception as e:
        print(f"ERROR during API startup: {e}", flush=True)
        raise
    yield


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
