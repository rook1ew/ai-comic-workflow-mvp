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


class ProjectImagePromptItem(BaseModel):
    asset_task_id: int
    internal_shot_id: int
    source_shot_id: str | None = None
    character: str | None = None
    location: str | None = None
    emotion: str | None = None
    camera: str | None = None
    dialogue: str | None = None
    base_prompt: str
    enhanced_prompt: str
    negative_prompt: str
    copy_ready_prompt: str


class ProjectImagePromptExport(BaseModel):
    project_id: int
    items_count: int
    items: list[ProjectImagePromptItem] = Field(default_factory=list)


class ProjectVideoPromptItem(BaseModel):
    asset_task_id: int
    internal_shot_id: int
    source_shot_id: str | None = None
    image_asset_url: str | None = None
    duration: int | float | None = None
    character: str | None = None
    location: str | None = None
    emotion: str | None = None
    camera: str | None = None
    dialogue: str | None = None
    base_video_prompt: str
    copy_ready_video_prompt: str
    negative_prompt: str
    ready_for_video_prompt: bool
    blocking_issues: list[str] = Field(default_factory=list)


class ProjectVideoPromptExport(BaseModel):
    project_id: int
    items_count: int
    items: list[ProjectVideoPromptItem] = Field(default_factory=list)


class ProjectManualImageProgressItem(BaseModel):
    asset_task_id: int
    internal_shot_id: int
    source_shot_id: str | None = None
    status: str
    has_asset: bool
    asset_url: str | None = None
    manual_upload: bool
    needs_manual_image: bool
    character: str | None = None
    location: str | None = None
    emotion: str | None = None


class ProjectManualImageProgress(BaseModel):
    project_id: int
    image_tasks_count: int
    completed_image_tasks_count: int
    missing_image_tasks_count: int
    manual_uploaded_count: int
    items: list[ProjectManualImageProgressItem] = Field(default_factory=list)
    next_action: str


class ProjectVideoReadinessItem(BaseModel):
    asset_task_id: int
    internal_shot_id: int
    source_shot_id: str | None = None
    status: str
    has_image_asset: bool
    image_asset_url: str | None = None
    has_duration: bool
    duration: int | float | None = None
    ready_for_video: bool
    blocking_issues: list[str] = Field(default_factory=list)
    character: str | None = None
    location: str | None = None
    emotion: str | None = None
    video_prompt: str


class ProjectVideoReadiness(BaseModel):
    project_id: int
    video_tasks_count: int
    ready_video_tasks_count: int
    blocked_video_tasks_count: int
    items: list[ProjectVideoReadinessItem] = Field(default_factory=list)
    next_action: str


class ProjectManualVideoProgressItem(BaseModel):
    asset_task_id: int
    internal_shot_id: int
    source_shot_id: str | None = None
    status: str
    has_asset: bool
    asset_url: str | None = None
    manual_upload: bool
    needs_manual_video: bool
    character: str | None = None
    location: str | None = None
    emotion: str | None = None
    duration: int | float | None = None


class ProjectManualVideoProgress(BaseModel):
    project_id: int
    video_tasks_count: int
    completed_video_tasks_count: int
    missing_video_tasks_count: int
    manual_uploaded_count: int
    items: list[ProjectManualVideoProgressItem] = Field(default_factory=list)
    next_action: str


class ManualProductionBlockingSummary(BaseModel):
    missing_image_tasks_count: int
    blocked_video_tasks_count: int
    missing_video_tasks_count: int


class ProjectManualProductionSummary(BaseModel):
    project_id: int
    stage: str
    next_action: str
    image: ProjectManualImageProgress
    video_readiness: ProjectVideoReadiness
    video: ProjectManualVideoProgress
    blocking_summary: ManualProductionBlockingSummary
    recommended_steps: list[str] = Field(default_factory=list)


class PublishReadinessChecks(BaseModel):
    manual_production_completed: bool
    all_image_tasks_have_assets: bool
    all_video_tasks_have_assets: bool
    has_failed_tasks: bool
    has_needs_human_revision_tasks: bool
    has_publish_record: bool


class PublishReadinessSummary(BaseModel):
    image_tasks_count: int
    completed_image_tasks_count: int
    video_tasks_count: int
    completed_video_tasks_count: int
    publish_records_count: int


class ProjectPublishReadiness(BaseModel):
    project_id: int
    ready_for_publish: bool
    stage: str
    next_action: str
    checks: PublishReadinessChecks
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: PublishReadinessSummary


class ManualFinalChecklistChecks(BaseModel):
    images_completed: bool
    videos_completed: bool
    video_inputs_ready: bool
    no_failed_tasks: bool
    no_human_revision_tasks: bool
    publish_record_exists: bool


class ProjectManualFinalChecklist(BaseModel):
    project_id: int
    ready_for_delivery: bool
    production_stage: str
    publish_stage: str
    project_status: ProjectStatus
    has_publish_record: bool
    next_action: str
    checks: ManualFinalChecklistChecks
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: PublishReadinessSummary
    recommended_steps: list[str] = Field(default_factory=list)
