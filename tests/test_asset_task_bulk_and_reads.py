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
