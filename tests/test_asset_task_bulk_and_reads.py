def _create_project_graph(client, confirmed=True):
    project = client.post("/projects", json={"name": "Project A"}).json()
    client.post(
        "/characters",
        json={
            "project_id": project["id"],
            "name": "Lin Xia",
            "role_type": "lead",
            "profile": "Lead character",
            "visual_notes": "Short hair, office outfit",
            "voice_style": "Calm",
            "main_reference_confirmed": confirmed,
        },
    )
    episode = client.post("/episodes", json={"project_id": project["id"], "title": "Episode 1", "episode_number": 1}).json()
    scene = client.post(
        "/scenes",
        json={"episode_id": episode["id"], "scene_number": 1, "title": "Meeting Room", "description": "Opening scene"},
    ).json()
    shot1 = client.post(
        "/shots",
        json={
            "scene_id": scene["id"],
            "shot_number": 1,
            "framing": "medium",
            "core_action": "Lead opens the door",
            "image_prompt": "image prompt 1",
            "video_prompt": "video prompt 1",
            "voice_prompt": "voice prompt 1",
            "bgm_prompt": "bgm prompt 1",
        },
    ).json()
    shot2 = client.post(
        "/shots",
        json={
            "scene_id": scene["id"],
            "shot_number": 2,
            "framing": "close-up",
            "core_action": "Hero looks at the door",
            "image_prompt": "image prompt 2",
            "video_prompt": "video prompt 2",
            "voice_prompt": "voice prompt 2",
            "bgm_prompt": "bgm prompt 2",
        },
    ).json()
    return project, shot1, shot2


def test_get_asset_task_by_id(client):
    project, shot1, _ = _create_project_graph(client)
    task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    response = client.get(f"/asset-tasks/{task['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == task["id"]
    assert response.json()["shot_id"] == shot1["id"]


def test_get_project_asset_tasks(client):
    project, shot1, _ = _create_project_graph(client)
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"})
    response = client.get(f"/projects/{project['id']}/asset-tasks")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_project_assets(client):
    project, shot1, _ = _create_project_graph(client)
    task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(f"/asset-tasks/{task['id']}/run")
    response = client.get(f"/projects/{project['id']}/assets")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["asset_task_id"] == task["id"]


def test_get_project_summary(client):
    project, _, _ = _create_project_graph(client)
    response = client.get(f"/projects/{project['id']}/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["episodes_count"] == 1
    assert body["shots_count"] == 2
    assert body["next_action"] == "create_asset_tasks"


def test_bulk_create_asset_tasks(client):
    project, shot1, shot2 = _create_project_graph(client)
    response = client.post(
        f"/projects/{project['id']}/asset-tasks/bulk",
        json={"video_shot_ids": [shot2["id"]], "provider_name": "mock"},
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body) == 7
    shot1_modalities = sorted(item["modality"] for item in body if item["shot_id"] == shot1["id"])
    shot2_modalities = sorted(item["modality"] for item in body if item["shot_id"] == shot2["id"])
    assert shot1_modalities == ["bgm", "image", "voice"]
    assert shot2_modalities == ["bgm", "image", "video", "voice"]


def test_bulk_create_should_require_confirmed_character_reference(client):
    project, _, _ = _create_project_graph(client, confirmed=False)
    response = client.post(f"/projects/{project['id']}/asset-tasks/bulk", json={})
    assert response.status_code == 400
    assert "confirmed character reference" in response.json()["detail"]


def test_bulk_create_should_avoid_duplicates(client):
    project, _, shot2 = _create_project_graph(client)
    first = client.post(f"/projects/{project['id']}/asset-tasks/bulk", json={"video_shot_ids": [shot2["id"]]})
    second = client.post(f"/projects/{project['id']}/asset-tasks/bulk", json={"video_shot_ids": [shot2["id"]]})
    assert first.status_code == 201
    assert second.status_code == 201
    assert len(second.json()) == 0
    tasks = client.get(f"/projects/{project['id']}/asset-tasks").json()
    assert len(tasks) == 7


def test_bulk_run_asset_tasks(client):
    project, _, shot2 = _create_project_graph(client)
    client.post(f"/projects/{project['id']}/asset-tasks/bulk", json={"video_shot_ids": [shot2["id"]]})
    response = client.post(f"/projects/{project['id']}/asset-tasks/run-bulk")
    assert response.status_code == 200
    body = response.json()
    assert body["succeeded_count"] == 7
    assert body["failed_count"] == 0
    assert len(body["results"]) == 7


def test_bulk_run_should_continue_if_one_task_fails(client):
    project, shot1, shot2 = _create_project_graph(client)
    failing_task = client.post(
        "/asset-tasks",
        json={
            "shot_id": shot1["id"],
            "modality": "image",
            "provider_name": "mock",
            "input_payload": {"should_fail": True},
        },
    ).json()
    success_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"},
    ).json()
    response = client.post(f"/projects/{project['id']}/asset-tasks/run-bulk")
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2
    result_by_id = {item["task_id"]: item for item in body["results"]}
    assert result_by_id[failing_task["id"]]["status"] == "failed"
    assert result_by_id[success_task["id"]]["status"] == "succeeded"
    assert body["succeeded_count"] == 1
    assert body["failed_count"] == 1


def test_project_summary_should_reflect_task_and_asset_counts(client):
    project, _, shot2 = _create_project_graph(client)
    client.post(f"/projects/{project['id']}/asset-tasks/bulk", json={"video_shot_ids": [shot2["id"]]})
    client.post(f"/projects/{project['id']}/asset-tasks/run-bulk")
    response = client.get(f"/projects/{project['id']}/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["asset_tasks_count"] == 7
    assert body["assets_count"] == 7
    assert body["succeeded_tasks_count"] == 7
    assert body["failed_tasks_count"] == 0
    assert body["needs_human_revision_count"] == 0


def test_project_provider_debug_summary_returns_all_asset_tasks(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Provider Debug Summary Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "comic-realism",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 7,
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
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": ["SH01"]})
    client.post(f"/coze/project/{project_id}/run-asset-tasks")

    response = client.get(f"/projects/{project_id}/provider-debug-summary")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project_id
    assert body["asset_tasks_count"] == 4
    assert len(body["items"]) == 4


def test_project_image_prompts_returns_all_image_tasks(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(f"/asset-tasks/{image_task_1['id']}/run")

    response = client.get(f"/projects/{project['id']}/image-prompts")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["items_count"] == 2
    assert len(body["items"]) == 2


def test_project_image_prompts_returns_enhanced_and_copy_ready_prompt(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Manual Prompt Export Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Lin Xia opens the door",
                        "emotion": "nervous",
                        "camera": "medium close-up",
                        "dialogue": "Sorry, wrong room.",
                        "image_prompt": "young woman opening a meeting room door",
                        "video_prompt": "video prompt 1",
                        "voice_prompt": "voice prompt 1",
                        "bgm_prompt": "bgm prompt 1",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={})
    run_response = client.post(f"/coze/project/{project_id}/run-asset-tasks")
    assert run_response.status_code == 200

    response = client.get(f"/projects/{project_id}/image-prompts")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert "young woman opening a meeting room door" in item["enhanced_prompt"]
    assert item["copy_ready_prompt"]
    assert item["negative_prompt"] in item["copy_ready_prompt"]
    assert "Lin Xia" in item["copy_ready_prompt"]


def test_project_image_prompts_include_editing_fields(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Editing Fields Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Lin Xia opens the door",
                        "emotion": "nervous",
                        "camera": "medium close-up",
                        "shot_type": "dialogue",
                        "camera_motion": "slow_push_in",
                        "subject_motion": "blink",
                        "transition": "cut",
                        "subtitle_text": "对不起，我走错了。",
                        "sfx": "door_open",
                        "editing_notes": "Push in slightly as she enters.",
                        "dialogue": "Sorry, wrong room.",
                        "image_prompt": "young woman opening a meeting room door",
                        "video_prompt": "video prompt 1",
                        "voice_prompt": "voice prompt 1",
                        "bgm_prompt": "bgm prompt 1",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={})

    response = client.get(f"/projects/{project_id}/image-prompts")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["shot_type"] == "dialogue"
    assert item["camera_motion"] == "slow_push_in"
    assert item["subject_motion"] == "blink"
    assert item["transition"] == "cut"
    assert item["subtitle_text"] == "对不起，我走错了。"
    assert item["sfx"] == "door_open"
    assert item["editing_notes"] == "Push in slightly as she enters."


def test_project_visual_asset_library_returns_characters_scenes_and_props(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Visual Asset Library Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "visual_asset_library_json": {
            "characters": [{"asset_key": "lin_wan", "name": "Lin Xia"}],
            "scenes": [{"asset_key": "meeting_room_a", "name": "Meeting Room A"}],
            "props": [{"asset_key": "employee_badge", "name": "Employee Badge"}],
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]

    response = client.get(f"/projects/{project_id}/visual-asset-library")
    assert response.status_code == 200
    body = response.json()
    assert body["characters_count"] == 1
    assert body["scenes_count"] == 1
    assert body["props_count"] == 1
    assert body["characters"][0]["asset_key"] == "lin_wan"
    assert body["next_action"] == "ready_for_reference_guided_image_generation"


def test_project_image_prompts_return_visual_asset_refs_and_reference_guidance(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Image Prompt Ref Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "visual_asset_library_json": {
            "characters": [
                {
                    "asset_key": "lin_wan",
                    "name": "Lin Xia",
                    "main_reference_url": "file:///D:/AI漫剧角色库/LinWan_main.png",
                    "must_keep": ["same hairstyle"],
                    "avoid": ["celebrity likeness"],
                }
            ],
            "scenes": [
                {
                    "asset_key": "meeting_room_a",
                    "name": "Meeting Room A",
                    "main_reference_url": "file:///D:/AI漫剧场景库/meeting_room_a_main.png",
                    "must_keep": ["conference table"],
                    "avoid": ["fantasy background"],
                }
            ],
            "props": [
                {
                    "asset_key": "employee_badge",
                    "name": "Employee Badge",
                    "main_reference_url": "file:///D:/AI漫剧道具库/employee_badge_main.png",
                }
            ],
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Lin Xia opens the door",
                        "emotion": "nervous",
                        "camera": "medium close-up",
                        "character_asset_keys": ["lin_wan"],
                        "scene_asset_key": "meeting_room_a",
                        "prop_asset_keys": ["employee_badge"],
                        "dialogue": "Sorry, wrong room.",
                        "image_prompt": "young woman opening a meeting room door",
                        "video_prompt": "video prompt 1",
                        "voice_prompt": "voice prompt 1",
                        "bgm_prompt": "bgm prompt 1",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={})

    response = client.get(f"/projects/{project_id}/image-prompts")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["character_asset_keys"] == ["lin_wan"]
    assert item["scene_asset_key"] == "meeting_room_a"
    assert item["prop_asset_keys"] == ["employee_badge"]
    assert item["visual_asset_refs"]["characters"][0]["asset_key"] == "lin_wan"
    assert item["visual_asset_refs"]["scene"]["asset_key"] == "meeting_room_a"
    assert item["visual_asset_refs"]["props"][0]["asset_key"] == "employee_badge"
    assert "Recommended character reference:" in item["copy_ready_prompt"]
    assert "Recommended scene reference:" in item["copy_ready_prompt"]
    assert "Recommended prop reference:" in item["copy_ready_prompt"]


def test_project_image_prompts_return_creative_fields_and_production_grade_prompt(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Midnight Peephole",
            "genre": "urban horror suspense",
            "platform": "coze",
            "target_duration": 45,
            "target_audience": "18-30",
            "visual_style": "anime-comic realism",
            "status": "draft",
        },
        "visual_asset_library_json": {
            "characters": [{"asset_key": "shen_zhixia", "name": "沈知夏", "main_reference_url": "file:///D:/refs/shen.png"}],
            "scenes": [{"asset_key": "entry_door", "name": "Apartment Entry Door", "main_reference_url": "file:///D:/refs/door.png"}],
            "props": [{"asset_key": "peephole", "name": "Peephole", "main_reference_url": "file:///D:/refs/peephole.png"}],
        },
        "characters_json": {
            "characters": [
                {
                    "name": "沈知夏",
                    "role": "lead",
                    "appearance": "pale face, black hair",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"core_hook": "someone outside looks exactly like her"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "沈知夏",
                        "location": "Old Apartment Bedroom",
                        "core_action": "She wakes up from urgent knocking",
                        "emotion": "alarmed",
                        "camera": "close-up",
                        "dialogue": "谁在外面？",
                        "shot_type": "reveal",
                        "camera_motion": "slow_push_in",
                        "subject_motion": "blink, slight_body_shift",
                        "transition": "cut",
                        "subtitle_text": "谁在外面？",
                        "sfx": "urgent_knock",
                        "editing_notes": "Hold the empty doorway space for tension.",
                        "shot_purpose": "opening horror hook",
                        "conflict_beat": "safety of room vs unknown outside threat",
                        "emotion_shift": "sleepy to frightened",
                        "visual_focus": "phone time and dark doorway",
                        "image_prompt_intent": "single-shot suspense keyframe",
                        "composition": "tight 9:16 frame with negative space near the door",
                        "lighting": "low light with cold phone glow",
                        "subtitle_position": "lower center",
                        "negative_constraints": ["not a poster", "not a character sheet"],
                        "character_asset_keys": ["shen_zhixia"],
                        "scene_asset_key": "entry_door",
                        "prop_asset_keys": ["peephole"],
                        "image_prompt": "woman startled awake in a dark apartment bedroom by sudden knocking",
                        "video_prompt": "she freezes as knocking continues behind the door",
                        "voice_prompt": "frightened whisper",
                        "bgm_prompt": "low suspense drone",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    create_resp = client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": []}).json()
    assert create_resp["data"]["asset_tasks_count"] >= 3

    response = client.get(f"/projects/{project_id}/image-prompts")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["shot_purpose"] == "opening horror hook"
    assert item["conflict_beat"] == "safety of room vs unknown outside threat"
    assert item["visual_focus"] == "phone time and dark doorway"
    assert "storyboard shot image for a vertical AI comic drama" in item["copy_ready_prompt"]
    assert "generate one single-shot storyboard keyframe for later editing" in item["copy_ready_prompt"]
    assert "not a poster" in item["copy_ready_prompt"]
    assert "not a character sheet" in item["copy_ready_prompt"]
    assert "not a multi-panel comic page" in item["copy_ready_prompt"]
    assert "Recommended character reference:" in item["copy_ready_prompt"]
    assert "Shot purpose: opening horror hook" in item["copy_ready_prompt"]
    assert "Conflict beat: safety of room vs unknown outside threat" in item["copy_ready_prompt"]
    assert "Visual focus: phone time and dark doorway" in item["copy_ready_prompt"]
    assert "disturbing clue" in item["copy_ready_prompt"]
    assert "changed understanding of the scene" in item["copy_ready_prompt"]
    assert "low light" in item["copy_ready_prompt"]
    assert "silence" in item["copy_ready_prompt"]
    assert "unease" in item["copy_ready_prompt"]
    assert "negative space" in item["copy_ready_prompt"]
    assert "mock://character/reference.png" not in item["copy_ready_prompt"]


def test_editing_shot_board_returns_visual_asset_refs(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Editing Board Ref Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "visual_asset_library_json": {
            "characters": [{"asset_key": "lin_wan", "name": "Lin Xia"}],
            "scenes": [{"asset_key": "meeting_room_a", "name": "Meeting Room A"}],
            "props": [{"asset_key": "employee_badge", "name": "Employee Badge"}],
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Lin Xia opens the door",
                        "emotion": "nervous",
                        "camera": "medium close-up",
                        "shot_type": "dialogue",
                        "camera_motion": "slow_push_in",
                        "subject_motion": "blink",
                        "transition": "cut",
                        "subtitle_text": "对不起，我走错了。",
                        "sfx": "door_open",
                        "editing_notes": "Push in slightly as she enters.",
                        "character_asset_keys": ["lin_wan"],
                        "scene_asset_key": "meeting_room_a",
                        "prop_asset_keys": ["employee_badge"],
                        "dialogue": "Sorry, wrong room.",
                        "image_prompt": "young woman opening a meeting room door",
                        "video_prompt": "video prompt 1",
                        "voice_prompt": "voice prompt 1",
                        "bgm_prompt": "bgm prompt 1",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={})
    tasks = client.get(f"/projects/{project_id}/asset-tasks").json()
    image_task = next(task for task in tasks if task["modality"] == "image")
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={"asset_url": "file:///D:/AI漫剧图片库/SH01.png", "asset_type": "image", "notes": "manual image"},
    )

    response = client.get(f"/projects/{project_id}/editing-shot-board")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["character_asset_keys"] == ["lin_wan"]
    assert item["scene_asset_key"] == "meeting_room_a"
    assert item["prop_asset_keys"] == ["employee_badge"]
    assert item["visual_asset_refs"]["characters"][0]["asset_key"] == "lin_wan"


def test_editing_shot_board_returns_creative_fields(client):
    project_id = _create_editing_cue_sheet_project(
        client,
        shots=[
            {
                "shot_id": "SH01",
                "duration_sec": 3,
                "character": "Lin Xia",
                "location": "Meeting Room",
                "core_action": "Lin Xia opens the door",
                "emotion": "nervous",
                "camera": "medium close-up",
                "dialogue": "不好意思，我走错了。",
                "shot_type": "suspense",
                "camera_motion": "slow_push_in",
                "subject_motion": "blink",
                "transition": "cut",
                "subtitle_text": "不好意思，我走错了。",
                "sfx": "door_open",
                "editing_notes": "Use slight zoom-in and nervous pause.",
                "shot_purpose": "awkward entrance beat",
                "conflict_beat": "enter vs retreat",
                "emotion_shift": "tense to embarrassed",
                "visual_focus": "doorway and expression",
                "image_prompt_intent": "single keyframe",
                "composition": "tight doorway framing",
                "lighting": "cold office light",
                "subtitle_position": "lower center",
                "negative_constraints": ["not a poster"],
                "image_prompt": "young woman opening a meeting room door",
                "video_prompt": "office door opens, awkward pause",
                "voice_prompt": "voice prompt 1",
                "bgm_prompt": "bgm prompt 1",
                "status": "prompt_ready",
            }
        ],
        upload_manual_images=True,
    )
    response = client.get(f"/projects/{project_id}/editing-shot-board")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["shot_purpose"] == "awkward entrance beat"
    assert item["conflict_beat"] == "enter vs retreat"
    assert item["visual_focus"] == "doorway and expression"
    assert item["lighting"] == "cold office light"


def test_project_image_prompts_unexecuted_image_task_still_returns_prompt(client):
    project, shot1, _ = _create_project_graph(client)
    task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()

    response = client.get(f"/projects/{project['id']}/image-prompts")
    assert response.status_code == 200
    item = next(exported for exported in response.json()["items"] if exported["asset_task_id"] == task["id"])
    assert item["enhanced_prompt"]
    assert item["copy_ready_prompt"]
    assert item["base_prompt"] == "image prompt 1"


def test_project_image_prompts_missing_project_returns_404(client):
    response = client.get("/projects/9999/image-prompts")
    assert response.status_code == 404


def test_manual_image_progress_returns_all_project_image_tasks(client):
    project, shot1, shot2 = _create_project_graph(client)
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"})

    response = client.get(f"/projects/{project['id']}/manual-image-progress")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["image_tasks_count"] == 2
    assert len(body["items"]) == 2


def test_manual_image_progress_shows_manual_uploaded_task(client):
    project, shot1, shot2 = _create_project_graph(client)
    task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"})
    client.post(
        f"/asset-tasks/{task_1['id']}/manual-asset",
        json={
            "asset_url": "file:///D:/ai-comic-assets/SH01.png",
            "asset_type": "image",
            "notes": "manual upload",
        },
    )

    response = client.get(f"/projects/{project['id']}/manual-image-progress")
    assert response.status_code == 200
    item = next(exported for exported in response.json()["items"] if exported["asset_task_id"] == task_1["id"])
    assert item["has_asset"] is True
    assert item["manual_upload"] is True
    assert item["needs_manual_image"] is False
    assert item["asset_url"] == "file:///D:/ai-comic-assets/SH01.png"


def test_manual_image_progress_shows_missing_items_and_continue_action(client):
    project, shot1, shot2 = _create_project_graph(client)
    task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{task_1['id']}/manual-asset",
        json={
            "asset_url": "file:///D:/ai-comic-assets/SH01.png",
            "asset_type": "image",
            "notes": "manual upload",
        },
    )

    response = client.get(f"/projects/{project['id']}/manual-image-progress")
    body = response.json()
    item = next(exported for exported in body["items"] if exported["asset_task_id"] == task_2["id"])
    assert item["has_asset"] is False
    assert item["needs_manual_image"] is True
    assert body["completed_image_tasks_count"] == 1
    assert body["missing_image_tasks_count"] == 1
    assert body["manual_uploaded_count"] == 1
    assert body["next_action"] == "continue_manual_image_generation"


def test_manual_image_progress_all_completed_returns_manual_images_completed(client):
    project, shot1, shot2 = _create_project_graph(client)
    task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{task_1['id']}/manual-asset",
        json={
            "asset_url": "file:///D:/ai-comic-assets/SH01.png",
            "asset_type": "image",
            "notes": "manual upload 1",
        },
    )
    client.post(
        f"/asset-tasks/{task_2['id']}/manual-asset",
        json={
            "asset_url": "file:///D:/ai-comic-assets/SH02.png",
            "asset_type": "image",
            "notes": "manual upload 2",
        },
    )

    response = client.get(f"/projects/{project['id']}/manual-image-progress")
    body = response.json()
    assert body["completed_image_tasks_count"] == 2
    assert body["missing_image_tasks_count"] == 0
    assert body["manual_uploaded_count"] == 2
    assert body["next_action"] == "manual_images_completed"


def test_manual_image_progress_prefers_manual_asset_over_mock_asset(client):
    project, shot1, _ = _create_project_graph(client)
    task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(f"/asset-tasks/{task['id']}/run")
    client.post(
        f"/asset-tasks/{task['id']}/manual-asset",
        json={
            "asset_url": "file:///D:/ai-comic-assets/SH01_manual.png",
            "asset_type": "image",
            "notes": "manual preferred",
        },
    )

    response = client.get(f"/projects/{project['id']}/manual-image-progress")
    assert response.status_code == 200
    body = response.json()
    item = next(exported for exported in body["items"] if exported["asset_task_id"] == task["id"])
    assert item["asset_url"] == "file:///D:/ai-comic-assets/SH01_manual.png"
    assert item["manual_upload"] is True
    assert body["manual_uploaded_count"] == 1


def test_manual_image_progress_missing_project_returns_404(client):
    response = client.get("/projects/9999/manual-image-progress")
    assert response.status_code == 404


def test_video_readiness_returns_all_project_video_tasks(client):
    project, shot1, shot2 = _create_project_graph(client)
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock"})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock"})

    response = client.get(f"/projects/{project['id']}/video-readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["video_tasks_count"] == 2
    assert len(body["items"]) == 2


def test_video_readiness_ready_task_has_image_asset_and_duration(client):
    project, shot1, _ = _create_project_graph(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={
            "asset_url": "file:///D:/ai-comic-assets/SH01.png",
            "asset_type": "image",
            "notes": "manual upload",
        },
    )
    video_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()

    response = client.get(f"/projects/{project['id']}/video-readiness")
    item = next(exported for exported in response.json()["items"] if exported["asset_task_id"] == video_task["id"])
    assert item["has_image_asset"] is True
    assert item["image_asset_url"] == "file:///D:/ai-comic-assets/SH01.png"
    assert item["has_duration"] is True
    assert item["duration"] == 3
    assert item["ready_for_video"] is True
    assert item["blocking_issues"] == []


def test_video_readiness_includes_editing_fields(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Video Readiness Editing Fields Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Lin Xia opens the door",
                        "emotion": "nervous",
                        "camera": "medium close-up",
                        "shot_type": "dialogue",
                        "camera_motion": "slow_push_in",
                        "subject_motion": "blink",
                        "transition": "cut",
                        "subtitle_text": "对不起，我走错了。",
                        "sfx": "door_open",
                        "editing_notes": "Push in slightly as she enters.",
                        "dialogue": "Sorry, wrong room.",
                        "image_prompt": "young woman opening a meeting room door",
                        "video_prompt": "office door opens, awkward pause",
                        "voice_prompt": "voice prompt 1",
                        "bgm_prompt": "bgm prompt 1",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": ["SH01"]})
    image_task = next(task for task in client.get(f"/projects/{project_id}/asset-tasks").json() if task["modality"] == "image")
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image"},
    )

    response = client.get(f"/projects/{project_id}/video-readiness")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["shot_type"] == "dialogue"
    assert item["camera_motion"] == "slow_push_in"
    assert item["subject_motion"] == "blink"
    assert item["transition"] == "cut"
    assert item["subtitle_text"] == "对不起，我走错了。"
    assert item["sfx"] == "door_open"
    assert item["editing_notes"] == "Push in slightly as she enters."


def test_video_readiness_prefers_manual_image_asset_url_over_mock_asset(client):
    project, shot1, _ = _create_project_graph(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(f"/asset-tasks/{image_task['id']}/run")
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={
            "asset_url": "file:///D:/ai-comic-assets/SH01_manual.png",
            "asset_type": "image",
            "notes": "manual preferred",
        },
    )
    video_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()

    response = client.get(f"/projects/{project['id']}/video-readiness")
    item = next(exported for exported in response.json()["items"] if exported["asset_task_id"] == video_task["id"])
    assert item["image_asset_url"] == "file:///D:/ai-comic-assets/SH01_manual.png"
    assert item["ready_for_video"] is True


def test_video_readiness_missing_image_asset_sets_blocking_issue(client):
    project, shot1, _ = _create_project_graph(client)
    video_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()

    response = client.get(f"/projects/{project['id']}/video-readiness")
    item = next(exported for exported in response.json()["items"] if exported["asset_task_id"] == video_task["id"])
    assert item["ready_for_video"] is False
    assert "missing_image_asset" in item["blocking_issues"]


def test_video_readiness_missing_duration_sets_blocking_issue(client):
    project, shot1, _ = _create_project_graph(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={
            "asset_url": "file:///D:/ai-comic-assets/SH01.png",
            "asset_type": "image",
            "notes": "manual upload",
        },
    )
    video_task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock"}).json()

    response = client.get(f"/projects/{project['id']}/video-readiness")
    item = next(exported for exported in response.json()["items"] if exported["asset_task_id"] == video_task["id"])
    assert item["ready_for_video"] is False
    assert "missing_duration" in item["blocking_issues"]


def test_video_readiness_all_ready_returns_ready_for_video_generation(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual upload 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual upload 2"},
    )
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}})

    response = client.get(f"/projects/{project['id']}/video-readiness")
    body = response.json()
    assert body["ready_video_tasks_count"] == 2
    assert body["blocked_video_tasks_count"] == 0
    assert body["next_action"] == "ready_for_video_generation"


def test_video_readiness_blocked_tasks_do_not_return_ready_for_video_generation(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual upload"},
    )
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock"})

    response = client.get(f"/projects/{project['id']}/video-readiness")
    body = response.json()
    assert body["blocked_video_tasks_count"] >= 1
    assert body["next_action"] != "ready_for_video_generation"


def test_video_readiness_missing_project_returns_404(client):
    response = client.get("/projects/9999/video-readiness")
    assert response.status_code == 404


def test_project_video_prompts_returns_video_tasks(client):
    project, shot1, shot2 = _create_project_graph(client)
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}})

    response = client.get(f"/projects/{project['id']}/video-prompts")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["items_count"] == 2
    assert len(body["items"]) == 2


def test_project_video_prompts_include_image_asset_url_and_copy_ready_prompt(client):
    project, shot1, _ = _create_project_graph(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image"},
    )
    video_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()

    response = client.get(f"/projects/{project['id']}/video-prompts")
    assert response.status_code == 200
    item = next(exported for exported in response.json()["items"] if exported["asset_task_id"] == video_task["id"])
    assert item["image_asset_url"] == "file:///D:/ai-comic-assets/SH01.png"
    assert item["copy_ready_video_prompt"]
    assert item["negative_prompt"] in item["copy_ready_video_prompt"]
    assert item["ready_for_video_prompt"] is True


def test_project_video_prompts_include_editing_fields_and_prompt_clauses(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Video Editing Fields Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Lin Xia opens the door",
                        "emotion": "nervous",
                        "camera": "medium close-up",
                        "shot_type": "dialogue",
                        "camera_motion": "slow_push_in",
                        "subject_motion": "natural blinking and subtle mouth movement",
                        "transition": "cut",
                        "subtitle_text": "对不起，我走错了。",
                        "sfx": "door_open",
                        "editing_notes": "Push in slightly as she enters.",
                        "dialogue": "Sorry, wrong room.",
                        "image_prompt": "young woman opening a meeting room door",
                        "video_prompt": "office door opens, awkward pause",
                        "voice_prompt": "voice prompt 1",
                        "bgm_prompt": "bgm prompt 1",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": ["SH01"]})
    image_task = next(task for task in client.get(f"/projects/{project_id}/asset-tasks").json() if task["modality"] == "image")
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image"},
    )

    response = client.get(f"/projects/{project_id}/video-prompts")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["shot_type"] == "dialogue"
    assert item["camera_motion"] == "slow_push_in"
    assert item["subject_motion"] == "natural blinking and subtle mouth movement"
    assert item["transition"] == "cut"
    assert item["subtitle_text"] == "对不起，我走错了。"
    assert item["sfx"] == "door_open"
    assert item["editing_notes"] == "Push in slightly as she enters."
    assert "Camera motion: slow_push_in" in item["copy_ready_video_prompt"]
    assert "Subject motion: natural blinking and subtle mouth movement" in item["copy_ready_video_prompt"]
    assert "Subtitle cue: 对不起，我走错了。" in item["copy_ready_video_prompt"]
    assert "Sound effect cue: door_open" in item["copy_ready_video_prompt"]
    assert "Editing notes: Push in slightly as she enters." in item["copy_ready_video_prompt"]


def test_project_video_prompts_prefers_manual_image_asset_url_over_mock_asset(client):
    project, shot1, _ = _create_project_graph(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(f"/asset-tasks/{image_task['id']}/run")
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={
            "asset_url": "file:///D:/ai-comic-assets/SH01_manual.png",
            "asset_type": "image",
            "notes": "manual preferred",
        },
    )
    video_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()

    response = client.get(f"/projects/{project['id']}/video-prompts")
    assert response.status_code == 200
    item = next(exported for exported in response.json()["items"] if exported["asset_task_id"] == video_task["id"])
    assert item["image_asset_url"] == "file:///D:/ai-comic-assets/SH01_manual.png"


def test_project_video_prompts_missing_image_asset_returns_blocking_issue(client):
    project, shot1, _ = _create_project_graph(client)
    video_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()

    response = client.get(f"/projects/{project['id']}/video-prompts")
    assert response.status_code == 200
    item = next(exported for exported in response.json()["items"] if exported["asset_task_id"] == video_task["id"])
    assert item["image_asset_url"] is None
    assert item["ready_for_video_prompt"] is False
    assert "missing_image_asset" in item["blocking_issues"]


def test_project_video_prompts_missing_project_returns_404(client):
    response = client.get("/projects/9999/video-prompts")
    assert response.status_code == 404


def test_manual_video_progress_returns_all_project_video_tasks(client):
    project, shot1, shot2 = _create_project_graph(client)
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock"})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock"})

    response = client.get(f"/projects/{project['id']}/manual-video-progress")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["video_tasks_count"] == 2
    assert len(body["items"]) == 2


def test_manual_video_progress_shows_manual_uploaded_task(client):
    project, shot1, _ = _create_project_graph(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image"},
    )
    video_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video"},
    )

    response = client.get(f"/projects/{project['id']}/manual-video-progress")
    assert response.status_code == 200
    item = next(exported for exported in response.json()["items"] if exported["asset_task_id"] == video_task["id"])
    assert item["has_asset"] is True
    assert item["manual_upload"] is True
    assert item["needs_manual_video"] is False
    assert item["asset_url"] == "file:///D:/ai-comic-assets/SH01_video.mp4"
    assert item["duration"] == 3


def test_manual_video_progress_shows_missing_items_and_continue_action(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image"},
    )
    ready_video_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    missing_video_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock"},
    ).json()
    client.post(
        f"/asset-tasks/{ready_video_task['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video"},
    )

    response = client.get(f"/projects/{project['id']}/manual-video-progress")
    body = response.json()
    item = next(exported for exported in body["items"] if exported["asset_task_id"] == missing_video_task["id"])
    assert item["has_asset"] is False
    assert item["needs_manual_video"] is True
    assert body["completed_video_tasks_count"] == 1
    assert body["missing_video_tasks_count"] == 1
    assert body["manual_uploaded_count"] == 1
    assert body["next_action"] == "continue_manual_video_generation"


def test_manual_video_progress_all_completed_returns_manual_videos_completed(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    video_task_1 = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    video_task_2 = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task_1['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video 1"},
    )
    client.post(
        f"/asset-tasks/{video_task_2['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02_video.mp4", "asset_type": "video", "notes": "manual video 2"},
    )

    response = client.get(f"/projects/{project['id']}/manual-video-progress")
    body = response.json()
    assert body["completed_video_tasks_count"] == 2
    assert body["missing_video_tasks_count"] == 0
    assert body["manual_uploaded_count"] == 2
    assert body["next_action"] == "manual_videos_completed"


def test_manual_video_progress_prefers_manual_asset_over_mock_asset(client):
    project, shot1, _ = _create_project_graph(client)
    video_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    client.post(f"/asset-tasks/{video_task['id']}/run")
    client.post(
        f"/asset-tasks/{video_task['id']}/manual-video-asset",
        json={
            "asset_url": "file:///D:/AI漫剧-视频素材库/走错会议室.mp4",
            "asset_type": "video",
            "notes": "manual preferred",
        },
    )

    response = client.get(f"/projects/{project['id']}/manual-video-progress")
    assert response.status_code == 200
    body = response.json()
    item = next(exported for exported in body["items"] if exported["asset_task_id"] == video_task["id"])
    assert item["asset_url"] == "file:///D:/AI漫剧-视频素材库/走错会议室.mp4"
    assert item["manual_upload"] is True
    assert body["manual_uploaded_count"] == 1


def test_manual_video_progress_missing_project_returns_404(client):
    response = client.get("/projects/9999/manual-video-progress")
    assert response.status_code == 404


def test_manual_production_summary_returns_three_sections(client):
    project, shot1, shot2 = _create_project_graph(client)
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"})
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock"})

    response = client.get(f"/projects/{project['id']}/manual-production-summary")
    assert response.status_code == 200
    body = response.json()
    assert "image" in body
    assert "video_readiness" in body
    assert "video" in body


def test_manual_production_summary_stage_manual_image_generation(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"})
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image"},
    )
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}})

    response = client.get(f"/projects/{project['id']}/manual-production-summary")
    body = response.json()
    assert body["stage"] == "manual_image_generation"
    assert body["next_action"] == "continue_manual_image_generation"


def test_manual_production_summary_stage_video_input_fixing(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock"})

    response = client.get(f"/projects/{project['id']}/manual-production-summary")
    body = response.json()
    assert body["stage"] == "video_input_fixing"
    assert body["next_action"] == "fix_video_inputs"


def test_manual_production_summary_stage_manual_video_generation(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}})

    response = client.get(f"/projects/{project['id']}/manual-production-summary")
    body = response.json()
    assert body["stage"] == "manual_video_generation"
    assert body["next_action"] == "continue_manual_video_generation"


def test_manual_production_summary_stage_completed(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    video_task_1 = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    video_task_2 = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task_1['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video 1"},
    )
    client.post(
        f"/asset-tasks/{video_task_2['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02_video.mp4", "asset_type": "video", "notes": "manual video 2"},
    )

    response = client.get(f"/projects/{project['id']}/manual-production-summary")
    body = response.json()
    assert body["stage"] == "manual_production_completed"
    assert body["next_action"] == "ready_for_publish_or_composition"


def test_manual_production_summary_recommended_steps_not_empty(client):
    project, shot1, _ = _create_project_graph(client)
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"})

    response = client.get(f"/projects/{project['id']}/manual-production-summary")
    body = response.json()
    assert body["recommended_steps"]


def test_manual_production_summary_missing_project_returns_404(client):
    response = client.get("/projects/9999/manual-production-summary")
    assert response.status_code == 404


def test_publish_readiness_returns_missing_image_assets(client):
    project, shot1, shot2 = _create_project_graph(client)
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"})
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}})

    response = client.get(f"/projects/{project['id']}/publish-readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["ready_for_publish"] is False
    assert body["stage"] == "manual_image_generation"
    assert body["next_action"] == "continue_manual_image_generation"
    assert "missing_image_assets" in body["blocking_issues"]


def test_publish_readiness_returns_missing_video_assets(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}})

    response = client.get(f"/projects/{project['id']}/publish-readiness")
    body = response.json()
    assert body["ready_for_publish"] is False
    assert body["stage"] == "manual_video_generation"
    assert body["next_action"] == "continue_manual_video_generation"
    assert "missing_video_assets" in body["blocking_issues"]


def test_publish_readiness_returns_ready_when_image_and_video_complete(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    video_task_1 = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    video_task_2 = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task_1['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video 1"},
    )
    client.post(
        f"/asset-tasks/{video_task_2['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02_video.mp4", "asset_type": "video", "notes": "manual video 2"},
    )

    response = client.get(f"/projects/{project['id']}/publish-readiness")
    body = response.json()
    assert body["ready_for_publish"] is True
    assert body["stage"] == "ready_for_publish"
    assert body["next_action"] == "create_publish_record"


def test_publish_readiness_returns_failed_tasks_exist(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    video_task_1 = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    video_task_2 = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task_1['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video 1"},
    )
    client.post(
        f"/asset-tasks/{video_task_2['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02_video.mp4", "asset_type": "video", "notes": "manual video 2"},
    )
    failing_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "voice", "provider_name": "mock", "input_payload": {"should_fail": True}},
    ).json()
    client.post(f"/asset-tasks/{failing_task['id']}/run")

    response = client.get(f"/projects/{project['id']}/publish-readiness")
    body = response.json()
    assert body["ready_for_publish"] is False
    assert body["stage"] == "review_failed_tasks"
    assert body["next_action"] == "review_failed_tasks"
    assert "failed_tasks_exist" in body["blocking_issues"]


def test_publish_readiness_returns_needs_human_revision_tasks_exist(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    video_task_1 = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    video_task_2 = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task_1['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video 1"},
    )
    client.post(
        f"/asset-tasks/{video_task_2['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02_video.mp4", "asset_type": "video", "notes": "manual video 2"},
    )
    client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "voice", "provider_name": "mock", "retry_count": 4, "max_retries": 3},
    )

    response = client.get(f"/projects/{project['id']}/publish-readiness")
    body = response.json()
    assert body["ready_for_publish"] is False
    assert body["stage"] == "review_human_revision_tasks"
    assert body["next_action"] == "review_human_revision_tasks"
    assert "needs_human_revision_tasks_exist" in body["blocking_issues"]


def test_publish_readiness_returns_completed_when_publish_record_exists(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    video_task_1 = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    video_task_2 = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task_1['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video 1"},
    )
    client.post(
        f"/asset-tasks/{video_task_2['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02_video.mp4", "asset_type": "video", "notes": "manual video 2"},
    )
    client.post(
        "/publish-records",
        json={
            "project_id": project["id"],
            "platform": "douyin",
            "title": "Episode 1",
            "published_at": "2026-04-26T10:00:00",
            "link": "https://www.douyin.com/video/demo",
        },
    )

    response = client.get(f"/projects/{project['id']}/publish-readiness")
    body = response.json()
    assert body["ready_for_publish"] is True
    assert body["stage"] == "published"
    assert body["next_action"] == "completed"
    assert body["checks"]["has_publish_record"] is True


def test_publish_readiness_missing_project_returns_404(client):
    response = client.get("/projects/9999/publish-readiness")
    assert response.status_code == 404


def test_manual_final_checklist_returns_sections_and_recommended_steps(client):
    project, shot1, _ = _create_project_graph(client)
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"})

    response = client.get(f"/projects/{project['id']}/manual-final-checklist")
    assert response.status_code == 200
    body = response.json()
    assert "production_stage" in body
    assert "publish_stage" in body
    assert "checks" in body
    assert body["recommended_steps"]


def test_manual_final_checklist_not_ready_when_manual_production_incomplete(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"})
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image"},
    )

    response = client.get(f"/projects/{project['id']}/manual-final-checklist")
    body = response.json()
    assert body["ready_for_delivery"] is False
    assert body["production_stage"] == "manual_image_generation"
    assert body["next_action"] == "continue_manual_image_generation"
    assert "manual_production_not_completed" in body["blocking_issues"]


def test_manual_final_checklist_not_ready_when_publish_readiness_blocked(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    video_task_1 = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    video_task_2 = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task_1['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video 1"},
    )
    client.post(
        f"/asset-tasks/{video_task_2['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02_video.mp4", "asset_type": "video", "notes": "manual video 2"},
    )
    failing_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "voice", "provider_name": "mock", "input_payload": {"should_fail": True}},
    ).json()
    client.post(f"/asset-tasks/{failing_task['id']}/run")

    response = client.get(f"/projects/{project['id']}/manual-final-checklist")
    body = response.json()
    assert body["ready_for_delivery"] is False
    assert body["publish_stage"] == "review_failed_tasks"
    assert "failed_tasks_exist" in body["blocking_issues"]


def test_manual_final_checklist_ready_without_publish_record(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    video_task_1 = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    video_task_2 = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task_1['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video 1"},
    )
    client.post(
        f"/asset-tasks/{video_task_2['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02_video.mp4", "asset_type": "video", "notes": "manual video 2"},
    )

    response = client.get(f"/projects/{project['id']}/manual-final-checklist")
    body = response.json()
    assert body["ready_for_delivery"] is True
    assert body["publish_stage"] == "ready_for_publish"
    assert body["next_action"] == "create_publish_record"


def test_manual_final_checklist_completed_when_publish_record_exists(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    video_task_1 = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    video_task_2 = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task_1['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video 1"},
    )
    client.post(
        f"/asset-tasks/{video_task_2['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02_video.mp4", "asset_type": "video", "notes": "manual video 2"},
    )
    client.post(
        "/publish-records",
        json={
            "project_id": project["id"],
            "platform": "douyin",
            "title": "Episode 1",
            "published_at": "2026-04-26T10:00:00",
            "link": "https://www.douyin.com/video/demo",
        },
    )

    response = client.get(f"/projects/{project['id']}/manual-final-checklist")
    body = response.json()
    assert body["ready_for_delivery"] is True
    assert body["next_action"] == "completed"
    assert body["checks"]["publish_record_exists"] is True


def test_manual_final_checklist_includes_failed_tasks_exist(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    video_task_1 = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    video_task_2 = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task_1['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video 1"},
    )
    client.post(
        f"/asset-tasks/{video_task_2['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02_video.mp4", "asset_type": "video", "notes": "manual video 2"},
    )
    failing_task = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "voice", "provider_name": "mock", "input_payload": {"should_fail": True}},
    ).json()
    client.post(f"/asset-tasks/{failing_task['id']}/run")

    response = client.get(f"/projects/{project['id']}/manual-final-checklist")
    body = response.json()
    assert "failed_tasks_exist" in body["blocking_issues"]


def test_manual_final_checklist_includes_needs_human_revision_tasks_exist(client):
    project, shot1, shot2 = _create_project_graph(client)
    image_task_1 = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    image_task_2 = client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task_1['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image 1"},
    )
    client.post(
        f"/asset-tasks/{image_task_2['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02.png", "asset_type": "image", "notes": "manual image 2"},
    )
    video_task_1 = client.post(
        "/asset-tasks",
        json={"shot_id": shot1["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 3}},
    ).json()
    video_task_2 = client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock", "input_payload": {"duration": 5}},
    ).json()
    client.post(
        f"/asset-tasks/{video_task_1['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4", "asset_type": "video", "notes": "manual video 1"},
    )
    client.post(
        f"/asset-tasks/{video_task_2['id']}/manual-video-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH02_video.mp4", "asset_type": "video", "notes": "manual video 2"},
    )
    client.post(
        "/asset-tasks",
        json={"shot_id": shot2["id"], "modality": "voice", "provider_name": "mock", "retry_count": 4, "max_retries": 3},
    )

    response = client.get(f"/projects/{project['id']}/manual-final-checklist")
    body = response.json()
    assert "needs_human_revision_tasks_exist" in body["blocking_issues"]


def test_manual_final_checklist_missing_project_returns_404(client):
    response = client.get("/projects/9999/manual-final-checklist")
    assert response.status_code == 404


def test_project_provider_debug_summary_includes_image_enhanced_prompt(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Provider Debug Image Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "comic-realism",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
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
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": []})
    client.post(f"/coze/project/{project_id}/run-asset-tasks")

    response = client.get(f"/projects/{project_id}/provider-debug-summary")
    body = response.json()
    image_item = next(item for item in body["items"] if item["modality"] == "image")
    assert image_item["enhanced_prompt"] is not None
    assert image_item["storyboard_context"]["source_shot_id"] == "SH01"


def test_project_provider_debug_summary_includes_video_image_url_and_duration(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Provider Debug Video Summary Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "comic-realism",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 7,
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
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": ["SH01"]})
    client.post(f"/coze/project/{project_id}/run-asset-tasks")

    response = client.get(f"/projects/{project_id}/provider-debug-summary")
    body = response.json()
    video_item = next(item for item in body["items"] if item["modality"] == "video")
    assert video_item["input_payload"]["image_url"].startswith("https://mock.assets/image/")
    assert video_item["input_payload"]["duration"] == 7


def test_project_provider_debug_summary_counts_statuses(client):
    project, shot1, shot2 = _create_project_graph(client)
    client.post(
        "/asset-tasks",
        json={
            "shot_id": shot1["id"],
            "modality": "image",
            "provider_name": "mock",
            "input_payload": {"should_fail": True},
        },
    )
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "image", "provider_name": "mock"})
    client.post(f"/projects/{project['id']}/asset-tasks/run-bulk")

    response = client.get(f"/projects/{project['id']}/provider-debug-summary")
    body = response.json()
    assert body["summary"]["succeeded_count"] == 1
    assert body["summary"]["failed_count"] == 1
    assert body["summary"]["needs_human_revision_count"] == 0


def test_project_provider_debug_summary_returns_404_for_missing_project(client):
    response = client.get("/projects/999999/provider-debug-summary")
    assert response.status_code == 404


def test_project_provider_debug_summary_counts_dry_run_and_blocked_real_provider_tasks(client, monkeypatch):
    monkeypatch.setenv("ENABLE_REAL_IMAGE_PROVIDER", "true")
    monkeypatch.setenv("IMAGE_PROVIDER_MODE", "image2_real")
    monkeypatch.setenv("IMAGE2_API_KEY", "fake-key")
    monkeypatch.setenv("IMAGE2_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("IMAGE2_DRY_RUN", "true")
    monkeypatch.setenv("IMAGE2_MAX_REAL_CALLS_PER_RUN", "1")
    from app.core.config import get_settings
    from app.services.asset_task_service import reset_image2_real_call_counter
    get_settings.cache_clear()
    reset_image2_real_call_counter()

    project, shot1, _ = _create_project_graph(client)
    task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "image2_real"}).json()
    monkeypatch.setenv("IMAGE2_ALLOW_TASK_IDS", str(task["id"]))
    get_settings.cache_clear()

    client.post(f"/asset-tasks/{task['id']}/run")
    response = client.get(f"/projects/{project['id']}/provider-debug-summary")
    assert response.status_code == 200
    body = response.json()
    item = next(entry for entry in body["items"] if entry["asset_task_id"] == task["id"])
    assert item["provider_audit"]["provider_name"] == "image2_real"
    assert item["blocked_reason"] == "IMAGE2_DRY_RUN is true."
    assert item["dry_run"] is True
    assert item["real_call"] is False
    assert item["preflight_passed"] is False
    assert body["summary"]["dry_run_tasks_count"] == 1
    assert body["summary"]["blocked_real_provider_tasks_count"] == 1
    get_settings.cache_clear()
    reset_image2_real_call_counter()


def test_project_provider_readiness_returns_ready_for_complete_mock_project(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Provider Readiness Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "comic-realism",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 7,
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
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": ["SH01"]})
    client.post(f"/coze/project/{project_id}/run-asset-tasks")

    response = client.get(f"/projects/{project_id}/provider-readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["ready_for_image_provider"] is True
    assert body["ready_for_video_provider"] is True
    assert body["blocking_issues"] == []


def test_project_provider_readiness_returns_blocking_issues_for_missing_debug_requirements(client):
    project, shot1, shot2 = _create_project_graph(client)
    client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"})
    client.post("/asset-tasks", json={"shot_id": shot2["id"], "modality": "video", "provider_name": "mock"})

    response = client.get(f"/projects/{project['id']}/provider-readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["ready_for_image_provider"] is False
    assert body["ready_for_video_provider"] is False
    assert any("missing enhanced_prompt" in issue.lower() for issue in body["blocking_issues"])
    assert any("missing image_url" in issue.lower() for issue in body["blocking_issues"])


def test_project_provider_readiness_returns_404_for_missing_project(client):
    response = client.get("/projects/999999/provider-readiness")
    assert response.status_code == 404


def test_editing_shot_board_returns_all_project_shots(client):
    project, shot1, shot2 = _create_project_graph(client)
    response = client.get(f"/projects/{project['id']}/editing-shot-board")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["shots_count"] == 2
    assert len(body["items"]) == 2


def test_editing_shot_board_prefers_manual_image_asset_url(client):
    project, shot1, _ = _create_project_graph(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(f"/asset-tasks/{image_task['id']}/run")
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={
            "asset_url": "file:///D:/AI漫剧图片库/SH01.png",
            "asset_type": "image",
            "notes": "manual preferred",
        },
    )

    response = client.get(f"/projects/{project['id']}/editing-shot-board")
    assert response.status_code == 200
    item = next(exported for exported in response.json()["items"] if exported["internal_shot_id"] == shot1["id"])
    assert item["image_asset_url"] == "file:///D:/AI漫剧图片库/SH01.png"
    assert item["has_image_asset"] is True


def test_editing_shot_board_missing_image_asset_returns_blocking_issue(client):
    project, shot1, _ = _create_project_graph(client)
    response = client.get(f"/projects/{project['id']}/editing-shot-board")
    assert response.status_code == 200
    item = next(exported for exported in response.json()["items"] if exported["internal_shot_id"] == shot1["id"])
    assert item["ready_for_editing"] is False
    assert "missing_image_asset" in item["blocking_issues"]
    assert response.json()["next_action"] == "continue_image_generation"


def test_editing_shot_board_old_payload_without_editing_fields_does_not_crash(client):
    project, shot1, _ = _create_project_graph(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={"asset_url": "file:///D:/ai-comic-assets/SH01.png", "asset_type": "image", "notes": "manual image"},
    )

    response = client.get(f"/projects/{project['id']}/editing-shot-board")
    assert response.status_code == 200
    item = next(exported for exported in response.json()["items"] if exported["internal_shot_id"] == shot1["id"])
    assert item["shot_type"] is None
    assert "missing_editing_fields" in item["blocking_issues"]


def test_editing_shot_board_returns_editing_fields(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Editing Shot Board Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Lin Xia opens the door",
                        "emotion": "nervous",
                        "camera": "medium close-up",
                        "shot_type": "dialogue",
                        "camera_motion": "slow_push_in",
                        "subject_motion": "blink, slight_body_shift",
                        "transition": "cut",
                        "subtitle_text": "Sorry, wrong room.",
                        "sfx": "door_open",
                        "editing_notes": "Use slight zoom-in and nervous pause.",
                        "dialogue": "Sorry, wrong room.",
                        "image_prompt": "young woman opening a meeting room door",
                        "video_prompt": "office door opens, awkward pause",
                        "voice_prompt": "voice prompt 1",
                        "bgm_prompt": "bgm prompt 1",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    tasks_response = client.post(f"/coze/project/{project_id}/create-asset-tasks", json={})
    assert tasks_response.status_code == 200
    project_summary = client.get(f"/projects/{project_id}/summary").json()
    assert project_summary["shots_count"] == 1

    board_response = client.get(f"/projects/{project_id}/editing-shot-board")
    assert board_response.status_code == 200
    item = board_response.json()["items"][0]
    assert item["shot_type"] == "dialogue"
    assert item["camera_motion"] == "slow_push_in"
    assert item["subject_motion"] == "blink, slight_body_shift"
    assert item["transition"] == "cut"
    assert item["subtitle_text"] == "Sorry, wrong room."
    assert item["sfx"] == "door_open"
    assert item["editing_notes"] == "Use slight zoom-in and nervous pause."


def test_editing_shot_board_all_ready_returns_ready_for_manual_editing(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Editing Board Ready Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Lin Xia opens the door",
                        "emotion": "nervous",
                        "camera": "medium close-up",
                        "shot_type": "dialogue",
                        "camera_motion": "slow_push_in",
                        "subject_motion": "blink",
                        "transition": "cut",
                        "subtitle_text": "Sorry, wrong room.",
                        "sfx": "door_open",
                        "editing_notes": "Use slight zoom-in and nervous pause.",
                        "dialogue": "Sorry, wrong room.",
                        "image_prompt": "young woman opening a meeting room door",
                        "video_prompt": "office door opens, awkward pause",
                        "voice_prompt": "voice prompt 1",
                        "bgm_prompt": "bgm prompt 1",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={})
    tasks = client.get(f"/projects/{project_id}/asset-tasks").json()
    image_task = next(task for task in tasks if task["modality"] == "image")
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={"asset_url": "file:///D:/AI漫剧图片库/SH01.png", "asset_type": "image", "notes": "manual image"},
    )

    response = client.get(f"/projects/{project_id}/editing-shot-board")
    assert response.status_code == 200
    body = response.json()
    assert body["ready_shots_count"] == 1
    assert body["blocked_shots_count"] == 0
    assert body["next_action"] == "ready_for_manual_editing"


def test_editing_shot_board_missing_project_returns_404(client):
    response = client.get("/projects/999999/editing-shot-board")
    assert response.status_code == 404


def test_editing_timeline_returns_items_in_shot_order_and_computes_times(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Editing Timeline Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Lin Xia opens the door",
                        "emotion": "nervous",
                        "camera": "medium close-up",
                        "shot_type": "dialogue",
                        "camera_motion": "slow_push_in",
                        "subject_motion": "blink",
                        "transition": "cut",
                        "subtitle_text": "Sorry, wrong room.",
                        "sfx": "door_open",
                        "editing_notes": "Use slight zoom-in and nervous pause.",
                        "dialogue": "Sorry, wrong room.",
                        "image_prompt": "young woman opening a meeting room door",
                        "video_prompt": "office door opens, awkward pause",
                        "voice_prompt": "voice prompt 1",
                        "bgm_prompt": "bgm prompt 1",
                        "status": "prompt_ready",
                    },
                    {
                        "shot_id": "SH02",
                        "duration_sec": 5,
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Everyone stares at Lin Xia",
                        "emotion": "awkward",
                        "camera": "wide shot",
                        "shot_type": "reaction",
                        "camera_motion": "static",
                        "subject_motion": "slight_body_shift",
                        "transition": "cut",
                        "subtitle_text": "……",
                        "sfx": "room_tension",
                        "editing_notes": "Hold for reaction.",
                        "dialogue": "…",
                        "image_prompt": "everyone stares in silence",
                        "video_prompt": "room goes silent",
                        "voice_prompt": "silence",
                        "bgm_prompt": "tension",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={})
    tasks = client.get(f"/projects/{project_id}/asset-tasks").json()
    image_tasks = [task for task in tasks if task["modality"] == "image"]
    client.post(
        f"/asset-tasks/{image_tasks[0]['id']}/manual-asset",
        json={"asset_url": "file:///D:/AI漫剧图片库/SH01.png", "asset_type": "image", "notes": "manual 1"},
    )
    client.post(
        f"/asset-tasks/{image_tasks[1]['id']}/manual-asset",
        json={"asset_url": "file:///D:/AI漫剧图片库/SH02.png", "asset_type": "image", "notes": "manual 2"},
    )

    response = client.get(f"/projects/{project_id}/editing-timeline")
    assert response.status_code == 200
    body = response.json()
    assert body["shots_count"] == 2
    assert body["total_duration"] == 8
    assert body["items"][0]["source_shot_id"] == "SH01"
    assert body["items"][0]["start_time"] == 0
    assert body["items"][0]["end_time"] == 3
    assert body["items"][1]["source_shot_id"] == "SH02"
    assert body["items"][1]["start_time"] == 3
    assert body["items"][1]["end_time"] == 8


def test_editing_timeline_prefers_manual_image_asset_url(client):
    project, shot1, _ = _create_project_graph(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot1["id"], "modality": "image", "provider_name": "mock"}).json()
    client.post(f"/asset-tasks/{image_task['id']}/run")
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={"asset_url": "file:///D:/AI漫剧图片库/SH01.png", "asset_type": "image", "notes": "manual preferred"},
    )

    response = client.get(f"/projects/{project['id']}/editing-timeline")
    assert response.status_code == 200
    item = next(exported for exported in response.json()["items"] if exported["internal_shot_id"] == shot1["id"])
    assert item["image_asset_url"] == "file:///D:/AI漫剧图片库/SH01.png"


def test_editing_timeline_missing_image_asset_blocks_timeline(client):
    project, _, _ = _create_project_graph(client)
    response = client.get(f"/projects/{project['id']}/editing-timeline")
    assert response.status_code == 200
    body = response.json()
    assert body["ready_for_timeline"] is False
    assert "missing_image_asset" in body["blocking_issues"]


def test_editing_timeline_missing_duration_defaults_to_three_seconds(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Editing Timeline Default Duration Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Lin Xia opens the door",
                        "emotion": "nervous",
                        "camera": "medium close-up",
                        "shot_type": "dialogue",
                        "camera_motion": "slow_push_in",
                        "subject_motion": "blink",
                        "transition": "cut",
                        "subtitle_text": "Sorry, wrong room.",
                        "sfx": "door_open",
                        "editing_notes": "Use slight zoom-in and nervous pause.",
                        "dialogue": "Sorry, wrong room.",
                        "image_prompt": "young woman opening a meeting room door",
                        "video_prompt": "office door opens, awkward pause",
                        "voice_prompt": "voice prompt 1",
                        "bgm_prompt": "bgm prompt 1",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={})
    tasks = client.get(f"/projects/{project_id}/asset-tasks").json()
    image_task = next(task for task in tasks if task["modality"] == "image")
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={"asset_url": "file:///D:/AI漫剧图片库/SH01.png", "asset_type": "image", "notes": "manual image"},
    )

    response = client.get(f"/projects/{project_id}/editing-timeline")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["duration"] == 3
    assert "duration_defaulted" in item["warnings"]


def test_editing_timeline_all_ready_returns_ready_for_manual_timeline_editing(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Editing Timeline Ready Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(f"/characters/{character_id}/confirm-reference", json={"main_reference_url": "mock://character/reference.png"})
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "Lin Xia",
                        "location": "Meeting Room",
                        "core_action": "Lin Xia opens the door",
                        "emotion": "nervous",
                        "camera": "medium close-up",
                        "shot_type": "dialogue",
                        "camera_motion": "slow_push_in",
                        "subject_motion": "blink",
                        "transition": "cut",
                        "subtitle_text": "Sorry, wrong room.",
                        "sfx": "door_open",
                        "editing_notes": "Use slight zoom-in and nervous pause.",
                        "dialogue": "Sorry, wrong room.",
                        "image_prompt": "young woman opening a meeting room door",
                        "video_prompt": "office door opens, awkward pause",
                        "voice_prompt": "voice prompt 1",
                        "bgm_prompt": "bgm prompt 1",
                        "status": "prompt_ready",
                    }
                ]
            },
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={})
    tasks = client.get(f"/projects/{project_id}/asset-tasks").json()
    image_task = next(task for task in tasks if task["modality"] == "image")
    client.post(
        f"/asset-tasks/{image_task['id']}/manual-asset",
        json={"asset_url": "file:///D:/AI漫剧图片库/SH01.png", "asset_type": "image", "notes": "manual image"},
    )

    response = client.get(f"/projects/{project_id}/editing-timeline")
    assert response.status_code == 200
    body = response.json()
    assert body["ready_for_timeline"] is True
    assert body["next_action"] == "ready_for_manual_timeline_editing"


def test_editing_timeline_missing_project_returns_404(client):
    response = client.get("/projects/999999/editing-timeline")
    assert response.status_code == 404


def _create_editing_cue_sheet_project(
    client,
    *,
    shots: list[dict],
    upload_manual_images: bool = False,
):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Editing Cue Sheet Demo",
            "genre": "urban",
            "platform": "coze",
            "target_duration": 60,
            "target_audience": "young-adult",
            "visual_style": "anime-comic",
            "core_conflict": "identity confusion",
            "hook": "wrong room",
            "ending_hook": "unexpected promotion",
            "selling_points": ["fast"],
            "status": "draft",
        },
        "characters_json": {
            "characters": [
                {
                    "name": "Lin Xia",
                    "role": "lead",
                    "main_reference_confirmed": False,
                }
            ]
        },
    }).json()
    project_id = init["data"]["project_id"]
    character_id = init["data"]["character_ids"][0]
    client.post(
        f"/characters/{character_id}/confirm-reference",
        json={"main_reference_url": "mock://character/reference.png"},
    )
    client.post(
        f"/coze/project/{project_id}/storyboard",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {"shots": shots},
        },
    )
    client.post(f"/coze/project/{project_id}/create-asset-tasks", json={})
    tasks = client.get(f"/projects/{project_id}/asset-tasks").json()
    if upload_manual_images:
        for task in tasks:
            if task["modality"] == "image":
                shot_id = task["shot_id"]
                client.post(
                    f"/asset-tasks/{task['id']}/manual-asset",
                    json={
                        "asset_url": f"file:///D:/AI漫剧图片库/shot_{shot_id}.png",
                        "asset_type": "image",
                        "notes": "manual image",
                    },
                )
    return project_id


def test_editing_cue_sheet_returns_items_and_plain_text(client):
    project_id = _create_editing_cue_sheet_project(
        client,
        shots=[
            {
                "shot_id": "SH01",
                "duration_sec": 3,
                "character": "Lin Xia",
                "location": "Meeting Room",
                "core_action": "Lin Xia opens the door",
                "emotion": "nervous",
                "camera": "medium close-up",
                "dialogue": "不好意思，我走错了。",
                "shot_type": "dialogue",
                "camera_motion": "slow_push_in",
                "subject_motion": "blink, slight_body_shift",
                "transition": "cut",
                "subtitle_text": "不好意思，我走错了。",
                "sfx": "door_open",
                "editing_notes": "Use slight zoom-in and nervous pause.",
                "image_prompt": "young woman opening a meeting room door",
                "video_prompt": "office door opens, awkward pause",
                "voice_prompt": "voice prompt 1",
                "bgm_prompt": "bgm prompt 1",
                "status": "prompt_ready",
            },
            {
                "shot_id": "SH02",
                "duration_sec": 5,
                "character": "Lin Xia",
                "location": "Meeting Room",
                "core_action": "Coworker mocks her",
                "emotion": "tense",
                "camera": "close-up",
                "dialogue": "你怎么又走错了？",
                "shot_type": "reaction",
                "camera_motion": "zoom_in",
                "subject_motion": "mouth_move",
                "transition": "cut",
                "subtitle_text": "你怎么又走错了？",
                "sfx": "crowd_murmur",
                "editing_notes": "Hold for reaction beat.",
                "image_prompt": "coworker mocking in meeting room",
                "video_prompt": "awkward office reaction shot",
                "voice_prompt": "voice prompt 2",
                "bgm_prompt": "bgm prompt 2",
                "status": "prompt_ready",
            },
        ],
        upload_manual_images=True,
    )

    response = client.get(f"/projects/{project_id}/editing-cue-sheet")
    assert response.status_code == 200
    body = response.json()
    assert body["shots_count"] == 2
    assert len(body["items"]) == 2
    assert body["plain_text"]
    first = body["items"][0]
    assert "SH01" in first["cue_line"]
    assert "0.0s-3.0s" in first["cue_line"]
    assert "图片:" in first["cue_line"]
    assert "字幕:" in first["cue_line"]
    assert "音效:" in first["cue_line"]
    assert "镜头:" in first["cue_line"]
    assert "人物微动:" in first["cue_line"]
    assert "转场:" in first["cue_line"]
    assert "备注:" in first["cue_line"]
    assert first["cue_line"] in body["plain_text"]
    assert body["items"][1]["cue_line"] in body["plain_text"]


def test_editing_cue_sheet_prefers_manual_image_asset_url(client):
    project_id = _create_editing_cue_sheet_project(
        client,
        shots=[
            {
                "shot_id": "SH01",
                "duration_sec": 3,
                "character": "Lin Xia",
                "location": "Meeting Room",
                "core_action": "Lin Xia opens the door",
                "emotion": "nervous",
                "camera": "medium close-up",
                "dialogue": "不好意思，我走错了。",
                "shot_type": "dialogue",
                "camera_motion": "slow_push_in",
                "subject_motion": "blink",
                "transition": "cut",
                "subtitle_text": "不好意思，我走错了。",
                "sfx": "door_open",
                "editing_notes": "Use slight zoom-in and nervous pause.",
                "image_prompt": "young woman opening a meeting room door",
                "video_prompt": "office door opens, awkward pause",
                "voice_prompt": "voice prompt 1",
                "bgm_prompt": "bgm prompt 1",
                "status": "prompt_ready",
            }
        ],
        upload_manual_images=True,
    )

    response = client.get(f"/projects/{project_id}/editing-cue-sheet")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["image_asset_url"].startswith("file:///D:/AI漫剧图片库/")


def test_editing_cue_sheet_missing_image_blocks_export(client):
    project_id = _create_editing_cue_sheet_project(
        client,
        shots=[
            {
                "shot_id": "SH01",
                "duration_sec": 3,
                "character": "Lin Xia",
                "location": "Meeting Room",
                "core_action": "Lin Xia opens the door",
                "emotion": "nervous",
                "camera": "medium close-up",
                "dialogue": "不好意思，我走错了。",
                "shot_type": "dialogue",
                "camera_motion": "slow_push_in",
                "subject_motion": "blink",
                "transition": "cut",
                "subtitle_text": "不好意思，我走错了。",
                "sfx": "door_open",
                "editing_notes": "Use slight zoom-in and nervous pause.",
                "image_prompt": "young woman opening a meeting room door",
                "video_prompt": "office door opens, awkward pause",
                "voice_prompt": "voice prompt 1",
                "bgm_prompt": "bgm prompt 1",
                "status": "prompt_ready",
            }
        ],
        upload_manual_images=False,
    )

    response = client.get(f"/projects/{project_id}/editing-cue-sheet")
    assert response.status_code == 200
    body = response.json()
    assert body["ready_for_cue_sheet"] is False
    assert "missing_image_asset" in body["blocking_issues"]
    assert body["next_action"] == "fix_editing_inputs"


def test_editing_cue_sheet_missing_subtitle_and_sfx_add_warnings_without_blocking(client):
    project_id = _create_editing_cue_sheet_project(
        client,
        shots=[
            {
                "shot_id": "SH01",
                "duration_sec": 3,
                "character": "Lin Xia",
                "location": "Meeting Room",
                "core_action": "Lin Xia opens the door",
                "emotion": "nervous",
                "camera": "medium close-up",
                "dialogue": "不好意思，我走错了。",
                "shot_type": "dialogue",
                "camera_motion": "slow_push_in",
                "subject_motion": "blink",
                "transition": "cut",
                "editing_notes": "Use slight zoom-in and nervous pause.",
                "image_prompt": "young woman opening a meeting room door",
                "video_prompt": "office door opens, awkward pause",
                "voice_prompt": "voice prompt 1",
                "bgm_prompt": "bgm prompt 1",
                "status": "prompt_ready",
            }
        ],
        upload_manual_images=True,
    )

    response = client.get(f"/projects/{project_id}/editing-cue-sheet")
    assert response.status_code == 200
    body = response.json()
    item = body["items"][0]
    assert "missing_subtitle_text" in item["warnings"]
    assert "missing_sfx" in item["warnings"]
    assert body["ready_for_cue_sheet"] is True
    assert body["next_action"] == "ready_for_manual_editing"


def test_editing_cue_sheet_all_ready_returns_ready_for_manual_editing(client):
    project_id = _create_editing_cue_sheet_project(
        client,
        shots=[
            {
                "shot_id": "SH01",
                "duration_sec": 3,
                "character": "Lin Xia",
                "location": "Meeting Room",
                "core_action": "Lin Xia opens the door",
                "emotion": "nervous",
                "camera": "medium close-up",
                "dialogue": "不好意思，我走错了。",
                "shot_type": "dialogue",
                "camera_motion": "slow_push_in",
                "subject_motion": "blink",
                "transition": "cut",
                "subtitle_text": "不好意思，我走错了。",
                "sfx": "door_open",
                "editing_notes": "Use slight zoom-in and nervous pause.",
                "image_prompt": "young woman opening a meeting room door",
                "video_prompt": "office door opens, awkward pause",
                "voice_prompt": "voice prompt 1",
                "bgm_prompt": "bgm prompt 1",
                "status": "prompt_ready",
            }
        ],
        upload_manual_images=True,
    )

    response = client.get(f"/projects/{project_id}/editing-cue-sheet")
    assert response.status_code == 200
    body = response.json()
    assert body["ready_for_cue_sheet"] is True
    assert body["next_action"] == "ready_for_manual_editing"


def test_editing_cue_sheet_missing_project_returns_404(client):
    response = client.get("/projects/999999/editing-cue-sheet")
    assert response.status_code == 404
