from sqlalchemy import inspect

from app.core.status_machine import ASSET_TASK_TRANSITIONS, PROJECT_TRANSITIONS, SHOT_TRANSITIONS, ensure_transition
from app.models.asset_task import AssetTask
from app.models.character import Character
from app.models.episode import Episode
from app.models.enums import AssetModality, AssetTaskStatus, ProjectStatus, ShotStatus
from app.models.project import Project
from app.models.scene import Scene
from app.models.shot import Shot
from app.schemas.asset_task import AssetTaskCreate
from app.schemas.shot import ShotCreate


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["docs"] == "/docs"


def test_database_tables_exist(db_session):
    table_names = set(inspect(db_session.bind).get_table_names())
    assert {
        "projects",
        "episodes",
        "characters",
        "scenes",
        "shots",
        "asset_tasks",
        "assets",
        "reviews",
        "publish_records",
    }.issubset(table_names)


def test_project_model_defaults(db_session):
    project = Project(name="测试项目")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    assert project.status == ProjectStatus.DRAFT
    assert project.target_platforms == []
    assert project.tags == []


def test_shot_schema_requires_all_prompts():
    shot = ShotCreate(
        scene_id=1,
        shot_number=1,
        framing="medium",
        core_action="角色推门进入",
        image_prompt="图片提示词",
        video_prompt="视频提示词",
        voice_prompt="配音提示词",
        bgm_prompt="BGM 提示词",
    )
    assert shot.status == ShotStatus.PROMPT_READY


def test_shot_core_action_rejects_multiple_actions():
    try:
        ShotCreate(
            scene_id=1,
            shot_number=1,
            framing="medium",
            core_action="角色推门进入，然后转身挥手",
            image_prompt="图片提示词",
            video_prompt="视频提示词",
            voice_prompt="配音提示词",
            bgm_prompt="BGM 提示词",
        )
    except ValueError as exc:
        assert "one core action" in str(exc)
    else:
        raise AssertionError("Expected validation error for multiple actions")


def test_asset_task_defaults(db_session):
    project = Project(name="项目A")
    episode = Episode(project=project, title="EP1", episode_number=1)
    scene = Scene(episode=episode, scene_number=1, title="场景1", description="描述")
    shot = Shot(
        scene=scene,
        shot_number=1,
        framing="close-up",
        core_action="角色抬头",
        image_prompt="图片",
        video_prompt="视频",
        voice_prompt="配音",
        bgm_prompt="音乐",
        status=ShotStatus.PROMPT_READY,
    )
    task = AssetTask(shot=shot, modality=AssetModality.IMAGE, provider_name="mock", input_payload={})
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.status == AssetTaskStatus.QUEUED
    assert task.retry_count == 0
    assert task.max_retries == 3


def test_asset_task_schema_caps_retry_limit():
    task = AssetTaskCreate(shot_id=1, modality=AssetModality.VIDEO)
    assert task.max_retries == 3


def test_status_machine_allows_expected_transitions():
    ensure_transition(ProjectStatus.DRAFT, ProjectStatus.APPROVED, PROJECT_TRANSITIONS, "project")
    ensure_transition(ShotStatus.PROMPT_READY, ShotStatus.GENERATING, SHOT_TRANSITIONS, "shot")
    ensure_transition(AssetTaskStatus.QUEUED, AssetTaskStatus.RUNNING, ASSET_TASK_TRANSITIONS, "asset task")


def test_status_machine_rejects_invalid_transition():
    try:
        ensure_transition(ProjectStatus.DRAFT, ProjectStatus.PUBLISHED, PROJECT_TRANSITIONS, "project")
    except ValueError as exc:
        assert "Invalid project transition" in str(exc)
    else:
        raise AssertionError("Expected invalid project transition to raise")


def test_character_reference_fields_persist(db_session):
    project = Project(name="项目B")
    character = Character(
        project=project,
        name="林夏",
        role_type="lead",
        profile="女主",
        visual_notes="短发职业装",
        voice_style="冷静",
        main_reference_url="https://example.com/reference.png",
        main_reference_confirmed=True,
    )
    db_session.add(character)
    db_session.commit()
    db_session.refresh(character)

    assert character.main_reference_confirmed is True
    assert character.main_reference_url.endswith(".png")
