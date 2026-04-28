import re

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.asset_task import AssetTask
from app.models.character import Character
from app.models.enums import AssetTaskStatus
from app.models.enums import AssetModality
from app.models.episode import Episode
from app.models.project import Project
from app.models.publish_record import PublishRecord
from app.models.scene import Scene
from app.models.shot import Shot
from app.schemas.project import ProjectCreate
from app.schemas.project import ProjectImagePromptExport
from app.schemas.project import ProjectImagePromptItem
from app.schemas.project import ProjectVideoPromptExport
from app.schemas.project import ProjectVideoPromptItem
from app.schemas.project import ProjectManualProductionSummary
from app.schemas.project import ManualProductionBlockingSummary
from app.schemas.project import ProjectManualImageProgress
from app.schemas.project import ProjectManualImageProgressItem
from app.schemas.project import ProjectManualFinalChecklist
from app.schemas.project import ProjectEditingShotBoard
from app.schemas.project import EditingShotBoardItem
from app.schemas.project import ProjectEditingTimeline
from app.schemas.project import EditingTimelineItem
from app.schemas.project import ProjectEditingCueSheet
from app.schemas.project import EditingCueSheetItem
from app.schemas.project import ProjectManualVideoProgress
from app.schemas.project import ProjectManualVideoProgressItem
from app.schemas.project import ProjectPublishReadiness
from app.schemas.project import ProjectReferenceCoverageReport
from app.schemas.project import ProjectSummary
from app.schemas.project import ProjectVisualAssetPromptExport
from app.schemas.project import ProjectVisualAssetCandidates
from app.schemas.project import ProjectVisualAssetLibrary
from app.schemas.project import ManualFinalChecklistChecks
from app.schemas.project import PublishReadinessChecks
from app.schemas.project import PublishReadinessSummary
from app.schemas.project import ProjectVideoReadiness
from app.schemas.project import ProjectVideoReadinessItem
from app.schemas.project import VisualAssetRefs
from app.schemas.project import VisualAssetLibraryEntry
from app.schemas.project import VisualAssetCandidate
from app.schemas.project import VisualAssetLibraryImportCandidatesRequest
from app.schemas.project import VisualAssetLibraryImportCandidatesResponse
from app.schemas.project import VisualAssetLibraryManualImportRequest
from app.schemas.project import VisualAssetPromptItem
from app.schemas.project import ReferenceCoverageItem
from app.schemas.project import ReferenceCoverageMissingAsset
from app.services.prompt_enhancer import build_image_enhanced_prompt
from app.services.repository import create_and_refresh

MANUAL_IMAGE_NEGATIVE_PROMPT = (
    "不要模仿具体IP、明星、影视角色或已知动漫角色；不要水印；不要乱码文字；"
    "不要多余肢体；不要低清晰度。"
)

MANUAL_VIDEO_NEGATIVE_PROMPT = (
    "Do not imitate specific IP, celebrities, film characters, or known anime characters; "
    "no scene change; no watermark; no text overlay; no distorted hands; no extra limbs; no face morphing."
)


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


def get_project_visual_asset_library(db: Session, project_id: int) -> ProjectVisualAssetLibrary:
    project = get_project_or_404(db, project_id)
    library = _get_visual_asset_library(project)
    assets_without_reference_url: list[dict] = []
    for bucket_name in ("characters", "scenes", "props"):
        for item in library[bucket_name]:
            if not isinstance(item, dict):
                continue
            if str(item.get("main_reference_url") or "").strip():
                continue
            assets_without_reference_url.append(
                {
                    "asset_type": bucket_name[:-1] if bucket_name.endswith("s") else bucket_name,
                    "asset_key": item.get("asset_key"),
                    "name": item.get("name"),
                }
            )

    if not any(library.values()):
        next_action = "extract_or_manual_import_assets"
    elif assets_without_reference_url:
        next_action = "complete_reference_urls"
    else:
        next_action = "ready_for_reference_guided_image_generation"

    return ProjectVisualAssetLibrary(
        project_id=project_id,
        characters_count=len(library["characters"]),
        scenes_count=len(library["scenes"]),
        props_count=len(library["props"]),
        missing_reference_url_count=len(assets_without_reference_url),
        assets_without_reference_url=assets_without_reference_url,
        characters=library["characters"],
        scenes=library["scenes"],
        props=library["props"],
        next_action=next_action,
    )


def export_project_visual_asset_prompts(db: Session, project_id: int) -> ProjectVisualAssetPromptExport:
    project = get_project_or_404(db, project_id)
    library = _get_visual_asset_library(project)
    project_style = _extract_project_style(project)
    project_genre = _extract_project_genre(project)
    character_record_lookup = _build_character_record_lookup(db, project_id)
    lead_asset = _find_lead_character_asset(library)

    if not any(library.values()):
        return ProjectVisualAssetPromptExport(
            project_id=project_id,
            characters_count=0,
            scenes_count=0,
            props_count=0,
            items_count=0,
            characters=[],
            scenes=[],
            props=[],
            next_action="extract_or_manual_import_assets",
        )

    def build_item(asset: dict, asset_type: str) -> VisualAssetPromptItem:
        asset_key = str(asset.get("asset_key") or "").strip() or "asset"
        name = str(asset.get("name") or asset_key).strip() or asset_key
        target_reference_url = str(asset.get("main_reference_url") or "").strip() or None
        suggested_reference_filename = _suggest_reference_filename(asset_type, asset_key)

        if asset_type == "character":
            record = character_record_lookup.get(asset_key)
            copy_ready_prompt = _build_character_reference_prompt(
                asset=asset,
                record=record,
                project_style=project_style,
                project_genre=project_genre,
                lead_asset=lead_asset,
            )
            prompt_type = "character_main_reference"
        elif asset_type == "scene":
            copy_ready_prompt = _build_scene_reference_prompt(
                asset=asset,
                project_style=project_style,
                project_genre=project_genre,
            )
            prompt_type = "scene_main_reference"
        else:
            copy_ready_prompt = _build_prop_reference_prompt(
                asset=asset,
                project_style=project_style,
            )
            prompt_type = "prop_main_reference"

        return VisualAssetPromptItem(
            asset_key=asset_key,
            name=name,
            asset_type=asset_type,
            prompt_type=prompt_type,
            target_reference_url=target_reference_url,
            suggested_reference_filename=suggested_reference_filename,
            copy_ready_prompt=copy_ready_prompt,
            must_keep=asset.get("must_keep") if isinstance(asset.get("must_keep"), list) else [],
            avoid=asset.get("avoid") if isinstance(asset.get("avoid"), list) else [],
        )

    character_items = [build_item(item, "character") for item in library["characters"] if isinstance(item, dict)]
    scene_items = [build_item(item, "scene") for item in library["scenes"] if isinstance(item, dict)]
    prop_items = [build_item(item, "prop") for item in library["props"] if isinstance(item, dict)]

    return ProjectVisualAssetPromptExport(
        project_id=project_id,
        characters_count=len(character_items),
        scenes_count=len(scene_items),
        props_count=len(prop_items),
        items_count=len(character_items) + len(scene_items) + len(prop_items),
        characters=character_items,
        scenes=scene_items,
        props=prop_items,
        next_action="generate_reference_images",
    )


def get_project_reference_coverage_report(db: Session, project_id: int) -> ProjectReferenceCoverageReport:
    project = get_project_or_404(db, project_id)
    library = _get_visual_asset_library(project)
    lookup = _build_visual_asset_lookup(project)

    shots = (
        db.query(Shot)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id)
        .order_by(Shot.id.asc())
        .all()
    )

    items: list[ReferenceCoverageItem] = []
    ready_shots_count = 0
    missing_reference_url_count = 0
    missing_asset_key_count = 0
    shots_missing_all_bindings = 0
    report_warnings: list[str] = []
    report_suggestions: list[str] = []

    for shot in shots:
        shot_metadata = shot.metadata_json or {}
        character_asset_keys = shot_metadata.get("character_asset_keys")
        if not isinstance(character_asset_keys, list):
            character_asset_keys = []
        character_asset_keys = [str(key).strip() for key in character_asset_keys if str(key).strip()]

        scene_asset_key = str(shot_metadata.get("scene_asset_key") or "").strip() or None

        prop_asset_keys = shot_metadata.get("prop_asset_keys")
        if not isinstance(prop_asset_keys, list):
            prop_asset_keys = []
        prop_asset_keys = [str(key).strip() for key in prop_asset_keys if str(key).strip()]

        warnings: list[str] = []
        suggestions: list[str] = []
        missing_character_asset_keys: list[str] = []
        missing_prop_asset_keys: list[str] = []
        missing_scene_asset_key: str | None = None
        assets_missing_reference_url: list[ReferenceCoverageMissingAsset] = []

        if not character_asset_keys:
            warnings.append("missing_character_asset_keys")
            suggestions.append("Bind character reference assets to this shot before image generation.")
        if not scene_asset_key:
            warnings.append("missing_scene_asset_key")
            suggestions.append("Bind a scene reference asset to this shot for stronger environment consistency.")
        if not prop_asset_keys:
            suggestions.append("consider_prop_reference_if_key_object_exists")

        for asset_key in character_asset_keys:
            asset = lookup["characters"].get(asset_key)
            if asset is None:
                missing_character_asset_keys.append(asset_key)
            elif not str(asset.get("main_reference_url") or "").strip():
                assets_missing_reference_url.append(
                    ReferenceCoverageMissingAsset(
                        asset_type="character",
                        asset_key=asset.get("asset_key"),
                        name=asset.get("name"),
                    )
                )

        if scene_asset_key:
            scene_asset = lookup["scenes"].get(scene_asset_key)
            if scene_asset is None:
                missing_scene_asset_key = scene_asset_key
            elif not str(scene_asset.get("main_reference_url") or "").strip():
                assets_missing_reference_url.append(
                    ReferenceCoverageMissingAsset(
                        asset_type="scene",
                        asset_key=scene_asset.get("asset_key"),
                        name=scene_asset.get("name"),
                    )
                )

        for asset_key in prop_asset_keys:
            asset = lookup["props"].get(asset_key)
            if asset is None:
                missing_prop_asset_keys.append(asset_key)
            elif not str(asset.get("main_reference_url") or "").strip():
                assets_missing_reference_url.append(
                    ReferenceCoverageMissingAsset(
                        asset_type="prop",
                        asset_key=asset.get("asset_key"),
                        name=asset.get("name"),
                    )
                )

        if missing_character_asset_keys or missing_scene_asset_key or missing_prop_asset_keys:
            warnings.append("missing_visual_asset_ref")
            if missing_character_asset_keys:
                suggestions.append(
                    f"Import or correct missing character asset keys: {', '.join(missing_character_asset_keys)}."
                )
            if missing_scene_asset_key:
                suggestions.append(f"Import or correct missing scene asset key: {missing_scene_asset_key}.")
            if missing_prop_asset_keys:
                suggestions.append(f"Import or correct missing prop asset keys: {', '.join(missing_prop_asset_keys)}.")

        if assets_missing_reference_url:
            warnings.append("reference_url_missing")
            for asset in assets_missing_reference_url:
                asset_type_label = asset.asset_type
                asset_key_label = asset.asset_key or asset.name or "unknown_asset"
                suggestions.append(
                    f"Add main_reference_url for {asset_type_label} {asset_key_label} before generating this shot."
                )

        warnings = list(dict.fromkeys(warnings))
        suggestions = list(dict.fromkeys(suggestions))

        character_refs_found = bool(character_asset_keys) and not missing_character_asset_keys
        scene_ref_found = bool(scene_asset_key) and missing_scene_asset_key is None
        prop_refs_found = bool(prop_asset_keys) and not missing_prop_asset_keys

        character_refs_complete = character_refs_found and all(
            str((lookup["characters"].get(asset_key) or {}).get("main_reference_url") or "").strip()
            for asset_key in character_asset_keys
        )
        scene_ref_complete = bool(scene_asset_key) and missing_scene_asset_key is None and bool(
            str((lookup["scenes"].get(scene_asset_key) or {}).get("main_reference_url") or "").strip()
        )
        ready_for_reference_guided_image = character_refs_complete and scene_ref_complete

        if not character_asset_keys and not scene_asset_key and not prop_asset_keys:
            shots_missing_all_bindings += 1

        if ready_for_reference_guided_image:
            ready_shots_count += 1

        missing_reference_url_count += len(assets_missing_reference_url)
        missing_asset_key_count += (
            len(missing_character_asset_keys)
            + len(missing_prop_asset_keys)
            + (1 if missing_scene_asset_key else 0)
        )
        report_warnings.extend(warnings)
        report_suggestions.extend(suggestions)

        items.append(
            ReferenceCoverageItem(
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                character_asset_keys=character_asset_keys,
                scene_asset_key=scene_asset_key,
                prop_asset_keys=prop_asset_keys,
                character_refs_found=character_refs_found,
                scene_ref_found=scene_ref_found,
                prop_refs_found=prop_refs_found,
                missing_character_asset_keys=missing_character_asset_keys,
                missing_scene_asset_key=missing_scene_asset_key,
                missing_prop_asset_keys=missing_prop_asset_keys,
                assets_missing_reference_url=assets_missing_reference_url,
                ready_for_reference_guided_image=ready_for_reference_guided_image,
                warnings=warnings,
                suggestions=suggestions,
            )
        )

    report_warnings = list(dict.fromkeys(report_warnings))
    report_suggestions = list(dict.fromkeys(report_suggestions))

    if not any(library.values()):
        report_suggestions.insert(0, "Visual Asset Library is empty. Extract or manually import reference assets first.")
        next_action = "extract_or_manual_import_assets"
    elif missing_asset_key_count > 0:
        next_action = "review_missing_asset_keys"
    elif missing_reference_url_count > 0:
        next_action = "complete_reference_urls"
    elif shots and shots_missing_all_bindings > (len(shots) / 2):
        next_action = "bind_reference_assets_to_shots"
    else:
        next_action = "ready_for_reference_guided_image_generation"

    return ProjectReferenceCoverageReport(
        project_id=project_id,
        shots_count=len(items),
        ready_shots_count=ready_shots_count,
        warning_shots_count=len(items) - ready_shots_count,
        missing_reference_url_count=missing_reference_url_count,
        missing_asset_key_count=missing_asset_key_count,
        items=items,
        blocking_issues=[],
        warnings=report_warnings,
        suggestions=report_suggestions,
        next_action=next_action,
    )


def _extract_project_style(project: Project) -> str | None:
    if project.description:
        for line in project.description.splitlines():
            if line.startswith("visual_style="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value
    for tag in project.tags:
        if "style" in tag.lower() or "comic" in tag.lower() or "realism" in tag.lower():
            return tag
    return None


def _get_first_confirmed_character_reference(db: Session, project_id: int) -> str | None:
    character = (
        db.query(Character)
        .filter(Character.project_id == project_id, Character.main_reference_confirmed.is_(True))
        .order_by(Character.id.asc())
        .first()
    )
    if character is None:
        return None
    return character.main_reference_url


def _select_preferred_asset(assets: list[Asset]) -> Asset | None:
    if not assets:
        return None

    manual_assets = [
        asset
        for asset in assets
        if bool((asset.metadata_json or {}).get("manual_upload"))
    ]
    if manual_assets:
        return max(manual_assets, key=lambda asset: asset.id)

    return max(assets, key=lambda asset: asset.id)


def _get_preferred_task_asset(
    db: Session,
    *,
    asset_task_id: int,
    modality: AssetModality,
) -> Asset | None:
    assets = (
        db.query(Asset)
        .filter(Asset.asset_task_id == asset_task_id, Asset.modality == modality)
        .order_by(Asset.id.asc())
        .all()
    )
    return _select_preferred_asset(assets)


def _get_preferred_shot_asset(
    db: Session,
    *,
    shot_id: int,
    modality: AssetModality,
) -> Asset | None:
    assets = (
        db.query(Asset)
        .filter(Asset.shot_id == shot_id, Asset.modality == modality)
        .order_by(Asset.id.asc())
        .all()
    )
    return _select_preferred_asset(assets)


def _build_copy_ready_prompt(enhanced_prompt: str, negative_prompt: str) -> str:
    return "\n".join([enhanced_prompt.strip(), f"Negative prompt: {negative_prompt}"]).strip()


def _clean_reference_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("mock://"):
        return None
    return url


def _strip_mock_reference_urls(text: str) -> str:
    cleaned_lines = [line for line in text.splitlines() if "mock://character/reference.png" not in line]
    return "\n".join(cleaned_lines).strip()


def _stringify_list(values: list[str] | None) -> str | None:
    filtered = [str(value).strip() for value in (values or []) if str(value).strip()]
    if not filtered:
        return None
    return ", ".join(filtered)


def _build_shot_type_prompt_hint(shot_type: str | None) -> str | None:
    normalized = (shot_type or "").strip().lower()
    if normalized == "dialogue":
        return "Dialogue focus: emphasize readable facial expression, mouth shape, and subtitle-safe framing."
    if normalized == "reaction":
        return "Reaction focus: emphasize emotional reaction and facial clarity."
    if normalized == "reveal":
        return "Reveal focus: emphasize a disturbing clue, changed understanding of the scene, and suspenseful reveal."
    if normalized == "close_up":
        return "Close-up focus: emphasize facial detail and clean framing."
    if normalized == "transition":
        return "Transition focus: emphasize clean composition and transition-friendly framing."
    if normalized == "action":
        return "Action focus: emphasize clear body movement and readable staging."
    if normalized == "suspense":
        return "Suspense focus: emphasize silence, negative space, tension, visual uncertainty, low light, and unease."
    return None


def _get_visual_asset_library(project: Project) -> dict:
    library = project.visual_asset_library_json or {}
    if not isinstance(library, dict):
        return {"characters": [], "scenes": [], "props": []}
    return {
        "characters": library.get("characters") if isinstance(library.get("characters"), list) else [],
        "scenes": library.get("scenes") if isinstance(library.get("scenes"), list) else [],
        "props": library.get("props") if isinstance(library.get("props"), list) else [],
    }


def _normalize_asset_type(asset_type: str) -> tuple[str, str]:
    normalized = (asset_type or "").strip().lower()
    mapping = {
        "character": ("character", "characters"),
        "scene": ("scene", "scenes"),
        "prop": ("prop", "props"),
    }
    if normalized not in mapping:
        raise HTTPException(status_code=400, detail="asset_type must be one of: character, scene, prop")
    return mapping[normalized]


def _slugify_asset_key(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "_", (value or "").strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "asset"


def _upsert_visual_asset_entry(existing_items: list[dict], asset: dict) -> tuple[list[dict], bool]:
    incoming_key = str(asset.get("asset_key") or "").strip()
    if not incoming_key:
        raise HTTPException(status_code=400, detail="asset.asset_key is required")

    updated = False
    next_items: list[dict] = []
    for item in existing_items:
        if isinstance(item, dict) and str(item.get("asset_key") or "").strip() == incoming_key:
            merged = dict(item)
            merged.update(asset)
            next_items.append(merged)
            updated = True
        else:
            next_items.append(item)
    if not updated:
        next_items.append(asset)
    return next_items, updated


def _save_visual_asset_library(project: Project, library: dict, db: Session) -> None:
    project.visual_asset_library_json = library
    db.add(project)
    db.commit()
    db.refresh(project)


def _build_visual_asset_lookup(project: Project) -> dict[str, dict[str, dict]]:
    library = _get_visual_asset_library(project)
    return {
        "characters": {
            str(item.get("asset_key")): item
            for item in library["characters"]
            if isinstance(item, dict) and str(item.get("asset_key") or "").strip()
        },
        "scenes": {
            str(item.get("asset_key")): item
            for item in library["scenes"]
            if isinstance(item, dict) and str(item.get("asset_key") or "").strip()
        },
        "props": {
            str(item.get("asset_key")): item
            for item in library["props"]
            if isinstance(item, dict) and str(item.get("asset_key") or "").strip()
        },
    }


def _parse_key_value_lines(text: str | None) -> dict[str, str]:
    data: dict[str, str] = {}
    if not text:
        return data
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            data[key] = value
    return data


def _suggest_reference_filename(asset_type: str, asset_key: str) -> str:
    normalized_key = asset_key or "asset"
    if asset_type == "character":
        return f"file:///D:/AI漫剧角色库/{normalized_key}_main.png"
    if asset_type == "scene":
        return f"file:///D:/AI漫剧场景库/{normalized_key}_main.png"
    return f"file:///D:/AI漫剧道具库/{normalized_key}_main.png"


def _extract_project_genre(project: Project) -> str | None:
    if project.description:
        for line in project.description.splitlines():
            if line.startswith("genre="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value
    for tag in project.tags:
        if str(tag).strip():
            return str(tag).strip()
    return None


def _build_character_record_lookup(db: Session, project_id: int) -> dict[str, Character]:
    records = (
        db.query(Character)
        .filter(Character.project_id == project_id)
        .order_by(Character.id.asc())
        .all()
    )
    return {_slugify_asset_key(record.name): record for record in records}


def _find_lead_character_asset(library: dict) -> dict | None:
    for item in library.get("characters", []):
        if isinstance(item, dict) and str(item.get("role") or "").strip().lower() == "lead":
            return item
    for item in library.get("characters", []):
        if isinstance(item, dict):
            return item
    return None


def _is_mirror_double_asset(asset: dict) -> bool:
    asset_key = str(asset.get("asset_key") or "").lower()
    role = str(asset.get("role") or "").lower()
    name = str(asset.get("name") or "").lower()
    combined = " ".join([asset_key, role, name])
    keywords = ["mirror-double", "mirror_double", "double", "door_double", "替身", "镜像"]
    return any(keyword in combined for keyword in keywords)


def _build_character_reference_prompt(
    *,
    asset: dict,
    record: Character | None,
    project_style: str | None,
    project_genre: str | None,
    lead_asset: dict | None,
) -> str:
    name = str(asset.get("name") or asset.get("asset_key") or "Unknown Character")
    role = str(asset.get("role") or (record.role_type if record is not None else "") or "").strip()
    profile_data = _parse_key_value_lines(record.profile if record is not None else None)
    visual_data = _parse_key_value_lines(record.visual_notes if record is not None else None)
    must_keep = asset.get("must_keep") if isinstance(asset.get("must_keep"), list) else []
    avoid = asset.get("avoid") if isinstance(asset.get("avoid"), list) else []

    lines = [
        "Task type: character main reference image for an AI comic drama.",
        "Output goal: create a stable reusable character reference image, not a storyboard shot.",
        "This is not a scene shot. not a poster. not a multi-panel comic page. not a dramatic action frame.",
        "Image requirements: front-facing or three-quarter half-body reference, clear face, clear hairstyle, clear outfit, clean readable silhouette, simple background, vertical 9:16, anime-comic realism.",
        f"Character name: {name}",
        f"Role: {role}" if role else None,
        f"Project visual style: {project_style}" if project_style else None,
        f"Project genre: {project_genre}" if project_genre else None,
        f"Appearance summary: {visual_data.get('appearance_summary') or visual_data.get('appearance')}" if (visual_data.get('appearance_summary') or visual_data.get('appearance')) else None,
        f"Social identity: {profile_data.get('social_identity')}" if profile_data.get("social_identity") else None,
        f"First impression: {profile_data.get('first_impression')}" if profile_data.get("first_impression") else None,
        f"Public mask: {profile_data.get('public_mask')}" if profile_data.get("public_mask") else None,
        f"Inner truth: {profile_data.get('inner_truth')}" if profile_data.get("inner_truth") else None,
        f"Core keywords: {profile_data.get('core_keywords')}" if profile_data.get("core_keywords") else None,
        f"Must keep: {', '.join(must_keep[:6])}" if must_keep else None,
        f"Avoid: {', '.join(avoid[:6])}" if avoid else None,
        "Safety: original character only. Do not imitate celebrities, real people, known anime characters, film characters, or copyrighted IP.",
    ]

    if _is_mirror_double_asset(asset):
        lines.append("Character note: this character is an abnormal double or uncanny mirror counterpart of the protagonist.")
        if lead_asset and str(lead_asset.get("asset_key") or "") != str(asset.get("asset_key") or ""):
            lines.append(
                f"Identity anchor: keep core face identity aligned with lead character {lead_asset.get('name') or lead_asset.get('asset_key')} while making the expression hollow and disturbing."
            )
        lines.append("Avoid monster face, gore, and exaggerated creature design.")

    return "\n".join(line for line in lines if line).strip()


def _build_scene_reference_prompt(
    *,
    asset: dict,
    project_style: str | None,
    project_genre: str | None,
) -> str:
    name = str(asset.get("name") or asset.get("asset_key") or "Unknown Scene")
    must_keep = asset.get("must_keep") if isinstance(asset.get("must_keep"), list) else []
    avoid = asset.get("avoid") if isinstance(asset.get("avoid"), list) else []
    genre_text = (project_genre or "").lower()
    suspensey = any(keyword in genre_text for keyword in ["thriller", "suspense", "horror", "怪谈", "惊悚", "悬疑"])
    lines = [
        "Task type: scene main reference image for an AI comic drama.",
        "Output goal: create a stable reusable scene reference image, not a storyboard shot.",
        "No characters. No foreground acting. No poster layout. No text overlay.",
        "Image requirements: clearly show spatial layout, show key fixed elements, consistent lighting, clean reusable background, vertical 9:16, anime-comic realism.",
        f"Scene name: {name}",
        f"Project visual style: {project_style}" if project_style else None,
        f"Project genre: {project_genre}" if project_genre else None,
        f"Must keep: {', '.join(must_keep[:6])}" if must_keep else None,
        f"Avoid: {', '.join(avoid[:6])}" if avoid else None,
    ]
    if suspensey:
        lines.append("Atmosphere: low light, narrow space, silence, unease, realistic old apartment texture, cinematic suspense, no gore.")
    return "\n".join(line for line in lines if line).strip()


def _build_prop_reference_prompt(
    *,
    asset: dict,
    project_style: str | None,
) -> str:
    name = str(asset.get("name") or asset.get("asset_key") or "Unknown Prop")
    must_keep = asset.get("must_keep") if isinstance(asset.get("must_keep"), list) else []
    avoid = asset.get("avoid") if isinstance(asset.get("avoid"), list) else []
    lines = [
        "Task type: prop main reference image for an AI comic drama.",
        "Output goal: create a stable reusable prop reference image, not a storyboard shot.",
        "Single object only. Clear view. Simple background. No brand logo. No readable copyrighted text. No watermark.",
        "Image requirements: clear shape, clear material, clear color, front or close-up view, anime-comic realism, reusable for later shots.",
        f"Prop name: {name}",
        f"Project visual style: {project_style}" if project_style else None,
        f"Must keep: {', '.join(must_keep[:6])}" if must_keep else None,
        f"Avoid: {', '.join(avoid[:6])}" if avoid else None,
    ]
    return "\n".join(line for line in lines if line).strip()


def manual_import_project_visual_asset(
    db: Session,
    project_id: int,
    payload: VisualAssetLibraryManualImportRequest,
) -> ProjectVisualAssetLibrary:
    project = get_project_or_404(db, project_id)
    _, bucket = _normalize_asset_type(payload.asset_type)
    if payload.merge_mode != "upsert":
        raise HTTPException(status_code=400, detail="merge_mode must be upsert")

    library = _get_visual_asset_library(project)
    asset_data = payload.asset.model_dump()
    bucket_items, _ = _upsert_visual_asset_entry(library[bucket], asset_data)
    library[bucket] = bucket_items
    _save_visual_asset_library(project, library, db)
    return get_project_visual_asset_library(db, project_id)


def _candidate_from_parts(
    *,
    asset_key: str,
    name: str,
    asset_type: str,
    reason: str,
    source: str,
    already_in_library: bool,
) -> VisualAssetCandidate:
    return VisualAssetCandidate(
        asset_key=asset_key,
        name=name,
        asset_type=asset_type,
        reason=reason,
        source=source,
        suggested_main_reference_url="",
        must_keep=[],
        avoid=[],
        already_in_library=already_in_library,
    )


def _extract_prop_candidates_from_text(text: str) -> list[tuple[str, str]]:
    normalized = (text or "").lower()
    keyword_map = [
        ("smartphone", ["smartphone", "phone", "手机"]),
        ("peephole", ["peephole", "猫眼"]),
        ("door_lock", ["door lock", "doorlock", "门锁"]),
        ("employee_badge", ["badge", "工牌"]),
        ("folder", ["folder", "文件夹"]),
        ("contract", ["contract", "合同"]),
        ("invitation", ["invitation", "邀请函"]),
        ("champagne", ["champagne", "香槟"]),
    ]
    found: list[tuple[str, str]] = []
    for asset_key, keywords in keyword_map:
        if any(keyword in normalized for keyword in keywords):
            found.append((asset_key, keywords[0]))
    return found


def extract_project_visual_asset_candidates(db: Session, project_id: int) -> ProjectVisualAssetCandidates:
    project = get_project_or_404(db, project_id)
    library = _get_visual_asset_library(project)
    lookup = _build_visual_asset_lookup(project)

    characters_by_key: dict[str, VisualAssetCandidate] = {}
    scenes_by_key: dict[str, VisualAssetCandidate] = {}
    props_by_key: dict[str, VisualAssetCandidate] = {}

    character_records = db.query(Character).filter(Character.project_id == project_id).order_by(Character.id.asc()).all()
    for character in character_records:
        asset_key = _slugify_asset_key(character.name)
        characters_by_key.setdefault(
            asset_key,
            _candidate_from_parts(
                asset_key=asset_key,
                name=character.name,
                asset_type="character",
                reason="character record exists in project",
                source="character records",
                already_in_library=asset_key in lookup["characters"],
            ),
        )

    shots = (
        db.query(Shot)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id)
        .order_by(Shot.id.asc())
        .all()
    )
    for shot in shots:
        metadata = shot.metadata_json or {}
        character_name = str(metadata.get("character") or "").strip()
        if character_name:
            asset_key = _slugify_asset_key(character_name)
            characters_by_key.setdefault(
                asset_key,
                _candidate_from_parts(
                    asset_key=asset_key,
                    name=character_name,
                    asset_type="character",
                    reason="character appears in storyboard shots",
                    source="storyboard.character",
                    already_in_library=asset_key in lookup["characters"],
                ),
            )
        for asset_key in metadata.get("character_asset_keys") or []:
            normalized_key = str(asset_key).strip()
            if not normalized_key:
                continue
            characters_by_key.setdefault(
                normalized_key,
                _candidate_from_parts(
                    asset_key=normalized_key,
                    name=character_name or normalized_key,
                    asset_type="character",
                    reason="character asset key referenced by storyboard shot",
                    source="storyboard.character_asset_keys",
                    already_in_library=normalized_key in lookup["characters"],
                ),
            )

        location_name = str(metadata.get("location") or "").strip()
        if location_name:
            scene_key = _slugify_asset_key(location_name)
            scenes_by_key.setdefault(
                scene_key,
                _candidate_from_parts(
                    asset_key=scene_key,
                    name=location_name,
                    asset_type="scene",
                    reason=f"main setting used in {metadata.get('source_shot_id') or f'Shot {shot.id}'}",
                    source="storyboard.location",
                    already_in_library=scene_key in lookup["scenes"],
                ),
            )
        scene_asset_key = str(metadata.get("scene_asset_key") or "").strip()
        if scene_asset_key:
            scenes_by_key.setdefault(
                scene_asset_key,
                _candidate_from_parts(
                    asset_key=scene_asset_key,
                    name=location_name or scene_asset_key,
                    asset_type="scene",
                    reason="scene asset key referenced by storyboard shot",
                    source="storyboard.scene_asset_key",
                    already_in_library=scene_asset_key in lookup["scenes"],
                ),
            )

        for prop_key in metadata.get("prop_asset_keys") or []:
            normalized_key = str(prop_key).strip()
            if not normalized_key:
                continue
            props_by_key.setdefault(
                normalized_key,
                _candidate_from_parts(
                    asset_key=normalized_key,
                    name=normalized_key.replace("_", " "),
                    asset_type="prop",
                    reason="prop asset key referenced by storyboard shot",
                    source="storyboard.prop_asset_keys",
                    already_in_library=normalized_key in lookup["props"],
                ),
            )

        searchable_text = " ".join(
            [
                str(shot.core_action or ""),
                str(shot.image_prompt or ""),
                str(metadata.get("dialogue") or shot.dialogue or ""),
            ]
        )
        for prop_key, keyword in _extract_prop_candidates_from_text(searchable_text):
            props_by_key.setdefault(
                prop_key,
                _candidate_from_parts(
                    asset_key=prop_key,
                    name=prop_key.replace("_", " "),
                    asset_type="prop",
                    reason=f"key object inferred from shot text via keyword '{keyword}'",
                    source="storyboard/core_action/image_prompt/dialogue",
                    already_in_library=prop_key in lookup["props"],
                ),
            )

    return ProjectVisualAssetCandidates(
        project_id=project_id,
        characters=list(characters_by_key.values()),
        scenes=list(scenes_by_key.values()),
        props=list(props_by_key.values()),
        next_action="review_candidates_before_import",
    )


def import_project_visual_asset_candidates(
    db: Session,
    project_id: int,
    payload: VisualAssetLibraryImportCandidatesRequest,
) -> VisualAssetLibraryImportCandidatesResponse:
    project = get_project_or_404(db, project_id)
    if payload.merge_mode != "upsert":
        raise HTTPException(status_code=400, detail="merge_mode must be upsert")

    library = _get_visual_asset_library(project)
    imported_count = 0
    updated_count = 0

    for bucket, assets in (
        ("characters", payload.characters),
        ("scenes", payload.scenes),
        ("props", payload.props),
    ):
        bucket_items = library[bucket]
        for asset in assets:
            before_exists = any(
                isinstance(item, dict) and str(item.get("asset_key") or "").strip() == asset.asset_key
                for item in bucket_items
            )
            bucket_items, updated = _upsert_visual_asset_entry(bucket_items, asset.model_dump())
            if updated or before_exists:
                updated_count += 1
            else:
                imported_count += 1
        library[bucket] = bucket_items

    _save_visual_asset_library(project, library, db)
    refreshed = _get_visual_asset_library(project)
    return VisualAssetLibraryImportCandidatesResponse(
        project_id=project_id,
        characters_count=len(refreshed["characters"]),
        scenes_count=len(refreshed["scenes"]),
        props_count=len(refreshed["props"]),
        imported_count=imported_count,
        updated_count=updated_count,
        next_action="ready_for_reference_guided_image_generation",
    )


def _to_visual_asset_entry(item: dict | None) -> VisualAssetLibraryEntry | None:
    if not isinstance(item, dict):
        return None
    return VisualAssetLibraryEntry(
        asset_key=item.get("asset_key"),
        name=item.get("name"),
        main_reference_url=item.get("main_reference_url"),
        must_keep=item.get("must_keep") if isinstance(item.get("must_keep"), list) else [],
        avoid=item.get("avoid") if isinstance(item.get("avoid"), list) else [],
    )


def _resolve_visual_asset_refs(project: Project, shot_metadata: dict) -> VisualAssetRefs:
    lookup = _build_visual_asset_lookup(project)
    character_asset_keys = shot_metadata.get("character_asset_keys")
    if not isinstance(character_asset_keys, list):
        character_asset_keys = []
    prop_asset_keys = shot_metadata.get("prop_asset_keys")
    if not isinstance(prop_asset_keys, list):
        prop_asset_keys = []
    scene_asset_key = shot_metadata.get("scene_asset_key")

    return VisualAssetRefs(
        characters=[
            entry
            for entry in (_to_visual_asset_entry(lookup["characters"].get(str(asset_key))) for asset_key in character_asset_keys)
            if entry is not None
        ],
        scene=_to_visual_asset_entry(lookup["scenes"].get(str(scene_asset_key))) if scene_asset_key else None,
        props=[
            entry
            for entry in (_to_visual_asset_entry(lookup["props"].get(str(asset_key))) for asset_key in prop_asset_keys)
            if entry is not None
        ],
    )


def _build_visual_reference_prompt_suffix(visual_asset_refs: VisualAssetRefs) -> str:
    lines: list[str] = []
    if visual_asset_refs.characters:
        character = visual_asset_refs.characters[0]
        lines.append(
            "Recommended character reference: "
            f"{character.name or character.asset_key or 'unknown'}"
            + (f" ({character.main_reference_url})" if character.main_reference_url else "")
        )
        if character.must_keep:
            lines.append(f"Must keep: {', '.join(character.must_keep[:4])}")
        if character.avoid:
            lines.append(f"Avoid: {', '.join(character.avoid[:4])}")
    if visual_asset_refs.scene:
        scene = visual_asset_refs.scene
        lines.append(
            "Recommended scene reference: "
            f"{scene.name or scene.asset_key or 'unknown'}"
            + (f" ({scene.main_reference_url})" if scene.main_reference_url else "")
        )
        if scene.must_keep:
            lines.append(f"Scene must keep: {', '.join(scene.must_keep[:4])}")
        if scene.avoid:
            lines.append(f"Scene avoid: {', '.join(scene.avoid[:4])}")
    if visual_asset_refs.props:
        prop_names = [prop.name or prop.asset_key or "unknown" for prop in visual_asset_refs.props[:3]]
        lines.append(f"Recommended prop reference: {', '.join(prop_names)}")
    return "\n".join(lines).strip()


def _build_production_grade_image_prompt(
    *,
    enhanced_prompt: str,
    negative_prompt: str,
    shot_metadata: dict,
    visual_asset_refs: VisualAssetRefs,
) -> str:
    lines: list[str] = [
        "Task type: storyboard shot image for a vertical AI comic drama.",
        "Output goal: generate one single-shot storyboard keyframe for later editing.",
        enhanced_prompt.strip(),
        "Do not create a poster, character sheet, collage, or multi-panel comic page. not a poster. not a character sheet. not a collage. not a multi-panel comic page.",
        "Shot clarity: show one clear narrative moment only; focus on readable acting and expression; make the character action and spatial relationship clear; maintain clean composition for later subtitle placement; suitable for storyboard-based short-drama editing.",
        "Atmosphere: low light, narrow space, silence, unease, off-screen threat, suspenseful pause, psychological fear, cinematic horror atmosphere without gore.",
    ]

    shot_type_hint = _build_shot_type_prompt_hint(shot_metadata.get("shot_type"))
    if shot_type_hint:
        lines.append(shot_type_hint)

    creative_pairs = [
        ("Shot purpose", shot_metadata.get("shot_purpose")),
        ("Conflict beat", shot_metadata.get("conflict_beat")),
        ("Emotion shift", shot_metadata.get("emotion_shift")),
        ("Visual focus", shot_metadata.get("visual_focus")),
        ("Image prompt intent", shot_metadata.get("image_prompt_intent")),
        ("Composition", shot_metadata.get("composition")),
        ("Lighting", shot_metadata.get("lighting")),
        ("Subtitle position", shot_metadata.get("subtitle_position")),
        ("Shot type", shot_metadata.get("shot_type")),
        ("Camera motion", shot_metadata.get("camera_motion")),
        ("Subject motion", shot_metadata.get("subject_motion")),
        ("Transition", shot_metadata.get("transition")),
        ("Subtitle cue", shot_metadata.get("subtitle_text")),
        ("Sound effect cue", shot_metadata.get("sfx")),
        ("Editing notes", shot_metadata.get("editing_notes")),
    ]
    for label, value in creative_pairs:
        if str(value or "").strip():
            lines.append(f"{label}: {value}")

    negative_constraints = _stringify_list(shot_metadata.get("negative_constraints"))
    if negative_constraints:
        lines.append(f"Shot-specific negative constraints: {negative_constraints}")

    character_refs = [
        f"{entry.name or entry.asset_key}: {_clean_reference_url(entry.main_reference_url) or '[local ref]'}"
        for entry in visual_asset_refs.characters
    ]
    if character_refs:
        lines.append(f"Recommended character reference: {'; '.join(character_refs)}")
    if visual_asset_refs.scene is not None:
        scene_ref_url = _clean_reference_url(visual_asset_refs.scene.main_reference_url) or "[local ref]"
        lines.append(
            f"Recommended scene reference: {(visual_asset_refs.scene.name or visual_asset_refs.scene.asset_key)}: {scene_ref_url}"
        )
    prop_refs = [
        f"{entry.name or entry.asset_key}: {_clean_reference_url(entry.main_reference_url) or '[local ref]'}"
        for entry in visual_asset_refs.props
    ]
    if prop_refs:
        lines.append(f"Recommended prop reference: {'; '.join(prop_refs)}")

    must_keep_parts: list[str] = []
    avoid_parts: list[str] = []
    for entry in [*visual_asset_refs.characters, *visual_asset_refs.props]:
        must_keep_parts.extend(entry.must_keep)
        avoid_parts.extend(entry.avoid)
    if visual_asset_refs.scene is not None:
        must_keep_parts.extend(visual_asset_refs.scene.must_keep)
        avoid_parts.extend(visual_asset_refs.scene.avoid)
    must_keep_text = _stringify_list(must_keep_parts)
    avoid_text = _stringify_list(avoid_parts)
    if must_keep_text:
        lines.append(f"Must keep: {must_keep_text}")
    if avoid_text:
        lines.append(f"Avoid: {avoid_text}")

    lines.append(
        "Maintain character identity, face, hairstyle, outfit, body proportion, and spatial readability for later subtitle and edit timing."
    )
    lines.append(f"Negative prompt: {negative_prompt}")

    return "\n".join(line for line in lines if str(line).strip()).strip()


def _build_visual_reference_cue_suffix(
    character_asset_keys: list[str],
    scene_asset_key: str | None,
    prop_asset_keys: list[str],
) -> str | None:
    cue_parts: list[str] = []
    if character_asset_keys:
        cue_parts.append(f"角色 {', '.join(character_asset_keys)}")
    if scene_asset_key:
        cue_parts.append(f"场景 {scene_asset_key}")
    if prop_asset_keys:
        cue_parts.append(f"道具 {', '.join(prop_asset_keys)}")
    if not cue_parts:
        return None
    return f"参考素材: {' / '.join(cue_parts)}"


def _get_missing_visual_asset_refs(project: Project, shot_metadata: dict) -> list[str]:
    lookup = _build_visual_asset_lookup(project)
    missing: list[str] = []
    for asset_key in shot_metadata.get("character_asset_keys") or []:
        key = str(asset_key).strip()
        if key and key not in lookup["characters"]:
            missing.append(f"missing_character_asset:{key}")
    scene_asset_key = str(shot_metadata.get("scene_asset_key") or "").strip()
    if scene_asset_key and scene_asset_key not in lookup["scenes"]:
        missing.append(f"missing_scene_asset:{scene_asset_key}")
    for asset_key in shot_metadata.get("prop_asset_keys") or []:
        key = str(asset_key).strip()
        if key and key not in lookup["props"]:
            missing.append(f"missing_prop_asset:{key}")
    return missing


def _build_copy_ready_video_prompt(
    *,
    image_asset_url: str | None,
    duration: int | float | None,
    base_video_prompt: str,
    core_action: str,
    character: str | None,
    location: str | None,
    emotion: str | None,
    camera: str | None,
    dialogue: str | None,
    shot_type: str | None,
    camera_motion: str | None,
    subject_motion: str | None,
    transition: str | None,
    subtitle_text: str | None,
    sfx: str | None,
    editing_notes: str | None,
    negative_prompt: str,
) -> str:
    parts = [
        "Use uploaded image as first frame." if image_asset_url else "Image asset is missing; upload image first before video generation.",
        f"Image asset URL: {image_asset_url}" if image_asset_url else None,
        f"Duration: {duration} seconds." if duration is not None else "Duration is missing and must be confirmed before generation.",
        "Format: 9:16 vertical anime-comic video.",
        f"Base video prompt: {base_video_prompt}",
        f"Core action: {core_action}",
        f"Character: {character}" if character else None,
        f"Location: {location}" if location else None,
        f"Emotion: {emotion}" if emotion else None,
        f"Camera: {camera}" if camera else None,
        f"Dialogue cue: {dialogue}" if dialogue else None,
        f"Shot type: {shot_type}" if shot_type else None,
        f"Camera motion: {camera_motion}" if camera_motion else None,
        f"Subject motion: {subject_motion}" if subject_motion else None,
        f"Transition: {transition}" if transition else None,
        f"Subtitle cue: {subtitle_text}" if subtitle_text else None,
        f"Sound effect cue: {sfx}" if sfx else None,
        f"Editing notes: {editing_notes}" if editing_notes else None,
        "Keep character identity, face, hairstyle, and outfit consistent.",
        f"Negative prompt: {negative_prompt}",
    ]
    return "\n".join(part for part in parts if part).strip()


def export_project_image_prompts(db: Session, project_id: int) -> ProjectImagePromptExport:
    project = get_project_or_404(db, project_id)
    style = _extract_project_style(project)
    character_reference_url = _get_first_confirmed_character_reference(db, project_id)

    tasks = (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.modality == AssetModality.IMAGE)
        .order_by(AssetTask.id.asc())
        .all()
    )

    items: list[ProjectImagePromptItem] = []
    for task in tasks:
        shot = task.shot
        shot_metadata = shot.metadata_json or {}
        visual_asset_refs = _resolve_visual_asset_refs(project, shot_metadata)
        missing_visual_asset_refs = _get_missing_visual_asset_refs(project, shot_metadata)
        asset = _get_preferred_task_asset(db, asset_task_id=task.id, modality=AssetModality.IMAGE)

        asset_input_payload = {}
        if asset is not None:
            asset_input_payload = (asset.metadata_json or {}).get("input_payload") or {}

        base_prompt = (
            asset_input_payload.get("base_prompt")
            or task.input_payload.get("base_prompt")
            or shot.image_prompt
        )
        storyboard_context = (
            asset_input_payload.get("storyboard_context")
            or {
                "source_shot_id": shot_metadata.get("source_shot_id"),
                "duration_sec": shot_metadata.get("duration_sec"),
                "character": shot_metadata.get("character"),
                "location": shot_metadata.get("location"),
                "emotion": shot_metadata.get("emotion"),
                "camera": shot_metadata.get("camera"),
                "dialogue": shot_metadata.get("dialogue"),
            }
        )
        clean_character_reference_url = _clean_reference_url(character_reference_url)
        enhanced_prompt = (
            asset_input_payload.get("enhanced_prompt")
            or task.input_payload.get("enhanced_prompt")
            or build_image_enhanced_prompt(
                base_prompt=shot.image_prompt,
                visual_style=style,
                character_reference_url=clean_character_reference_url,
                storyboard_context=storyboard_context,
            )
        )
        enhanced_prompt = _strip_mock_reference_urls(enhanced_prompt)
        copy_ready_prompt = _build_production_grade_image_prompt(
            enhanced_prompt=enhanced_prompt,
            negative_prompt=MANUAL_IMAGE_NEGATIVE_PROMPT,
            shot_metadata=shot_metadata,
            visual_asset_refs=visual_asset_refs,
        )

        items.append(
            ProjectImagePromptItem(
                asset_task_id=task.id,
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                emotion=shot_metadata.get("emotion"),
                camera=shot_metadata.get("camera"),
                dialogue=shot_metadata.get("dialogue"),
                shot_type=shot_metadata.get("shot_type"),
                camera_motion=shot_metadata.get("camera_motion"),
                subject_motion=shot_metadata.get("subject_motion"),
                transition=shot_metadata.get("transition"),
                subtitle_text=shot_metadata.get("subtitle_text"),
                sfx=shot_metadata.get("sfx"),
                editing_notes=shot_metadata.get("editing_notes"),
                shot_purpose=shot_metadata.get("shot_purpose"),
                conflict_beat=shot_metadata.get("conflict_beat"),
                emotion_shift=shot_metadata.get("emotion_shift"),
                visual_focus=shot_metadata.get("visual_focus"),
                image_prompt_intent=shot_metadata.get("image_prompt_intent"),
                storyboard_clarity=shot_metadata.get("storyboard_clarity"),
                pacing_note=shot_metadata.get("pacing_note"),
                audience_feeling=shot_metadata.get("audience_feeling"),
                reference_priority=shot_metadata.get("reference_priority"),
                composition=shot_metadata.get("composition"),
                lighting=shot_metadata.get("lighting"),
                subtitle_position=shot_metadata.get("subtitle_position"),
                negative_constraints=shot_metadata.get("negative_constraints") if isinstance(shot_metadata.get("negative_constraints"), list) else [],
                character_asset_keys=shot_metadata.get("character_asset_keys") if isinstance(shot_metadata.get("character_asset_keys"), list) else [],
                scene_asset_key=shot_metadata.get("scene_asset_key"),
                prop_asset_keys=shot_metadata.get("prop_asset_keys") if isinstance(shot_metadata.get("prop_asset_keys"), list) else [],
                visual_asset_refs=visual_asset_refs,
                missing_visual_asset_refs=missing_visual_asset_refs,
                base_prompt=base_prompt,
                enhanced_prompt=enhanced_prompt,
                negative_prompt=MANUAL_IMAGE_NEGATIVE_PROMPT,
                copy_ready_prompt=copy_ready_prompt,
            )
        )

    return ProjectImagePromptExport(
        project_id=project_id,
        items_count=len(items),
        items=items,
    )


def export_project_video_prompts(db: Session, project_id: int) -> ProjectVideoPromptExport:
    project = get_project_or_404(db, project_id)

    tasks = (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.modality == AssetModality.VIDEO)
        .order_by(AssetTask.id.asc())
        .all()
    )

    items: list[ProjectVideoPromptItem] = []
    for task in tasks:
        shot = task.shot
        shot_metadata = shot.metadata_json or {}
        visual_asset_refs = _resolve_visual_asset_refs(project, shot_metadata)
        image_asset = _get_preferred_shot_asset(db, shot_id=shot.id, modality=AssetModality.IMAGE)
        image_asset_url = image_asset.file_url if image_asset is not None else None
        duration = _extract_video_duration(task, shot)
        blocking_issues: list[str] = []
        if not image_asset_url:
            blocking_issues.append("missing_image_asset")

        base_video_prompt = shot.video_prompt
        copy_ready_video_prompt = _build_copy_ready_video_prompt(
            image_asset_url=image_asset_url,
            duration=duration,
            base_video_prompt=base_video_prompt,
            core_action=shot.core_action,
            character=shot_metadata.get("character"),
            location=shot_metadata.get("location"),
            emotion=shot_metadata.get("emotion"),
            camera=shot_metadata.get("camera"),
            dialogue=shot_metadata.get("dialogue"),
            shot_type=shot_metadata.get("shot_type"),
            camera_motion=shot_metadata.get("camera_motion"),
            subject_motion=shot_metadata.get("subject_motion"),
            transition=shot_metadata.get("transition"),
            subtitle_text=shot_metadata.get("subtitle_text"),
            sfx=shot_metadata.get("sfx"),
            editing_notes=shot_metadata.get("editing_notes"),
            negative_prompt=MANUAL_VIDEO_NEGATIVE_PROMPT,
        )

        items.append(
            ProjectVideoPromptItem(
                asset_task_id=task.id,
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                image_asset_url=image_asset_url,
                duration=duration,
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                emotion=shot_metadata.get("emotion"),
                camera=shot_metadata.get("camera"),
                dialogue=shot_metadata.get("dialogue"),
                shot_type=shot_metadata.get("shot_type"),
                camera_motion=shot_metadata.get("camera_motion"),
                subject_motion=shot_metadata.get("subject_motion"),
                transition=shot_metadata.get("transition"),
                subtitle_text=shot_metadata.get("subtitle_text"),
                sfx=shot_metadata.get("sfx"),
                editing_notes=shot_metadata.get("editing_notes"),
                shot_purpose=shot_metadata.get("shot_purpose"),
                conflict_beat=shot_metadata.get("conflict_beat"),
                emotion_shift=shot_metadata.get("emotion_shift"),
                visual_focus=shot_metadata.get("visual_focus"),
                image_prompt_intent=shot_metadata.get("image_prompt_intent"),
                storyboard_clarity=shot_metadata.get("storyboard_clarity"),
                pacing_note=shot_metadata.get("pacing_note"),
                audience_feeling=shot_metadata.get("audience_feeling"),
                reference_priority=shot_metadata.get("reference_priority"),
                composition=shot_metadata.get("composition"),
                lighting=shot_metadata.get("lighting"),
                subtitle_position=shot_metadata.get("subtitle_position"),
                negative_constraints=shot_metadata.get("negative_constraints") if isinstance(shot_metadata.get("negative_constraints"), list) else [],
                character_asset_keys=shot_metadata.get("character_asset_keys") if isinstance(shot_metadata.get("character_asset_keys"), list) else [],
                scene_asset_key=shot_metadata.get("scene_asset_key"),
                prop_asset_keys=shot_metadata.get("prop_asset_keys") if isinstance(shot_metadata.get("prop_asset_keys"), list) else [],
                visual_asset_refs=visual_asset_refs,
                base_video_prompt=base_video_prompt,
                copy_ready_video_prompt=copy_ready_video_prompt,
                negative_prompt=MANUAL_VIDEO_NEGATIVE_PROMPT,
                ready_for_video_prompt=bool(image_asset_url and duration is not None),
                blocking_issues=blocking_issues,
            )
        )

    return ProjectVideoPromptExport(
        project_id=project_id,
        items_count=len(items),
        items=items,
    )


def get_project_manual_image_progress(db: Session, project_id: int) -> ProjectManualImageProgress:
    get_project_or_404(db, project_id)

    tasks = (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.modality == AssetModality.IMAGE)
        .order_by(AssetTask.id.asc())
        .all()
    )

    items: list[ProjectManualImageProgressItem] = []
    completed_image_tasks_count = 0
    manual_uploaded_count = 0

    for task in tasks:
        shot = task.shot
        shot_metadata = shot.metadata_json or {}
        asset = _get_preferred_task_asset(db, asset_task_id=task.id, modality=AssetModality.IMAGE)
        has_asset = asset is not None and bool(asset.file_url)
        manual_upload = bool((asset.metadata_json or {}).get("manual_upload")) if asset is not None else False
        if has_asset:
            completed_image_tasks_count += 1
        if manual_upload:
            manual_uploaded_count += 1

        items.append(
            ProjectManualImageProgressItem(
                asset_task_id=task.id,
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                status=task.status.value,
                has_asset=has_asset,
                asset_url=asset.file_url if asset is not None else None,
                manual_upload=manual_upload,
                needs_manual_image=not has_asset,
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                emotion=shot_metadata.get("emotion"),
            )
        )

    image_tasks_count = len(items)
    missing_image_tasks_count = image_tasks_count - completed_image_tasks_count
    next_action = "manual_images_completed" if image_tasks_count > 0 and missing_image_tasks_count == 0 else "continue_manual_image_generation"

    return ProjectManualImageProgress(
        project_id=project_id,
        image_tasks_count=image_tasks_count,
        completed_image_tasks_count=completed_image_tasks_count,
        missing_image_tasks_count=missing_image_tasks_count,
        manual_uploaded_count=manual_uploaded_count,
        items=items,
        next_action=next_action,
    )


def _extract_video_duration(task: AssetTask, shot: Shot) -> int | float | None:
    shot_metadata = shot.metadata_json or {}
    return (
        shot_metadata.get("duration_sec")
        or (task.input_payload or {}).get("duration")
        or (task.input_payload or {}).get("duration_sec")
    )


def _has_basic_editing_fields(shot_metadata: dict) -> bool:
    return any(
        shot_metadata.get(field_name)
        for field_name in [
            "shot_type",
            "camera_motion",
            "subject_motion",
            "transition",
            "subtitle_text",
            "sfx",
            "editing_notes",
        ]
    )


def get_project_video_readiness(db: Session, project_id: int) -> ProjectVideoReadiness:
    get_project_or_404(db, project_id)

    tasks = (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.modality == AssetModality.VIDEO)
        .order_by(AssetTask.id.asc())
        .all()
    )

    items: list[ProjectVideoReadinessItem] = []
    ready_video_tasks_count = 0
    blocked_video_tasks_count = 0

    for task in tasks:
        shot = task.shot
        shot_metadata = shot.metadata_json or {}
        image_asset = _get_preferred_shot_asset(db, shot_id=shot.id, modality=AssetModality.IMAGE)
        has_image_asset = image_asset is not None and bool(image_asset.file_url)
        duration = _extract_video_duration(task, shot)
        has_duration = duration is not None

        blocking_issues: list[str] = []
        if not has_image_asset:
            blocking_issues.append("missing_image_asset")
        if not has_duration:
            blocking_issues.append("missing_duration")

        ready_for_video = has_image_asset and has_duration
        if ready_for_video:
            ready_video_tasks_count += 1
        else:
            blocked_video_tasks_count += 1

        items.append(
            ProjectVideoReadinessItem(
                asset_task_id=task.id,
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                status=task.status.value,
                has_image_asset=has_image_asset,
                image_asset_url=image_asset.file_url if image_asset is not None else None,
                has_duration=has_duration,
                duration=duration,
                ready_for_video=ready_for_video,
                blocking_issues=blocking_issues,
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                emotion=shot_metadata.get("emotion"),
                video_prompt=shot.video_prompt,
                shot_type=shot_metadata.get("shot_type"),
                camera_motion=shot_metadata.get("camera_motion"),
                subject_motion=shot_metadata.get("subject_motion"),
                transition=shot_metadata.get("transition"),
                subtitle_text=shot_metadata.get("subtitle_text"),
                sfx=shot_metadata.get("sfx"),
                editing_notes=shot_metadata.get("editing_notes"),
            )
        )

    if blocked_video_tasks_count == 0:
        next_action = "ready_for_video_generation"
    elif any("missing_image_asset" in item.blocking_issues for item in items):
        next_action = "continue_manual_image_generation"
    else:
        next_action = "fix_video_inputs"

    return ProjectVideoReadiness(
        project_id=project_id,
        video_tasks_count=len(items),
        ready_video_tasks_count=ready_video_tasks_count,
        blocked_video_tasks_count=blocked_video_tasks_count,
        items=items,
        next_action=next_action,
    )


def get_project_manual_video_progress(db: Session, project_id: int) -> ProjectManualVideoProgress:
    get_project_or_404(db, project_id)

    tasks = (
        db.query(AssetTask)
        .join(Shot, AssetTask.shot_id == Shot.id)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id, AssetTask.modality == AssetModality.VIDEO)
        .order_by(AssetTask.id.asc())
        .all()
    )

    items: list[ProjectManualVideoProgressItem] = []
    completed_video_tasks_count = 0
    manual_uploaded_count = 0

    for task in tasks:
        shot = task.shot
        shot_metadata = shot.metadata_json or {}
        asset = _get_preferred_task_asset(db, asset_task_id=task.id, modality=AssetModality.VIDEO)
        has_asset = asset is not None and bool(asset.file_url)
        manual_upload = bool((asset.metadata_json or {}).get("manual_upload")) if asset is not None else False
        duration = _extract_video_duration(task, shot)
        if has_asset:
            completed_video_tasks_count += 1
        if manual_upload:
            manual_uploaded_count += 1

        items.append(
            ProjectManualVideoProgressItem(
                asset_task_id=task.id,
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                status=task.status.value,
                has_asset=has_asset,
                asset_url=asset.file_url if asset is not None else None,
                manual_upload=manual_upload,
                needs_manual_video=not has_asset,
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                emotion=shot_metadata.get("emotion"),
                duration=duration,
            )
        )

    video_tasks_count = len(items)
    missing_video_tasks_count = video_tasks_count - completed_video_tasks_count
    next_action = "manual_videos_completed" if video_tasks_count > 0 and missing_video_tasks_count == 0 else "continue_manual_video_generation"

    return ProjectManualVideoProgress(
        project_id=project_id,
        video_tasks_count=video_tasks_count,
        completed_video_tasks_count=completed_video_tasks_count,
        missing_video_tasks_count=missing_video_tasks_count,
        manual_uploaded_count=manual_uploaded_count,
        items=items,
        next_action=next_action,
    )


def get_project_manual_production_summary(db: Session, project_id: int) -> ProjectManualProductionSummary:
    get_project_or_404(db, project_id)

    image = get_project_manual_image_progress(db, project_id)
    video_readiness = get_project_video_readiness(db, project_id)
    video = get_project_manual_video_progress(db, project_id)

    blocking_summary = ManualProductionBlockingSummary(
        missing_image_tasks_count=image.missing_image_tasks_count,
        blocked_video_tasks_count=video_readiness.blocked_video_tasks_count,
        missing_video_tasks_count=video.missing_video_tasks_count,
    )

    recommended_steps: list[str] = []
    if image.missing_image_tasks_count > 0:
        stage = "manual_image_generation"
        next_action = "continue_manual_image_generation"
        recommended_steps = [
            "Continue generating missing images from image-prompts.",
            "Upload generated images with manual-asset.",
            "Run video-readiness again before manual video generation.",
        ]
    elif video_readiness.blocked_video_tasks_count > 0:
        stage = "video_input_fixing"
        next_action = "fix_video_inputs"
        recommended_steps = [
            "Review blocked video tasks in video-readiness.",
            "Fix missing image assets or duration before generating video.",
            "Re-run video-readiness until all video tasks are ready.",
        ]
    elif video.missing_video_tasks_count > 0:
        stage = "manual_video_generation"
        next_action = "continue_manual_video_generation"
        recommended_steps = [
            "Generate missing videos with Seedance or another manual video tool.",
            "Upload generated videos with manual-video-asset.",
            "Check manual-video-progress until every video task has an asset.",
        ]
    else:
        stage = "manual_production_completed"
        next_action = "ready_for_publish_or_composition"
        recommended_steps = [
            "Review the completed manual production assets.",
            "Proceed to composition, publishing, or final QA.",
        ]

    return ProjectManualProductionSummary(
        project_id=project_id,
        stage=stage,
        next_action=next_action,
        image=image,
        video_readiness=video_readiness,
        video=video,
        blocking_summary=blocking_summary,
        recommended_steps=recommended_steps,
    )


def get_project_publish_readiness(db: Session, project_id: int) -> ProjectPublishReadiness:
    get_project_or_404(db, project_id)

    manual_production = get_project_manual_production_summary(db, project_id)
    project_summary = get_project_summary(db, project_id)

    checks = PublishReadinessChecks(
        manual_production_completed=manual_production.stage == "manual_production_completed",
        all_image_tasks_have_assets=manual_production.image.missing_image_tasks_count == 0,
        all_video_tasks_have_assets=manual_production.video.missing_video_tasks_count == 0,
        has_failed_tasks=project_summary.failed_tasks_count > 0,
        has_needs_human_revision_tasks=project_summary.needs_human_revision_count > 0,
        has_publish_record=project_summary.publish_records_count > 0,
    )

    summary = PublishReadinessSummary(
        image_tasks_count=manual_production.image.image_tasks_count,
        completed_image_tasks_count=manual_production.image.completed_image_tasks_count,
        video_tasks_count=manual_production.video.video_tasks_count,
        completed_video_tasks_count=manual_production.video.completed_video_tasks_count,
        publish_records_count=project_summary.publish_records_count,
    )

    blocking_issues: list[str] = []
    warnings: list[str] = []

    if not checks.all_image_tasks_have_assets:
        stage = "manual_image_generation"
        next_action = "continue_manual_image_generation"
        ready_for_publish = False
        blocking_issues.append("missing_image_assets")
    elif not checks.all_video_tasks_have_assets:
        stage = "manual_video_generation"
        next_action = "continue_manual_video_generation"
        ready_for_publish = False
        blocking_issues.append("missing_video_assets")
    elif checks.has_failed_tasks:
        stage = "review_failed_tasks"
        next_action = "review_failed_tasks"
        ready_for_publish = False
        blocking_issues.append("failed_tasks_exist")
    elif checks.has_needs_human_revision_tasks:
        stage = "review_human_revision_tasks"
        next_action = "review_human_revision_tasks"
        ready_for_publish = False
        blocking_issues.append("needs_human_revision_tasks_exist")
    elif checks.has_publish_record:
        stage = "published"
        next_action = "completed"
        ready_for_publish = True
    else:
        stage = "ready_for_publish"
        next_action = "create_publish_record"
        ready_for_publish = True
        warnings.append("No publish record exists yet.")

    return ProjectPublishReadiness(
        project_id=project_id,
        ready_for_publish=ready_for_publish,
        stage=stage,
        next_action=next_action,
        checks=checks,
        blocking_issues=blocking_issues,
        warnings=warnings,
        summary=summary,
    )


def get_project_manual_final_checklist(db: Session, project_id: int) -> ProjectManualFinalChecklist:
    project = get_project_or_404(db, project_id)
    manual_production = get_project_manual_production_summary(db, project_id)
    publish_readiness = get_project_publish_readiness(db, project_id)

    checks = ManualFinalChecklistChecks(
        images_completed=manual_production.image.missing_image_tasks_count == 0,
        videos_completed=manual_production.video.missing_video_tasks_count == 0,
        video_inputs_ready=manual_production.video_readiness.blocked_video_tasks_count == 0,
        no_failed_tasks="failed_tasks_exist" not in publish_readiness.blocking_issues,
        no_human_revision_tasks="needs_human_revision_tasks_exist" not in publish_readiness.blocking_issues,
        publish_record_exists=publish_readiness.checks.has_publish_record,
    )

    blocking_issues: list[str] = []
    warnings = list(publish_readiness.warnings)
    recommended_steps: list[str] = []

    if manual_production.stage != "manual_production_completed":
        ready_for_delivery = False
        next_action = manual_production.next_action
        blocking_issues.append("manual_production_not_completed")
        blocking_issues.extend(publish_readiness.blocking_issues)
        recommended_steps = list(manual_production.recommended_steps)
    elif not publish_readiness.ready_for_publish:
        ready_for_delivery = False
        next_action = publish_readiness.next_action
        blocking_issues.extend(publish_readiness.blocking_issues)
        if publish_readiness.stage == "review_failed_tasks":
            recommended_steps = [
                "Review failed tasks before moving into delivery.",
                "Re-run or manually fix the failed tasks.",
            ]
        elif publish_readiness.stage == "review_human_revision_tasks":
            recommended_steps = [
                "Review tasks marked as needs_human_revision.",
                "Fix the blocking tasks before publish or composition.",
            ]
        else:
            recommended_steps = list(manual_production.recommended_steps)
    elif publish_readiness.checks.has_publish_record:
        ready_for_delivery = True
        next_action = "completed"
        recommended_steps = [
            "Publish record already exists.",
            "Proceed to final delivery, composition, or archive workflow.",
        ]
    else:
        ready_for_delivery = True
        next_action = "create_publish_record"
        recommended_steps = [
            "Create publish record or proceed to final composition/export.",
        ]

    # De-duplicate while preserving order.
    seen: set[str] = set()
    deduped_blocking_issues: list[str] = []
    for item in blocking_issues:
        if item and item not in seen:
            seen.add(item)
            deduped_blocking_issues.append(item)

    return ProjectManualFinalChecklist(
        project_id=project_id,
        ready_for_delivery=ready_for_delivery,
        production_stage=manual_production.stage,
        publish_stage=publish_readiness.stage,
        project_status=project.status,
        has_publish_record=publish_readiness.checks.has_publish_record,
        next_action=next_action,
        checks=checks,
        blocking_issues=deduped_blocking_issues,
        warnings=warnings,
        summary=publish_readiness.summary,
        recommended_steps=recommended_steps,
    )


def get_project_editing_shot_board(db: Session, project_id: int) -> ProjectEditingShotBoard:
    project = get_project_or_404(db, project_id)

    shots = (
        db.query(Shot)
        .join(Scene, Shot.scene_id == Scene.id)
        .join(Episode, Scene.episode_id == Episode.id)
        .filter(Episode.project_id == project_id)
        .order_by(Shot.id.asc())
        .all()
    )

    items: list[EditingShotBoardItem] = []
    ready_shots_count = 0
    blocked_shots_count = 0
    missing_image_count = 0
    missing_editing_fields_count = 0

    for shot in shots:
        shot_metadata = shot.metadata_json or {}
        visual_asset_refs = _resolve_visual_asset_refs(project, shot_metadata)
        image_asset = _get_preferred_shot_asset(db, shot_id=shot.id, modality=AssetModality.IMAGE)
        image_asset_url = image_asset.file_url if image_asset is not None else None
        has_image_asset = bool(image_asset_url)
        duration = shot_metadata.get("duration_sec")

        blocking_issues: list[str] = []
        if not has_image_asset:
            blocking_issues.append("missing_image_asset")
            missing_image_count += 1

        has_editing_fields = _has_basic_editing_fields(shot_metadata)
        if not has_editing_fields:
            blocking_issues.append("missing_editing_fields")
            missing_editing_fields_count += 1

        ready_for_editing = has_image_asset and has_editing_fields
        if ready_for_editing:
            ready_shots_count += 1
        else:
            blocked_shots_count += 1

        items.append(
            EditingShotBoardItem(
                internal_shot_id=shot.id,
                source_shot_id=shot_metadata.get("source_shot_id"),
                character=shot_metadata.get("character"),
                location=shot_metadata.get("location"),
                emotion=shot_metadata.get("emotion"),
                duration=duration,
                image_asset_url=image_asset_url,
                has_image_asset=has_image_asset,
                shot_type=shot_metadata.get("shot_type"),
                camera_motion=shot_metadata.get("camera_motion"),
                subject_motion=shot_metadata.get("subject_motion"),
                transition=shot_metadata.get("transition"),
                subtitle_text=shot_metadata.get("subtitle_text"),
                sfx=shot_metadata.get("sfx"),
                editing_notes=shot_metadata.get("editing_notes"),
                shot_purpose=shot_metadata.get("shot_purpose"),
                conflict_beat=shot_metadata.get("conflict_beat"),
                emotion_shift=shot_metadata.get("emotion_shift"),
                visual_focus=shot_metadata.get("visual_focus"),
                image_prompt_intent=shot_metadata.get("image_prompt_intent"),
                storyboard_clarity=shot_metadata.get("storyboard_clarity"),
                pacing_note=shot_metadata.get("pacing_note"),
                audience_feeling=shot_metadata.get("audience_feeling"),
                reference_priority=shot_metadata.get("reference_priority"),
                composition=shot_metadata.get("composition"),
                lighting=shot_metadata.get("lighting"),
                subtitle_position=shot_metadata.get("subtitle_position"),
                negative_constraints=shot_metadata.get("negative_constraints") if isinstance(shot_metadata.get("negative_constraints"), list) else [],
                character_asset_keys=shot_metadata.get("character_asset_keys") if isinstance(shot_metadata.get("character_asset_keys"), list) else [],
                scene_asset_key=shot_metadata.get("scene_asset_key"),
                prop_asset_keys=shot_metadata.get("prop_asset_keys") if isinstance(shot_metadata.get("prop_asset_keys"), list) else [],
                visual_asset_refs=visual_asset_refs,
                ready_for_editing=ready_for_editing,
                blocking_issues=blocking_issues,
            )
        )

    if missing_image_count > 0:
        next_action = "continue_image_generation"
    elif missing_editing_fields_count > 0:
        next_action = "review_editing_fields"
    else:
        next_action = "ready_for_manual_editing"

    return ProjectEditingShotBoard(
        project_id=project_id,
        shots_count=len(items),
        ready_shots_count=ready_shots_count,
        blocked_shots_count=blocked_shots_count,
        items=items,
        next_action=next_action,
    )


def get_project_editing_timeline(db: Session, project_id: int) -> ProjectEditingTimeline:
    shot_board = get_project_editing_shot_board(db, project_id)

    timeline_items: list[EditingTimelineItem] = []
    current_time: int | float = 0
    blocking_issue_set: set[str] = set()
    ready_for_timeline = True

    for order, shot_item in enumerate(shot_board.items, start=1):
        warnings: list[str] = []
        duration = shot_item.duration
        if duration in (None, ""):
            duration = 3
            warnings.append("duration_defaulted")

        start_time = current_time
        end_time = current_time + duration
        current_time = end_time

        item_blocking_issues = list(shot_item.blocking_issues)
        if item_blocking_issues:
            ready_for_timeline = False
            for issue in item_blocking_issues:
                blocking_issue_set.add(issue)

        timeline_items.append(
            EditingTimelineItem(
                order=order,
                internal_shot_id=shot_item.internal_shot_id,
                source_shot_id=shot_item.source_shot_id,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                image_asset_url=shot_item.image_asset_url,
                subtitle_text=shot_item.subtitle_text,
                sfx=shot_item.sfx,
                camera_motion=shot_item.camera_motion,
                subject_motion=shot_item.subject_motion,
                transition=shot_item.transition,
                editing_notes=shot_item.editing_notes,
                shot_purpose=shot_item.shot_purpose,
                visual_focus=shot_item.visual_focus,
                lighting=shot_item.lighting,
                subtitle_position=shot_item.subtitle_position,
                ready_for_editing=shot_item.ready_for_editing,
                blocking_issues=item_blocking_issues,
                warnings=warnings,
            )
        )

    if not ready_for_timeline:
        if "missing_image_asset" in blocking_issue_set:
            next_action = "continue_image_generation"
        else:
            next_action = "review_editing_fields"
    else:
        next_action = "ready_for_manual_timeline_editing"

    return ProjectEditingTimeline(
        project_id=project_id,
        shots_count=len(timeline_items),
        total_duration=current_time,
        ready_for_timeline=ready_for_timeline,
        items=timeline_items,
        blocking_issues=sorted(blocking_issue_set),
        next_action=next_action,
    )


def get_project_editing_cue_sheet(db: Session, project_id: int) -> ProjectEditingCueSheet:
    timeline = get_project_editing_timeline(db, project_id)

    items: list[EditingCueSheetItem] = []
    blocking_issue_set: set[str] = set(timeline.blocking_issues)
    ready_for_cue_sheet = True
    cue_lines: list[str] = []

    for item in timeline.items:
        item_warnings = list(item.warnings)
        item_blocking_issues = list(item.blocking_issues)

        if not item.subtitle_text:
            item_warnings.append("missing_subtitle_text")
        if not item.sfx:
            item_warnings.append("missing_sfx")
        if not item.camera_motion:
            item_warnings.append("missing_camera_motion")
        if not item.subject_motion:
            item_warnings.append("missing_subject_motion")
        if not item.transition:
            item_warnings.append("missing_transition")
        if not item.editing_notes:
            item_warnings.append("missing_editing_notes")

        if item_blocking_issues:
            ready_for_cue_sheet = False
            for issue in item_blocking_issues:
                blocking_issue_set.add(issue)

        time_range = f"{float(item.start_time):.1f}s-{float(item.end_time):.1f}s"
        cue_segments = [
            item.source_shot_id or f"SHOT-{item.internal_shot_id}",
            time_range,
            f"图片: {item.image_asset_url or '[missing image]'}",
            f"字幕: {item.subtitle_text or '[none]'}",
            f"音效: {item.sfx or '[none]'}",
            f"镜头: {item.camera_motion or '[none]'}",
            f"人物微动: {item.subject_motion or '[none]'}",
            f"转场: {item.transition or '[none]'}",
            f"剧情功能: {item.shot_purpose or '[none]'}",
            f"视觉焦点: {item.visual_focus or '[none]'}",
            f"打光: {item.lighting or '[none]'}",
            f"备注: {item.editing_notes or '[none]'}",
        ]
        cue_line = " | ".join(cue_segments)
        cue_lines.append(cue_line)

        items.append(
            EditingCueSheetItem(
                order=item.order,
                source_shot_id=item.source_shot_id,
                time_range=time_range,
                duration=item.duration,
                image_asset_url=item.image_asset_url,
                subtitle_text=item.subtitle_text,
                sfx=item.sfx,
                camera_motion=item.camera_motion,
                subject_motion=item.subject_motion,
                transition=item.transition,
                editing_notes=item.editing_notes,
                shot_purpose=item.shot_purpose,
                visual_focus=item.visual_focus,
                lighting=item.lighting,
                subtitle_position=item.subtitle_position,
                cue_line=cue_line,
                ready_for_editing=item.ready_for_editing,
                blocking_issues=item_blocking_issues,
                warnings=item_warnings,
            )
        )

    next_action = "ready_for_manual_editing" if ready_for_cue_sheet else "fix_editing_inputs"

    return ProjectEditingCueSheet(
        project_id=project_id,
        shots_count=timeline.shots_count,
        total_duration=timeline.total_duration,
        ready_for_cue_sheet=ready_for_cue_sheet,
        items=items,
        plain_text="\n".join(cue_lines),
        blocking_issues=sorted(blocking_issue_set),
        next_action=next_action,
    )
