from app.models.shot import Shot
from app.schemas.coze import CozeFullDemoFlowRequest
from app.services.coze_service import coze_full_demo_flow


def _full_demo_flow_payload():
    return {
        "project_card_json": {
            "project_title": "Urban Hook Full Demo",
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
                }
            ]
        },
        "video_shot_ids": ["SH01"],
        "publish_record_json": {
            "platform": "抖音",
            "title": "Episode 1",
            "published_at": "2026-04-25T10:00:00",
            "url": "https://www.douyin.com/video/demo",
        },
    }


def test_coze_full_demo_flow_runs_complete(client):
    response = client.post("/coze/project/full-demo-flow", json=_full_demo_flow_payload())
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["code"] == "OK"
    assert body["message"] == "Full demo flow completed"
    assert body["next_action"] == "completed"

    data = body["data"]
    assert data["project_id"] >= 1
    assert len(data["character_ids"]) == 1
    assert data["episode_id"] >= 1
    assert data["shots_count"] == 1
    assert data["asset_tasks_count"] == 4
    assert data["assets_count"] == 4
    assert data["publish_record_id"] >= 1
    assert data["final_summary"]["project_status"] == "published"
    assert data["final_summary"]["publish_records_count"] == 1
    assert data["final_summary"]["next_action"] == "completed"


def test_coze_summary_completed_is_consistent_after_full_demo_flow(client):
    response = client.post("/coze/project/full-demo-flow", json=_full_demo_flow_payload())
    project_id = response.json()["data"]["project_id"]

    summary = client.get(f"/coze/project/{project_id}/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["next_action"] == "completed"
    assert body["data"]["next_action"] == "completed"


def test_full_demo_flow_saves_duration_sec(db_session):
    response = coze_full_demo_flow(db_session, CozeFullDemoFlowRequest(**_full_demo_flow_payload()))
    project_id = response.data["project_id"]

    shot = (
        db_session.query(Shot)
        .join(Shot.scene)
        .join(Shot.scene.property.mapper.class_.episode)  # type: ignore[attr-defined]
        .filter(Shot.scene.property.mapper.class_.episode.property.mapper.class_.project_id == project_id)  # type: ignore[attr-defined]
        .first()
    )
    assert shot is not None
    assert shot.metadata_json["source_shot_id"] == "SH01"
    assert shot.metadata_json["duration_sec"] == 3
