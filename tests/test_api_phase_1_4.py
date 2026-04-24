from datetime import UTC, datetime


def test_create_project(client):
    response = client.post(
        "/projects",
        json={"name": "项目A", "description": "测试项目", "target_platforms": ["coze"], "tags": ["mvp"]},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "项目A"
    assert body["status"] == "draft"


def test_create_character(client):
    project = client.post("/projects", json={"name": "项目A"}).json()
    response = client.post(
        "/characters",
        json={
            "project_id": project["id"],
            "name": "林夏",
            "role_type": "lead",
            "profile": "女主",
            "visual_notes": "短发职业装",
            "voice_style": "冷静",
            "main_reference_url": "https://example.com/ref.png",
            "main_reference_confirmed": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["main_reference_confirmed"] is True


def test_create_episode(client):
    project = client.post("/projects", json={"name": "项目A"}).json()
    response = client.post(
        "/episodes",
        json={"project_id": project["id"], "title": "第一集", "episode_number": 1, "script_card": "剧本卡"},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "第一集"


def test_create_scene(client):
    project = client.post("/projects", json={"name": "项目A"}).json()
    episode = client.post(
        "/episodes",
        json={"project_id": project["id"], "title": "第一集", "episode_number": 1},
    ).json()
    response = client.post(
        "/scenes",
        json={"episode_id": episode["id"], "scene_number": 1, "title": "会议室", "description": "初见场景"},
    )
    assert response.status_code == 201
    assert response.json()["scene_number"] == 1


def test_create_shot(client):
    project = client.post("/projects", json={"name": "项目A"}).json()
    episode = client.post("/episodes", json={"project_id": project["id"], "title": "第一集", "episode_number": 1}).json()
    scene = client.post(
        "/scenes",
        json={"episode_id": episode["id"], "scene_number": 1, "title": "会议室", "description": "初见场景"},
    ).json()
    response = client.post(
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
    )
    assert response.status_code == 201
    assert response.json()["core_action"] == "女主推门进入会议室"


def test_shot_missing_prompts_should_fail(client):
    project = client.post("/projects", json={"name": "项目A"}).json()
    episode = client.post("/episodes", json={"project_id": project["id"], "title": "第一集", "episode_number": 1}).json()
    scene = client.post(
        "/scenes",
        json={"episode_id": episode["id"], "scene_number": 1, "title": "会议室", "description": "初见场景"},
    ).json()
    response = client.post(
        "/shots",
        json={
            "scene_id": scene["id"],
            "shot_number": 1,
            "framing": "medium",
            "core_action": "女主推门进入会议室",
            "image_prompt": "图像提示词",
            "video_prompt": "视频提示词",
            "voice_prompt": "配音提示词",
        },
    )
    assert response.status_code == 422


def test_create_asset_task(client):
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
    response = client.post(
        "/asset-tasks",
        json={"shot_id": shot["id"], "modality": "image", "provider_name": "mock", "input_payload": {"prompt": "x"}},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "queued"


def test_retry_limit_behavior(client):
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
    response = client.post(
        "/asset-tasks",
        json={
            "shot_id": shot["id"],
            "modality": "video",
            "provider_name": "mock",
            "retry_count": 4,
            "max_retries": 3,
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "needs_human_revision"


def test_create_review(client):
    project = client.post("/projects", json={"name": "项目A"}).json()
    response = client.post(
        "/reviews",
        json={
            "target_type": "project",
            "target_id": project["id"],
            "conclusion": "approved",
            "issue_description": "整体结构可行",
            "revision_suggestion": "继续补分镜",
            "reviewed_at": datetime.now(UTC).isoformat(),
            "reviewer": "producer",
        },
    )
    assert response.status_code == 201
    assert response.json()["target_type"] == "project"


def test_create_publish_record(client):
    project = client.post("/projects", json={"name": "项目A"}).json()
    response = client.post(
        "/publish-records",
        json={
            "project_id": project["id"],
            "platform": "douyin",
            "title": "第一条",
            "published_at": datetime.now(UTC).isoformat(),
            "link": "https://example.com/video/1",
        },
    )
    assert response.status_code == 201
    assert response.json()["platform"] == "douyin"


def test_dashboard_summary(client):
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
    client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "image", "provider_name": "mock"})
    client.post(
        "/reviews",
        json={
            "target_type": "shot",
            "target_id": shot["id"],
            "conclusion": "approved",
            "issue_description": "通过",
            "revision_suggestion": "继续下一步",
            "reviewed_at": datetime.now(UTC).isoformat(),
            "reviewer": "producer",
        },
    )
    client.post(
        "/publish-records",
        json={
            "project_id": project["id"],
            "platform": "douyin",
            "title": "第一条",
            "published_at": datetime.now(UTC).isoformat(),
            "link": "https://example.com/video/1",
        },
    )

    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_projects"] == 1
    assert body["total_shots"] == 1
    assert body["total_asset_tasks"] == 1
    assert body["total_reviews"] == 1
    assert body["total_publish_records"] == 1
