from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.asset_task import AssetTask
from app.models.enums import AssetTaskStatus
from app.models.episode import Episode
from app.models.project import Project
from app.models.publish_record import PublishRecord
from app.models.scene import Scene
from app.models.shot import Shot
from app.schemas.project import ProjectCreate
from app.schemas.project import ProjectSummary
from app.services.repository import create_and_refresh


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
