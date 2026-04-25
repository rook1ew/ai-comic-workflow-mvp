from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
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
from app.schemas.project import ProviderReadinessResponse
from app.services.prompt_enhancer import build_image_enhanced_prompt
from app.services.repository import create_and_refresh

_IMAGE2_REAL_CALLS_THIS_RUN = 0


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


def reset_image2_real_call_counter() -> None:
    global _IMAGE2_REAL_CALLS_THIS_RUN
    _IMAGE2_REAL_CALLS_THIS_RUN = 0


def _build_image2_preflight_result(task: AssetTask, request_payload: dict, blocked_reason: str, *, dry_run: bool) -> dict:
    settings = get_settings()
    preflight_checks = {
        "provider_name_is_image2_real": task.provider_name == "image2_real",
        "mode_is_image2_real": settings.image_provider_mode == "image2_real",
        "real_provider_enabled": settings.enable_real_image_provider,
        "has_api_key": bool(settings.image2_api_key.strip()),
        "has_base_url": bool(settings.image2_base_url.strip()),
        "dry_run_disabled": not settings.image2_dry_run,
        "task_allowed": task.id in settings.image2_allow_task_ids,
        "within_call_limit": _IMAGE2_REAL_CALLS_THIS_RUN < settings.image2_max_real_calls_per_run,
        "modality_is_image": task.modality == AssetModality.IMAGE,
        "has_enhanced_prompt": bool(str(request_payload.get("enhanced_prompt") or "").strip()),
    }
    provider_audit = {
        "provider_name": "image2_real",
        "modality": "image",
        "request_payload": request_payload,
        "response_payload": None,
        "error_body": None,
        "job_id": None,
        "usage": None,
        "latency_ms": None,
        "real_call": False,
        "dry_run": dry_run,
        "blocked_reason": blocked_reason,
        "preflight_passed": False,
        "preflight_checks": preflight_checks,
    }
    return {
        "provider_audit": provider_audit,
        "provider_name": "image2_real",
        "request_payload": request_payload,
        "response_payload": None,
        "error_body": None,
        "job_id": None,
        "usage": None,
        "latency_ms": None,
        "real_call": False,
        "dry_run": dry_run,
        "blocked_reason": blocked_reason,
        "preflight_passed": False,
        "preflight_checks": preflight_checks,
        "task_id": task.id,
    }


def _run_image2_real_preflight(task: AssetTask, request_payload: dict) -> tuple[bool, dict, str | None]:
    global _IMAGE2_REAL_CALLS_THIS_RUN

    if task.modality != AssetModality.IMAGE or task.provider_name != "image2_real":
        return True, {}, None

    settings = get_settings()
    blocked_reason: str | None = None

    if settings.image_provider_mode != "image2_real":
        blocked_reason = "IMAGE_PROVIDER_MODE must be image2_real before using provider_name=image2_real."
    elif not settings.enable_real_image_provider:
        blocked_reason = "Real Image2 provider is disabled. Set ENABLE_REAL_IMAGE_PROVIDER=true before using provider_name=image2_real."
    elif not settings.image2_api_key.strip():
        blocked_reason = "IMAGE2_API_KEY is required before using provider_name=image2_real."
    elif not settings.image2_base_url.strip():
        blocked_reason = "IMAGE2_BASE_URL is required before using provider_name=image2_real."
    elif task.id not in settings.image2_allow_task_ids:
        blocked_reason = "Asset task id is not allowed by IMAGE2_ALLOW_TASK_IDS."
    elif _IMAGE2_REAL_CALLS_THIS_RUN >= settings.image2_max_real_calls_per_run:
        blocked_reason = "IMAGE2_MAX_REAL_CALLS_PER_RUN limit reached."
    elif task.modality != AssetModality.IMAGE:
        blocked_reason = "image2_real only supports image tasks."
    elif not str(request_payload.get("enhanced_prompt") or "").strip():
        blocked_reason = "enhanced_prompt is required before using provider_name=image2_real."
    elif settings.image2_dry_run:
        blocked_reason = "IMAGE2_DRY_RUN is true."
    else:
        _IMAGE2_REAL_CALLS_THIS_RUN += 1
        blocked_reason = "Real Image2 HTTP calls remain blocked in v0.3-C. No external request was sent."

    return False, _build_image2_preflight_result(
        task,
        request_payload,
        blocked_reason,
        dry_run=settings.image2_dry_run,
    ), blocked_reason


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

    ensure_transition(task.status, AssetTaskStatus.RUNNING, ASSET_TASK_TRANSITIONS, "asset task")
    task.status = AssetTaskStatus.RUNNING
    task.error_message = None
    db.commit()

    try:
        provider = get_provider(task.modality, task.provider_name)
        payload = _build_provider_payload(db, task)
        preflight_allowed, preflight_result, blocked_reason = _run_image2_real_preflight(task, payload)
        if not preflight_allowed:
            raise ProviderExecutionError(blocked_reason or "image2_real preflight blocked the request.")
        request = ProviderRequest(
            shot_id=task.shot_id,
            modality=task.modality.value,
            payload=payload,
        )
        result = provider.generate(request)
    except ProviderExecutionError as exc:
        task.retry_count += 1
        task.error_message = str(exc)
        if task.provider_name == "image2_real":
            task.output_payload = preflight_result if 'preflight_result' in locals() and preflight_result else {
                "provider_name": "image2_real",
                "real_call": False,
                "dry_run": get_settings().image2_dry_run,
                "blocked_reason": str(exc),
            }
        else:
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
        provider_name=getattr(result, "provider_name", None) or result.metadata.get("provider_name") or task.provider_name,
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
    elif task.output_payload and isinstance(task.output_payload, dict):
        provider_audit_payload = task.output_payload.get("provider_audit") or {}
        input_payload = dict(
            provider_audit_payload.get("request_payload")
            or task.output_payload.get("request_payload")
            or input_payload
        )

    provider_audit = {}
    if asset is not None:
        provider_audit = dict(asset.metadata_json.get("provider_audit") or {})
    elif task.output_payload and isinstance(task.output_payload, dict):
        provider_audit = dict(task.output_payload.get("provider_audit") or {})

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
        provider_audit=provider_audit,
        blocked_reason=provider_audit.get("blocked_reason") or (task.output_payload or {}).get("blocked_reason") if task.output_payload else None,
        dry_run=provider_audit.get("dry_run"),
        real_call=provider_audit.get("real_call"),
        preflight_passed=provider_audit.get("preflight_passed"),
        preflight_checks=provider_audit.get("preflight_checks") or {},
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
    dry_run_tasks_count = sum(1 for item in items if item.dry_run is True)
    blocked_real_provider_tasks_count = sum(1 for item in items if item.blocked_reason)
    real_call_tasks_count = sum(1 for item in items if item.real_call is True)

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
            dry_run_tasks_count=dry_run_tasks_count,
            blocked_real_provider_tasks_count=blocked_real_provider_tasks_count,
            real_call_tasks_count=real_call_tasks_count,
        ),
    )


def get_project_provider_readiness(db: Session, project_id: int) -> ProviderReadinessResponse:
    debug_summary = get_project_provider_debug_summary(db, project_id)
    stats = debug_summary.summary

    blocking_issues: list[str] = []
    warnings: list[str] = []

    if stats.image_tasks_count == 0:
        blocking_issues.append("Project has no image tasks.")
    if stats.failed_count > 0:
        blocking_issues.append("Project has failed asset tasks.")
    if stats.needs_human_revision_count > 0:
        blocking_issues.append("Project has asset tasks that need human revision.")
    if stats.missing_enhanced_prompt_count > 0:
        blocking_issues.append("Some image tasks are missing enhanced_prompt.")
    if stats.missing_image_url_for_video_count > 0:
        blocking_issues.append("Some video tasks are missing image_url.")

    video_duration_missing_count = sum(
        1
        for item in debug_summary.items
        if item.modality == AssetModality.VIDEO and not (item.input_payload or {}).get("duration")
    )
    if video_duration_missing_count > 0:
        blocking_issues.append("Some video tasks are missing duration.")

    if stats.video_tasks_count == 0:
        warnings.append("Project has no video tasks; video provider readiness is based on the current absence of video work.")

    ready_for_image_provider = (
        stats.image_tasks_count > 0
        and stats.failed_count == 0
        and stats.needs_human_revision_count == 0
        and stats.missing_enhanced_prompt_count == 0
    )
    ready_for_video_provider = (
        stats.video_tasks_count == 0
        or (
            stats.failed_count == 0
            and stats.needs_human_revision_count == 0
            and stats.missing_image_url_for_video_count == 0
            and video_duration_missing_count == 0
        )
    )

    return ProviderReadinessResponse(
        project_id=project_id,
        ready_for_image_provider=ready_for_image_provider,
        ready_for_video_provider=ready_for_video_provider,
        blocking_issues=blocking_issues,
        warnings=warnings,
        summary=debug_summary.model_dump(),
    )
