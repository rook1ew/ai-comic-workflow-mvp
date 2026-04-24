from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.status_machine import ASSET_TASK_TRANSITIONS, ensure_transition
from app.models.asset import Asset
from app.models.asset_task import AssetTask
from app.models.character import Character
from app.models.enums import AssetModality, AssetTaskStatus
from app.models.episode import Episode
from app.models.scene import Scene
from app.models.shot import Shot
from app.providers.base import ProviderExecutionError
from app.providers.factory import get_provider
from app.providers.schemas import ProviderRequest
from app.schemas.asset_task import AssetTaskCreate, BulkAssetTaskCreateRequest, BulkAssetTaskRunResponse, BulkAssetTaskRunResult
from app.services.repository import create_and_refresh


def _ensure_confirmed_character_reference(db: Session, project_id: int) -> None:
    confirmed_count = (
        db.query(Character)
        .filter(Character.project_id == project_id, Character.main_reference_confirmed.is_(True))
        .count()
    )
    if confirmed_count == 0:
        raise HTTPException(status_code=400, detail="At least one confirmed character reference is required before creating asset tasks")


def _get_project_shots(db: Session, project_id: int) -> list[Shot]:
    return (
        db.query(Shot)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id)
        .order_by(Shot.id.asc())
        .all()
    )


def create_asset_task(db: Session, payload: AssetTaskCreate) -> AssetTask:
    shot = db.get(Shot, payload.shot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    project = shot.scene.episode.project
    if project is None:
        raise HTTPException(status_code=400, detail="Shot project context is invalid")

    _ensure_confirmed_character_reference(db, project.id)

    task = AssetTask(**payload.model_dump())
    if task.retry_count > task.max_retries:
        task.status = AssetTaskStatus.NEEDS_HUMAN_REVISION
    return create_and_refresh(db, task)


def get_asset_task_or_404(db: Session, asset_task_id: int) -> AssetTask:
    task = db.get(AssetTask, asset_task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Asset task not found")
    return task


def list_project_asset_tasks(db: Session, project_id: int) -> list[AssetTask]:
    return (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id)
        .order_by(AssetTask.id.asc())
        .all()
    )


def list_project_assets(db: Session, project_id: int) -> list[Asset]:
    return (
        db.query(Asset)
        .join(Shot, Asset.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id)
        .order_by(Asset.id.asc())
        .all()
    )


def bulk_create_project_asset_tasks(db: Session, project_id: int, payload: BulkAssetTaskCreateRequest) -> list[AssetTask]:
    _ensure_confirmed_character_reference(db, project_id)
    shots = _get_project_shots(db, project_id)
    if not shots:
        raise HTTPException(status_code=400, detail="Project has no shots to create asset tasks for")

    created_tasks: list[AssetTask] = []
    base_modalities = [AssetModality.IMAGE, AssetModality.VOICE, AssetModality.BGM]

    for shot in shots:
        modalities = list(base_modalities)
        if shot.id in payload.video_shot_ids:
            modalities.append(AssetModality.VIDEO)
        for modality in modalities:
            existing = db.query(AssetTask).filter(AssetTask.shot_id == shot.id, AssetTask.modality == modality).first()
            if existing is not None:
                continue
            task = AssetTask(
                shot_id=shot.id,
                modality=modality,
                provider_name=payload.provider_name,
                status=AssetTaskStatus.QUEUED,
                input_payload={},
            )
            db.add(task)
            created_tasks.append(task)

    db.commit()
    for task in created_tasks:
        db.refresh(task)
    return created_tasks


def run_asset_task(db: Session, asset_task_id: int) -> AssetTask:
    task = get_asset_task_or_404(db, asset_task_id)

    if task.status == AssetTaskStatus.NEEDS_HUMAN_REVISION:
        return task

    provider = get_provider(task.modality, task.provider_name)
    ensure_transition(task.status, AssetTaskStatus.RUNNING, ASSET_TASK_TRANSITIONS, "asset task")
    task.status = AssetTaskStatus.RUNNING
    task.error_message = None
    db.commit()

    request = ProviderRequest(
        shot_id=task.shot_id,
        modality=task.modality.value,
        payload=task.input_payload or {},
    )

    try:
        result = provider.generate(request)
    except ProviderExecutionError as exc:
        task.retry_count += 1
        task.error_message = str(exc)
        task.output_payload = None
        if task.retry_count > task.max_retries:
            task.status = AssetTaskStatus.NEEDS_HUMAN_REVISION
        else:
            task.status = AssetTaskStatus.FAILED
        db.commit()
        db.refresh(task)
        return task

    asset = Asset(
        shot_id=task.shot_id,
        asset_task_id=task.id,
        modality=task.modality,
        provider_name=result.provider_name,
        file_url=result.url,
        metadata_json=result.metadata,
    )
    db.add(asset)
    task.output_payload = result.model_dump()
    task.status = AssetTaskStatus.SUCCEEDED
    db.commit()
    db.refresh(task)
    return task


def bulk_run_project_asset_tasks(db: Session, project_id: int) -> BulkAssetTaskRunResponse:
    tasks = (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.status.in_([AssetTaskStatus.QUEUED, AssetTaskStatus.NEEDS_RETRY]))
        .order_by(AssetTask.id.asc())
        .all()
    )

    results: list[BulkAssetTaskRunResult] = []
    succeeded_count = 0
    failed_count = 0
    needs_human_revision_count = 0

    for task in tasks:
        executed = run_asset_task(db, task.id)
        results.append(
            BulkAssetTaskRunResult(
                task_id=executed.id,
                shot_id=executed.shot_id,
                modality=executed.modality,
                status=executed.status,
                error_message=executed.error_message,
            )
        )
        if executed.status == AssetTaskStatus.SUCCEEDED:
            succeeded_count += 1
        elif executed.status == AssetTaskStatus.NEEDS_HUMAN_REVISION:
            needs_human_revision_count += 1
        else:
            failed_count += 1

    return BulkAssetTaskRunResponse(
        project_id=project_id,
        succeeded_count=succeeded_count,
        failed_count=failed_count,
        needs_human_revision_count=needs_human_revision_count,
        results=results,
    )
