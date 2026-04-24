from fastapi import HTTPException
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.character import Character
from app.models.enums import AssetTaskStatus, ProjectStatus
from app.models.publish_record import PublishRecord
from app.schemas.asset_task import BulkAssetTaskCreateRequest
from app.schemas.character import CharacterCreate
from app.schemas.coze import (
    ConfirmCharacterReferenceRequest,
    CozeCreateAssetTasksRequest,
    CozeGenerateScriptRequest,
    CozePublishRecordRequest,
    CozeProjectInitRequest,
    CozeResponse,
    CozeStoryboardRequest,
)
from app.schemas.episode import EpisodeCreate
from app.schemas.publish_record import PublishRecordCreate
from app.schemas.project import ProjectCreate
from app.schemas.scene import SceneCreate
from app.schemas.shot import ShotCreate
from app.services.asset_task_service import (
    bulk_create_project_asset_tasks,
    bulk_run_project_asset_tasks,
    list_project_asset_tasks,
)
from app.services.character_service import confirm_character_reference, create_character
from app.services.episode_service import create_episode, get_or_create_default_episode, update_episode_script_card
from app.services.publish_service import create_publish_record
from app.services.project_service import create_project, get_project_or_404, get_project_summary
from app.services.scene_service import create_scene
from app.services.shot_service import create_shot


def _build_project_description(project_card) -> str:
    parts = [
        f"genre={project_card.genre}" if project_card.genre else None,
        f"target_duration={project_card.target_duration}" if project_card.target_duration is not None else None,
        f"target_audience={project_card.target_audience}" if project_card.target_audience else None,
        f"visual_style={project_card.visual_style}" if project_card.visual_style else None,
        f"core_conflict={project_card.core_conflict}" if project_card.core_conflict else None,
        f"hook={project_card.hook}" if project_card.hook else None,
        f"ending_hook={project_card.ending_hook}" if project_card.ending_hook else None,
    ]
    return "\n".join(part for part in parts if part)


def _build_character_profile(character) -> str:
    lines = [
        f"role={character.role}",
        f"age_vibe={character.age_vibe}" if character.age_vibe else None,
        f"personality={character.personality}" if character.personality else None,
        f"must_keep={', '.join(character.must_keep)}" if character.must_keep else None,
        f"avoid={', '.join(character.avoid)}" if character.avoid else None,
    ]
    return "\n".join(line for line in lines if line)


def _build_character_visual_notes(character) -> str:
    lines = [
        f"appearance={character.appearance}" if character.appearance else None,
        f"hair={character.hair}" if character.hair else None,
        f"outfit={character.outfit}" if character.outfit else None,
    ]
    return "\n".join(line for line in lines if line) or "unspecified"


def _build_script_card(script_card_json) -> str:
    lines = [
        f"opening_hook={script_card_json.opening_hook}" if script_card_json.opening_hook else None,
        f"conflict={script_card_json.conflict}" if script_card_json.conflict else None,
        f"escalation={script_card_json.escalation}" if script_card_json.escalation else None,
        f"turning_point={script_card_json.turning_point}" if script_card_json.turning_point else None,
        f"ending_hook={script_card_json.ending_hook}" if script_card_json.ending_hook else None,
    ]
    return "\n".join(line for line in lines if line)


def coze_project_init(db: Session, payload: CozeProjectInitRequest) -> CozeResponse:
    project = create_project(
        db,
        ProjectCreate(
            name=payload.project_card_json.project_title,
            description=_build_project_description(payload.project_card_json),
            target_platforms=[payload.project_card_json.platform] if payload.project_card_json.platform else [],
            tags=[tag for tag in [payload.project_card_json.genre, payload.project_card_json.target_audience, payload.project_card_json.visual_style] if tag],
            status=payload.project_card_json.status,
        ),
    )

    character_ids: list[int] = []
    for item in payload.characters_json.characters:
        character = create_character(
            db,
            CharacterCreate(
                project_id=project.id,
                name=item.name,
                role_type=item.role,
                profile=_build_character_profile(item),
                visual_notes=_build_character_visual_notes(item),
                voice_style=item.speaking_style or "unspecified",
                main_reference_confirmed=item.main_reference_confirmed,
            ),
        )
        character_ids.append(character.id)

    return CozeResponse(
        message="Project and characters initialized",
        data={"project_id": project.id, "character_ids": character_ids},
        next_action="confirm_character_reference",
    )


def coze_confirm_character_reference(db: Session, character_id: int, payload: ConfirmCharacterReferenceRequest) -> CozeResponse:
    character = confirm_character_reference(db, character_id, payload.main_reference_url)
    return CozeResponse(
        message="Character reference confirmed",
        data={
            "character_id": character.id,
            "main_reference_confirmed": character.main_reference_confirmed,
            "main_reference_url": character.main_reference_url,
        },
        next_action="create_storyboard",
    )


def coze_storyboard(db: Session, project_id: int, payload: CozeStoryboardRequest) -> CozeResponse:
    get_project_or_404(db, project_id)

    episode = get_or_create_default_episode(db, project_id)
    episode = update_episode_script_card(db, episode.id, _build_script_card(payload.script_card_json))

    scenes_by_location: dict[str, int] = {}
    shots_count = 0
    for index, shot_item in enumerate(payload.storyboard_json.shots, start=1):
        location_key = (shot_item.location or "default_scene").strip() or "default_scene"
        scene_id = scenes_by_location.get(location_key)
        if scene_id is None:
            scene = create_scene(
                db,
                SceneCreate(
                    episode_id=episode.id,
                    scene_number=len(scenes_by_location) + 1,
                    title=location_key,
                    description=f"Scene for {location_key}",
                ),
            )
            scene_id = scene.id
            scenes_by_location[location_key] = scene_id

        shot_number = index
        if shot_item.shot_id.upper().startswith("SH"):
            try:
                shot_number = int(shot_item.shot_id[2:])
            except ValueError:
                shot_number = index

        create_shot(
            db,
            ShotCreate(
                scene_id=scene_id,
                shot_number=shot_number,
                framing=shot_item.camera or "medium",
                core_action=shot_item.core_action,
                dialogue=shot_item.dialogue,
                image_prompt=shot_item.image_prompt,
                video_prompt=shot_item.video_prompt,
                voice_prompt=shot_item.voice_prompt,
                bgm_prompt=shot_item.bgm_prompt,
                status=shot_item.status,
            ),
        )
        shots_count += 1

    return CozeResponse(
        message="Storyboard imported",
        data={"project_id": project_id, "episode_id": episode.id, "shots_count": shots_count},
        next_action="create_asset_tasks",
    )


def coze_generate_script(db: Session, project_id: int, payload: CozeGenerateScriptRequest) -> CozeResponse:
    get_project_or_404(db, project_id)
    episode = get_or_create_default_episode(db, project_id)
    episode = update_episode_script_card(db, episode.id, _build_script_card(payload.script_card_json))
    return CozeResponse(
        message="Script card saved",
        data={"project_id": project_id, "episode_id": episode.id},
        next_action="create_storyboard",
    )


def _map_video_shot_ids_to_numeric(video_shot_ids: list[str]) -> list[int]:
    mapped: list[int] = []
    for shot_id in video_shot_ids:
        normalized = shot_id.strip().upper()
        if normalized.startswith("SH"):
            try:
                mapped.append(int(normalized[2:]))
                continue
            except ValueError:
                pass
        raise HTTPException(status_code=400, detail=f"Invalid shot id: {shot_id}")
    return mapped


def coze_create_asset_tasks(db: Session, project_id: int, payload: CozeCreateAssetTasksRequest) -> CozeResponse:
    before_count = len(list_project_asset_tasks(db, project_id))
    created = bulk_create_project_asset_tasks(
        db,
        project_id,
        BulkAssetTaskCreateRequest(video_shot_ids=_map_video_shot_ids_to_numeric(payload.video_shot_ids)),
    )
    after_count = len(list_project_asset_tasks(db, project_id))
    return CozeResponse(
        message="Asset tasks created",
        data={
            "created_count": len(created),
            "skipped_count": max(after_count - before_count - len(created), 0),
            "asset_tasks_count": after_count,
        },
        next_action="run_asset_tasks",
    )


def coze_run_asset_tasks(db: Session, project_id: int) -> CozeResponse:
    result = bulk_run_project_asset_tasks(db, project_id)
    return CozeResponse(
        message="Asset tasks executed",
        data={
            "succeeded_count": result.succeeded_count,
            "failed_count": result.failed_count,
            "needs_human_revision_count": result.needs_human_revision_count,
        },
        next_action="check_summary",
    )


def coze_publish_record(db: Session, project_id: int, payload: CozePublishRecordRequest) -> CozeResponse:
    project = get_project_or_404(db, project_id)
    record = create_publish_record(
        db,
        PublishRecordCreate(
            project_id=project_id,
            platform=payload.platform,
            title=payload.title,
            published_at=datetime.fromisoformat(payload.published_at.replace("Z", "+00:00")),
            link=payload.url,
        ),
    )
    project.status = ProjectStatus.PUBLISHED
    db.commit()
    db.refresh(project)
    return CozeResponse(
        message="Publish record created",
        data={"publish_record_id": record.id, "project_id": project_id},
        next_action="completed",
    )


def _coze_next_action(db: Session, project_id: int, summary) -> str:
    publish_records_count = db.query(PublishRecord).filter(PublishRecord.project_id == project_id).count()
    if publish_records_count > 0 and summary.project_status == ProjectStatus.PUBLISHED:
        return "completed"

    confirmed_character_count = (
        db.query(Character)
        .filter(Character.project_id == project_id, Character.main_reference_confirmed.is_(True))
        .count()
    )
    if confirmed_character_count == 0:
        return "confirm_character_reference"

    if summary.shots_count == 0:
        return "create_storyboard"

    if summary.asset_tasks_count == 0:
        return "create_asset_tasks"

    if summary.failed_tasks_count > 0 or summary.needs_human_revision_count > 0:
        return "review_failed_tasks"

    if summary.succeeded_tasks_count == 0 or summary.succeeded_tasks_count < summary.asset_tasks_count:
        queued_or_retry = len(
            [
                task
                for task in list_project_asset_tasks(db, project_id)
                if task.status in {AssetTaskStatus.QUEUED, AssetTaskStatus.NEEDS_RETRY}
            ]
        )
        if queued_or_retry > 0:
            return "run_asset_tasks"

    if summary.asset_tasks_count > 0 and summary.succeeded_tasks_count == summary.asset_tasks_count:
        return "ready_to_publish"

    return summary.next_action


def coze_project_summary(db: Session, project_id: int) -> CozeResponse:
    summary = get_project_summary(db, project_id)
    return CozeResponse(
        message="Project summary fetched",
        data=summary.model_dump(),
        next_action=_coze_next_action(db, project_id, summary),
    )
