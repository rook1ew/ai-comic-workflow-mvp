from pydantic import BaseModel, Field

from app.models.enums import AssetModality, AssetTaskStatus
from app.schemas.asset import AssetResponse
from app.schemas.common import TimestampedResponse


class AssetTaskCreate(BaseModel):
    shot_id: int
    modality: AssetModality
    provider_name: str = Field(default="mock", min_length=1, max_length=100)
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0, le=3)
    input_payload: dict = Field(default_factory=dict)


class AssetTaskResponse(TimestampedResponse):
    shot_id: int
    modality: AssetModality
    status: AssetTaskStatus
    retry_count: int
    max_retries: int
    error_message: str | None
    provider_name: str
    input_payload: dict
    output_payload: dict | None
    assets: list[AssetResponse] = Field(default_factory=list)


class BulkAssetTaskCreateRequest(BaseModel):
    video_shot_ids: list[int] = Field(default_factory=list)
    provider_name: str = Field(default="mock", min_length=1, max_length=100)


class BulkAssetTaskRunResult(BaseModel):
    task_id: int
    shot_id: int
    modality: AssetModality
    status: AssetTaskStatus
    error_message: str | None = None


class BulkAssetTaskRunResponse(BaseModel):
    project_id: int
    succeeded_count: int
    failed_count: int
    needs_human_revision_count: int
    results: list[BulkAssetTaskRunResult]


class ProviderDebugSnapshot(BaseModel):
    asset_task_id: int
    shot_id: str | None = None
    internal_shot_id: int
    modality: AssetModality
    provider_name: str
    status: AssetTaskStatus
    input_payload: dict = Field(default_factory=dict)
    enhanced_prompt: str | None = None
    storyboard_context: dict = Field(default_factory=dict)
    asset_url: str | None = None
    asset_id: int | None = None
    error_message: str | None = None


class ProjectProviderDebugSummaryStats(BaseModel):
    image_tasks_count: int
    video_tasks_count: int
    succeeded_count: int
    failed_count: int
    needs_human_revision_count: int
    missing_enhanced_prompt_count: int
    missing_image_url_for_video_count: int


class ProjectProviderDebugSummary(BaseModel):
    project_id: int
    asset_tasks_count: int
    items: list[ProviderDebugSnapshot] = Field(default_factory=list)
    summary: ProjectProviderDebugSummaryStats
