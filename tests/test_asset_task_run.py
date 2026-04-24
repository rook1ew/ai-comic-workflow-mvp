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
