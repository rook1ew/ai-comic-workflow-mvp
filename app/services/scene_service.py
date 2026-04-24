from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.episode import Episode
from app.models.scene import Scene
from app.schemas.scene import SceneCreate
from app.services.repository import create_and_refresh


def create_scene(db: Session, payload: SceneCreate) -> Scene:
    if db.get(Episode, payload.episode_id) is None:
        raise HTTPException(status_code=404, detail="Episode not found")
    scene = Scene(**payload.model_dump())
    return create_and_refresh(db, scene)
