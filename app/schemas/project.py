from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus
from app.schemas.common import TimestampedResponse


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    target_platforms: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    visual_asset_library_json: dict = Field(default_factory=dict)
    status: ProjectStatus = ProjectStatus.DRAFT


class ProjectResponse(TimestampedResponse):
    name: str
    description: str | None
    target_platforms: list[str]
    tags: list[str]
    visual_asset_library_json: dict
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


class VisualAssetLibraryEntry(BaseModel):
    asset_key: str | None = None
    name: str | None = None
    main_reference_url: str | None = None
    selected_appearance_key: str | None = None
    selected_appearance_url: str | None = None
    appearances_count: int = 0
    must_keep: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)


class VisualAssetRefs(BaseModel):
    characters: list[VisualAssetLibraryEntry] = Field(default_factory=list)
    scene: VisualAssetLibraryEntry | None = None
    props: list[VisualAssetLibraryEntry] = Field(default_factory=list)


class ProjectVisualAssetLibrary(BaseModel):
    project_id: int
    characters_count: int
    scenes_count: int
    props_count: int
    missing_reference_url_count: int = 0
    assets_without_reference_url: list[dict] = Field(default_factory=list)
    characters: list[dict] = Field(default_factory=list)
    scenes: list[dict] = Field(default_factory=list)
    props: list[dict] = Field(default_factory=list)
    next_action: str


class VisualAssetPromptItem(BaseModel):
    asset_key: str
    name: str
    asset_type: str
    prompt_type: str
    prompt_kind: str | None = None
    output_goal: str | None = None
    continuity_note: str | None = None
    target_reference_url: str | None = None
    suggested_reference_filename: str | None = None
    base_prompt: str = ""
    negative_prompt: str = ""
    copy_ready_prompt: str
    must_keep: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)


class ProjectVisualAssetPromptExport(BaseModel):
    project_id: int
    characters_count: int
    scenes_count: int
    props_count: int
    items_count: int
    characters: list[VisualAssetPromptItem] = Field(default_factory=list)
    scenes: list[VisualAssetPromptItem] = Field(default_factory=list)
    props: list[VisualAssetPromptItem] = Field(default_factory=list)
    next_action: str


class ReferenceCoverageMissingAsset(BaseModel):
    asset_type: str
    asset_key: str | None = None
    name: str | None = None


class ReferenceCoverageItem(BaseModel):
    internal_shot_id: int
    source_shot_id: str | None = None
    character: str | None = None
    location: str | None = None
    character_asset_keys: list[str] = Field(default_factory=list)
    scene_asset_key: str | None = None
    prop_asset_keys: list[str] = Field(default_factory=list)
    character_refs_found: bool
    scene_ref_found: bool
    prop_refs_found: bool
    missing_character_asset_keys: list[str] = Field(default_factory=list)
    missing_scene_asset_key: str | None = None
    missing_prop_asset_keys: list[str] = Field(default_factory=list)
    assets_missing_reference_url: list[ReferenceCoverageMissingAsset] = Field(default_factory=list)
    ready_for_reference_guided_image: bool
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class ProjectReferenceCoverageReport(BaseModel):
    project_id: int
    shots_count: int
    ready_shots_count: int
    warning_shots_count: int
    missing_reference_url_count: int
    missing_asset_key_count: int
    items: list[ReferenceCoverageItem] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    next_action: str


class VisualAssetLibraryManualImportAsset(BaseModel):
    asset_key: str
    name: str | None = None
    main_reference_url: str | None = None
    must_keep: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)


class VisualAssetLibraryManualImportRequest(BaseModel):
    asset_type: str
    asset: VisualAssetLibraryManualImportAsset
    merge_mode: str = "upsert"


class VisualAssetCandidate(BaseModel):
    asset_key: str
    name: str
    asset_type: str
    reason: str
    source: str
    suggested_main_reference_url: str | None = None
    must_keep: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    already_in_library: bool = False


class ProjectVisualAssetCandidates(BaseModel):
    project_id: int
    characters: list[VisualAssetCandidate] = Field(default_factory=list)
    scenes: list[VisualAssetCandidate] = Field(default_factory=list)
    props: list[VisualAssetCandidate] = Field(default_factory=list)
    next_action: str


class VisualAssetLibraryImportCandidatesRequest(BaseModel):
    characters: list[VisualAssetLibraryManualImportAsset] = Field(default_factory=list)
    scenes: list[VisualAssetLibraryManualImportAsset] = Field(default_factory=list)
    props: list[VisualAssetLibraryManualImportAsset] = Field(default_factory=list)
    merge_mode: str = "upsert"


class VisualAssetLibraryImportCandidatesResponse(BaseModel):
    project_id: int
    characters_count: int
    scenes_count: int
    props_count: int
    imported_count: int
    updated_count: int
    next_action: str


class ProjectImagePromptItem(BaseModel):
    asset_task_id: int
    internal_shot_id: int
    source_shot_id: str | None = None
    character: str | None = None
    location: str | None = None
    emotion: str | None = None
    camera: str | None = None
    dialogue: str | None = None
    shot_type: str | None = None
    camera_motion: str | None = None
    subject_motion: str | None = None
    transition: str | None = None
    subtitle_text: str | None = None
    sfx: str | None = None
    editing_notes: str | None = None
    shot_purpose: str | None = None
    conflict_beat: str | None = None
    emotion_shift: str | None = None
    visual_focus: str | None = None
    image_prompt_intent: str | None = None
    storyboard_clarity: str | None = None
    pacing_note: str | None = None
    audience_feeling: str | None = None
    reference_priority: str | None = None
    composition: str | None = None
    lighting: str | None = None
    subtitle_position: str | None = None
    negative_constraints: list[str] = Field(default_factory=list)
    character_asset_keys: list[str] = Field(default_factory=list)
    scene_asset_key: str | None = None
    prop_asset_keys: list[str] = Field(default_factory=list)
    visual_asset_refs: VisualAssetRefs = Field(default_factory=VisualAssetRefs)
    missing_visual_asset_refs: list[str] = Field(default_factory=list)
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
    shot_type: str | None = None
    camera_motion: str | None = None
    subject_motion: str | None = None
    transition: str | None = None
    subtitle_text: str | None = None
    sfx: str | None = None
    editing_notes: str | None = None
    shot_purpose: str | None = None
    conflict_beat: str | None = None
    emotion_shift: str | None = None
    visual_focus: str | None = None
    image_prompt_intent: str | None = None
    storyboard_clarity: str | None = None
    pacing_note: str | None = None
    audience_feeling: str | None = None
    reference_priority: str | None = None
    composition: str | None = None
    lighting: str | None = None
    subtitle_position: str | None = None
    negative_constraints: list[str] = Field(default_factory=list)
    character_asset_keys: list[str] = Field(default_factory=list)
    scene_asset_key: str | None = None
    prop_asset_keys: list[str] = Field(default_factory=list)
    visual_asset_refs: VisualAssetRefs = Field(default_factory=VisualAssetRefs)
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
    shot_type: str | None = None
    camera_motion: str | None = None
    subject_motion: str | None = None
    transition: str | None = None
    subtitle_text: str | None = None
    sfx: str | None = None
    editing_notes: str | None = None


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


class EditingShotBoardItem(BaseModel):
    internal_shot_id: int
    source_shot_id: str | None = None
    character: str | None = None
    location: str | None = None
    emotion: str | None = None
    duration: int | float | None = None
    image_asset_url: str | None = None
    has_image_asset: bool
    shot_type: str | None = None
    camera_motion: str | None = None
    subject_motion: str | None = None
    transition: str | None = None
    subtitle_text: str | None = None
    sfx: str | None = None
    editing_notes: str | None = None
    shot_purpose: str | None = None
    conflict_beat: str | None = None
    emotion_shift: str | None = None
    visual_focus: str | None = None
    image_prompt_intent: str | None = None
    storyboard_clarity: str | None = None
    pacing_note: str | None = None
    audience_feeling: str | None = None
    reference_priority: str | None = None
    composition: str | None = None
    lighting: str | None = None
    subtitle_position: str | None = None
    negative_constraints: list[str] = Field(default_factory=list)
    character_asset_keys: list[str] = Field(default_factory=list)
    scene_asset_key: str | None = None
    prop_asset_keys: list[str] = Field(default_factory=list)
    visual_asset_refs: VisualAssetRefs = Field(default_factory=VisualAssetRefs)
    ready_for_editing: bool
    blocking_issues: list[str] = Field(default_factory=list)


class ProjectEditingShotBoard(BaseModel):
    project_id: int
    shots_count: int
    ready_shots_count: int
    blocked_shots_count: int
    items: list[EditingShotBoardItem] = Field(default_factory=list)
    next_action: str


class EditingTimelineItem(BaseModel):
    order: int
    internal_shot_id: int
    source_shot_id: str | None = None
    start_time: int | float
    end_time: int | float
    duration: int | float
    image_asset_url: str | None = None
    subtitle_text: str | None = None
    sfx: str | None = None
    camera_motion: str | None = None
    subject_motion: str | None = None
    transition: str | None = None
    editing_notes: str | None = None
    shot_purpose: str | None = None
    visual_focus: str | None = None
    lighting: str | None = None
    subtitle_position: str | None = None
    ready_for_editing: bool
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ProjectEditingTimeline(BaseModel):
    project_id: int
    shots_count: int
    total_duration: int | float
    ready_for_timeline: bool
    items: list[EditingTimelineItem] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    next_action: str


class EditingCueSheetItem(BaseModel):
    order: int
    source_shot_id: str | None = None
    time_range: str
    duration: int | float
    image_asset_url: str | None = None
    subtitle_text: str | None = None
    sfx: str | None = None
    camera_motion: str | None = None
    subject_motion: str | None = None
    transition: str | None = None
    editing_notes: str | None = None
    shot_purpose: str | None = None
    visual_focus: str | None = None
    lighting: str | None = None
    subtitle_position: str | None = None
    cue_line: str
    ready_for_editing: bool
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ProjectEditingCueSheet(BaseModel):
    project_id: int
    shots_count: int
    total_duration: int | float
    ready_for_cue_sheet: bool
    items: list[EditingCueSheetItem] = Field(default_factory=list)
    plain_text: str
    blocking_issues: list[str] = Field(default_factory=list)
    next_action: str


class StoryboardProductionBoardAssetRef(BaseModel):
    asset_key: str | None = None
    name: str | None = None
    main_reference_url: str | None = None
    selected_appearance_key: str | None = None
    selected_appearance_url: str | None = None


class StoryboardProductionBoardItem(BaseModel):
    order: int
    source_shot_id: str | None = None
    internal_shot_id: int
    time_range: str
    duration: int | float
    human_shot_description: str
    segment_key: str | None = None
    segment_title: str | None = None
    segment_type: str | None = None
    beat_key: str | None = None
    beat_title: str | None = None
    beat_type: str | None = None
    storyboard_group_key: str | None = None
    storyboard_group_title: str | None = None
    story_function: str | None = None
    conflict_beat: str | None = None
    emotion_shift: str | None = None
    visual_focus: str | None = None
    character: str | None = None
    character_display: str | None = None
    character_description: str | None = None
    character_asset_keys: list[str] = Field(default_factory=list)
    character_asset_refs: list[StoryboardProductionBoardAssetRef] = Field(default_factory=list)
    scene: str | None = None
    scene_asset_key: str | None = None
    scene_asset_ref: StoryboardProductionBoardAssetRef | None = None
    prop_asset_keys: list[str] = Field(default_factory=list)
    prop_asset_refs: list[StoryboardProductionBoardAssetRef] = Field(default_factory=list)
    shot_type: str | None = None
    camera: str | None = None
    composition: str | None = None
    lighting: str | None = None
    core_action: str
    subject_motion: str | None = None
    camera_motion: str | None = None
    transition: str | None = None
    emotion: str | None = None
    dialogue: str | None = None
    subtitle_text: str | None = None
    subtitle_position: str | None = None
    sfx: str | None = None
    ambient_sound: str | None = None
    bgm_mood: str | None = None
    audio_timing_note: str | None = None
    has_any_image_asset: bool = False
    has_manual_image_asset: bool = False
    selected_image_asset_url: str | None = None
    selected_asset_source: str = "none"
    copy_ready_image_prompt: str
    copy_ready_motion_prompt: str
    editing_notes: str | None = None
    ready_for_image_generation: bool
    ready_for_editing: bool
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class ProjectStoryboardProductionBoard(BaseModel):
    project_id: int
    items_count: int
    total_duration: int | float
    items: list[StoryboardProductionBoardItem] = Field(default_factory=list)
    plain_text: str
    next_action: str


class ProjectCreativePipelineStatus(BaseModel):
    project_id: int
    story_source_exists: bool
    narrative_structure_exists: bool
    storyboard_package_exists: bool
    segments_count: int
    beats_count: int
    storyboard_groups_count: int
    shots_count: int
    visual_asset_library_exists: bool
    reference_coverage_ready: bool
    storyboard_images_ready: bool
    editing_ready: bool
    next_action: str
