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
    metadata_json: dict = Field(default_factory=dict)


class EpisodeStorySourceRequest(BaseModel):
    title: str | None = None
    raw_story: str = Field(min_length=1)
    genre: str | None = None
    target_duration_sec: int | None = Field(default=None, ge=1)
    audience: str | None = None
    tone: str | None = None
    manual_notes: str | None = None


class EpisodeStorySourceResponse(BaseModel):
    project_id: int
    episode_id: int
    story_source_exists: bool
    story_source: dict | None = None
    source_text_hash: str | None = None
    analysis_status: str | None = None
    next_action: str


class NarrativeStructureLiteRequest(BaseModel):
    segments: list[dict] = Field(default_factory=list)
    beats: list[dict] = Field(default_factory=list)
    storyboard_groups: list[dict] = Field(default_factory=list)
    manual_notes: str | None = None
    source: str | None = None


class NarrativeStructureLiteResponse(BaseModel):
    project_id: int
    episode_id: int
    narrative_structure_exists: bool
    narrative_structure: dict | None = None
    segments_count: int
    beats_count: int
    storyboard_groups_count: int
    next_action: str
