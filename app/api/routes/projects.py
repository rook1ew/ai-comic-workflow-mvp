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
    ProjectManualProductionSummary,
    ProjectManualVideoProgress,
    ProjectPublishReadiness,
    ProjectResponse,
    ProjectSummary,
    ProjectVideoReadiness,
    ProviderReadinessResponse,
)
from app.services.asset_task_service import get_project_provider_readiness
from app.services.project_service import (
    create_project,
    export_project_image_prompts,
    export_project_video_prompts,
    get_project_or_404,
    get_project_manual_image_progress,
    get_project_manual_final_checklist,
    get_project_editing_shot_board,
    get_project_manual_production_summary,
    get_project_manual_video_progress,
    get_project_publish_readiness,
    get_project_summary,
    get_project_video_readiness,
    list_projects,
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
