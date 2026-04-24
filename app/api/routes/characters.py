from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.character import CharacterCreate, CharacterResponse
from app.services.character_service import create_character

router = APIRouter()


@router.post("/characters", response_model=CharacterResponse, status_code=201)
def create_character_route(payload: CharacterCreate, db: Session = Depends(get_db)) -> CharacterResponse:
    return create_character(db, payload)
