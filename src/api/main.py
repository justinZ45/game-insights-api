from fastapi import FastAPI
from src.api.routers import games, genres, publishers

app = FastAPI(
    title="Game Insights API", description="Video game data API", version="1.0.0"
)

app.include_router(games.router)
app.include_router(genres.router)
app.include_router(publishers.router)
