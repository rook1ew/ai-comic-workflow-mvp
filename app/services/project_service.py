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
from app.schemas.project import ProjectManualImageProgress
from app.schemas.project import ProjectManualImageProgressItem
from app.schemas.project import ProjectSummary
from app.schemas.project import ProjectVideoReadiness
from app.schemas.project import ProjectVideoReadinessItem
from app.services.prompt_enhancer import build_image_enhanced_prompt
from app.services.repository import create_and_refresh

MANUAL_IMAGE_NEGATIVE_PROMPT = (
    "不要模仿具体IP、明星、影视角色或已知动漫角色；不要水印；不要乱码文字；"
    "不要多余肢体；不要低清晰度。"
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
