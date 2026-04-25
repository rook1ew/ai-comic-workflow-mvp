from app.models.shot import Shot
from app.schemas.coze import CozeProjectInitRequest, CozeStoryboardRequest
from app.services.coze_service import coze_project_init, coze_storyboard


def _coze_init_payload():
    return {
        "project_card_json": {
            "project_title": "Urban Hook",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "comic-realism",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast", "dramatic"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "age_vibe": "young professional",
                    "appearance": "sharp face",
                    "hair": "short black hair",
                    "outfit": "office wear",
                    "personality": "calm",
                    "speaking_style": "measured",
                    "must_keep": ["short hair"],
                    "avoid": ["fantasy armor"],
                    "main_reference_confirmed": False,
                }
            ]
        },
    }


def _coze_storyboard_payload():
    return {
        "script_card_json": {
            "opening_hook": "She walks into the wrong meeting room",
            "conflict": "Everyone mistakes her identity",
            "escalation": "She cannot explain in time",
            "turning_point": "The boss asks her to stay",
            "ending_hook": "A promotion rumor starts",
        },
        "storyboard_json": {
            "shots": [
                {
                    "shot_id": "SH01",
                    "duration_sec": 3,
                    "character": "Lin Xia",
                    "location": "Meeting Room",
                    "core_action": "Lin Xia opens the door",
                    "emotion": "nervous",
                    "camera": "medium",
                    "dialogue": "Sorry, wrong room.",
                    "image_prompt": "image prompt 1",
                    "video_prompt": "video prompt 1",
                    "voice_prompt": "voice prompt 1",
                    "bgm_prompt": "bgm prompt 1",
                    "status": "prompt_ready",
                },
                {
                    "shot_id": "SH02",
                    "duration_sec": 2,
                    "character": "Boss",
                    "location": "Meeting Room",
                    "core_action": "Boss looks up",
                    "emotion": "curious",
                    "camera": "close-up",
                    "dialogue": "Wait.",
                    "image_prompt": "image prompt 2",
                    "video_prompt": "video prompt 2",
                    "voice_prompt": "voice prompt 2",
                    "bgm_prompt": "bgm prompt 2",
                    "status": "prompt_ready",
                },
            ]
        },
    }


def test_coze_project_init_creates_project_and_characters(client):
    response = client.post("/coze/project/init", json=_coze_init_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["data"]["project_id"] >= 1
    assert len(body["data"]["character_ids"]) == 1


def test_coze_generate_script_endpoint_works(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    response = client.post(
        f"/coze/project/{project_id}/generate-script",
        json={
            "script_card_json": {
                "opening_hook": "Opening",
                "conflict": "Conflict",
                "escalation": "Escalation",
                "turning_point": "Turning",
                "ending_hook": "Ending",
            }
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["project_id"] == project_id
    assert body["data"]["episode_id"] >= 1
    assert body["next_action"] == "create_storyboard"


def test_generate_script_creates_default_episode_if_missing(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    response = client.post(
        f"/coze/project/{project_id}/generate-script",
        json={"script_card_json": {"opening_hook": "Opening only"}},
    )
    assert response.status_code == 200
    summary = client.get(f"/coze/project/{project_id}/summary").json()
    assert summary["data"]["episodes_count"] == 1


def test_generate_script_uses_unified_response_format(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    response = client.post(
        f"/coze/project/{project_id}/generate-script",
        json={"script_card_json": {"opening_hook": "Opening only"}},
    )
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "OK"
    assert "message" in body
    assert "data" in body
    assert body["next_action"] == "create_storyboard"


def test_coze_project_init_returns_unified_response_format(client):
    response = client.post("/coze/project/init", json=_coze_init_payload())
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "OK"
    assert "message" in body
    assert "data" in body
    assert body["next_action"] == "confirm_character_reference"


def test_confirm_character_reference(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    character_id = init["data"]["character_ids"][0]
    response = client.post(
        f"/characters/{character_id}/confirm-reference",
        json={"main_reference_url": "mock://character/reference.png"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["character_id"] == character_id
    assert body["data"]["main_reference_confirmed"] is True
    assert body["next_action"] == "create_storyboard"


def test_coze_storyboard_creates_episode_scene_shots(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    response = client.post(f"/coze/project/{project_id}/storyboard", json=_coze_storyboard_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["data"]["project_id"] == project_id
    assert body["data"]["episode_id"] >= 1
    assert body["data"]["shots_count"] == 2
    assert body["next_action"] == "create_asset_tasks"


def test_storyboard_import_saves_duration_sec(db_session):
    init_response = coze_project_init(db_session, CozeProjectInitRequest(**_coze_init_payload()))
    project_id = init_response.data["project_id"]
    storyboard_response = coze_storyboard(db_session, project_id, CozeStoryboardRequest(**_coze_storyboard_payload()))

    assert storyboard_response.data["shots_count"] == 2
    shots = db_session.query(Shot).order_by(Shot.shot_number.asc()).all()
    assert len(shots) == 2
    assert shots[0].metadata_json["source_shot_id"] == "SH01"
    assert shots[0].metadata_json["duration_sec"] == 3
    assert shots[1].metadata_json["source_shot_id"] == "SH02"
    assert shots[1].metadata_json["duration_sec"] == 2


def test_coze_create_asset_tasks_requires_confirmed_character(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    client.post(f"/coze/project/{project_id}/storyboard", json=_coze_storyboard_payload())
    response = client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": ["SH01"]})
    assert response.status_code == 400
    assert "confirmed character reference" in response.json()["detail"]


def test_coze_create_asset_tasks_works_after_confirmation(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(f"/coze/project/{project_id}/storyboard", json=_coze_storyboard_payload())
    response = client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": ["SH01"]})
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["created_count"] == 7
    assert body["next_action"] == "run_asset_tasks"


def test_coze_run_asset_tasks(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(f"/coze/project/{project_id}/storyboard", json=_coze_storyboard_payload())
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": ["SH01"]})
    response = client.post(f"/coze/project/{project_id}/run-asset-tasks")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["succeeded_count"] == 7
    assert body["next_action"] == "check_summary"


def test_coze_summary_returns_unified_response_format(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    response = client.get(f"/coze/project/{project_id}/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "OK"
    assert body["data"]["project_id"] == project_id
    assert "next_action" in body


def test_coze_publish_record_endpoint_works(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    response = client.post(
        f"/coze/project/{project_id}/publish-record",
        json={
            "platform": "douyin",
            "title": "Episode 1",
            "published_at": "2026-04-25T10:00:00+08:00",
            "url": "https://example.com/video/1",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["project_id"] == project_id
    assert body["data"]["publish_record_id"] >= 1


def test_publish_record_updates_project_status_to_published(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    response = client.post(
        f"/coze/project/{project_id}/publish-record",
        json={
            "platform": "douyin",
            "title": "Episode 1",
            "published_at": "2026-04-25T10:00:00+08:00",
            "url": "https://example.com/video/1",
        },
    )
    assert response.status_code == 200
    summary = client.get(f"/coze/project/{project_id}/summary").json()
    assert summary["data"]["project_status"] == "published"


def test_coze_publish_record_uses_unified_response_format(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    response = client.post(
        f"/coze/project/{project_id}/publish-record",
        json={
            "platform": "douyin",
            "title": "Episode 1",
            "published_at": "2026-04-25T10:00:00+08:00",
            "url": "https://example.com/video/1",
        },
    )
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "OK"
    assert "message" in body
    assert "data" in body
    assert body["next_action"] == "completed"


def test_summary_next_action_changes_based_on_project_state(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]

    summary = client.get(f"/coze/project/{project_id}/summary").json()
    assert summary["next_action"] == "confirm_character_reference"

    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    summary = client.get(f"/coze/project/{project_id}/summary").json()
    assert summary["next_action"] == "create_storyboard"

    client.post(f"/coze/project/{project_id}/storyboard", json=_coze_storyboard_payload())
    summary = client.get(f"/coze/project/{project_id}/summary").json()
    assert summary["next_action"] == "create_asset_tasks"

    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": ["SH01"]})
    summary = client.get(f"/coze/project/{project_id}/summary").json()
    assert summary["next_action"] == "run_asset_tasks"

    client.post(f"/coze/project/{project_id}/run-asset-tasks")
    summary = client.get(f"/coze/project/{project_id}/summary").json()
    assert summary["next_action"] == "ready_to_publish"

    client.post(
        f"/coze/project/{project_id}/publish-record",
        json={
            "platform": "douyin",
            "title": "Episode 1",
            "published_at": "2026-04-25T10:00:00+08:00",
            "url": "https://example.com/video/1",
        },
    )
    summary = client.get(f"/coze/project/{project_id}/summary").json()
    assert summary["next_action"] == "completed"


def test_summary_returns_completed_after_publish(client):
    init = client.post("/coze/project/init", json=_coze_init_payload()).json()
    project_id = init["data"]["project_id"]
    client.post(
        f"/coze/project/{project_id}/publish-record",
        json={
            "platform": "douyin",
            "title": "Episode 1",
            "published_at": "2026-04-25T10:00:00+08:00",
            "url": "https://example.com/video/1",
        },
    )
    summary = client.get(f"/coze/project/{project_id}/summary").json()
    assert summary["next_action"] == "completed"
    assert summary["data"]["next_action"] == "completed"
