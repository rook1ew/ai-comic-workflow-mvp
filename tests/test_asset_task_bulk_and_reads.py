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
