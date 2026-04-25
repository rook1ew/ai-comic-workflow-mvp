from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus
from app.schemas.common import TimestampedResponse


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    target_platforms: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    status: ProjectStatus = ProjectStatus.DRAFT


class ProjectResponse(TimestampedResponse):
    name: str
    description: str | None
    target_platforms: list[str]
    tags: list[str]
    status: ProjectStatus


class ProjectSummary(BaseModel):
    project_id: int
    project_status: ProjectStatus
    episodes_count: int
    scenes_count: int
    shots_count: int
    asset_tasks_count: int
    assets_count: int
    succeeded_tasks_count: int
    failed_tasks_count: int
    needs_human_revision_count: int
    publish_records_count: int
    next_action: str


class ProviderReadinessResponse(BaseModel):
    project_id: int
    ready_for_image_provider: bool
    ready_for_video_provider: bool
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)
