from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.status_machine import ASSET_TASK_TRANSITIONS, ensure_transition
from app.models.asset import Asset
from app.models.asset_task import AssetTask
from app.models.character import Character
from app.models.enums import AssetModality, AssetTaskStatus
from app.models.episode import Episode
from app.models.project import Project
from app.models.scene import Scene
from app.models.shot import Shot
from app.providers.base import ProviderExecutionError
from app.providers.factory import get_provider
from app.providers.schemas import ImageProviderInput, ProviderRequest, VideoProviderInput
from app.schemas.asset_task import (
    AssetTaskCreate,
    BulkAssetTaskCreateRequest,
    BulkAssetTaskRunResponse,
    BulkAssetTaskRunResult,
    ProjectProviderDebugSummary,
    ProjectProviderDebugSummaryStats,
    ProviderDebugSnapshot,
)
from app.services.prompt_enhancer import build_image_enhanced_prompt
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


def _get_project_for_shot(shot: Shot) -> Project:
    project = shot.scene.episode.project
    if project is None:
        raise HTTPException(status_code=400, detail="Shot project context is invalid")
    return project


def _get_first_confirmed_character_reference(db: Session, project_id: int) -> str | None:
    character = (
        db.query(Character)
        .filter(Character.project_id == project_id, Character.main_reference_confirmed.is_(True))
        .order_by(Character.id.asc())
        .first()
    )
    if character is None:
        return None
    return character.main_reference_url


def _extract_project_style(project: Project) -> str | None:
    if project.description:
        for line in project.description.splitlines():
            if line.startswith("visual_style="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value
    for tag in project.tags:
        if "style" in tag.lower() or "comic" in tag.lower() or "realism" in tag.lower():
            return tag
    return None


def _get_existing_image_asset_url(db: Session, shot_id: int) -> str | None:
    asset = (
        db.query(Asset)
        .filter(Asset.shot_id == shot_id, Asset.modality == AssetModality.IMAGE)
        .order_by(Asset.id.asc())
        .first()
    )
    if asset is None:
        return None
    return asset.file_url


def _build_storyboard_context(shot: Shot) -> dict:
    shot_metadata = shot.metadata_json or {}
    return {
        "source_shot_id": shot_metadata.get("source_shot_id"),
        "duration_sec": shot_metadata.get("duration_sec"),
        "character": shot_metadata.get("character"),
        "location": shot_metadata.get("location"),
        "emotion": shot_metadata.get("emotion"),
        "camera": shot_metadata.get("camera"),
        "dialogue": shot_metadata.get("dialogue"),
    } if shot_metadata else {}


def _build_provider_payload(db: Session, task: AssetTask) -> dict:
    shot = task.shot
    project = _get_project_for_shot(shot)
    base_payload = dict(task.input_payload or {})

    if task.modality == AssetModality.IMAGE:
        storyboard_context = _build_storyboard_context(shot)
        character_reference_url = _get_first_confirmed_character_reference(db, project.id)
        style = _extract_project_style(project)
        image_input = ImageProviderInput(
            prompt=shot.image_prompt,
            character_reference_url=character_reference_url,
            shot_id=shot.id,
            style=style,
            storyboard_context=storyboard_context,
        )
        return {
            **image_input.model_dump(),
            "base_prompt": shot.image_prompt,
            "enhanced_prompt": build_image_enhanced_prompt(
                base_prompt=shot.image_prompt,
                visual_style=style,
                character_reference_url=character_reference_url,
                storyboard_context=storyboard_context,
            ),
            **base_payload,
        }

    if task.modality == AssetModality.VIDEO:
        image_url = _get_existing_image_asset_url(db, shot.id)
        if image_url is None:
            raise ProviderExecutionError("Image asset is required before video generation")
        shot_metadata = shot.metadata_json or {}
        duration = shot_metadata.get("duration_sec") or base_payload.get("duration") or base_payload.get("duration_sec") or 3
        video_input = VideoProviderInput(
            image_url=image_url,
            prompt=shot.video_prompt,
            duration=duration,
            aspect_ratio="9:16",
            resolution="720p",
        )
        return {**video_input.model_dump(), **base_payload}

    return base_payload


def create_asset_task(db: Session, payload: AssetTaskCreate) -> AssetTask:
    shot = db.get(Shot, payload.shot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    project = _get_project_for_shot(shot)

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

    try:
        payload = _build_provider_payload(db, task)
        request = ProviderRequest(
            shot_id=task.shot_id,
            modality=task.modality.value,
            payload=payload,
        )
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


def get_provider_debug_snapshot(db: Session, asset_task_id: int) -> ProviderDebugSnapshot:
    task = get_asset_task_or_404(db, asset_task_id)
    asset = None
    if task.assets:
        asset = sorted(task.assets, key=lambda item: item.id)[-1]

    input_payload = dict(task.input_payload or {})
    if asset is not None:
        input_payload = dict(asset.metadata_json.get("input_payload") or input_payload)

    return ProviderDebugSnapshot(
        asset_task_id=task.id,
        shot_id=(task.shot.metadata_json or {}).get("source_shot_id"),
        internal_shot_id=task.shot_id,
        modality=task.modality,
        provider_name=task.provider_name,
        status=task.status,
        input_payload=input_payload,
        enhanced_prompt=input_payload.get("enhanced_prompt"),
        storyboard_context=input_payload.get("storyboard_context") or {},
        asset_url=asset.file_url if asset is not None else None,
        asset_id=asset.id if asset is not None else None,
        error_message=task.error_message,
    )


def get_project_provider_debug_summary(db: Session, project_id: int) -> ProjectProviderDebugSummary:
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = list_project_asset_tasks(db, project_id)
    items = [get_provider_debug_snapshot(db, task.id) for task in tasks]

    image_tasks_count = sum(1 for item in items if item.modality == AssetModality.IMAGE)
    video_tasks_count = sum(1 for item in items if item.modality == AssetModality.VIDEO)
    succeeded_count = sum(1 for item in items if item.status == AssetTaskStatus.SUCCEEDED)
    failed_count = sum(1 for item in items if item.status == AssetTaskStatus.FAILED)
    needs_human_revision_count = sum(1 for item in items if item.status == AssetTaskStatus.NEEDS_HUMAN_REVISION)
    missing_enhanced_prompt_count = sum(
        1 for item in items if item.modality == AssetModality.IMAGE and not item.enhanced_prompt
    )
    missing_image_url_for_video_count = sum(
        1
        for item in items
        if item.modality == AssetModality.VIDEO and not (item.input_payload or {}).get("image_url")
    )

    return ProjectProviderDebugSummary(
        project_id=project_id,
        asset_tasks_count=len(items),
        items=items,
        summary=ProjectProviderDebugSummaryStats(
            image_tasks_count=image_tasks_count,
            video_tasks_count=video_tasks_count,
            succeeded_count=succeeded_count,
            failed_count=failed_count,
            needs_human_revision_count=needs_human_revision_count,
            missing_enhanced_prompt_count=missing_enhanced_prompt_count,
            missing_image_url_for_video_count=missing_image_url_for_video_count,
        ),
    )
