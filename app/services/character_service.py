from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.character import Character
from app.models.character_appearance import CharacterAppearance
from app.models.project import Project
from app.schemas.character import CharacterAppearanceResponse
from app.schemas.character import CharacterAppearanceSelectResponse
from app.schemas.character import CharacterAppearanceUpsertRequest
from app.schemas.character import CharacterCreate
from app.schemas.character import ProjectCharacterAppearanceSummary
from app.schemas.character import ProjectCharacterAppearanceSummaryItem
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


def get_project_character_or_404(db: Session, project_id: int, character_id: int) -> Character:
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    character = db.get(Character, character_id)
    if character is None or character.project_id != project_id:
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


def serialize_character_appearance(appearance: CharacterAppearance) -> CharacterAppearanceResponse:
    return CharacterAppearanceResponse(
        id=appearance.id,
        created_at=appearance.created_at,
        updated_at=appearance.updated_at,
        project_id=appearance.project_id,
        character_id=appearance.character_id,
        appearance_key=appearance.appearance_key,
        appearance_type=appearance.appearance_type,
        title=appearance.title,
        description=appearance.description,
        image_url=appearance.image_url,
        is_selected=appearance.is_selected,
        order_index=appearance.order_index,
        change_reason=appearance.change_reason,
        must_keep=appearance.must_keep_json if isinstance(appearance.must_keep_json, list) else [],
        avoid=appearance.avoid_json if isinstance(appearance.avoid_json, list) else [],
        metadata_json=appearance.metadata_json if isinstance(appearance.metadata_json, dict) else {},
    )


def upsert_character_appearance(
    db: Session,
    project_id: int,
    character_id: int,
    payload: CharacterAppearanceUpsertRequest,
) -> CharacterAppearanceResponse:
    get_project_character_or_404(db, project_id, character_id)
    appearance = (
        db.query(CharacterAppearance)
        .filter(
            CharacterAppearance.project_id == project_id,
            CharacterAppearance.character_id == character_id,
            CharacterAppearance.appearance_key == payload.appearance_key,
        )
        .first()
    )
    if appearance is None:
        appearance = CharacterAppearance(
            project_id=project_id,
            character_id=character_id,
            appearance_key=payload.appearance_key,
            appearance_type=payload.appearance_type,
        )
        db.add(appearance)

    appearance.appearance_type = payload.appearance_type
    appearance.title = payload.title
    appearance.description = payload.description
    appearance.image_url = payload.image_url
    appearance.is_selected = payload.is_selected
    appearance.order_index = payload.order_index
    appearance.change_reason = payload.change_reason
    appearance.must_keep_json = payload.must_keep
    appearance.avoid_json = payload.avoid
    appearance.metadata_json = payload.metadata_json
    db.commit()
    db.refresh(appearance)

    if payload.is_selected:
        select_character_appearance(db, project_id, character_id, payload.appearance_key)
        db.refresh(appearance)
    return serialize_character_appearance(appearance)


def list_character_appearances(db: Session, project_id: int, character_id: int) -> list[CharacterAppearanceResponse]:
    get_project_character_or_404(db, project_id, character_id)
    appearances = (
        db.query(CharacterAppearance)
        .filter(
            CharacterAppearance.project_id == project_id,
            CharacterAppearance.character_id == character_id,
        )
        .order_by(CharacterAppearance.order_index.asc(), CharacterAppearance.id.asc())
        .all()
    )
    return [serialize_character_appearance(item) for item in appearances]


def select_character_appearance(
    db: Session,
    project_id: int,
    character_id: int,
    appearance_key: str,
) -> CharacterAppearanceSelectResponse:
    character = get_project_character_or_404(db, project_id, character_id)
    selected = (
        db.query(CharacterAppearance)
        .filter(
            CharacterAppearance.project_id == project_id,
            CharacterAppearance.character_id == character_id,
            CharacterAppearance.appearance_key == appearance_key,
        )
        .first()
    )
    if selected is None:
        raise HTTPException(status_code=404, detail="Character appearance not found")

    appearances = (
        db.query(CharacterAppearance)
        .filter(
            CharacterAppearance.project_id == project_id,
            CharacterAppearance.character_id == character_id,
        )
        .all()
    )
    for appearance in appearances:
        appearance.is_selected = appearance.id == selected.id

    character.main_reference_url = selected.image_url
    project = db.get(Project, project_id)
    synced_visual_asset = _sync_visual_asset_library_character(project, character, selected, len(appearances)) if project else None

    db.commit()
    db.refresh(selected)
    db.refresh(character)
    return CharacterAppearanceSelectResponse(
        project_id=project_id,
        character_id=character_id,
        selected_appearance=serialize_character_appearance(selected),
        character_main_reference_url=character.main_reference_url,
        synced_visual_asset=synced_visual_asset,
    )


def get_project_character_appearance_summary(db: Session, project_id: int) -> ProjectCharacterAppearanceSummary:
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    characters = (
        db.query(Character)
        .filter(Character.project_id == project_id)
        .order_by(Character.id.asc())
        .all()
    )
    items: list[ProjectCharacterAppearanceSummaryItem] = []
    project_next_action = "ready_for_reference_guided_generation"

    for character in characters:
        appearances = (
            db.query(CharacterAppearance)
            .filter(CharacterAppearance.project_id == project_id, CharacterAppearance.character_id == character.id)
            .order_by(CharacterAppearance.order_index.asc(), CharacterAppearance.id.asc())
            .all()
        )
        selected = next((item for item in appearances if item.is_selected), None)
        appearance_types = {str(item.appearance_type or "").strip().lower() for item in appearances}
        has_fullbody = any(value.startswith("fullbody") or value in {"full_body", "full-body"} for value in appearance_types)
        warnings: list[str] = []
        if not appearances:
            warnings.append("missing_character_appearances")
            next_action = "create_character_appearances"
        elif selected is None:
            warnings.append("missing_selected_appearance")
            next_action = "select_main_reference"
        else:
            next_action = "ready_for_reference_guided_generation"
        if "design_sheet" not in appearance_types:
            warnings.append("missing_design_sheet")
        if "main_reference" not in appearance_types:
            warnings.append("missing_main_reference")

        if project_next_action == "ready_for_reference_guided_generation" and next_action != "ready_for_reference_guided_generation":
            project_next_action = next_action

        items.append(
            ProjectCharacterAppearanceSummaryItem(
                character_id=character.id,
                name=character.name,
                role_type=character.role_type,
                main_reference_url=character.main_reference_url,
                selected_appearance_key=selected.appearance_key if selected else None,
                selected_appearance_url=selected.image_url if selected else None,
                appearances_count=len(appearances),
                has_design_sheet="design_sheet" in appearance_types,
                has_main_reference="main_reference" in appearance_types,
                has_face_detail="face_detail" in appearance_types,
                has_fullbody=has_fullbody,
                warnings=warnings,
                next_action=next_action,
            )
        )

    if not characters:
        project_next_action = "create_characters"

    return ProjectCharacterAppearanceSummary(
        project_id=project_id,
        characters_count=len(characters),
        items=items,
        next_action=project_next_action,
    )


def _sync_visual_asset_library_character(
    project: Project,
    character: Character,
    selected: CharacterAppearance,
    appearances_count: int,
) -> dict | None:
    library = project.visual_asset_library_json if isinstance(project.visual_asset_library_json, dict) else {}
    characters = library.get("characters") if isinstance(library.get("characters"), list) else []
    updated_characters: list[dict] = []
    synced: dict | None = None

    for item in characters:
        if not isinstance(item, dict):
            updated_characters.append(item)
            continue
        updated = dict(item)
        if synced is None and _visual_asset_character_matches(updated, character):
            updated["main_reference_url"] = selected.image_url
            updated["selected_appearance_key"] = selected.appearance_key
            updated["selected_appearance_url"] = selected.image_url
            updated["appearances_count"] = appearances_count
            synced = updated
        updated_characters.append(updated)

    if synced is not None:
        project.visual_asset_library_json = {**library, "characters": updated_characters}
    return synced


def _visual_asset_character_matches(item: dict, character: Character) -> bool:
    item_name = str(item.get("name") or "").strip()
    if item_name and item_name == character.name:
        return True
    asset_key = str(item.get("asset_key") or "").strip().lower()
    return bool(asset_key and asset_key == _slugify_character_asset_key(character.name))


def _slugify_character_asset_key(value: str) -> str:
    normalized = re_sub_non_word(value).strip("_").lower()
    return normalized or str(value or "").strip().lower()


def re_sub_non_word(value: str) -> str:
    import re

    return re.sub(r"[^0-9A-Za-z_\u4e00-\u9fff]+", "_", str(value or ""))
