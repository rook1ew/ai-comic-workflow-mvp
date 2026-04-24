from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse


class CharacterCreate(BaseModel):
    project_id: int
    name: str = Field(min_length=1, max_length=255)
    role_type: str = Field(min_length=1, max_length=100)
    profile: str = Field(min_length=1)
    visual_notes: str = Field(min_length=1)
    voice_style: str = Field(min_length=1)
    main_reference_url: str | None = None
    main_reference_confirmed: bool = False


class CharacterResponse(TimestampedResponse):
    project_id: int
    name: str
    role_type: str
    profile: str
    visual_notes: str
    voice_style: str
    main_reference_url: str | None
    main_reference_confirmed: bool
