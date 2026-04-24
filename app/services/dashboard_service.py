from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.asset_task import AssetTask
from app.models.character import Character
from app.models.episode import Episode
from app.models.project import Project
from app.models.publish_record import PublishRecord
from app.models.review import Review
from app.models.scene import Scene
from app.models.shot import Shot
from app.schemas.dashboard import DashboardSummary


def get_dashboard_summary(db: Session) -> DashboardSummary:
    return DashboardSummary(
        total_projects=db.query(func.count(Project.id)).scalar() or 0,
        total_episodes=db.query(func.count(Episode.id)).scalar() or 0,
        total_characters=db.query(func.count(Character.id)).scalar() or 0,
        total_scenes=db.query(func.count(Scene.id)).scalar() or 0,
        total_shots=db.query(func.count(Shot.id)).scalar() or 0,
        total_asset_tasks=db.query(func.count(AssetTask.id)).scalar() or 0,
        total_assets=db.query(func.count(Asset.id)).scalar() or 0,
        total_reviews=db.query(func.count(Review.id)).scalar() or 0,
        total_publish_records=db.query(func.count(PublishRecord.id)).scalar() or 0,
    )
