def test_episode_story_source_round_trip_and_hash(client):
    project = client.post("/projects", json={"name": "Story Intake Demo"}).json()
    episode = client.post("/episodes", json={"project_id": project["id"], "title": "Episode 1", "episode_number": 1}).json()

    payload = {
        "title": "深夜猫眼惊魂",
        "raw_story": "一个女生深夜独居，凌晨有人敲门，她从猫眼看到门外站着另一个自己。",
        "genre": "都市怪谈 / 恐怖惊悚悬疑",
        "target_duration_sec": 60,
        "audience": "18-30岁女性向惊悚悬疑用户",
        "tone": "低光、压迫、心理恐惧、无血腥",
        "manual_notes": "走静态图拼帧路线。",
    }

    response = client.post(f"/projects/{project['id']}/episodes/{episode['id']}/story-source", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["story_source_exists"] is True
    assert body["story_source"]["raw_story"] == payload["raw_story"]
    assert body["source_text_hash"]
    assert body["analysis_status"] == "story_source_added"
    assert body["next_action"] == "generate_narrative_structure"

    get_response = client.get(f"/projects/{project['id']}/episodes/{episode['id']}/story-source")
    assert get_response.status_code == 200
    get_body = get_response.json()
    assert get_body["story_source"]["title"] == payload["title"]
    assert get_body["source_text_hash"] == body["source_text_hash"]


def test_episode_story_source_missing_project_or_episode_returns_404(client):
    project = client.post("/projects", json={"name": "Missing Story Source Demo"}).json()
    episode = client.post("/episodes", json={"project_id": project["id"], "title": "Episode 1", "episode_number": 1}).json()
    payload = {"raw_story": "A midnight knocking story."}

    missing_project = client.post(f"/projects/999999/episodes/{episode['id']}/story-source", json=payload)
    assert missing_project.status_code == 404

    missing_episode = client.post(f"/projects/{project['id']}/episodes/999999/story-source", json=payload)
    assert missing_episode.status_code == 404


def test_narrative_structure_lite_round_trip(client):
    project = client.post("/projects", json={"name": "Narrative Lite Demo"}).json()
    episode = client.post("/episodes", json={"project_id": project["id"], "title": "Episode 1", "episode_number": 1}).json()
    payload = {
        "segments": [{"segment_key": "opening_hook", "title": "深夜敲门", "segment_type": "opening_hook", "shot_ids": ["SH01"]}],
        "beats": [{"beat_key": "urgent_knock", "title": "急促敲门", "beat_type": "fear_trigger", "shot_ids": ["SH01"]}],
        "storyboard_groups": [{"group_key": "opening_group", "title": "开场钩子分镜组", "shot_ids": ["SH01"]}],
        "manual_notes": "manual",
        "source": "coze",
    }

    response = client.post(f"/projects/{project['id']}/episodes/{episode['id']}/narrative-structure-lite", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["narrative_structure_exists"] is True
    assert body["segments_count"] == 1
    assert body["beats_count"] == 1
    assert body["storyboard_groups_count"] == 1
    assert body["next_action"] == "generate_storyboard_package"

    get_response = client.get(f"/projects/{project['id']}/episodes/{episode['id']}/narrative-structure-lite")
    assert get_response.status_code == 200
    get_body = get_response.json()
    assert get_body["narrative_structure"]["source"] == "coze"
    assert get_body["narrative_structure"]["segments"][0]["segment_key"] == "opening_hook"


def test_creative_pipeline_status_progression(client):
    project = client.post("/projects", json={"name": "Creative Pipeline Demo"}).json()
    episode = client.post("/episodes", json={"project_id": project["id"], "title": "Episode 1", "episode_number": 1}).json()

    initial = client.get(f"/projects/{project['id']}/creative-pipeline-status")
    assert initial.status_code == 200
    assert initial.json()["next_action"] == "add_story_source"

    client.post(
        f"/projects/{project['id']}/episodes/{episode['id']}/story-source",
        json={"title": "深夜猫眼惊魂", "raw_story": "她在深夜听到敲门。"},
    )
    after_story = client.get(f"/projects/{project['id']}/creative-pipeline-status")
    assert after_story.status_code == 200
    assert after_story.json()["next_action"] == "generate_narrative_structure"

    client.post(
        f"/projects/{project['id']}/episodes/{episode['id']}/narrative-structure-lite",
        json={"segments": [{"segment_key": "opening_hook", "title": "深夜敲门"}], "beats": [], "storyboard_groups": [], "source": "manual"},
    )
    after_structure = client.get(f"/projects/{project['id']}/creative-pipeline-status")
    assert after_structure.status_code == 200
    assert after_structure.json()["next_action"] == "generate_storyboard_package"

    storyboard_response = client.post(
        f"/coze/project/{project['id']}/storyboard-package",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "segment_key": "opening_hook",
                        "character": "沈知夏",
                        "location": "旧公寓卧室",
                        "core_action": "沈知夏被敲门声惊醒",
                        "emotion": "alarm",
                        "camera": "close-up",
                        "image_prompt": "woman wakes up in a dark apartment bedroom",
                        "video_prompt": "tense wake-up beat",
                        "voice_prompt": "voice prompt",
                        "bgm_prompt": "bgm prompt",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    assert storyboard_response.status_code == 201

    after_storyboard = client.get(f"/projects/{project['id']}/creative-pipeline-status")
    assert after_storyboard.status_code == 200
    body = after_storyboard.json()
    assert body["storyboard_package_exists"] is True
    assert body["shots_count"] == 1
    assert body["next_action"] == "extract_visual_asset_candidates"


def test_storyboard_production_board_returns_narrative_titles(client):
    project = client.post("/projects", json={"name": "Narrative Board Demo"}).json()
    episode = client.post("/episodes", json={"project_id": project["id"], "title": "Episode 1", "episode_number": 1}).json()
    client.post(
        f"/projects/{project['id']}/episodes/{episode['id']}/story-source",
        json={"title": "猫眼惊魂", "raw_story": "她在深夜从猫眼看见门外的另一个自己。"},
    )
    client.post(
        f"/projects/{project['id']}/episodes/{episode['id']}/narrative-structure-lite",
        json={
            "segments": [{"segment_key": "fear_reveal", "title": "猫眼异象", "segment_type": "fear_escalation"}],
            "beats": [{"beat_key": "peephole_double", "title": "猫眼里的另一个自己", "beat_type": "visual_reveal"}],
            "storyboard_groups": [{"group_key": "reveal_group", "title": "反转分镜组"}],
            "source": "manual",
        },
    )
    client.post(
        f"/coze/project/{project['id']}/storyboard-package",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "segment_key": "fear_reveal",
                        "beat_key": "peephole_double",
                        "storyboard_group_key": "reveal_group",
                        "character": "沈知夏",
                        "location": "旧公寓门口",
                        "core_action": "沈知夏从猫眼向外看去",
                        "emotion": "terror",
                        "camera": "close-up",
                        "image_prompt": "woman looking through a peephole in a dark apartment hallway",
                        "video_prompt": "suspense reveal",
                        "voice_prompt": "voice prompt",
                        "bgm_prompt": "bgm prompt",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )

    response = client.get(f"/projects/{project['id']}/storyboard-production-board")
    assert response.status_code == 200
    body = response.json()
    item = body["items"][0]
    assert item["segment_key"] == "fear_reveal"
    assert item["segment_title"] == "猫眼异象"
    assert item["segment_type"] == "fear_escalation"
    assert item["beat_key"] == "peephole_double"
    assert item["beat_title"] == "猫眼里的另一个自己"
    assert item["beat_type"] == "visual_reveal"
    assert item["storyboard_group_key"] == "reveal_group"
    assert item["storyboard_group_title"] == "反转分镜组"
    assert "段落: 猫眼异象" in body["plain_text"]
    assert "节拍: 猫眼里的另一个自己" in body["plain_text"]
