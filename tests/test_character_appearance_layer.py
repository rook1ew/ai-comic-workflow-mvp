def _create_project_with_character_library(client):
    project = client.post(
        "/projects",
        json={
            "name": "Character Appearance Demo",
            "visual_asset_library_json": {
                "characters": [
                    {
                        "asset_key": "shen_zhixia",
                        "name": "Shen Zhixia",
                        "role": "lead",
                        "main_reference_url": "",
                        "must_keep": ["straight black hair", "soft homewear silhouette"],
                        "avoid": ["changed hairstyle", "celebrity likeness"],
                    }
                ],
                "scenes": [],
                "props": [],
            },
        },
    ).json()
    character = client.post(
        "/characters",
        json={
            "project_id": project["id"],
            "name": "Shen Zhixia",
            "role_type": "lead",
            "profile": "social_identity: illustrator\nfirst_impression: tired and cautious",
            "visual_notes": "appearance_summary: straight black hair, pale homewear, tired eyes",
            "voice_style": "soft",
        },
    ).json()
    return project, character


def _appearance_payload(key="shen_zhixia_design_sheet", appearance_type="design_sheet", image_url=None, is_selected=False):
    return {
        "appearance_key": key,
        "appearance_type": appearance_type,
        "title": "Shen Zhixia design sheet",
        "description": "Multi-view character design sheet.",
        "image_url": image_url or f"file:///D:/AI-comic-characters/{key}.png",
        "is_selected": is_selected,
        "order_index": 1,
        "change_reason": "initial character appearance",
        "must_keep": ["straight black hair", "tired sensitive eyes"],
        "avoid": ["known anime character", "changed outfit"],
    }


def test_character_appearance_create_upsert_list_and_select_syncs_character_and_library(client):
    project, character = _create_project_with_character_library(client)

    create_response = client.post(
        f"/projects/{project['id']}/characters/{character['id']}/appearances",
        json=_appearance_payload(),
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["appearance_key"] == "shen_zhixia_design_sheet"
    assert created["appearance_type"] == "design_sheet"
    assert created["must_keep"] == ["straight black hair", "tired sensitive eyes"]

    upsert_response = client.post(
        f"/projects/{project['id']}/characters/{character['id']}/appearances",
        json=_appearance_payload(image_url="file:///D:/AI-comic-characters/ShenZhixia_design_sheet_v2.png"),
    )
    assert upsert_response.status_code == 201
    assert upsert_response.json()["id"] == created["id"]
    assert upsert_response.json()["image_url"].endswith("ShenZhixia_design_sheet_v2.png")

    main_response = client.post(
        f"/projects/{project['id']}/characters/{character['id']}/appearances",
        json=_appearance_payload(
            key="shen_zhixia_main",
            appearance_type="main_reference",
            image_url="file:///D:/AI-comic-characters/ShenZhixia_main.png",
        ),
    )
    assert main_response.status_code == 201

    list_response = client.get(f"/projects/{project['id']}/characters/{character['id']}/appearances")
    assert list_response.status_code == 200
    assert [item["appearance_key"] for item in list_response.json()] == ["shen_zhixia_design_sheet", "shen_zhixia_main"]

    select_response = client.post(
        f"/projects/{project['id']}/characters/{character['id']}/appearances/shen_zhixia_main/select"
    )
    assert select_response.status_code == 200
    selected_body = select_response.json()
    assert selected_body["character_main_reference_url"] == "file:///D:/AI-comic-characters/ShenZhixia_main.png"
    assert selected_body["synced_visual_asset"]["main_reference_url"] == "file:///D:/AI-comic-characters/ShenZhixia_main.png"
    assert selected_body["synced_visual_asset"]["selected_appearance_key"] == "shen_zhixia_main"

    appearances = client.get(f"/projects/{project['id']}/characters/{character['id']}/appearances").json()
    selected = [item for item in appearances if item["is_selected"]]
    assert len(selected) == 1
    assert selected[0]["appearance_key"] == "shen_zhixia_main"

    library = client.get(f"/projects/{project['id']}/visual-asset-library").json()
    character_asset = library["characters"][0]
    assert character_asset["main_reference_url"] == "file:///D:/AI-comic-characters/ShenZhixia_main.png"
    assert character_asset["selected_appearance_key"] == "shen_zhixia_main"
    assert character_asset["selected_appearance_url"] == "file:///D:/AI-comic-characters/ShenZhixia_main.png"
    assert character_asset["appearances_count"] == 2


def test_character_appearance_summary_flags_and_legacy_character_compatibility(client):
    project, character = _create_project_with_character_library(client)
    initial = client.get(f"/projects/{project['id']}/character-appearance-summary")
    assert initial.status_code == 200
    initial_item = initial.json()["items"][0]
    assert initial_item["appearances_count"] == 0
    assert initial_item["next_action"] == "create_character_appearances"

    for key, appearance_type in [
        ("design", "design_sheet"),
        ("main", "main_reference"),
        ("face", "face_detail"),
        ("front", "fullbody_front"),
    ]:
        client.post(
            f"/projects/{project['id']}/characters/{character['id']}/appearances",
            json=_appearance_payload(key=f"shen_zhixia_{key}", appearance_type=appearance_type),
        )
    client.post(f"/projects/{project['id']}/characters/{character['id']}/appearances/shen_zhixia_main/select")

    summary = client.get(f"/projects/{project['id']}/character-appearance-summary")
    assert summary.status_code == 200
    item = summary.json()["items"][0]
    assert item["appearances_count"] == 4
    assert item["has_design_sheet"] is True
    assert item["has_main_reference"] is True
    assert item["has_face_detail"] is True
    assert item["has_fullbody"] is True
    assert item["next_action"] == "ready_for_reference_guided_generation"


def test_visual_asset_prompts_use_selected_appearance(client):
    project, character = _create_project_with_character_library(client)
    client.post(
        f"/projects/{project['id']}/characters/{character['id']}/appearances",
        json=_appearance_payload(
            key="shen_zhixia_main",
            appearance_type="main_reference",
            image_url="file:///D:/AI-comic-characters/ShenZhixia_main.png",
            is_selected=True,
        ),
    )

    response = client.get(f"/projects/{project['id']}/visual-asset-prompts")
    assert response.status_code == 200
    prompt = response.json()["characters"][0]["copy_ready_prompt"]
    assert "Selected appearance reference: file:///D:/AI-comic-characters/ShenZhixia_main.png" in prompt
    assert "Use this selected appearance as the primary identity anchor" in prompt


def test_storyboard_production_board_returns_selected_appearance_info(client):
    project, character = _create_project_with_character_library(client)
    client.post(
        f"/projects/{project['id']}/characters/{character['id']}/appearances",
        json=_appearance_payload(
            key="shen_zhixia_main",
            appearance_type="main_reference",
            image_url="file:///D:/AI-comic-characters/ShenZhixia_main.png",
            is_selected=True,
        ),
    )
    episode = client.post("/episodes", json={"project_id": project["id"], "title": "Episode 1", "episode_number": 1}).json()
    client.post(
        f"/coze/project/{project['id']}/storyboard-package",
        json={
            "script_card_json": {"opening_hook": "Opening"},
            "storyboard_json": {
                "shots": [
                    {
                        "shot_id": "SH01",
                        "duration_sec": 3,
                        "character": "Shen Zhixia",
                        "location": "Old apartment bedroom",
                        "core_action": "Shen Zhixia wakes up from urgent knocking",
                        "emotion": "alarm",
                        "camera": "close-up",
                        "image_prompt": "woman wakes up in a dark apartment bedroom",
                        "video_prompt": "subtle suspense motion",
                        "voice_prompt": "soft frightened voice",
                        "bgm_prompt": "low suspense ambience",
                        "status": "prompt_ready",
                        "character_asset_keys": ["shen_zhixia"],
                    }
                ]
            },
        },
    )
    assert episode["id"]

    response = client.get(f"/projects/{project['id']}/storyboard-production-board")
    assert response.status_code == 200
    refs = response.json()["items"][0]["character_asset_refs"]
    assert refs[0]["selected_appearance_key"] == "shen_zhixia_main"
    assert refs[0]["selected_appearance_url"] == "file:///D:/AI-comic-characters/ShenZhixia_main.png"


def test_character_appearance_missing_project_or_character_returns_404(client):
    project, character = _create_project_with_character_library(client)
    payload = _appearance_payload()

    missing_project = client.post(f"/projects/999999/characters/{character['id']}/appearances", json=payload)
    assert missing_project.status_code == 404

    missing_character = client.post(f"/projects/{project['id']}/characters/999999/appearances", json=payload)
    assert missing_character.status_code == 404
