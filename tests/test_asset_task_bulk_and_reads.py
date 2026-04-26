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
