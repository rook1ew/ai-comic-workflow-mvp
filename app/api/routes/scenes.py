from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.scene import SceneCreate, SceneResponse
from app.services.scene_service import create_scene

router = APIRouter()


@router.post("/scenes", response_model=SceneResponse, status_code=201)
def create_scene_route(payload: SceneCreate, db: Session = Depends(get_db)) -> SceneResponse:
    return create_scene(db, payload)
