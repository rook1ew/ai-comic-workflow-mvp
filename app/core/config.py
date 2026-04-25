from functools import lru_cache
from os import getenv

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    app_name: str = "Coze AI Comic MVP"
    app_env: str = "local"
    database_url: str = "sqlite:///./data/app.db"
    image_provider_mode: str = "mock"
    image2_api_key: str = ""
    image2_base_url: str = ""
    image2_model: str = "image2"
    enable_real_image_provider: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=getenv("APP_NAME", "Coze AI Comic MVP"),
        app_env=getenv("APP_ENV", "local"),
        database_url=getenv("DATABASE_URL", "sqlite:///./data/app.db"),
        image_provider_mode=getenv("IMAGE_PROVIDER_MODE", "mock"),
        image2_api_key=getenv("IMAGE2_API_KEY", ""),
        image2_base_url=getenv("IMAGE2_BASE_URL", ""),
        image2_model=getenv("IMAGE2_MODEL", "image2"),
        enable_real_image_provider=getenv("ENABLE_REAL_IMAGE_PROVIDER", "false").lower() in {"1", "true", "yes", "on"},
    )
