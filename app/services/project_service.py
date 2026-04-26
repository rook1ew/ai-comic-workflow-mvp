from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.asset_task import AssetTask
from app.models.character import Character
from app.models.enums import AssetTaskStatus
from app.models.enums import AssetModality
from app.models.episode import Episode
from app.models.project import Project
from app.models.publish_record import PublishRecord
from app.models.scene import Scene
from app.models.shot import Shot
from app.schemas.project import ProjectCreate
from app.schemas.project import ProjectImagePromptExport
from app.schemas.project import ProjectImagePromptItem
from app.schemas.project import ProjectVideoPromptExport
from app.schemas.project import ProjectVideoPromptItem
from app.schemas.project import ProjectManualProductionSummary
from app.schemas.project import ManualProductionBlockingSummary
from app.schemas.project import ProjectManualImageProgress
from app.schemas.project import ProjectManualImageProgressItem
from app.schemas.project import ProjectManualFinalChecklist
from app.schemas.project import ProjectManualVideoProgress
from app.schemas.project import ProjectManualVideoProgressItem
from app.schemas.project import ProjectPublishReadiness
from app.schemas.project import ProjectSummary
from app.schemas.project import ManualFinalChecklistChecks
from app.schemas.project import PublishReadinessChecks
from app.schemas.project import PublishReadinessSummary
from app.schemas.project import ProjectVideoReadiness
from app.schemas.project import ProjectVideoReadinessItem
from app.services.prompt_enhancer import build_image_enhanced_prompt
from app.services.repository import create_and_refresh

MANUAL_IMAGE_NEGATIVE_PROMPT = (
    "不要模仿具体IP、明星、影视角色或已知动漫角色；不要水印；不要乱码文字；"
    "不要多余肢体；不要低清晰度。"
)

MANUAL_VIDEO_NEGATIVE_PROMPT = (
    "Do not imitate specific IP, celebrities, film characters, or known anime characters; "
    "no scene change; no watermark; no text overlay; no distorted hands; no extra limbs; no face morphing."
)


def create_project(db: Session, payload: ProjectCreate) -> Project:
    project = Project(**payload.model_dump())
    return create_and_refresh(db, project)


def list_projects(db: Session) -> list[Project]:
    return db.query(Project).order_by(Project.id.desc()).all()


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def get_project_summary(db: Session, project_id: int) -> ProjectSummary:
    project = get_project_or_404(db, project_id)

    episodes_count = db.query(func.count(Episode.id)).filter(Episode.project_id == project_id).scalar() or 0
    scenes_count = (
        db.query(func.count(Scene.id))
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id)
        .scalar()
        or 0
    )
    shots_count = (
        db.query(func.count(Shot.id))
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id)
        .scalar()
        or 0
    )
    asset_tasks_count = (
        db.query(func.count(AssetTask.id))
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id)
        .scalar()
        or 0
    )
    assets_count = (
        db.query(func.count(Asset.id))
        .join(Shot, Asset.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id)
        .scalar()
        or 0
    )
    succeeded_tasks_count = (
        db.query(func.count(AssetTask.id))
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.status == AssetTaskStatus.SUCCEEDED)
        .scalar()
        or 0
    )
    failed_tasks_count = (
        db.query(func.count(AssetTask.id))
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.status == AssetTaskStatus.FAILED)
        .scalar()
        or 0
    )
    needs_human_revision_count = (
        db.query(func.count(AssetTask.id))
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.status == AssetTaskStatus.NEEDS_HUMAN_REVISION)
        .scalar()
        or 0
    )
    publish_records_count = db.query(func.count(PublishRecord.id)).filter(PublishRecord.project_id == project_id).scalar() or 0

    if shots_count == 0:
        next_action = "create_storyboard"
    elif asset_tasks_count == 0:
        next_action = "create_asset_tasks"
    elif succeeded_tasks_count < asset_tasks_count:
        next_action = "run_asset_tasks"
    elif publish_records_count == 0:
        next_action = "create_publish_record"
    else:
        next_action = "review_project"

    return ProjectSummary(
        project_id=project.id,
        project_status=project.status,
        episodes_count=episodes_count,
        scenes_count=scenes_count,
        shots_count=shots_count,
        asset_tasks_count=asset_tasks_count,
        assets_count=assets_count,
        succeeded_tasks_count=succeeded_tasks_count,
        failed_tasks_count=failed_tasks_count,
        needs_human_revision_count=needs_human_revision_count,
        publish_records_count=publish_records_count,
        next_action=next_action,
    )


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


def _build_copy_ready_prompt(enhanced_prompt: str, negative_prompt: str) -> str:
    return "\n".join(
        [
            enhanced_prompt.strip(),
            "Format: vertical anime comic style, 9:16 composition, high detail, consistent character design.",
            f"Negative prompt: {negative_prompt}",
        ]
    ).strip()


def _build_copy_ready_video_prompt(
    *,
    image_asset_url: str | None,
    duration: int | float | None,
    base_video_prompt: str,
    core_action: str,
    character: str | None,
    location: str | None,
    emotion: str | None,
    camera: str | None,
    dialogue: str | None,
    negative_prompt: str,
) -> str:
    parts = [
        "Use uploaded image as first frame." if image_asset_url else "Image asset is missing; upload image first before video generation.",
        f"Image asset URL: {image_asset_url}" if image_asset_url else None,
        f"Duration: {duration} seconds." if duration is not None else "Duration is missing and must be confirmed before generation.",
        "Format: 9:16 vertical anime-comic video.",
        f"Base video prompt: {base_video_prompt}",
        f"Core action: {core_action}",
        f"Character: {character}" if character else None,
        f"Location: {location}" if location else None,
        f"Emotion: {emotion}" if emotion else None,
        f"Camera: {camera}" if camera else None,
        f"Dialogue cue: {dialogue}" if dialogue else None,
        "Keep character identity, face, hairstyle, and outfit consistent.",
        f"Negative prompt: {negative_prompt}",
    ]
    return "\n".join(part for part in parts if part).strip()


def export_project_image_prompts(db: Session, project_id: int) -> ProjectImagePromptExport:
    project = get_project_or_404(db, project_id)
    style = _extract_project_style(project)
    character_reference_url = _get_first_confirmed_character_reference(db, project_id)

    tasks = (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.modality == AssetModality.IMAGE)
        .order_by(AssetTask.id.asc())
        .all()
    )

    items: list[ProjectImagePromptItem] = []
    for task in tasks:
        shot = task.shot
        shot_metadata = shot.metadata_json or {}
        asset = (
            db.query(Asset)
            .filter(Asset.asset_task_id == task.id, Asset.modality == AssetModality.IMAGE)
            .order_by(Asset.id.asc())
            .first()
        )

        asset_input_payload = {}
        if asset is not None:
            asset_input_payload = (asset.metadata_json or {}).get("input_payload") or {}

        base_prompt = (
            asset_input_payload.get("base_prompt")
            or task.input_payload.get("base_prompt")
            or shot.image_prompt
        )
        storyboard_context = (
            asset_input_payload.get("storyboard_context")
            or {
                "source_shot_id": shot_metadata.get("source_shot_id"),
                "duration_sec": shot_metadata.get("duration_sec"),
                "character": shot_metadata.get("character"),
                "location": shot_metadata.get("location"),
                "emotion": shot_metadata.get("emotion"),
                "camera": shot_metadata.get("camera"),
                "dialogue": shot_metadata.get("dialogue"),
            }
        )
        enhanced_prompt = (
            asset_input_payload.get("enhanced_prompt")
            or task.input_payload.get("enhanced_prompt")
            or build_image_enhanced_prompt(
                base_prompt=shot.image_prompt,
                visual_style=style,
                character_reference_url=character_reference_url,
                storyboard_context=storyboard_context,
            )
        )
        copy_ready_prompt = _build_copy_ready_prompt(enhanced_prompt, MANUAL_IMAGE_NEGATIVE_PROMPT)

        items.append(
            ProjectImagePromptItem(
                asset_task_id=task.id,
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                emotion=shot_metadata.get("emotion"),
                camera=shot_metadata.get("camera"),
                dialogue=shot_metadata.get("dialogue"),
                base_prompt=base_prompt,
                enhanced_prompt=enhanced_prompt,
                negative_prompt=MANUAL_IMAGE_NEGATIVE_PROMPT,
                copy_ready_prompt=copy_ready_prompt,
            )
        )

    return ProjectImagePromptExport(
        project_id=project_id,
        items_count=len(items),
        items=items,
    )


def export_project_video_prompts(db: Session, project_id: int) -> ProjectVideoPromptExport:
    get_project_or_404(db, project_id)

    tasks = (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.modality == AssetModality.VIDEO)
        .order_by(AssetTask.id.asc())
        .all()
    )

    items: list[ProjectVideoPromptItem] = []
    for task in tasks:
        shot = task.shot
        shot_metadata = shot.metadata_json or {}
        image_asset = (
            db.query(Asset)
            .filter(Asset.shot_id == shot.id, Asset.modality == AssetModality.IMAGE)
            .order_by(Asset.id.asc())
            .first()
        )
        image_asset_url = image_asset.file_url if image_asset is not None else None
        duration = _extract_video_duration(task, shot)
        blocking_issues: list[str] = []
        if not image_asset_url:
            blocking_issues.append("missing_image_asset")

        base_video_prompt = shot.video_prompt
        copy_ready_video_prompt = _build_copy_ready_video_prompt(
            image_asset_url=image_asset_url,
            duration=duration,
            base_video_prompt=base_video_prompt,
            core_action=shot.core_action,
            character=shot_metadata.get("character"),
            location=shot_metadata.get("location"),
            emotion=shot_metadata.get("emotion"),
            camera=shot_metadata.get("camera"),
            dialogue=shot_metadata.get("dialogue"),
            negative_prompt=MANUAL_VIDEO_NEGATIVE_PROMPT,
        )

        items.append(
            ProjectVideoPromptItem(
                asset_task_id=task.id,
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                image_asset_url=image_asset_url,
                duration=duration,
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                emotion=shot_metadata.get("emotion"),
                camera=shot_metadata.get("camera"),
                dialogue=shot_metadata.get("dialogue"),
                base_video_prompt=base_video_prompt,
                copy_ready_video_prompt=copy_ready_video_prompt,
                negative_prompt=MANUAL_VIDEO_NEGATIVE_PROMPT,
                ready_for_video_prompt=bool(image_asset_url and duration is not None),
                blocking_issues=blocking_issues,
            )
        )

    return ProjectVideoPromptExport(
        project_id=project_id,
        items_count=len(items),
        items=items,
    )


def get_project_manual_image_progress(db: Session, project_id: int) -> ProjectManualImageProgress:
    get_project_or_404(db, project_id)

    tasks = (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.modality == AssetModality.IMAGE)
        .order_by(AssetTask.id.asc())
        .all()
    )

    items: list[ProjectManualImageProgressItem] = []
    completed_image_tasks_count = 0
    manual_uploaded_count = 0

    for task in tasks:
        shot = task.shot
        shot_metadata = shot.metadata_json or {}
        asset = (
            db.query(Asset)
            .filter(Asset.asset_task_id == task.id, Asset.modality == AssetModality.IMAGE)
            .order_by(Asset.id.asc())
            .first()
        )
        has_asset = asset is not None and bool(asset.file_url)
        manual_upload = bool((asset.metadata_json or {}).get("manual_upload")) if asset is not None else False
        if has_asset:
            completed_image_tasks_count += 1
        if manual_upload:
            manual_uploaded_count += 1

        items.append(
            ProjectManualImageProgressItem(
                asset_task_id=task.id,
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                status=task.status.value,
                has_asset=has_asset,
                asset_url=asset.file_url if asset is not None else None,
                manual_upload=manual_upload,
                needs_manual_image=not has_asset,
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                emotion=shot_metadata.get("emotion"),
            )
        )

    image_tasks_count = len(items)
    missing_image_tasks_count = image_tasks_count - completed_image_tasks_count
    next_action = "manual_images_completed" if image_tasks_count > 0 and missing_image_tasks_count == 0 else "continue_manual_image_generation"

    return ProjectManualImageProgress(
        project_id=project_id,
        image_tasks_count=image_tasks_count,
        completed_image_tasks_count=completed_image_tasks_count,
        missing_image_tasks_count=missing_image_tasks_count,
        manual_uploaded_count=manual_uploaded_count,
        items=items,
        next_action=next_action,
    )


def _extract_video_duration(task: AssetTask, shot: Shot) -> int | float | None:
    shot_metadata = shot.metadata_json or {}
    return (
        shot_metadata.get("duration_sec")
        or (task.input_payload or {}).get("duration")
        or (task.input_payload or {}).get("duration_sec")
    )


def get_project_video_readiness(db: Session, project_id: int) -> ProjectVideoReadiness:
    get_project_or_404(db, project_id)

    tasks = (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.modality == AssetModality.VIDEO)
        .order_by(AssetTask.id.asc())
        .all()
    )

    items: list[ProjectVideoReadinessItem] = []
    ready_video_tasks_count = 0
    blocked_video_tasks_count = 0

    for task in tasks:
        shot = task.shot
        shot_metadata = shot.metadata_json or {}
        image_asset = (
            db.query(Asset)
            .filter(Asset.shot_id == shot.id, Asset.modality == AssetModality.IMAGE)
            .order_by(Asset.id.asc())
            .first()
        )
        has_image_asset = image_asset is not None and bool(image_asset.file_url)
        duration = _extract_video_duration(task, shot)
        has_duration = duration is not None

        blocking_issues: list[str] = []
        if not has_image_asset:
            blocking_issues.append("missing_image_asset")
        if not has_duration:
            blocking_issues.append("missing_duration")

        ready_for_video = has_image_asset and has_duration
        if ready_for_video:
            ready_video_tasks_count += 1
        else:
            blocked_video_tasks_count += 1

        items.append(
            ProjectVideoReadinessItem(
                asset_task_id=task.id,
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                status=task.status.value,
                has_image_asset=has_image_asset,
                image_asset_url=image_asset.file_url if image_asset is not None else None,
                has_duration=has_duration,
                duration=duration,
                ready_for_video=ready_for_video,
                blocking_issues=blocking_issues,
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                emotion=shot_metadata.get("emotion"),
                video_prompt=shot.video_prompt,
            )
        )

    if blocked_video_tasks_count == 0:
        next_action = "ready_for_video_generation"
    elif any("missing_image_asset" in item.blocking_issues for item in items):
        next_action = "continue_manual_image_generation"
    else:
        next_action = "fix_video_inputs"

    return ProjectVideoReadiness(
        project_id=project_id,
        video_tasks_count=len(items),
        ready_video_tasks_count=ready_video_tasks_count,
        blocked_video_tasks_count=blocked_video_tasks_count,
        items=items,
        next_action=next_action,
    )


def get_project_manual_video_progress(db: Session, project_id: int) -> ProjectManualVideoProgress:
    get_project_or_404(db, project_id)

    tasks = (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.modality == AssetModality.VIDEO)
        .order_by(AssetTask.id.asc())
        .all()
    )

    items: list[ProjectManualVideoProgressItem] = []
    completed_video_tasks_count = 0
    manual_uploaded_count = 0

    for task in tasks:
        shot = task.shot
        shot_metadata = shot.metadata_json or {}
        asset = (
            db.query(Asset)
            .filter(Asset.asset_task_id == task.id, Asset.modality == AssetModality.VIDEO)
            .order_by(Asset.id.asc())
            .first()
        )
        has_asset = asset is not None and bool(asset.file_url)
        manual_upload = bool((asset.metadata_json or {}).get("manual_upload")) if asset is not None else False
        duration = _extract_video_duration(task, shot)
        if has_asset:
            completed_video_tasks_count += 1
        if manual_upload:
            manual_uploaded_count += 1

        items.append(
            ProjectManualVideoProgressItem(
                asset_task_id=task.id,
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                status=task.status.value,
                has_asset=has_asset,
                asset_url=asset.file_url if asset is not None else None,
                manual_upload=manual_upload,
                needs_manual_video=not has_asset,
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                emotion=shot_metadata.get("emotion"),
                duration=duration,
            )
        )

    video_tasks_count = len(items)
    missing_video_tasks_count = video_tasks_count - completed_video_tasks_count
    next_action = "manual_videos_completed" if video_tasks_count > 0 and missing_video_tasks_count == 0 else "continue_manual_video_generation"

    return ProjectManualVideoProgress(
        project_id=project_id,
        video_tasks_count=video_tasks_count,
        completed_video_tasks_count=completed_video_tasks_count,
        missing_video_tasks_count=missing_video_tasks_count,
        manual_uploaded_count=manual_uploaded_count,
        items=items,
        next_action=next_action,
    )


def get_project_manual_production_summary(db: Session, project_id: int) -> ProjectManualProductionSummary:
    get_project_or_404(db, project_id)

    image = get_project_manual_image_progress(db, project_id)
    video_readiness = get_project_video_readiness(db, project_id)
    video = get_project_manual_video_progress(db, project_id)

    blocking_summary = ManualProductionBlockingSummary(
        missing_image_tasks_count=image.missing_image_tasks_count,
        blocked_video_tasks_count=video_readiness.blocked_video_tasks_count,
        missing_video_tasks_count=video.missing_video_tasks_count,
    )

    recommended_steps: list[str] = []
    if image.missing_image_tasks_count > 0:
        stage = "manual_image_generation"
        next_action = "continue_manual_image_generation"
        recommended_steps = [
            "Continue generating missing images from image-prompts.",
            "Upload generated images with manual-asset.",
            "Run video-readiness again before manual video generation.",
        ]
    elif video_readiness.blocked_video_tasks_count > 0:
        stage = "video_input_fixing"
        next_action = "fix_video_inputs"
        recommended_steps = [
            "Review blocked video tasks in video-readiness.",
            "Fix missing image assets or duration before generating video.",
            "Re-run video-readiness until all video tasks are ready.",
        ]
    elif video.missing_video_tasks_count > 0:
        stage = "manual_video_generation"
        next_action = "continue_manual_video_generation"
        recommended_steps = [
            "Generate missing videos with Seedance or another manual video tool.",
            "Upload generated videos with manual-video-asset.",
            "Check manual-video-progress until every video task has an asset.",
        ]
    else:
        stage = "manual_production_completed"
        next_action = "ready_for_publish_or_composition"
        recommended_steps = [
            "Review the completed manual production assets.",
            "Proceed to composition, publishing, or final QA.",
        ]

    return ProjectManualProductionSummary(
        project_id=project_id,
        stage=stage,
        next_action=next_action,
        image=image,
        video_readiness=video_readiness,
        video=video,
        blocking_summary=blocking_summary,
        recommended_steps=recommended_steps,
    )


def get_project_publish_readiness(db: Session, project_id: int) -> ProjectPublishReadiness:
    get_project_or_404(db, project_id)

    manual_production = get_project_manual_production_summary(db, project_id)
    project_summary = get_project_summary(db, project_id)

    checks = PublishReadinessChecks(
        manual_production_completed=manual_production.stage == "manual_production_completed",
        all_image_tasks_have_assets=manual_production.image.missing_image_tasks_count == 0,
        all_video_tasks_have_assets=manual_production.video.missing_video_tasks_count == 0,
        has_failed_tasks=project_summary.failed_tasks_count > 0,
        has_needs_human_revision_tasks=project_summary.needs_human_revision_count > 0,
        has_publish_record=project_summary.publish_records_count > 0,
    )

    summary = PublishReadinessSummary(
        image_tasks_count=manual_production.image.image_tasks_count,
        completed_image_tasks_count=manual_production.image.completed_image_tasks_count,
        video_tasks_count=manual_production.video.video_tasks_count,
        completed_video_tasks_count=manual_production.video.completed_video_tasks_count,
        publish_records_count=project_summary.publish_records_count,
    )

    blocking_issues: list[str] = []
    warnings: list[str] = []

    if not checks.all_image_tasks_have_assets:
        stage = "manual_image_generation"
        next_action = "continue_manual_image_generation"
        ready_for_publish = False
        blocking_issues.append("missing_image_assets")
    elif not checks.all_video_tasks_have_assets:
        stage = "manual_video_generation"
        next_action = "continue_manual_video_generation"
        ready_for_publish = False
        blocking_issues.append("missing_video_assets")
    elif checks.has_failed_tasks:
        stage = "review_failed_tasks"
        next_action = "review_failed_tasks"
        ready_for_publish = False
        blocking_issues.append("failed_tasks_exist")
    elif checks.has_needs_human_revision_tasks:
        stage = "review_human_revision_tasks"
        next_action = "review_human_revision_tasks"
        ready_for_publish = False
        blocking_issues.append("needs_human_revision_tasks_exist")
    elif checks.has_publish_record:
        stage = "published"
        next_action = "completed"
        ready_for_publish = True
    else:
        stage = "ready_for_publish"
        next_action = "create_publish_record"
        ready_for_publish = True
        warnings.append("No publish record exists yet.")

    return ProjectPublishReadiness(
        project_id=project_id,
        ready_for_publish=ready_for_publish,
        stage=stage,
        next_action=next_action,
        checks=checks,
        blocking_issues=blocking_issues,
        warnings=warnings,
        summary=summary,
    )


def get_project_manual_final_checklist(db: Session, project_id: int) -> ProjectManualFinalChecklist:
    project = get_project_or_404(db, project_id)
    manual_production = get_project_manual_production_summary(db, project_id)
    publish_readiness = get_project_publish_readiness(db, project_id)

    checks = ManualFinalChecklistChecks(
        images_completed=manual_production.image.missing_image_tasks_count == 0,
        videos_completed=manual_production.video.missing_video_tasks_count == 0,
        video_inputs_ready=manual_production.video_readiness.blocked_video_tasks_count == 0,
        no_failed_tasks="failed_tasks_exist" not in publish_readiness.blocking_issues,
        no_human_revision_tasks="needs_human_revision_tasks_exist" not in publish_readiness.blocking_issues,
        publish_record_exists=publish_readiness.checks.has_publish_record,
    )

    blocking_issues: list[str] = []
    warnings = list(publish_readiness.warnings)
    recommended_steps: list[str] = []

    if manual_production.stage != "manual_production_completed":
        ready_for_delivery = False
        next_action = manual_production.next_action
        blocking_issues.append("manual_production_not_completed")
        blocking_issues.extend(publish_readiness.blocking_issues)
        recommended_steps = list(manual_production.recommended_steps)
    elif not publish_readiness.ready_for_publish:
        ready_for_delivery = False
        next_action = publish_readiness.next_action
        blocking_issues.extend(publish_readiness.blocking_issues)
        if publish_readiness.stage == "review_failed_tasks":
            recommended_steps = [
                "Review failed tasks before moving into delivery.",
                "Re-run or manually fix the failed tasks.",
            ]
        elif publish_readiness.stage == "review_human_revision_tasks":
            recommended_steps = [
                "Review tasks marked as needs_human_revision.",
                "Fix the blocking tasks before publish or composition.",
            ]
        else:
            recommended_steps = list(manual_production.recommended_steps)
    elif publish_readiness.checks.has_publish_record:
        ready_for_delivery = True
        next_action = "completed"
        recommended_steps = [
            "Publish record already exists.",
            "Proceed to final delivery, composition, or archive workflow.",
        ]
    else:
        ready_for_delivery = True
        next_action = "create_publish_record"
        recommended_steps = [
            "Create publish record or proceed to final composition/export.",
        ]

    # De-duplicate while preserving order.
    seen: set[str] = set()
    deduped_blocking_issues: list[str] = []
    for item in blocking_issues:
        if item and item not in seen:
            seen.add(item)
            deduped_blocking_issues.append(item)

    return ProjectManualFinalChecklist(
        project_id=project_id,
        ready_for_delivery=ready_for_delivery,
        production_stage=manual_production.stage,
        publish_stage=publish_readiness.stage,
        project_status=project.status,
        has_publish_record=publish_readiness.checks.has_publish_record,
        next_action=next_action,
        checks=checks,
        blocking_issues=deduped_blocking_issues,
        warnings=warnings,
        summary=publish_readiness.summary,
        recommended_steps=recommended_steps,
    )
