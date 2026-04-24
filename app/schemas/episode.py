from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse


class EpisodeCreate(BaseModel):
    project_id: int
    title: str = Field(min_length=1, max_length=255)
    episode_number: int = Field(ge=1)
    script_card: str | None = None


class EpisodeResponse(TimestampedResponse):
    project_id: int
    title: str
    episode_number: int
    script_card: str | None
