from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.character import Character
from app.models.project import Project
from app.schemas.character import CharacterCreate
from app.services.repository import create_and_refresh


def create_character(db: Session, payload: CharacterCreate) -> Character:
    if db.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    character = Character(**payload.model_dump())
    return create_and_refresh(db, character)


def get_character_or_404(db: Session, character_id: int) -> Character:
    character = db.get(Character, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


def confirm_character_reference(db: Session, character_id: int, main_reference_url: str | None) -> Character:
    character = get_character_or_404(db, character_id)
    character.main_reference_confirmed = True
    if main_reference_url is not None:
        character.main_reference_url = main_reference_url
    db.commit()
    db.refresh(character)
    return character
