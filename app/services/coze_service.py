from fastapi import HTTPException
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.character import Character
from app.models.enums import AssetTaskStatus, ProjectStatus
from app.models.episode import Episode
from app.models.publish_record import PublishRecord
from app.models.scene import Scene
from app.models.shot import Shot
from app.schemas.asset_task import BulkAssetTaskCreateRequest
from app.schemas.character import CharacterCreate
from app.schemas.coze import (
    ConfirmCharacterReferenceRequest,
    CozeCreateAssetTasksRequest,
    CozeFullDemoFlowRequest,
    CozeGenerateScriptRequest,
    CozePayloadValidationRequest,
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
from app.services.shot_service import create_shot, update_shot_metadata


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
        f"gender={character.gender}" if getattr(character, "gender", None) else None,
        f"age={character.age}" if getattr(character, "age", None) else None,
        f"social_identity={character.social_identity}" if getattr(character, "social_identity", None) else None,
        f"first_impression={character.first_impression}" if getattr(character, "first_impression", None) else None,
        f"public_mask={character.public_mask}" if getattr(character, "public_mask", None) else None,
        f"inner_truth={character.inner_truth}" if getattr(character, "inner_truth", None) else None,
        f"core_keywords={', '.join(character.core_keywords)}" if getattr(character, "core_keywords", None) else None,
        f"personality_contradiction={character.personality_contradiction}" if getattr(character, "personality_contradiction", None) else None,
        f"habits={', '.join(character.habits)}" if getattr(character, "habits", None) else None,
        f"language_style={character.language_style}" if getattr(character, "language_style", None) else None,
        f"decision_style={character.decision_style}" if getattr(character, "decision_style", None) else None,
        f"stress_reaction={character.stress_reaction}" if getattr(character, "stress_reaction", None) else None,
        f"values={', '.join(character.values)}" if getattr(character, "values", None) else None,
        f"fear={character.fear}" if getattr(character, "fear", None) else None,
        f"desire={character.desire}" if getattr(character, "desire", None) else None,
        f"trauma={character.trauma}" if getattr(character, "trauma", None) else None,
        f"secret={character.secret}" if getattr(character, "secret", None) else None,
        f"family_background={character.family_background}" if getattr(character, "family_background", None) else None,
        f"growth_environment={character.growth_environment}" if getattr(character, "growth_environment", None) else None,
        f"economic_status={character.economic_status}" if getattr(character, "economic_status", None) else None,
        f"education_background={character.education_background}" if getattr(character, "education_background", None) else None,
        f"key_events={', '.join(character.key_events)}" if getattr(character, "key_events", None) else None,
        f"current_status={character.current_status}" if getattr(character, "current_status", None) else None,
        f"core_problem={character.core_problem}" if getattr(character, "core_problem", None) else None,
        f"relationship_status={character.relationship_status}" if getattr(character, "relationship_status", None) else None,
        f"closest_person={character.closest_person}" if getattr(character, "closest_person", None) else None,
        f"enemy_person={character.enemy_person}" if getattr(character, "enemy_person", None) else None,
        f"complex_relationships={', '.join(character.complex_relationships)}" if getattr(character, "complex_relationships", None) else None,
        f"emotional_bond={character.emotional_bond}" if getattr(character, "emotional_bond", None) else None,
        f"arc_start={character.arc_start}" if getattr(character, "arc_start", None) else None,
        f"arc_end={character.arc_end}" if getattr(character, "arc_end", None) else None,
        f"arc_type={character.arc_type}" if getattr(character, "arc_type", None) else None,
        f"catalyst={character.catalyst}" if getattr(character, "catalyst", None) else None,
        f"turning_point={character.turning_point}" if getattr(character, "turning_point", None) else None,
        f"growth_theme={character.growth_theme}" if getattr(character, "growth_theme", None) else None,
        f"catchphrase={character.catchphrase}" if getattr(character, "catchphrase", None) else None,
        f"signature_action={character.signature_action}" if getattr(character, "signature_action", None) else None,
        f"must_keep={', '.join(character.must_keep)}" if character.must_keep else None,
        f"avoid={', '.join(character.avoid)}" if character.avoid else None,
    ]
    return "\n".join(line for line in lines if line)


def _build_character_visual_notes(character) -> str:
    lines = [
        f"appearance={character.appearance}" if character.appearance else None,
        f"appearance_summary={character.appearance_summary}" if getattr(character, "appearance_summary", None) else None,
        f"hair={character.hair}" if character.hair else None,
        f"outfit={character.outfit}" if character.outfit else None,
    ]
    return "\n".join(line for line in lines if line) or "unspecified"


def _build_script_card(script_card_json) -> str:
    lines = [
        f"logline={script_card_json.logline}" if getattr(script_card_json, "logline", None) else None,
        f"genre_tags={', '.join(script_card_json.genre_tags)}" if getattr(script_card_json, "genre_tags", None) else None,
        f"audience_profile={script_card_json.audience_profile}" if getattr(script_card_json, "audience_profile", None) else None,
        f"audience_emotion={script_card_json.audience_emotion}" if getattr(script_card_json, "audience_emotion", None) else None,
        f"commercial_positioning={script_card_json.commercial_positioning}" if getattr(script_card_json, "commercial_positioning", None) else None,
        f"core_hook={script_card_json.core_hook}" if getattr(script_card_json, "core_hook", None) else None,
        f"opening_hook={script_card_json.opening_hook}" if script_card_json.opening_hook else None,
        f"conflict={script_card_json.conflict}" if script_card_json.conflict else None,
        f"escalation={script_card_json.escalation}" if script_card_json.escalation else None,
        f"fear_beat={script_card_json.fear_beat}" if getattr(script_card_json, "fear_beat", None) else None,
        f"suspense_beat={script_card_json.suspense_beat}" if getattr(script_card_json, "suspense_beat", None) else None,
        f"misdirection_beat={script_card_json.misdirection_beat}" if getattr(script_card_json, "misdirection_beat", None) else None,
        f"reveal_beat={script_card_json.reveal_beat}" if getattr(script_card_json, "reveal_beat", None) else None,
        f"payoff_beat={script_card_json.payoff_beat}" if getattr(script_card_json, "payoff_beat", None) else None,
        f"cliffhanger={script_card_json.cliffhanger}" if getattr(script_card_json, "cliffhanger", None) else None,
        f"episode_theme={script_card_json.episode_theme}" if getattr(script_card_json, "episode_theme", None) else None,
        f"emotional_curve={script_card_json.emotional_curve}" if getattr(script_card_json, "emotional_curve", None) else None,
        f"conflict_chain={script_card_json.conflict_chain}" if getattr(script_card_json, "conflict_chain", None) else None,
        f"power_dynamic={script_card_json.power_dynamic}" if getattr(script_card_json, "power_dynamic", None) else None,
        f"secret_reveal_plan={script_card_json.secret_reveal_plan}" if getattr(script_card_json, "secret_reveal_plan", None) else None,
        f"next_episode_hook={script_card_json.next_episode_hook}" if getattr(script_card_json, "next_episode_hook", None) else None,
        f"turning_point={script_card_json.turning_point}" if script_card_json.turning_point else None,
        f"ending_hook={script_card_json.ending_hook}" if script_card_json.ending_hook else None,
    ]
    return "\n".join(line for line in lines if line)


def _build_shot_metadata(shot_item) -> dict:
    return {
        "source_shot_id": shot_item.shot_id,
        "duration_sec": shot_item.duration_sec,
        "character": shot_item.character,
        "location": shot_item.location,
        "emotion": shot_item.emotion,
        "camera": shot_item.camera,
        "dialogue": shot_item.dialogue,
        "shot_type": shot_item.shot_type,
        "camera_motion": shot_item.camera_motion,
        "subject_motion": shot_item.subject_motion,
        "transition": shot_item.transition,
        "subtitle_text": shot_item.subtitle_text,
        "sfx": shot_item.sfx,
        "editing_notes": shot_item.editing_notes,
        "shot_purpose": shot_item.shot_purpose,
        "conflict_beat": shot_item.conflict_beat,
        "emotion_shift": shot_item.emotion_shift,
        "visual_focus": shot_item.visual_focus,
        "image_prompt_intent": shot_item.image_prompt_intent,
        "storyboard_clarity": shot_item.storyboard_clarity,
        "pacing_note": shot_item.pacing_note,
        "audience_feeling": shot_item.audience_feeling,
        "reference_priority": shot_item.reference_priority,
        "composition": shot_item.composition,
        "lighting": shot_item.lighting,
        "subtitle_position": shot_item.subtitle_position,
        "negative_constraints": shot_item.negative_constraints,
        "character_asset_keys": shot_item.character_asset_keys,
        "scene_asset_key": shot_item.scene_asset_key,
        "prop_asset_keys": shot_item.prop_asset_keys,
    }


def _extract_visual_asset_library(payload) -> dict:
    direct = getattr(payload, "visual_asset_library_json", None)
    if isinstance(direct, dict):
        return direct
    project_card = getattr(payload, "project_card_json", None)
    nested = getattr(project_card, "visual_asset_library_json", None) if project_card is not None else None
    if isinstance(nested, dict):
        return nested
    return {}


def _core_action_looks_multi_action(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = " ".join(value.split())
    separators = [",", "，", ";", "；", " and ", "然后", "同时", "接着", "随后"]
    return any(separator in normalized for separator in separators)


def coze_validate_payload(payload: CozePayloadValidationRequest) -> CozeResponse:
    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    project_card = payload.project_card_json or {}
    characters_json = payload.characters_json
    visual_asset_library_json = payload.visual_asset_library_json
    script_card = payload.script_card_json or {}
    storyboard_json = payload.storyboard_json
    publish_record = payload.publish_record_json or {}
    visual_asset_library = visual_asset_library_json if visual_asset_library_json is not None else project_card.get("visual_asset_library_json")

    if not str(project_card.get("project_title") or "").strip():
        warnings.append("project_card_json.project_title is recommended.")
    if not str(project_card.get("visual_style") or "").strip():
        suggestions.append("project_card_json.visual_style is recommended for more consistent image prompts.")

    visual_asset_lookup: dict[str, set[str]] = {"characters": set(), "scenes": set(), "props": set()}
    if visual_asset_library is not None:
        if not isinstance(visual_asset_library, dict):
            errors.append("visual_asset_library_json must be an object.")
            visual_asset_library = {}
        for bucket in ("characters", "scenes", "props"):
            value = visual_asset_library.get(bucket)
            if value is not None and not isinstance(value, list):
                errors.append(f"visual_asset_library_json.{bucket} must be an array.")
                continue
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and str(item.get("asset_key") or "").strip():
                        visual_asset_lookup[bucket].add(str(item.get("asset_key")).strip())
    else:
        suggestions.append("visual_asset_library_json is recommended for reference-guided long-form consistency.")

    if not isinstance(characters_json, dict):
        errors.append("characters_json must be an object.")
        characters = []
    else:
        characters = characters_json.get("characters") or []
    if not isinstance(characters, list):
        errors.append("characters_json.characters must be an array.")
        characters = []
    if len(characters) == 0:
        warnings.append("characters_json.characters is empty; richer character setup is recommended.")
    for index, character in enumerate(characters, start=1):
        if not isinstance(character, dict):
            warnings.append(f"characters_json.characters[{index - 1}] should be an object.")
            continue
        if not str(character.get("name") or "").strip():
            warnings.append(f"characters_json.characters[{index - 1}].name is recommended.")
        if not str(character.get("role") or "").strip():
            warnings.append(f"characters_json.characters[{index - 1}].role is recommended.")
        if not str(character.get("appearance") or "").strip():
            warnings.append(f"characters_json.characters[{index - 1}].appearance is recommended.")
        if not str(character.get("main_reference_url") or "").strip():
            suggestions.append(f"characters_json.characters[{index - 1}].main_reference_url is recommended for reference consistency.")
        rich_fields = [
            "public_mask",
            "inner_truth",
            "fear",
            "desire",
            "secret",
            "arc_start",
            "arc_end",
        ]
        if not any(str(character.get(field) or "").strip() for field in rich_fields):
            suggestions.append(
                f"characters_json.characters[{index - 1}] would benefit from richer profile fields like public_mask, inner_truth, fear, desire, or secret."
            )

    story_bible_fields = [
        "logline",
        "core_hook",
        "fear_beat",
        "suspense_beat",
        "misdirection_beat",
        "reveal_beat",
        "payoff_beat",
        "cliffhanger",
        "secret_reveal_plan",
        "next_episode_hook",
    ]
    if not any(str(script_card.get(field) or "").strip() for field in story_bible_fields):
        suggestions.append("script_card_json would benefit from story bible fields such as core_hook, fear_beat, suspense_beat, reveal_beat, and cliffhanger.")

    if not isinstance(storyboard_json, dict):
        errors.append("storyboard_json must be an object.")
        shots = []
    else:
        shots = storyboard_json.get("shots") or []
    if not isinstance(shots, list) or len(shots) == 0:
        errors.append("storyboard_json.shots must contain at least one shot.")
        shots = []

    shot_ids: set[str] = set()
    for index, shot in enumerate(shots, start=1):
        if not isinstance(shot, dict):
            errors.append(f"storyboard_json.shots[{index - 1}] must be an object.")
            continue
        if not str((shot or {}).get("shot_id") or "").strip():
            errors.append(f"storyboard_json.shots[{index - 1}].shot_id is required.")
        if "core_action" in (shot or {}) and not isinstance((shot or {}).get("core_action"), str):
            errors.append(f"storyboard_json.shots[{index - 1}].core_action must be a string.")
        if not str((shot or {}).get("image_prompt") or "").strip():
            errors.append(f"storyboard_json.shots[{index - 1}].image_prompt is required.")
        shot_id = str((shot or {}).get("shot_id") or "").strip()
        if shot_id:
            shot_ids.add(shot_id)
        if not str((shot or {}).get("core_action") or "").strip():
            warnings.append(f"storyboard_json.shots[{index - 1}].core_action is recommended.")
        elif _core_action_looks_multi_action((shot or {}).get("core_action")):
            warnings.append(f"storyboard_json.shots[{index - 1}].core_action_may_contain_multiple_actions")
            suggestions.append(
                f"storyboard_json.shots[{index - 1}]: keep core_action focused on one primary action and move secondary details to editing_notes, visual_focus, or pacing_note."
            )
        if (shot or {}).get("duration_sec") in (None, ""):
            warnings.append(f"storyboard_json.shots[{index - 1}].duration_sec is recommended.")
        if not str((shot or {}).get("video_prompt") or "").strip():
            warnings.append(f"storyboard_json.shots[{index - 1}].video_prompt is recommended.")
        if not str((shot or {}).get("voice_prompt") or "").strip():
            suggestions.append(f"storyboard_json.shots[{index - 1}].voice_prompt is recommended.")
        if not str((shot or {}).get("bgm_prompt") or "").strip():
            suggestions.append(f"storyboard_json.shots[{index - 1}].bgm_prompt is recommended.")
        character_asset_keys = (shot or {}).get("character_asset_keys")
        if character_asset_keys is not None and not isinstance(character_asset_keys, list):
            errors.append(f"storyboard_json.shots[{index - 1}].character_asset_keys must be an array.")
        if isinstance(character_asset_keys, list):
            for asset_key in character_asset_keys:
                if str(asset_key) not in visual_asset_lookup["characters"]:
                    warnings.append(
                        f"storyboard_json.shots[{index - 1}].character_asset_keys references unknown asset_key: {asset_key}."
                    )
        elif visual_asset_lookup["characters"]:
            suggestions.append(f"storyboard_json.shots[{index - 1}].character_asset_keys is recommended when character reference packs exist.")
        scene_asset_key = (shot or {}).get("scene_asset_key")
        if scene_asset_key is not None and not isinstance(scene_asset_key, str):
            errors.append(f"storyboard_json.shots[{index - 1}].scene_asset_key must be a string.")
        if isinstance(scene_asset_key, str) and scene_asset_key and scene_asset_key not in visual_asset_lookup["scenes"]:
            warnings.append(
                f"storyboard_json.shots[{index - 1}].scene_asset_key references unknown asset_key: {scene_asset_key}."
            )
        elif visual_asset_lookup["scenes"]:
            suggestions.append(f"storyboard_json.shots[{index - 1}].scene_asset_key is recommended when scene reference packs exist.")
        prop_asset_keys = (shot or {}).get("prop_asset_keys")
        if prop_asset_keys is not None and not isinstance(prop_asset_keys, list):
            errors.append(f"storyboard_json.shots[{index - 1}].prop_asset_keys must be an array.")
        if isinstance(prop_asset_keys, list):
            for asset_key in prop_asset_keys:
                if str(asset_key) not in visual_asset_lookup["props"]:
                    warnings.append(
                        f"storyboard_json.shots[{index - 1}].prop_asset_keys references unknown asset_key: {asset_key}."
                    )
        elif visual_asset_lookup["props"]:
            suggestions.append(f"storyboard_json.shots[{index - 1}].prop_asset_keys is recommended when prop reference packs exist.")

        editing_fields = ["shot_type", "camera_motion", "subject_motion", "transition", "subtitle_text", "sfx", "editing_notes"]
        if not any(str((shot or {}).get(field) or "").strip() for field in editing_fields):
            suggestions.append(
                f"storyboard_json.shots[{index - 1}] would benefit from editing fields such as shot_type, camera_motion, subject_motion, transition, subtitle_text, sfx, or editing_notes."
            )

        creative_fields = [
            "shot_purpose",
            "conflict_beat",
            "emotion_shift",
            "visual_focus",
            "image_prompt_intent",
            "composition",
            "lighting",
            "subtitle_position",
        ]
        if not any(str((shot or {}).get(field) or "").strip() for field in creative_fields):
            suggestions.append(
                f"storyboard_json.shots[{index - 1}] would benefit from creative fields such as shot_purpose, conflict_beat, visual_focus, composition, lighting, or subtitle_position."
            )

    for video_shot_id in payload.video_shot_ids:
        if video_shot_id not in shot_ids:
            errors.append(f"video_shot_ids contains unknown shot id: {video_shot_id}.")

    if not str(publish_record.get("platform") or "").strip():
        warnings.append("publish_record_json.platform is recommended.")
    if not str(publish_record.get("title") or "").strip():
        warnings.append("publish_record_json.title is recommended.")

    is_valid = len(errors) == 0
    return CozeResponse(
        message="Payload validation completed",
        data={
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "shots_count": len(shots),
            "characters_count": len(characters),
            "video_shot_ids_count": len(payload.video_shot_ids),
        },
        next_action="ready_for_full_demo_flow" if is_valid else "fix_payload",
    )


def coze_project_init(db: Session, payload: CozeProjectInitRequest) -> CozeResponse:
    project = create_project(
        db,
        ProjectCreate(
            name=payload.project_card_json.project_title,
            description=_build_project_description(payload.project_card_json),
            target_platforms=[payload.project_card_json.platform] if payload.project_card_json.platform else [],
            tags=[tag for tag in [payload.project_card_json.genre, payload.project_card_json.target_audience, payload.project_card_json.visual_style] if tag],
            visual_asset_library_json=_extract_visual_asset_library(payload),
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

        created_shot = create_shot(
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
        update_shot_metadata(
            db,
            created_shot.id,
            _build_shot_metadata(shot_item),
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


def _map_video_shot_ids_to_internal_shot_ids(db: Session, project_id: int, video_shot_ids: list[str]) -> list[int]:
    if not video_shot_ids:
        return []

    shots = (
        db.query(Shot)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id)
        .all()
    )
    source_shot_id_to_internal_id: dict[str, int] = {}
    for shot in shots:
        source_shot_id = str((shot.metadata_json or {}).get("source_shot_id") or "").strip()
        if source_shot_id:
            source_shot_id_to_internal_id[source_shot_id.upper()] = shot.id

    internal_ids: list[int] = []
    missing_ids: list[str] = []
    for shot_id in video_shot_ids:
        normalized = shot_id.strip().upper()
        internal_id = source_shot_id_to_internal_id.get(normalized)
        if internal_id is None:
            missing_ids.append(shot_id)
            continue
        internal_ids.append(internal_id)

    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"video_shot_ids contains unknown storyboard shot ids: {', '.join(missing_ids)}",
        )

    return internal_ids


def coze_create_asset_tasks(db: Session, project_id: int, payload: CozeCreateAssetTasksRequest) -> CozeResponse:
    before_count = len(list_project_asset_tasks(db, project_id))
    internal_video_shot_ids = _map_video_shot_ids_to_internal_shot_ids(db, project_id, payload.video_shot_ids)
    created = bulk_create_project_asset_tasks(
        db,
        project_id,
        BulkAssetTaskCreateRequest(video_shot_ids=internal_video_shot_ids),
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
    next_action = _coze_next_action(db, project_id, summary)
    summary_data = summary.model_dump()
    summary_data["next_action"] = next_action
    return CozeResponse(
        message="Project summary fetched",
        data=summary_data,
        next_action=next_action,
    )


def coze_full_demo_flow(db: Session, payload: CozeFullDemoFlowRequest) -> CozeResponse:
    init_response = coze_project_init(
        db,
        CozeProjectInitRequest(
            project_card_json=payload.project_card_json,
            characters_json=payload.characters_json,
            visual_asset_library_json=payload.visual_asset_library_json,
        ),
    )
    project_id = init_response.data["project_id"]
    character_ids: list[int] = init_response.data["character_ids"]
    if not character_ids:
        raise HTTPException(status_code=400, detail="At least one character is required")

    coze_confirm_character_reference(
        db,
        character_ids[0],
        ConfirmCharacterReferenceRequest(main_reference_url="mock://character/reference.png"),
    )

    script_response = coze_generate_script(
        db,
        project_id,
        CozeGenerateScriptRequest(script_card_json=payload.script_card_json),
    )
    episode_id = script_response.data["episode_id"]

    storyboard_response = coze_storyboard(
        db,
        project_id,
        CozeStoryboardRequest(
            script_card_json=payload.script_card_json,
            storyboard_json=payload.storyboard_json,
        ),
    )

    asset_task_response = coze_create_asset_tasks(
        db,
        project_id,
        CozeCreateAssetTasksRequest(video_shot_ids=payload.video_shot_ids),
    )
    run_response = coze_run_asset_tasks(db, project_id)
    publish_response = coze_publish_record(db, project_id, payload.publish_record_json)
    summary_response = coze_project_summary(db, project_id)

    return CozeResponse(
        message="Full demo flow completed",
        data={
            "project_id": project_id,
            "character_ids": character_ids,
            "episode_id": episode_id,
            "shots_count": storyboard_response.data["shots_count"],
            "asset_tasks_count": asset_task_response.data["asset_tasks_count"],
            "assets_count": summary_response.data["assets_count"],
            "publish_record_id": publish_response.data["publish_record_id"],
            "final_summary": summary_response.data,
        },
        next_action="completed",
    )
