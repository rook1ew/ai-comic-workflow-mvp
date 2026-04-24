from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Coze-first MVP backend for AI comic-drama workflow validation.",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/")
    def read_root():
        return {
            "success": True,
            "code": "OK",
            "message": f"{settings.app_name} is running",
            "data": {"docs": "/docs", "environment": settings.app_env},
            "next_action": "open_api_docs",
        }

    app.include_router(api_router)

    return app


app = create_app()
