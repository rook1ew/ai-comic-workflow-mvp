from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse


class SceneCreate(BaseModel):
    episode_id: int
    scene_number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)


class SceneResponse(TimestampedResponse):
    episode_id: int
    scene_number: int
    title: str
    description: str
