from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.audio import router as audio_router
from app.api.routes.books import router as books_router
from app.api.routes.progress import router as progress_router
from app.core.config import get_settings
from app.db.models import Base
from app.db.session import engine

settings = get_settings()

app = FastAPI(title="BOOKFLIX API", version="0.1.0")

origins = [origin.strip() for origin in settings.BOOKFLIX_ALLOW_ORIGINS.split(",") if origin.strip()]
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    (settings.storage_path / "epubs").mkdir(parents=True, exist_ok=True)
    (settings.storage_path / "audio").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(books_router)
app.include_router(audio_router)
app.include_router(progress_router)
