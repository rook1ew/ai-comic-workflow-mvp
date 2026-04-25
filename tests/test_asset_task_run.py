def _create_ready_shot(client):
    project = client.post("/projects", json={"name": "项目A"}).json()
    client.post(
        "/characters",
        json={
            "project_id": project["id"],
            "name": "林夏",
            "role_type": "lead",
            "profile": "女主",
            "visual_notes": "短发职业装",
            "voice_style": "冷静",
            "main_reference_confirmed": True,
        },
    )
    episode = client.post("/episodes", json={"project_id": project["id"], "title": "第一集", "episode_number": 1}).json()
    scene = client.post(
        "/scenes",
        json={"episode_id": episode["id"], "scene_number": 1, "title": "会议室", "description": "初见场景"},
    ).json()
    shot = client.post(
        "/shots",
        json={
            "scene_id": scene["id"],
            "shot_number": 1,
            "framing": "medium",
            "core_action": "女主推门进入会议室",
            "image_prompt": "图像提示词",
            "video_prompt": "视频提示词",
            "voice_prompt": "配音提示词",
            "bgm_prompt": "音乐提示词",
        },
    ).json()
    return shot


def test_run_image_asset_task_success(client):
    shot = _create_ready_shot(client)
    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "image", "provider_name": "mock"}).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "succeeded"
    assert len(body["assets"]) == 1
    assert body["assets"][0]["asset_type"] == "image"


def test_run_video_asset_task_success(client):
    shot = _create_ready_shot(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "image", "provider_name": "mock"}).json()
    image_response = client.post(f"/asset-tasks/{image_task['id']}/run")
    assert image_response.status_code == 200
    assert image_response.json()["status"] == "succeeded"

    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "video", "provider_name": "mock"}).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"
    assert response.json()["assets"][0]["asset_type"] == "video"


def test_run_voice_asset_task_success(client):
    shot = _create_ready_shot(client)
    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "voice", "provider_name": "mock"}).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"
    assert response.json()["assets"][0]["asset_type"] == "voice"


def test_run_bgm_asset_task_success(client):
    shot = _create_ready_shot(client)
    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "bgm", "provider_name": "mock"}).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"
    assert response.json()["assets"][0]["asset_type"] == "bgm"


def test_provider_failure_should_update_task_error_message(client):
    shot = _create_ready_shot(client)
    task = client.post(
        "/asset-tasks",
        json={
            "shot_id": shot["id"],
            "modality": "image",
            "provider_name": "mock",
            "input_payload": {"should_fail": True},
        },
    ).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "forced failure" in body["error_message"]


def test_retry_over_max_should_become_needs_human_revision(client):
    shot = _create_ready_shot(client)
    task = client.post(
        "/asset-tasks",
        json={
            "shot_id": shot["id"],
            "modality": "image",
            "provider_name": "mock",
            "retry_count": 3,
            "max_retries": 3,
            "input_payload": {"should_fail": True},
        },
    ).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    assert response.json()["status"] == "needs_human_revision"


def test_asset_should_be_created_after_task_succeeded(client):
    shot = _create_ready_shot(client)
    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "image", "provider_name": "mock"}).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    body = response.json()
    assert len(body["assets"]) == 1
    asset = body["assets"][0]
    assert asset["shot_id"] == shot["id"]
    assert asset["asset_task_id"] == task["id"]
    assert asset["url"].startswith("https://mock.assets/")


def test_image_task_metadata_contains_image_input_payload(client):
    shot = _create_ready_shot(client)
    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "image", "provider_name": "mock"}).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200

    metadata = response.json()["assets"][0]["metadata_json"]
    assert metadata["provider_name"] == "mock"
    assert metadata["modality"] == "image"
    assert metadata["mock"] is True
    assert metadata["input_payload"]["prompt"] == shot["image_prompt"]
    assert metadata["input_payload"]["shot_id"] == shot["id"]
    assert "character_reference_url" in metadata["input_payload"]
    assert "style" in metadata["input_payload"]


def test_video_task_metadata_contains_video_input_payload(client):
    shot = _create_ready_shot(client)
    image_task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "image", "provider_name": "mock"}).json()
    image_response = client.post(f"/asset-tasks/{image_task['id']}/run")
    assert image_response.status_code == 200
    image_url = image_response.json()["assets"][0]["url"]

    video_task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "video", "provider_name": "mock"}).json()
    response = client.post(f"/asset-tasks/{video_task['id']}/run")
    assert response.status_code == 200

    metadata = response.json()["assets"][0]["metadata_json"]
    assert metadata["provider_name"] == "mock"
    assert metadata["modality"] == "video"
    assert metadata["mock"] is True
    assert metadata["input_payload"]["image_url"] == image_url
    assert metadata["input_payload"]["prompt"] == shot["video_prompt"]
    assert metadata["input_payload"]["duration"] == 3
    assert metadata["input_payload"]["aspect_ratio"] == "9:16"
    assert metadata["input_payload"]["resolution"] == "720p"


def test_video_task_uses_storyboard_duration_when_available(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Duration Demo",
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
    run_response = client.post(f"/coze/project/{project_id}/run-asset-tasks")
    assert run_response.status_code == 200

    summary = client.get(f"/coze/project/{project_id}/summary").json()
    assert summary["data"]["assets_count"] == 4

    asset_tasks = client.get(f"/projects/{project_id}/asset-tasks").json()
    video_task = next(task for task in asset_tasks if task["modality"] == "video")
    video_result = client.get(f"/asset-tasks/{video_task['id']}").json()
    metadata = video_result["assets"][0]["metadata_json"]
    assert metadata["input_payload"]["duration"] == 7


def test_video_task_without_image_asset_should_not_succeed(client):
    shot = _create_ready_shot(client)
    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "video", "provider_name": "mock"}).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"failed", "needs_human_revision"}
    assert "Image asset is required before video generation" in body["error_message"]
