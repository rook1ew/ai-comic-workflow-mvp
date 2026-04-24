from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.asset import AssetResponse
from app.schemas.asset_task import AssetTaskCreate, AssetTaskResponse, BulkAssetTaskCreateRequest, BulkAssetTaskRunResponse
from app.services.asset_task_service import (
    bulk_create_project_asset_tasks,
    bulk_run_project_asset_tasks,
    create_asset_task,
    get_asset_task_or_404,
    list_project_asset_tasks,
    list_project_assets,
    run_asset_task,
)

router = APIRouter()


@router.post("/asset-tasks", response_model=AssetTaskResponse, status_code=201)
def create_asset_task_route(payload: AssetTaskCreate, db: Session = Depends(get_db)) -> AssetTaskResponse:
    return create_asset_task(db, payload)


@router.get("/asset-tasks/{asset_task_id}", response_model=AssetTaskResponse)
def get_asset_task_route(asset_task_id: int, db: Session = Depends(get_db)) -> AssetTaskResponse:
    return get_asset_task_or_404(db, asset_task_id)


@router.post("/asset-tasks/{asset_task_id}/run", response_model=AssetTaskResponse)
def run_asset_task_route(asset_task_id: int, db: Session = Depends(get_db)) -> AssetTaskResponse:
    return run_asset_task(db, asset_task_id)


@router.get("/projects/{project_id}/asset-tasks", response_model=list[AssetTaskResponse])
def get_project_asset_tasks_route(project_id: int, db: Session = Depends(get_db)) -> list[AssetTaskResponse]:
    return list_project_asset_tasks(db, project_id)


@router.get("/projects/{project_id}/assets", response_model=list[AssetResponse])
def get_project_assets_route(project_id: int, db: Session = Depends(get_db)) -> list[AssetResponse]:
    return list_project_assets(db, project_id)


@router.post("/projects/{project_id}/asset-tasks/bulk", response_model=list[AssetTaskResponse], status_code=201)
def bulk_create_project_asset_tasks_route(
    project_id: int,
    payload: BulkAssetTaskCreateRequest,
    db: Session = Depends(get_db),
) -> list[AssetTaskResponse]:
    return bulk_create_project_asset_tasks(db, project_id, payload)


@router.post("/projects/{project_id}/asset-tasks/run-bulk", response_model=BulkAssetTaskRunResponse)
def bulk_run_project_asset_tasks_route(project_id: int, db: Session = Depends(get_db)) -> BulkAssetTaskRunResponse:
    return bulk_run_project_asset_tasks(db, project_id)
