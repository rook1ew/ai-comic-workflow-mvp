from app.models.shot import Shot
from app.schemas.coze import CozeProjectInitRequest, CozeStoryboardRequest
from app.services.coze_service import coze_project_init, coze_storyboard
from app.services.episode_service import get_or_create_default_episode


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
                    "shot_type": "dialogue",
                    "camera_motion": "slow_push_in",
                    "subject_motion": "blink",
                    "transition": "cut",
                    "subtitle_text": "对不起，我走错了。",
                    "sfx": "door_open",
                    "editing_notes": "Push in slightly as she enters.",
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
    assert shots[0].metadata_json["shot_type"] == "dialogue"
    assert shots[0].metadata_json["camera_motion"] == "slow_push_in"
    assert shots[0].metadata_json["subject_motion"] == "blink"
    assert shots[0].metadata_json["transition"] == "cut"
    assert shots[0].metadata_json["subtitle_text"] == "对不起，我走错了。"
    assert shots[0].metadata_json["sfx"] == "door_open"
    assert shots[0].metadata_json["editing_notes"] == "Push in slightly as she enters."
    assert shots[1].metadata_json["source_shot_id"] == "SH02"
    assert shots[1].metadata_json["duration_sec"] == 2


def test_storyboard_import_saves_visual_asset_keys_to_shot_metadata(db_session):
    init_payload = _coze_init_payload()
    init_payload["visual_asset_library_json"] = {
        "characters": [{"asset_key": "lin_wan", "name": "Lin Xia"}],
        "scenes": [{"asset_key": "meeting_room_a", "name": "Meeting Room A"}],
        "props": [{"asset_key": "employee_badge", "name": "Employee Badge"}],
    }
    init_response = coze_project_init(db_session, CozeProjectInitRequest(**init_payload))
    project_id = init_response.data["project_id"]

    storyboard_payload = _coze_storyboard_payload()
    storyboard_payload["storyboard_json"]["shots"][0]["character_asset_keys"] = ["lin_wan"]
    storyboard_payload["storyboard_json"]["shots"][0]["scene_asset_key"] = "meeting_room_a"
    storyboard_payload["storyboard_json"]["shots"][0]["prop_asset_keys"] = ["employee_badge"]
    coze_storyboard(db_session, project_id, CozeStoryboardRequest(**storyboard_payload))

    shot = db_session.query(Shot).order_by(Shot.shot_number.asc()).first()
    assert shot is not None
    assert shot.metadata_json["character_asset_keys"] == ["lin_wan"]
    assert shot.metadata_json["scene_asset_key"] == "meeting_room_a"
    assert shot.metadata_json["prop_asset_keys"] == ["employee_badge"]


def test_storyboard_import_saves_creative_fields_to_shot_metadata(db_session):
    init_response = coze_project_init(db_session, CozeProjectInitRequest(**_coze_init_payload()))
    project_id = init_response.data["project_id"]
    storyboard_payload = _coze_storyboard_payload()
    shot = storyboard_payload["storyboard_json"]["shots"][0]
    shot["shot_purpose"] = "opening horror hook"
    shot["conflict_beat"] = "she is afraid to look outside"
    shot["emotion_shift"] = "sleepy to alarmed"
    shot["visual_focus"] = "phone time and frightened face"
    shot["image_prompt_intent"] = "single-shot suspense keyframe"
    shot["composition"] = "tight vertical close framing"
    shot["lighting"] = "low light from phone screen"
    shot["subtitle_position"] = "lower center"
    shot["negative_constraints"] = ["not a poster", "not a character sheet"]
    coze_storyboard(db_session, project_id, CozeStoryboardRequest(**storyboard_payload))

    saved_shot = db_session.query(Shot).order_by(Shot.shot_number.asc()).first()
    assert saved_shot is not None
    assert saved_shot.metadata_json["shot_purpose"] == "opening horror hook"
    assert saved_shot.metadata_json["conflict_beat"] == "she is afraid to look outside"
    assert saved_shot.metadata_json["visual_focus"] == "phone time and frightened face"
    assert saved_shot.metadata_json["lighting"] == "low light from phone screen"
    assert saved_shot.metadata_json["negative_constraints"] == ["not a poster", "not a character sheet"]


def test_storyboard_import_saves_narrative_structure_keys_to_shot_metadata(db_session):
    init_response = coze_project_init(db_session, CozeProjectInitRequest(**_coze_init_payload()))
    project_id = init_response.data["project_id"]
    episode = get_or_create_default_episode(db_session, project_id)
    episode.metadata_json = {
        "narrative_structure": {
            "segments": [{"segment_key": "opening_hook", "title": "Opening Hook", "segment_type": "opening_hook"}],
            "beats": [{"beat_key": "urgent_knock", "title": "Urgent Knock", "beat_type": "fear_trigger"}],
            "storyboard_groups": [{"group_key": "opening_group", "title": "Opening Group"}],
        }
    }
    db_session.commit()
    db_session.refresh(episode)

    storyboard_payload = _coze_storyboard_payload()
    storyboard_payload["storyboard_json"]["shots"][0]["segment_key"] = "opening_hook"
    storyboard_payload["storyboard_json"]["shots"][0]["beat_key"] = "urgent_knock"
    storyboard_payload["storyboard_json"]["shots"][0]["storyboard_group_key"] = "opening_group"

    storyboard_response = coze_storyboard(db_session, project_id, CozeStoryboardRequest(**storyboard_payload))
    shot = db_session.query(Shot).order_by(Shot.shot_number.asc()).first()

    assert shot is not None
    assert shot.metadata_json["segment_key"] == "opening_hook"
    assert shot.metadata_json["beat_key"] == "urgent_knock"
    assert shot.metadata_json["storyboard_group_key"] == "opening_group"
    assert storyboard_response.data["warnings"] == []


def test_storyboard_import_warns_when_narrative_structure_keys_are_missing(db_session):
    init_response = coze_project_init(db_session, CozeProjectInitRequest(**_coze_init_payload()))
    project_id = init_response.data["project_id"]
    episode = get_or_create_default_episode(db_session, project_id)
    episode.metadata_json = {"narrative_structure": {"segments": [], "beats": [], "storyboard_groups": []}}
    db_session.commit()
    db_session.refresh(episode)

    storyboard_payload = _coze_storyboard_payload()
    storyboard_payload["storyboard_json"]["shots"][0]["segment_key"] = "missing_segment"
    storyboard_payload["storyboard_json"]["shots"][0]["beat_key"] = "missing_beat"
    storyboard_payload["storyboard_json"]["shots"][0]["storyboard_group_key"] = "missing_group"

    storyboard_response = coze_storyboard(db_session, project_id, CozeStoryboardRequest(**storyboard_payload))
    warnings = storyboard_response.data["warnings"]

    assert "missing_segment_key:missing_segment" in warnings
    assert "missing_beat_key:missing_beat" in warnings
    assert "missing_storyboard_group_key:missing_group" in warnings


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


def test_validate_payload_returns_valid_true_for_complete_payload(client):
    response = client.post(
        "/coze/project/validate-payload",
        json={
            "project_card_json": {
                "project_title": "Urban Hook",
                "visual_style": "comic-realism",
            },
            "characters_json": {
                "characters": [
                    {
                        "name": "Lin Xia",
                        "role": "lead",
                        "appearance": "sharp face",
                    }
                ]
            },
            "script_card_json": {
                "opening_hook": "Opening",
                "conflict": "Conflict",
                "turning_point": "Turning",
                "ending_hook": "Ending",
            },
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "core_action": "Open the door",
                        "image_prompt": "image prompt",
                        "video_prompt": "video prompt",
                        "voice_prompt": "voice prompt",
                        "bgm_prompt": "bgm prompt",
                    }
                ]
            },
            "video_shot_ids": ["SH01"],
            "publish_record_json": {
                "platform": "douyin",
                "title": "Episode 1",
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["valid"] is True
    assert body["data"]["errors"] == []
    assert "suggestions" in body["data"]
    assert body["next_action"] == "ready_for_full_demo_flow"


def test_validate_payload_returns_errors_for_missing_required_fields(client):
    response = client.post(
        "/coze/project/validate-payload",
        json={
            "project_card_json": {},
            "characters_json": {"characters": [{}]},
            "script_card_json": {},
            "storyboard_json": {"shots": [{}]},
            "video_shot_ids": [],
            "publish_record_json": {},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["valid"] is False
    assert any("storyboard_json.shots[0].shot_id is required." in error for error in body["data"]["errors"])
    assert any("storyboard_json.shots[0].image_prompt is required." in error for error in body["data"]["errors"])
    assert body["next_action"] == "fix_payload"


def test_validate_payload_missing_creative_fields_returns_warnings_or_suggestions_not_errors(client):
    response = client.post(
        "/coze/project/validate-payload",
        json={
            "project_card_json": {"project_title": "Night Door"},
            "characters_json": {"characters": [{"name": "Shen Zhixia"}]},
            "script_card_json": {},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "core_action": "She wakes up from knocking",
                        "image_prompt": "woman startled awake at night",
                    }
                ]
            },
            "video_shot_ids": [],
            "publish_record_json": {},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["valid"] is True
    assert body["data"]["errors"] == []
    assert len(body["data"]["warnings"]) > 0
    assert len(body["data"]["suggestions"]) > 0


def test_validate_payload_warns_when_duration_sec_is_missing(client):
    response = client.post(
        "/coze/project/validate-payload",
        json={
            "project_card_json": {"project_title": "Urban Hook", "visual_style": "comic-realism"},
            "characters_json": {"characters": [{"name": "Lin Xia", "role": "lead", "appearance": "sharp face"}]},
            "script_card_json": {
                "opening_hook": "Opening",
                "conflict": "Conflict",
                "turning_point": "Turning",
                "ending_hook": "Ending",
            },
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "core_action": "Open the door",
                        "image_prompt": "image prompt",
                        "video_prompt": "video prompt",
                        "voice_prompt": "voice prompt",
                        "bgm_prompt": "bgm prompt",
                    }
                ]
            },
            "video_shot_ids": [],
            "publish_record_json": {"platform": "douyin", "title": "Episode 1"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["valid"] is True
    assert any("duration_sec is recommended" in warning for warning in body["data"]["warnings"])


def test_validate_payload_warns_for_compound_core_action_without_blocking(client):
    response = client.post(
        "/coze/project/validate-payload",
        json={
            "project_card_json": {"project_title": "Midnight Peephole", "visual_style": "anime-comic realism"},
            "characters_json": {"characters": [{"name": "Shen Zhixia", "role": "lead", "appearance": "tired eyes"}]},
            "script_card_json": {"core_hook": "something identical is outside the door"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "core_action": "She wakes up from urgent knocking, grabs the phone, and checks the time",
                        "image_prompt": "woman awake in a dark apartment bedroom",
                        "video_prompt": "she jolts awake and freezes",
                        "voice_prompt": "frightened whisper",
                        "bgm_prompt": "low suspense drone",
                    }
                ]
            },
            "video_shot_ids": [],
            "publish_record_json": {"platform": "manual_demo", "title": "Midnight Peephole"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["valid"] is True
    assert body["data"]["errors"] == []
    assert any("core_action_may_contain_multiple_actions" in warning for warning in body["data"]["warnings"])
    assert any("keep core_action focused on one primary action" in suggestion for suggestion in body["data"]["suggestions"])


def test_validate_payload_returns_error_for_unknown_video_shot_id(client):
    response = client.post(
        "/coze/project/validate-payload",
        json={
            "project_card_json": {"project_title": "Urban Hook", "visual_style": "comic-realism"},
            "characters_json": {"characters": [{"name": "Lin Xia", "role": "lead", "appearance": "sharp face"}]},
            "script_card_json": {
                "opening_hook": "Opening",
                "conflict": "Conflict",
                "turning_point": "Turning",
                "ending_hook": "Ending",
            },
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "core_action": "Open the door",
                        "image_prompt": "image prompt",
                        "video_prompt": "video prompt",
                        "voice_prompt": "voice prompt",
                        "bgm_prompt": "bgm prompt",
                    }
                ]
            },
            "video_shot_ids": ["SH99"],
            "publish_record_json": {"platform": "douyin", "title": "Episode 1"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["valid"] is False
    assert any("unknown shot id: SH99" in error for error in body["data"]["errors"])


def test_validate_payload_returns_errors_for_invalid_visual_asset_library_types(client):
    response = client.post(
        "/coze/project/validate-payload",
        json={
            "project_card_json": {"project_title": "Urban Hook", "visual_style": "comic-realism"},
            "visual_asset_library_json": {"characters": {}, "scenes": [], "props": "oops"},
            "characters_json": {"characters": [{"name": "Lin Xia", "role": "lead", "appearance": "sharp face"}]},
            "script_card_json": {
                "opening_hook": "Opening",
                "conflict": "Conflict",
                "turning_point": "Turning",
                "ending_hook": "Ending",
            },
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "core_action": "Open the door",
                        "character_asset_keys": "lin_wan",
                        "scene_asset_key": ["meeting_room_a"],
                        "prop_asset_keys": "employee_badge",
                        "image_prompt": "image prompt",
                        "video_prompt": "video prompt",
                        "voice_prompt": "voice prompt",
                        "bgm_prompt": "bgm prompt",
                    }
                ]
            },
            "video_shot_ids": [],
            "publish_record_json": {"platform": "douyin", "title": "Episode 1"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["valid"] is False
    assert any("visual_asset_library_json.characters must be an array." in error for error in body["data"]["errors"])
    assert any("visual_asset_library_json.props must be an array." in error for error in body["data"]["errors"])
    assert any("character_asset_keys must be an array." in error for error in body["data"]["errors"])
    assert any("scene_asset_key must be a string." in error for error in body["data"]["errors"])
    assert any("prop_asset_keys must be an array." in error for error in body["data"]["errors"])


def test_validate_payload_warns_for_unknown_visual_asset_keys(client):
    response = client.post(
        "/coze/project/validate-payload",
        json={
            "project_card_json": {"project_title": "Urban Hook", "visual_style": "comic-realism"},
            "visual_asset_library_json": {
                "characters": [{"asset_key": "lin_wan", "name": "Lin Xia"}],
                "scenes": [{"asset_key": "meeting_room_a", "name": "Meeting Room A"}],
                "props": [{"asset_key": "employee_badge", "name": "Employee Badge"}],
            },
            "characters_json": {"characters": [{"name": "Lin Xia", "role": "lead", "appearance": "sharp face"}]},
            "script_card_json": {
                "opening_hook": "Opening",
                "conflict": "Conflict",
                "turning_point": "Turning",
                "ending_hook": "Ending",
            },
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "core_action": "Open the door",
                        "character_asset_keys": ["unknown_character"],
                        "scene_asset_key": "unknown_scene",
                        "prop_asset_keys": ["unknown_prop"],
                        "image_prompt": "image prompt",
                        "video_prompt": "video prompt",
                        "voice_prompt": "voice prompt",
                        "bgm_prompt": "bgm prompt",
                    }
                ]
            },
            "video_shot_ids": [],
            "publish_record_json": {"platform": "douyin", "title": "Episode 1"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["valid"] is True
    assert any("references unknown asset_key: unknown_character" in warning for warning in body["data"]["warnings"])
    assert any("references unknown asset_key: unknown_scene" in warning for warning in body["data"]["warnings"])
    assert any("references unknown asset_key: unknown_prop" in warning for warning in body["data"]["warnings"])
