from app.services.prompt_enhancer import build_image_enhanced_prompt
from app.core.config import get_settings
from app.models.enums import AssetModality
from app.providers.base import ProviderExecutionError
from app.providers.factory import get_provider
from app.providers.image2 import Image2Provider
from app.providers.schemas import ImageProviderInput


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
    assert metadata["input_payload"]["base_prompt"] == shot["image_prompt"]
    assert "enhanced_prompt" in metadata["input_payload"]
    assert metadata["input_payload"]["shot_id"] == shot["id"]
    assert "character_reference_url" in metadata["input_payload"]
    assert "style" in metadata["input_payload"]
    assert metadata["input_payload"]["storyboard_context"] == {}


def test_image_task_metadata_contains_storyboard_context(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Storyboard Context Demo",
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
    asset_tasks = client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": []}).json()
    assert asset_tasks["data"]["created_count"] == 3

    task_list = client.get(f"/projects/{project_id}/asset-tasks").json()
    image_task = next(task for task in task_list if task["modality"] == "image")
    image_result = client.post(f"/asset-tasks/{image_task['id']}/run").json()

    storyboard_context = image_result["assets"][0]["metadata_json"]["input_payload"]["storyboard_context"]
    assert storyboard_context["source_shot_id"] == "SH01"
    assert storyboard_context["duration_sec"] == 3
    assert storyboard_context["character"] == "Lin Xia"
    assert storyboard_context["location"] == "Meeting Room"
    assert storyboard_context["emotion"] == "nervous"
    assert storyboard_context["camera"] == "medium"
    assert storyboard_context["dialogue"] == "Sorry, wrong room."
    assert "enhanced_prompt" in image_result["assets"][0]["metadata_json"]["input_payload"]
    assert "Lin Xia" in image_result["assets"][0]["metadata_json"]["input_payload"]["enhanced_prompt"]


def test_build_image_enhanced_prompt_contains_base_prompt():
    prompt = build_image_enhanced_prompt(
        base_prompt="close-up portrait in an office",
        visual_style=None,
        character_reference_url=None,
        storyboard_context=None,
    )
    assert "close-up portrait in an office" in prompt


def test_build_image_enhanced_prompt_contains_visual_style_and_storyboard_context():
    prompt = build_image_enhanced_prompt(
        base_prompt="character enters the boardroom",
        visual_style="comic realism",
        character_reference_url="mock://character/reference.png",
        storyboard_context={
            "source_shot_id": "SH01",
            "character": "Lin Xia",
            "location": "Meeting Room",
            "emotion": "nervous",
            "camera": "medium",
            "dialogue": "Sorry, wrong room.",
        },
    )
    assert "character enters the boardroom" in prompt
    assert "comic realism" in prompt
    assert "mock://character/reference.png" in prompt
    assert "Lin Xia" in prompt
    assert "Meeting Room" in prompt
    assert "nervous" in prompt
    assert "medium" in prompt
    assert "Sorry, wrong room." in prompt


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


def test_image_task_provider_debug_returns_enhanced_prompt_and_storyboard_context(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Provider Debug Demo",
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
    task_list = client.post(f"/coze/project/{project_id}/create-asset-tasks", json={"video_shot_ids": []})
    assert task_list.status_code == 200
    asset_tasks = client.get(f"/projects/{project_id}/asset-tasks").json()
    image_task = next(task for task in asset_tasks if task["modality"] == "image")
    client.post(f"/asset-tasks/{image_task['id']}/run")

    debug = client.get(f"/asset-tasks/{image_task['id']}/provider-debug")
    assert debug.status_code == 200
    body = debug.json()
    assert body["enhanced_prompt"] is not None
    assert body["storyboard_context"]["source_shot_id"] == "SH01"
    assert body["storyboard_context"]["character"] == "Lin Xia"
    assert body["asset_url"].startswith("https://mock.assets/image/")


def test_video_task_provider_debug_returns_image_url_and_duration(client):
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Provider Debug Video Demo",
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

    asset_tasks = client.get(f"/projects/{project_id}/asset-tasks").json()
    video_task = next(task for task in asset_tasks if task["modality"] == "video")
    debug = client.get(f"/asset-tasks/{video_task['id']}/provider-debug")
    assert debug.status_code == 200
    body = debug.json()
    assert body["input_payload"]["image_url"].startswith("https://mock.assets/image/")
    assert body["input_payload"]["duration"] == 7
    assert body["asset_url"].startswith("https://mock.assets/video/")


def test_unexecuted_task_provider_debug_returns_basic_info(client):
    shot = _create_ready_shot(client)
    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "image", "provider_name": "mock"}).json()
    debug = client.get(f"/asset-tasks/{task['id']}/provider-debug")
    assert debug.status_code == 200
    body = debug.json()
    assert body["asset_task_id"] == task["id"]
    assert body["asset_url"] is None
    assert body["asset_id"] is None
    assert body["input_payload"] == {}


def test_provider_debug_returns_404_for_missing_task(client):
    response = client.get("/asset-tasks/999999/provider-debug")
    assert response.status_code == 404


def test_default_configuration_keeps_image_task_on_mock_provider(client):
    get_settings.cache_clear()
    shot = _create_ready_shot(client)
    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "image", "provider_name": "mock"}).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    metadata = response.json()["assets"][0]["metadata_json"]
    assert metadata["provider_name"] == "mock"
    assert metadata["mock"] is True


def test_image2_stub_returns_stub_url_and_real_call_false(client):
    get_settings.cache_clear()
    shot = _create_ready_shot(client)
    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "image", "provider_name": "image2_stub"}).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "succeeded"
    asset = body["assets"][0]
    assert asset["url"] == f"mock://image2-stub/{shot['id']}.png"
    assert asset["metadata_json"]["provider_name"] == "image2_stub"
    assert asset["metadata_json"]["real_call"] is False
    assert asset["metadata_json"]["safety_note"] == "stub only, no real API call"


def test_image2_real_disabled_returns_clear_error(client, monkeypatch):
    monkeypatch.setenv("ENABLE_REAL_IMAGE_PROVIDER", "false")
    monkeypatch.setenv("IMAGE_PROVIDER_MODE", "image2_real")
    monkeypatch.setenv("IMAGE2_API_KEY", "fake-key")
    get_settings.cache_clear()

    shot = _create_ready_shot(client)
    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "image", "provider_name": "image2_real"}).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "Real Image2 provider is disabled" in body["error_message"]

    get_settings.cache_clear()


def test_image2_real_missing_api_key_returns_clear_error(client, monkeypatch):
    monkeypatch.setenv("ENABLE_REAL_IMAGE_PROVIDER", "true")
    monkeypatch.setenv("IMAGE_PROVIDER_MODE", "image2_real")
    monkeypatch.delenv("IMAGE2_API_KEY", raising=False)
    get_settings.cache_clear()

    shot = _create_ready_shot(client)
    task = client.post("/asset-tasks", json={"shot_id": shot["id"], "modality": "image", "provider_name": "image2_real"}).json()
    response = client.post(f"/asset-tasks/{task['id']}/run")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "IMAGE2_API_KEY is required" in body["error_message"]

    get_settings.cache_clear()


def test_provider_debug_supports_image2_stub_input_snapshot(client):
    get_settings.cache_clear()
    init = client.post("/coze/project/init", json={
        "project_card_json": {
            "project_title": "Image2 Stub Debug Demo",
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
    image_task = client.post(
        "/asset-tasks",
        json={"shot_id": 1, "modality": "image", "provider_name": "image2_stub"},
    ).json()
    client.post(f"/asset-tasks/{image_task['id']}/run")
    debug = client.get(f"/asset-tasks/{image_task['id']}/provider-debug")
    assert debug.status_code == 200
    body = debug.json()
    assert body["input_payload"]["enhanced_prompt"] is not None
    assert body["storyboard_context"]["source_shot_id"] == "SH01"
    assert body["asset_url"].startswith("mock://image2-stub/")


def test_image2_provider_build_request_payload_prefers_enhanced_prompt():
    provider = Image2Provider()
    payload = provider.build_request_payload(
        {
            "prompt": "base image prompt",
            "enhanced_prompt": "enhanced image prompt",
            "character_reference_url": "mock://character/reference.png",
            "shot_id": 1,
            "style": "comic-realism",
            "storyboard_context": {"source_shot_id": "SH01"},
        }
    )
    assert payload["prompt"] == "enhanced image prompt"


def test_image2_provider_build_request_payload_includes_reference_style_and_storyboard_context():
    provider = Image2Provider()
    payload = provider.build_request_payload(
        {
            "prompt": "base image prompt",
            "enhanced_prompt": "enhanced image prompt",
            "character_reference_url": "mock://character/reference.png",
            "shot_id": 7,
            "style": "comic-realism",
            "storyboard_context": {
                "source_shot_id": "SH01",
                "character": "Lin Xia",
            },
        }
    )
    assert payload["reference_image_url"] == "mock://character/reference.png"
    assert payload["style"] == "comic-realism"
    assert payload["metadata"]["shot_id"] == 7
    assert payload["metadata"]["storyboard_context"]["source_shot_id"] == "SH01"


def test_image2_provider_parse_response_extracts_image_url_job_id_and_usage():
    provider = Image2Provider()
    result = provider.parse_response(
        {
            "image_url": "https://example.com/image.png",
            "id": "job_123",
            "model": "image2",
            "usage": {"credits": 1},
        }
    )
    assert result.url == "https://example.com/image.png"
    assert result.metadata["provider_name"] == "image2_real"
    assert result.metadata["job_id"] == "job_123"
    assert result.metadata["usage"]["credits"] == 1
    assert result.metadata["real_call"] is True


def test_image2_provider_parse_response_missing_image_url_raises_clear_error():
    provider = Image2Provider()
    try:
        provider.parse_response({"id": "job_123"})
        assert False, "Expected ProviderExecutionError"
    except ProviderExecutionError as exc:
        assert "missing image_url" in str(exc).lower()


def test_image2_provider_map_error_handles_authentication_quota_timeout_and_unknown():
    provider = Image2Provider()
    assert provider.map_error({"code": "authentication_failed"}) == "Image2 provider authentication failed."
    assert provider.map_error({"message": "insufficient balance"}) == "Image2 provider quota or balance is insufficient."
    assert provider.map_error(TimeoutError("request timeout")) == "Image2 provider request timed out."
    assert provider.map_error(RuntimeError("boom")) == "Image2 provider returned an unknown error."


def test_provider_factory_recognizes_image2_real():
    provider = get_provider(AssetModality.IMAGE, "image2_real")
    assert isinstance(provider, Image2Provider)
