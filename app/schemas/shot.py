from pydantic import BaseModel, Field, field_validator

from app.models.enums import ShotStatus
from app.schemas.common import TimestampedResponse


class ShotCreate(BaseModel):
    scene_id: int
    shot_number: int = Field(ge=1)
    framing: str = Field(min_length=1, max_length=100)
    core_action: str = Field(min_length=1)
    dialogue: str | None = None
    image_prompt: str = Field(min_length=1)
    video_prompt: str = Field(min_length=1)
    voice_prompt: str = Field(min_length=1)
    bgm_prompt: str = Field(min_length=1)
    status: ShotStatus = ShotStatus.PROMPT_READY

    @field_validator("core_action")
    @classmethod
    def validate_core_action(cls, value: str) -> str:
        normalized = " ".join(value.split())
        separators = [",", "，", ";", "；", " and ", "然后", "同时"]
        if any(separator in normalized for separator in separators):
            raise ValueError("A shot allows only one core action description.")
        return normalized


class ShotResponse(TimestampedResponse):
    scene_id: int
    shot_number: int
    framing: str
    core_action: str
    dialogue: str | None
    image_prompt: str
    video_prompt: str
    voice_prompt: str
    bgm_prompt: str
    status: ShotStatus
