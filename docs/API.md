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

## Provider Configuration Notes

Current v0.3-A only prepares configuration and safety switches for a future
real `Image2Provider`.

Relevant settings:

- `IMAGE_PROVIDER_MODE=mock | image2_stub | image2_real`
- `IMAGE2_API_KEY`
- `IMAGE2_BASE_URL`
- `IMAGE2_MODEL`
- `ENABLE_REAL_IMAGE_PROVIDER=true | false`
- `IMAGE2_MAX_REAL_CALLS_PER_RUN`
- `IMAGE2_ALLOW_TASK_IDS`
- `IMAGE2_DRY_RUN=true | false`

Real image-provider calls are still blocked in v0.3-A. A future real call must
only be allowed when all of the following are true:

- `IMAGE_PROVIDER_MODE=image2_real`
- `ENABLE_REAL_IMAGE_PROVIDER=true`
- `IMAGE2_API_KEY` is present

In v0.3-B, the `Image2Provider` adapter structure exists, but real HTTP calls
are still intentionally blocked. This means request shaping, response parsing,
and error mapping can be tested without generating any real cost.

In v0.3-C, an additional preflight and dry-run protection layer exists:

- `image2_real` still does not send any real request
- `IMAGE2_DRY_RUN=true` blocks execution after building the request payload
- only explicitly allowed task ids may enter the future real-call path
- the run records debug fields such as `request_payload`, `real_call`,
  `dry_run`, and `blocked_reason`

In v0.3-D, these fields are standardized under a `provider_audit` structure.
This audit payload is the main record for future real-provider execution review.

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

### POST `/coze/project/validate-payload`

Validate a Coze full-demo-flow payload without creating a project or writing any
database records.

Use cases:

- check whether a real Coze payload is complete enough before calling full-demo-flow
- catch blocking field issues before the workflow starts
- surface warnings such as missing `visual_style` or `duration_sec`

Example response:

```json
{
  "success": true,
  "code": "OK",
  "message": "Payload validation completed",
  "data": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "shots_count": 1,
    "characters_count": 1,
    "video_shot_ids_count": 1
  },
  "next_action": "ready_for_full_demo_flow"
}
```

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
  "error_message": null,
  "provider_audit": {},
  "blocked_reason": null,
  "dry_run": null,
  "real_call": null,
  "preflight_passed": null,
  "preflight_checks": {}
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
      "error_message": null,
      "provider_audit": {},
      "blocked_reason": null,
      "dry_run": null,
      "real_call": null,
      "preflight_passed": null
    }
  ],
  "summary": {
    "image_tasks_count": 1,
    "video_tasks_count": 1,
    "succeeded_count": 2,
    "failed_count": 0,
    "needs_human_revision_count": 0,
    "missing_enhanced_prompt_count": 0,
    "missing_image_url_for_video_count": 0,
    "dry_run_tasks_count": 0,
    "blocked_real_provider_tasks_count": 0,
    "real_call_tasks_count": 0
  }
}
```

### GET `/projects/{project_id}/provider-readiness`

Project-level readiness check before switching from mock providers to real
`Image2` and `Seedance` providers.

Use cases:

- verify whether a project is ready for a real image provider
- verify whether video tasks have the required `image_url` and `duration`
- let Coze check project-wide provider readiness before a v0.3 real-provider rollout

Example response:

```json
{
  "project_id": 1,
  "ready_for_image_provider": true,
  "ready_for_video_provider": true,
  "blocking_issues": [],
  "warnings": [],
  "summary": {}
}
```

### GET `/projects/{project_id}/image-prompts`

Export copy-ready prompts for all image asset tasks in one project.

Use cases:

- manually copy prompts into ChatGPT image generation or other image tools
- review `enhanced_prompt` quality before any future real Image2 integration
- keep image production moving even when billing is not ready

Behavior:

- only returns `image` asset tasks
- if the image task has already succeeded, it prefers
  `Asset.metadata_json.input_payload.enhanced_prompt`
- if the image task has not run yet, it falls back to the existing prompt
  enhancer and current shot metadata
- it does not call any real provider API
- it does not require a real API key

Example response:

```json
{
  "project_id": 1,
  "items_count": 1,
  "items": [
    {
      "asset_task_id": 1,
      "internal_shot_id": 1,
      "source_shot_id": "SH01",
      "character": "Lin Xia",
      "location": "Meeting Room",
      "emotion": "nervous",
      "camera": "medium close-up",
      "dialogue": "Sorry, wrong room.",
      "base_prompt": "young woman opening a meeting room door",
      "enhanced_prompt": "Base image prompt: young woman opening a meeting room door",
      "negative_prompt": "不要模仿具体IP、明星、影视角色或已知动漫角色；不要水印；不要乱码文字；不要多余肢体；不要低清晰度。",
      "copy_ready_prompt": "Base image prompt: young woman opening a meeting room door\nFormat: vertical anime comic style, 9:16 composition, high detail, consistent character design.\nNegative prompt: 不要模仿具体IP、明星、影视角色或已知动漫角色；不要水印；不要乱码文字；不要多余肢体；不要低清晰度。"
    }
  ]
}
```

### POST `/asset-tasks/{asset_task_id}/manual-asset`

Register a manually generated image back to an existing image asset task.

Use cases:

- after copying `copy_ready_prompt` into ChatGPT image generation or another image tool
- after saving a manual image to a local path or hosted URL
- when billing is not ready but you still want to complete the image task lifecycle

Behavior:

- only supports `image` asset tasks
- creates a new `Asset` record with `provider_name = manual`
- marks the target asset task as `succeeded`
- writes manual registration info into `task.output_payload`
- does not call any real provider API

Request example:

```json
{
  "asset_url": "file:///D:/ai-comic-assets/SH01.png",
  "asset_type": "image",
  "notes": "手动用 ChatGPT 生成，已确认角色一致"
}
```

### POST `/asset-tasks/{asset_task_id}/manual-video-asset`

Register a manually generated video back to an existing video asset task.

Use cases:

- after using Seedance web or another external tool to generate video manually
- after saving a video to a local path or hosted URL
- when billing is not ready but you still want to complete the video task lifecycle

Behavior:

- only supports `video` asset tasks
- creates a new `Asset` record with `provider_name = manual`
- marks the target video asset task as `succeeded`
- writes manual registration info into `task.output_payload`
- does not call any real provider API

Request example:

```json
{
  "asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4",
  "asset_type": "video",
  "notes": "手动用 Seedance 网页端生成，已确认画面可用"
}
```

Response example:

```json
{
  "id": 10,
  "shot_id": 1,
  "modality": "video",
  "status": "succeeded",
  "retry_count": 0,
  "max_retries": 3,
  "error_message": null,
  "provider_name": "mock",
  "input_payload": {
    "duration": 3
  },
  "output_payload": {
    "manual_asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4",
    "manual_upload": true,
    "notes": "手动用 Seedance 网页端生成，已确认画面可用"
  },
  "assets": [
    {
      "asset_task_id": 10,
      "asset_type": "video",
      "url": "file:///D:/ai-comic-assets/SH01_video.mp4",
      "metadata_json": {
        "manual_upload": true,
        "notes": "手动用 Seedance 网页端生成，已确认画面可用",
        "source": "manual_video_generation",
        "asset_task_id": 10
      }
    }
  ]
}
```

### GET `/projects/{project_id}/manual-image-progress`

Project-level progress view for manual image generation and manual asset registration.

Use cases:

- quickly see which image tasks already have images
- find which image tasks still need manual generation
- confirm whether the project is ready to move from image generation to the video stage

Behavior:

- only counts `image` asset tasks
- if an image task already has an asset URL, `has_asset = true`
- if `metadata_json.manual_upload = true`, `manual_upload = true`
- if an image task has no asset URL, `needs_manual_image = true`
- if all image tasks are completed, `next_action = manual_images_completed`
- otherwise `next_action = continue_manual_image_generation`

Example response:

```json
{
  "project_id": 1,
  "image_tasks_count": 5,
  "completed_image_tasks_count": 2,
  "missing_image_tasks_count": 3,
  "manual_uploaded_count": 2,
  "items": [
    {
      "asset_task_id": 1,
      "internal_shot_id": 1,
      "source_shot_id": "SH01",
      "status": "succeeded",
      "has_asset": true,
      "asset_url": "file:///D:/ai-comic-assets/SH01.png",
      "manual_upload": true,
      "needs_manual_image": false,
      "character": "Lin Xia",
      "location": "Meeting Room",
      "emotion": "nervous"
    }
  ],
  "next_action": "continue_manual_image_generation"
}
```

### GET `/projects/{project_id}/video-readiness`

Project-level readiness view for all video asset tasks in one project.

Use cases:

- quickly see which video tasks are ready to enter video generation
- check whether each video task already has an image asset URL
- check whether each video task already has a duration
- decide whether to continue manual image work or move into the video stage

Behavior:

- only counts `video` asset tasks
- checks whether the same shot already has an image asset URL
- duration priority is:
  1. `Shot.metadata_json.duration_sec`
  2. `task.input_payload.duration`
  3. `task.input_payload.duration_sec`
- if both image asset and duration exist, `ready_for_video = true`
- if image is missing, `blocking_issues` includes `missing_image_asset`
- if duration is missing, `blocking_issues` includes `missing_duration`

Example response:

```json
{
  "project_id": 1,
  "video_tasks_count": 3,
  "ready_video_tasks_count": 2,
  "blocked_video_tasks_count": 1,
  "items": [
    {
      "asset_task_id": 10,
      "internal_shot_id": 1,
      "source_shot_id": "SH01",
      "status": "queued",
      "has_image_asset": true,
      "image_asset_url": "file:///D:/ai-comic-assets/SH01.png",
      "has_duration": true,
      "duration": 3,
      "ready_for_video": true,
      "blocking_issues": [],
      "character": "Lin Xia",
      "location": "Meeting Room",
      "emotion": "nervous",
      "video_prompt": "video prompt 1"
    }
  ],
  "next_action": "ready_for_video_generation"
}
```

### GET `/projects/{project_id}/manual-video-progress`

Project-level progress view for manual video generation and manual video asset registration.

Use cases:

- quickly see which video tasks already have videos
- find which video tasks still need manual video generation
- confirm whether the project has completed the manual video stage before publish or composition

Behavior:

- only counts `video` asset tasks
- if a video task already has an asset URL, `has_asset = true`
- if `metadata_json.manual_upload = true`, `manual_upload = true`
- if a video task has no asset URL, `needs_manual_video = true`
- duration priority is:
  1. `Shot.metadata_json.duration_sec`
  2. `task.input_payload.duration`
  3. `task.input_payload.duration_sec`
- if all video tasks are completed, `next_action = manual_videos_completed`
- otherwise `next_action = continue_manual_video_generation`

Example response:

```json
{
  "project_id": 1,
  "video_tasks_count": 5,
  "completed_video_tasks_count": 2,
  "missing_video_tasks_count": 3,
  "manual_uploaded_count": 2,
  "items": [
    {
      "asset_task_id": 10,
      "internal_shot_id": 1,
      "source_shot_id": "SH01",
      "status": "succeeded",
      "has_asset": true,
      "asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4",
      "manual_upload": true,
      "needs_manual_video": false,
      "character": "Lin Xia",
      "location": "Meeting Room",
      "emotion": "nervous",
      "duration": 3
    }
  ],
  "next_action": "manual_videos_completed"
}
```

Response example:

```json
{
  "id": 1,
  "shot_id": 1,
  "modality": "image",
  "status": "succeeded",
  "retry_count": 0,
  "max_retries": 3,
  "error_message": null,
  "provider_name": "mock",
  "input_payload": {},
  "output_payload": {
    "manual_asset_url": "file:///D:/ai-comic-assets/SH01.png",
    "manual_upload": true,
    "notes": "手动用 ChatGPT 生成，已确认角色一致"
  },
  "assets": [
    {
      "asset_task_id": 1,
      "asset_type": "image",
      "url": "file:///D:/ai-comic-assets/SH01.png",
      "metadata_json": {
        "manual_upload": true,
        "notes": "手动用 ChatGPT 生成，已确认角色一致",
        "source": "manual_image_generation",
        "asset_task_id": 1
      }
    }
  ]
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

### GET `/projects/{project_id}/manual-production-summary`

Project-level overview for the full manual production chain.

Use cases:

- check the current manual production stage with a single request
- decide whether to continue manual image generation, fix video inputs, or continue manual video generation
- give Coze or an operator one summary view before opening more detailed endpoints

Response example:

```json
{
  "project_id": 1,
  "stage": "manual_image_generation",
  "next_action": "continue_manual_image_generation",
  "image": {
    "image_tasks_count": 5,
    "completed_image_tasks_count": 2,
    "missing_image_tasks_count": 3,
    "manual_uploaded_count": 2,
    "next_action": "continue_manual_image_generation"
  },
  "video_readiness": {
    "video_tasks_count": 5,
    "ready_video_tasks_count": 2,
    "blocked_video_tasks_count": 3,
    "next_action": "continue_manual_image_generation"
  },
  "video": {
    "video_tasks_count": 5,
    "completed_video_tasks_count": 0,
    "missing_video_tasks_count": 5,
    "manual_uploaded_count": 0,
    "next_action": "continue_manual_video_generation"
  },
  "blocking_summary": {
    "missing_image_tasks_count": 3,
    "blocked_video_tasks_count": 3,
    "missing_video_tasks_count": 5
  },
  "recommended_steps": [
    "Continue generating missing images from image-prompts.",
    "Upload generated images with manual-asset.",
    "Run video-readiness again before manual video generation."
  ]
}
```

Stage rules:

- if image tasks are still missing assets: `stage = manual_image_generation`
- if all images are done but video inputs are still blocked: `stage = video_input_fixing`
- if video inputs are ready but video assets are still missing: `stage = manual_video_generation`
- if both image and video assets are complete: `stage = manual_production_completed`

### GET `/projects/{project_id}/publish-readiness`

Final project-level check before publish, composition, or release.

Use cases:

- check whether all manual image tasks and manual video tasks are complete
- detect failed tasks or human-revision tasks before creating a publish record
- decide whether the project can move into publish or composition

Response example:

```json
{
  "project_id": 1,
  "ready_for_publish": true,
  "stage": "ready_for_publish",
  "next_action": "create_publish_record",
  "checks": {
    "manual_production_completed": true,
    "all_image_tasks_have_assets": true,
    "all_video_tasks_have_assets": true,
    "has_failed_tasks": false,
    "has_needs_human_revision_tasks": false,
    "has_publish_record": false
  },
  "blocking_issues": [],
  "warnings": [
    "No publish record exists yet."
  ],
  "summary": {
    "image_tasks_count": 5,
    "completed_image_tasks_count": 5,
    "video_tasks_count": 5,
    "completed_video_tasks_count": 5,
    "publish_records_count": 0
  }
}
```

Decision rules:

- missing image assets: `stage = manual_image_generation`
- missing video assets: `stage = manual_video_generation`
- failed tasks exist: `stage = review_failed_tasks`
- needs-human-revision tasks exist: `stage = review_human_revision_tasks`
- everything complete and no publish record yet: `stage = ready_for_publish`
- publish record already exists: `stage = published`

### GET `/projects/{project_id}/manual-final-checklist`

Final delivery checklist for the manual production path.

Use cases:

- check whether the project is fully ready for composition, publish, or delivery
- combine manual production stage and publish readiness into one final decision
- let Coze or an operator read one endpoint before the final handoff

Response example:

```json
{
  "project_id": 1,
  "ready_for_delivery": true,
  "production_stage": "manual_production_completed",
  "publish_stage": "ready_for_publish",
  "project_status": "draft",
  "has_publish_record": false,
  "next_action": "create_publish_record",
  "checks": {
    "images_completed": true,
    "videos_completed": true,
    "video_inputs_ready": true,
    "no_failed_tasks": true,
    "no_human_revision_tasks": true,
    "publish_record_exists": false
  },
  "blocking_issues": [],
  "warnings": [
    "No publish record exists yet."
  ],
  "summary": {
    "image_tasks_count": 5,
    "completed_image_tasks_count": 5,
    "video_tasks_count": 5,
    "completed_video_tasks_count": 5,
    "publish_records_count": 0
  },
  "recommended_steps": [
    "Create publish record or proceed to final composition/export."
  ]
}
```

Decision rules:

- if manual production is not complete, this endpoint blocks delivery first
- if publish-readiness is blocked, this endpoint follows the publish-readiness stage
- if production is complete and publish-readiness is ready, delivery is allowed
- if a publish record already exists, `next_action = completed`
