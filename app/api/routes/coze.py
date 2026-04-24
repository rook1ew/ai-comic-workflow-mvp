from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.coze import (
    ConfirmCharacterReferenceRequest,
    CozeCreateAssetTasksRequest,
    CozeGenerateScriptRequest,
    CozePublishRecordRequest,
    CozeProjectInitRequest,
    CozeResponse,
    CozeStoryboardRequest,
)
from app.services.coze_service import (
    coze_confirm_character_reference,
    coze_create_asset_tasks,
    coze_generate_script,
    coze_project_init,
    coze_publish_record,
    coze_project_summary,
    coze_run_asset_tasks,
    coze_storyboard,
)

router = APIRouter()


@router.post("/coze/project/init", response_model=CozeResponse, status_code=201)
def coze_project_init_route(payload: CozeProjectInitRequest, db: Session = Depends(get_db)) -> CozeResponse:
    return coze_project_init(db, payload)


@router.post("/coze/project/{project_id}/generate-script", response_model=CozeResponse)
def coze_generate_script_route(
    project_id: int,
    payload: CozeGenerateScriptRequest,
    db: Session = Depends(get_db),
) -> CozeResponse:
    return coze_generate_script(db, project_id, payload)


@router.post("/characters/{character_id}/confirm-reference", response_model=CozeResponse)
def confirm_character_reference_route(
    character_id: int,
    payload: ConfirmCharacterReferenceRequest,
    db: Session = Depends(get_db),
) -> CozeResponse:
    return coze_confirm_character_reference(db, character_id, payload)


@router.post("/coze/project/{project_id}/storyboard", response_model=CozeResponse, status_code=201)
def coze_storyboard_route(project_id: int, payload: CozeStoryboardRequest, db: Session = Depends(get_db)) -> CozeResponse:
    return coze_storyboard(db, project_id, payload)


@router.post("/coze/project/{project_id}/create-asset-tasks", response_model=CozeResponse)
def coze_create_asset_tasks_route(
    project_id: int,
    payload: CozeCreateAssetTasksRequest,
    db: Session = Depends(get_db),
) -> CozeResponse:
    return coze_create_asset_tasks(db, project_id, payload)


@router.post("/coze/project/{project_id}/run-asset-tasks", response_model=CozeResponse)
def coze_run_asset_tasks_route(project_id: int, db: Session = Depends(get_db)) -> CozeResponse:
    return coze_run_asset_tasks(db, project_id)


@router.post("/coze/project/{project_id}/publish-record", response_model=CozeResponse)
def coze_publish_record_route(
    project_id: int,
    payload: CozePublishRecordRequest,
    db: Session = Depends(get_db),
) -> CozeResponse:
    return coze_publish_record(db, project_id, payload)


@router.get("/coze/project/{project_id}/summary", response_model=CozeResponse)
def coze_project_summary_route(project_id: int, db: Session = Depends(get_db)) -> CozeResponse:
    return coze_project_summary(db, project_id)
