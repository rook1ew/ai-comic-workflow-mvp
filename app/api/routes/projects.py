from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.episode import (
    EpisodeStorySourceRequest,
    EpisodeStorySourceResponse,
    NarrativeStructureLiteRequest,
    NarrativeStructureLiteResponse,
)
from app.schemas.character import ProjectCharacterAppearanceSummary
from app.schemas.project import (
    ProjectCreativePipelineStatus,
    ProjectCreate,
    ProjectImagePromptExport,
    ProjectVideoPromptExport,
    ProjectManualImageProgress,
    ProjectManualFinalChecklist,
    ProjectEditingShotBoard,
    ProjectEditingTimeline,
    ProjectEditingCueSheet,
    ProjectManualProductionSummary,
    ProjectManualVideoProgress,
    ProjectPublishReadiness,
    ProjectReferenceCoverageReport,
    ProjectStoryboardProductionBoard,
    ProjectResponse,
    ProjectSummary,
    ProjectVisualAssetPromptExport,
    ProjectVisualAssetCandidates,
    ProjectVisualAssetLibrary,
    ProjectVideoReadiness,
    ProviderReadinessResponse,
    VisualAssetLibraryImportCandidatesRequest,
    VisualAssetLibraryImportCandidatesResponse,
    VisualAssetLibraryManualImportRequest,
)
from app.services.episode_service import (
    get_project_episode_or_404,
    save_episode_narrative_structure_lite,
    save_episode_story_source,
)
from app.services.character_service import get_project_character_appearance_summary
from app.services.asset_task_service import get_project_provider_readiness
from app.services.project_service import (
    create_project,
    export_project_image_prompts,
    export_project_visual_asset_prompts,
    export_project_video_prompts,
    extract_project_visual_asset_candidates,
    get_project_or_404,
    get_project_manual_image_progress,
    get_project_manual_final_checklist,
    get_project_editing_shot_board,
    get_project_editing_timeline,
    get_project_editing_cue_sheet,
    get_project_storyboard_production_board,
    get_project_manual_production_summary,
    get_project_manual_video_progress,
    get_project_publish_readiness,
    get_project_reference_coverage_report,
    get_project_creative_pipeline_status,
    get_project_summary,
    get_project_visual_asset_library,
    get_project_video_readiness,
    list_projects,
    import_project_visual_asset_candidates,
    manual_import_project_visual_asset,
)

router = APIRouter()


def _build_story_source_response(project_id: int, episode) -> EpisodeStorySourceResponse:
    metadata = episode.metadata_json or {}
    story_source = metadata.get("story_source")
    return EpisodeStorySourceResponse(
        project_id=project_id,
        episode_id=episode.id,
        story_source_exists=isinstance(story_source, dict),
        story_source=story_source if isinstance(story_source, dict) else None,
        source_text_hash=metadata.get("source_text_hash"),
        analysis_status=metadata.get("analysis_status"),
        next_action="generate_narrative_structure" if isinstance(story_source, dict) else "add_story_source",
    )


def _build_narrative_structure_response(project_id: int, episode) -> NarrativeStructureLiteResponse:
    metadata = episode.metadata_json or {}
    narrative_structure = metadata.get("narrative_structure")
    if not isinstance(narrative_structure, dict):
        narrative_structure = None
    segments = narrative_structure.get("segments") if isinstance(narrative_structure, dict) else []
    beats = narrative_structure.get("beats") if isinstance(narrative_structure, dict) else []
    storyboard_groups = narrative_structure.get("storyboard_groups") if isinstance(narrative_structure, dict) else []
    return NarrativeStructureLiteResponse(
        project_id=project_id,
        episode_id=episode.id,
        narrative_structure_exists=isinstance(narrative_structure, dict),
        narrative_structure=narrative_structure,
        segments_count=len(segments) if isinstance(segments, list) else 0,
        beats_count=len(beats) if isinstance(beats, list) else 0,
        storyboard_groups_count=len(storyboard_groups) if isinstance(storyboard_groups, list) else 0,
        next_action="generate_storyboard_package" if isinstance(narrative_structure, dict) else "generate_narrative_structure",
    )


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project_route(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectResponse:
    return create_project(db, payload)


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects_route(db: Session = Depends(get_db)) -> list[ProjectResponse]:
    return list_projects(db)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project_route(project_id: int, db: Session = Depends(get_db)) -> ProjectResponse:
    return get_project_or_404(db, project_id)


@router.get("/projects/{project_id}/summary", response_model=ProjectSummary)
def get_project_summary_route(project_id: int, db: Session = Depends(get_db)) -> ProjectSummary:
    return get_project_summary(db, project_id)


@router.post("/projects/{project_id}/episodes/{episode_id}/story-source", response_model=EpisodeStorySourceResponse)
def save_episode_story_source_route(
    project_id: int,
    episode_id: int,
    payload: EpisodeStorySourceRequest,
    db: Session = Depends(get_db),
) -> EpisodeStorySourceResponse:
    episode = save_episode_story_source(db, project_id, episode_id, payload)
    return _build_story_source_response(project_id, episode)


@router.get("/projects/{project_id}/episodes/{episode_id}/story-source", response_model=EpisodeStorySourceResponse)
def get_episode_story_source_route(
    project_id: int,
    episode_id: int,
    db: Session = Depends(get_db),
) -> EpisodeStorySourceResponse:
    episode = get_project_episode_or_404(db, project_id, episode_id)
    return _build_story_source_response(project_id, episode)


@router.post("/projects/{project_id}/episodes/{episode_id}/narrative-structure-lite", response_model=NarrativeStructureLiteResponse)
def save_episode_narrative_structure_lite_route(
    project_id: int,
    episode_id: int,
    payload: NarrativeStructureLiteRequest,
    db: Session = Depends(get_db),
) -> NarrativeStructureLiteResponse:
    episode = save_episode_narrative_structure_lite(db, project_id, episode_id, payload)
    return _build_narrative_structure_response(project_id, episode)


@router.get("/projects/{project_id}/episodes/{episode_id}/narrative-structure-lite", response_model=NarrativeStructureLiteResponse)
def get_episode_narrative_structure_lite_route(
    project_id: int,
    episode_id: int,
    db: Session = Depends(get_db),
) -> NarrativeStructureLiteResponse:
    episode = get_project_episode_or_404(db, project_id, episode_id)
    return _build_narrative_structure_response(project_id, episode)


@router.get("/projects/{project_id}/creative-pipeline-status", response_model=ProjectCreativePipelineStatus)
def get_project_creative_pipeline_status_route(
    project_id: int,
    db: Session = Depends(get_db),
) -> ProjectCreativePipelineStatus:
    return get_project_creative_pipeline_status(db, project_id)


@router.get("/projects/{project_id}/character-appearance-summary", response_model=ProjectCharacterAppearanceSummary)
def get_project_character_appearance_summary_route(
    project_id: int,
    db: Session = Depends(get_db),
) -> ProjectCharacterAppearanceSummary:
    return get_project_character_appearance_summary(db, project_id)


@router.get("/projects/{project_id}/provider-readiness", response_model=ProviderReadinessResponse)
def get_project_provider_readiness_route(project_id: int, db: Session = Depends(get_db)) -> ProviderReadinessResponse:
    return get_project_provider_readiness(db, project_id)


@router.get("/projects/{project_id}/visual-asset-library", response_model=ProjectVisualAssetLibrary)
def get_project_visual_asset_library_route(project_id: int, db: Session = Depends(get_db)) -> ProjectVisualAssetLibrary:
    return get_project_visual_asset_library(db, project_id)


@router.get("/projects/{project_id}/reference-coverage-report", response_model=ProjectReferenceCoverageReport)
def get_project_reference_coverage_report_route(project_id: int, db: Session = Depends(get_db)) -> ProjectReferenceCoverageReport:
    return get_project_reference_coverage_report(db, project_id)


@router.get("/projects/{project_id}/visual-asset-prompts", response_model=ProjectVisualAssetPromptExport)
def get_project_visual_asset_prompts_route(project_id: int, db: Session = Depends(get_db)) -> ProjectVisualAssetPromptExport:
    return export_project_visual_asset_prompts(db, project_id)


@router.post("/projects/{project_id}/visual-asset-library/manual-import", response_model=ProjectVisualAssetLibrary)
def manual_import_project_visual_asset_route(
    project_id: int,
    payload: VisualAssetLibraryManualImportRequest,
    db: Session = Depends(get_db),
) -> ProjectVisualAssetLibrary:
    return manual_import_project_visual_asset(db, project_id, payload)


@router.post("/projects/{project_id}/visual-asset-candidates/extract", response_model=ProjectVisualAssetCandidates)
def extract_project_visual_asset_candidates_route(
    project_id: int,
    db: Session = Depends(get_db),
) -> ProjectVisualAssetCandidates:
    return extract_project_visual_asset_candidates(db, project_id)


@router.post("/projects/{project_id}/visual-asset-library/import-candidates", response_model=VisualAssetLibraryImportCandidatesResponse)
def import_project_visual_asset_candidates_route(
    project_id: int,
    payload: VisualAssetLibraryImportCandidatesRequest,
    db: Session = Depends(get_db),
) -> VisualAssetLibraryImportCandidatesResponse:
    return import_project_visual_asset_candidates(db, project_id, payload)


@router.get("/projects/{project_id}/image-prompts", response_model=ProjectImagePromptExport)
def get_project_image_prompts_route(project_id: int, db: Session = Depends(get_db)) -> ProjectImagePromptExport:
    return export_project_image_prompts(db, project_id)


@router.get("/projects/{project_id}/video-prompts", response_model=ProjectVideoPromptExport)
def get_project_video_prompts_route(project_id: int, db: Session = Depends(get_db)) -> ProjectVideoPromptExport:
    return export_project_video_prompts(db, project_id)


@router.get("/projects/{project_id}/manual-image-progress", response_model=ProjectManualImageProgress)
def get_project_manual_image_progress_route(project_id: int, db: Session = Depends(get_db)) -> ProjectManualImageProgress:
    return get_project_manual_image_progress(db, project_id)


@router.get("/projects/{project_id}/video-readiness", response_model=ProjectVideoReadiness)
def get_project_video_readiness_route(project_id: int, db: Session = Depends(get_db)) -> ProjectVideoReadiness:
    return get_project_video_readiness(db, project_id)


@router.get("/projects/{project_id}/manual-video-progress", response_model=ProjectManualVideoProgress)
def get_project_manual_video_progress_route(project_id: int, db: Session = Depends(get_db)) -> ProjectManualVideoProgress:
    return get_project_manual_video_progress(db, project_id)


@router.get("/projects/{project_id}/manual-production-summary", response_model=ProjectManualProductionSummary)
def get_project_manual_production_summary_route(project_id: int, db: Session = Depends(get_db)) -> ProjectManualProductionSummary:
    return get_project_manual_production_summary(db, project_id)


@router.get("/projects/{project_id}/publish-readiness", response_model=ProjectPublishReadiness)
def get_project_publish_readiness_route(project_id: int, db: Session = Depends(get_db)) -> ProjectPublishReadiness:
    return get_project_publish_readiness(db, project_id)


@router.get("/projects/{project_id}/manual-final-checklist", response_model=ProjectManualFinalChecklist)
def get_project_manual_final_checklist_route(project_id: int, db: Session = Depends(get_db)) -> ProjectManualFinalChecklist:
    return get_project_manual_final_checklist(db, project_id)


@router.get("/projects/{project_id}/editing-shot-board", response_model=ProjectEditingShotBoard)
def get_project_editing_shot_board_route(project_id: int, db: Session = Depends(get_db)) -> ProjectEditingShotBoard:
    return get_project_editing_shot_board(db, project_id)


@router.get("/projects/{project_id}/editing-timeline", response_model=ProjectEditingTimeline)
def get_project_editing_timeline_route(project_id: int, db: Session = Depends(get_db)) -> ProjectEditingTimeline:
    return get_project_editing_timeline(db, project_id)


@router.get("/projects/{project_id}/editing-cue-sheet", response_model=ProjectEditingCueSheet)
def get_project_editing_cue_sheet_route(project_id: int, db: Session = Depends(get_db)) -> ProjectEditingCueSheet:
    return get_project_editing_cue_sheet(db, project_id)


@router.get("/projects/{project_id}/storyboard-production-board", response_model=ProjectStoryboardProductionBoard)
def get_project_storyboard_production_board_route(project_id: int, db: Session = Depends(get_db)) -> ProjectStoryboardProductionBoard:
    return get_project_storyboard_production_board(db, project_id)
