# API

## Coze Unified Response

All `/coze/*` endpoints return:

```json
{
  "success": true,
  "code": "OK",
  "message": "",
  "data": {},
  "next_action": ""
}
```

## Coze Endpoints

### POST `/coze/project/init`

Create a project and characters from Coze-generated structured content.

### POST `/characters/{character_id}/confirm-reference`

Confirm a character main reference and optionally save `main_reference_url`.

### POST `/coze/project/{project_id}/generate-script`

Save Coze-generated `script_card_json` into the default episode.

### POST `/coze/project/{project_id}/storyboard`

Import storyboard content and create episode, scene, and shot records.

### POST `/coze/project/{project_id}/create-asset-tasks`

Bulk-create asset tasks for the project shots.

### POST `/coze/project/{project_id}/run-asset-tasks`

Bulk-run queued or retryable asset tasks with mock providers.

### POST `/coze/project/{project_id}/publish-record`

Create a publish record and mark the project as `published`.

### GET `/coze/project/{project_id}/summary`

Return project progress summary in Coze response format.  
When `project_status = published` and `publish_records_count > 0`, both:

- top-level `next_action`
- `data.next_action`

will be `completed`.

### GET `/asset-tasks/{asset_task_id}/provider-debug`

Read-only debug snapshot for provider input inspection before or after execution.

Use cases:

- inspect the final `input_payload` sent to the mock provider
- inspect `enhanced_prompt` for image tasks
- inspect `storyboard_context` for imported storyboard shots
- inspect `image_url` and `duration` for video tasks
- debug failed tasks without calling any real provider

Example response:

```json
{
  "asset_task_id": 1,
  "modality": "image",
  "provider_name": "mock",
  "status": "succeeded",
  "input_payload": {
    "prompt": "image prompt 1",
    "base_prompt": "image prompt 1",
    "enhanced_prompt": "Base image prompt: image prompt 1",
    "storyboard_context": {
      "source_shot_id": "SH01"
    }
  },
  "enhanced_prompt": "Base image prompt: image prompt 1",
  "storyboard_context": {
    "source_shot_id": "SH01"
  },
  "asset_url": "https://mock.assets/image/shot-1.txt",
  "asset_id": 1,
  "error_message": null
}
```

### GET `/projects/{project_id}/provider-debug-summary`

Project-level provider readiness summary for all asset tasks.

Use cases:

- inspect all image and video provider inputs for one project in a single call
- verify `enhanced_prompt` coverage before connecting a real image provider
- verify `image_url` and `duration` coverage before connecting a real video provider
- let Coze or a human operator check provider readiness across the whole project

Example response:

```json
{
  "project_id": 1,
  "asset_tasks_count": 4,
  "items": [
    {
      "asset_task_id": 1,
      "shot_id": "SH01",
      "internal_shot_id": 1,
      "modality": "image",
      "provider_name": "mock",
      "status": "succeeded",
      "enhanced_prompt": "Base image prompt: image prompt 1",
      "storyboard_context": {
        "source_shot_id": "SH01"
      },
      "input_payload": {
        "enhanced_prompt": "Base image prompt: image prompt 1"
      },
      "asset_url": "https://mock.assets/image/shot-1.txt",
      "asset_id": 1,
      "error_message": null
    }
  ],
  "summary": {
    "image_tasks_count": 1,
    "video_tasks_count": 1,
    "succeeded_count": 2,
    "failed_count": 0,
    "needs_human_revision_count": 0,
    "missing_enhanced_prompt_count": 0,
    "missing_image_url_for_video_count": 0
  }
}
```

### POST `/coze/project/full-demo-flow`

Single-call demo endpoint. It runs this full MVP sequence:

1. Create project and characters
2. Confirm the first character reference with `mock://character/reference.png`
3. Save `script_card_json`
4. Import `storyboard_json`
5. Create asset tasks
6. Run asset tasks
7. Create publish record
8. Return final summary

Request example:

```json
{
  "project_card_json": {
    "project_title": "Urban Hook Full Demo",
    "genre": "urban",
    "platform": "coze",
    "target_duration": 60,
    "target_audience": "young-adult",
    "visual_style": "comic-realism",
    "core_conflict": "identity confusion",
    "hook": "wrong room",
    "ending_hook": "unexpected promotion",
    "selling_points": ["fast", "dramatic"],
    "status": "draft"
  },
  "characters_json": {
    "characters": [
      {
        "name": "Lin Xia",
        "role": "lead",
        "age_vibe": "young professional",
        "appearance": "sharp face",
        "hair": "short black hair",
        "outfit": "office wear",
        "personality": "calm",
        "speaking_style": "measured",
        "must_keep": ["short hair"],
        "avoid": ["fantasy armor"],
        "main_reference_confirmed": false
      }
    ]
  },
  "script_card_json": {
    "opening_hook": "She walks into the wrong meeting room",
    "conflict": "Everyone mistakes her identity",
    "escalation": "She cannot explain in time",
    "turning_point": "The boss asks her to stay",
    "ending_hook": "A promotion rumor starts"
  },
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
        "status": "prompt_ready"
      }
    ]
  },
  "video_shot_ids": ["SH01"],
  "publish_record_json": {
    "platform": "抖音",
    "title": "Episode 1",
    "published_at": "2026-04-25T10:00:00",
    "url": "https://www.douyin.com/video/demo"
  }
}
```

Response example:

```json
{
  "success": true,
  "code": "OK",
  "message": "Full demo flow completed",
  "data": {
    "project_id": 1,
    "character_ids": [1],
    "episode_id": 1,
    "shots_count": 1,
    "asset_tasks_count": 4,
    "assets_count": 4,
    "publish_record_id": 1,
    "final_summary": {
      "project_id": 1,
      "project_status": "published",
      "episodes_count": 1,
      "scenes_count": 1,
      "shots_count": 1,
      "asset_tasks_count": 4,
      "assets_count": 4,
      "succeeded_tasks_count": 4,
      "failed_tasks_count": 0,
      "needs_human_revision_count": 0,
      "publish_records_count": 1,
      "next_action": "completed"
    }
  },
  "next_action": "completed"
}
```
