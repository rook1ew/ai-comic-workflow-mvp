from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.project import (
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
    get_project_manual_production_summary,
    get_project_manual_video_progress,
    get_project_publish_readiness,
    get_project_reference_coverage_report,
    get_project_summary,
    get_project_visual_asset_library,
    get_project_video_readiness,
    list_projects,
    import_project_visual_asset_candidates,
    manual_import_project_visual_asset,
)

router = APIRouter()


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
