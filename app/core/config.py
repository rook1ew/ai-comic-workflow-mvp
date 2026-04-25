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
    image2_max_real_calls_per_run: int = 1
    image2_allow_task_ids: list[int] = []
    image2_dry_run: bool = True


@lru_cache
def get_settings() -> Settings:
    raw_allow_task_ids = getenv("IMAGE2_ALLOW_TASK_IDS", "")
    allow_task_ids = [
        int(item.strip())
        for item in raw_allow_task_ids.split(",")
        if item.strip().isdigit()
    ]
    return Settings(
        app_name=getenv("APP_NAME", "Coze AI Comic MVP"),
        app_env=getenv("APP_ENV", "local"),
        database_url=getenv("DATABASE_URL", "sqlite:///./data/app.db"),
        image_provider_mode=getenv("IMAGE_PROVIDER_MODE", "mock"),
        image2_api_key=getenv("IMAGE2_API_KEY", ""),
        image2_base_url=getenv("IMAGE2_BASE_URL", ""),
        image2_model=getenv("IMAGE2_MODEL", "image2"),
        enable_real_image_provider=getenv("ENABLE_REAL_IMAGE_PROVIDER", "false").lower() in {"1", "true", "yes", "on"},
        image2_max_real_calls_per_run=int(getenv("IMAGE2_MAX_REAL_CALLS_PER_RUN", "1")),
        image2_allow_task_ids=allow_task_ids,
        image2_dry_run=getenv("IMAGE2_DRY_RUN", "true").lower() in {"1", "true", "yes", "on"},
    )
