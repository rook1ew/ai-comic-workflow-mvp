from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.character import CharacterAppearanceResponse
from app.schemas.character import CharacterAppearanceSelectResponse
from app.schemas.character import CharacterAppearanceUpsertRequest
from app.schemas.character import CharacterCreate
from app.schemas.character import CharacterResponse
from app.services.character_service import create_character
from app.services.character_service import list_character_appearances
from app.services.character_service import select_character_appearance
from app.services.character_service import upsert_character_appearance

router = APIRouter()


@router.post("/characters", response_model=CharacterResponse, status_code=201)
def create_character_route(payload: CharacterCreate, db: Session = Depends(get_db)) -> CharacterResponse:
    return create_character(db, payload)


@router.post(
    "/projects/{project_id}/characters/{character_id}/appearances",
    response_model=CharacterAppearanceResponse,
    status_code=201,
)
def upsert_character_appearance_route(
    project_id: int,
    character_id: int,
    payload: CharacterAppearanceUpsertRequest,
    db: Session = Depends(get_db),
) -> CharacterAppearanceResponse:
    return upsert_character_appearance(db, project_id, character_id, payload)


@router.get(
    "/projects/{project_id}/characters/{character_id}/appearances",
    response_model=list[CharacterAppearanceResponse],
)
def list_character_appearances_route(
    project_id: int,
    character_id: int,
    db: Session = Depends(get_db),
) -> list[CharacterAppearanceResponse]:
    return list_character_appearances(db, project_id, character_id)


@router.post(
    "/projects/{project_id}/characters/{character_id}/appearances/{appearance_key}/select",
    response_model=CharacterAppearanceSelectResponse,
)
def select_character_appearance_route(
    project_id: int,
    character_id: int,
    appearance_key: str,
    db: Session = Depends(get_db),
) -> CharacterAppearanceSelectResponse:
    return select_character_appearance(db, project_id, character_id, appearance_key)
