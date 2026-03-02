from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db.database import Base, engine
from app.routes import frontend, health, scoring, transactions

settings = get_settings()
static_dir = Path(__file__).resolve().parent / "static"

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
def on_startup() -> None:
    if settings.db_auto_create:
        Base.metadata.create_all(bind=engine)


app.include_router(health.router)
app.include_router(frontend.router)
app.include_router(transactions.router, prefix=settings.api_prefix)
app.include_router(scoring.router, prefix=settings.api_prefix)
