# API

## Coze 统一返回格式

所有 `/coze/*` 接口都返回：

```json
{
  "success": true,
  "code": "OK",
  "message": "",
  "data": {},
  "next_action": ""
}
```

## Coze 接口

### POST /coze/project/init

用途：

- 接收 Coze 已整理好的项目卡和角色 JSON
- 创建 `Project` 和 `Character`

请求示例：

```json
{
  "project_card_json": {
    "project_title": "Urban Hook",
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
  }
}
```

响应示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "Project and characters initialized",
  "data": {
    "project_id": 1,
    "character_ids": [1]
  },
  "next_action": "confirm_character_reference"
}
```

### POST /characters/{character_id}/confirm-reference

用途：

- 确认角色主参考

请求示例：

```json
{
  "main_reference_url": "mock://character/reference.png"
}
```

响应示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "Character reference confirmed",
  "data": {
    "character_id": 1,
    "main_reference_confirmed": true,
    "main_reference_url": "mock://character/reference.png"
  },
  "next_action": "create_storyboard"
}
```

### POST /coze/project/{project_id}/generate-script

用途：

- 不在后端生成剧本
- 只接收 Coze 已生成好的 `script_card_json`
- 若项目下没有 Episode，则创建默认 `Episode 1`
- 将剧本卡写入 `Episode.script_card`

请求示例：

```json
{
  "script_card_json": {
    "opening_hook": "She walks into the wrong meeting room",
    "conflict": "Everyone mistakes her identity",
    "escalation": "She cannot explain in time",
    "turning_point": "The boss asks her to stay",
    "ending_hook": "A promotion rumor starts"
  }
}
```

响应示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "Script card saved",
  "data": {
    "project_id": 1,
    "episode_id": 1
  },
  "next_action": "create_storyboard"
}
```

### POST /coze/project/{project_id}/storyboard

用途：

- 导入 Coze 已经生成好的 storyboard JSON
- 创建默认 Episode / Scene / Shots

请求示例：

```json
{
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
  }
}
```

响应示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "Storyboard imported",
  "data": {
    "project_id": 1,
    "episode_id": 1,
    "shots_count": 2
  },
  "next_action": "create_asset_tasks"
}
```

### POST /coze/project/{project_id}/create-asset-tasks

用途：

- 批量创建素材任务
- 默认每个 shot 创建 `image + voice + bgm`
- 指定镜头可额外创建 `video`

请求示例：

```json
{
  "video_shot_ids": ["SH01", "SH07"]
}
```

响应示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "Asset tasks created",
  "data": {
    "created_count": 7,
    "skipped_count": 0,
    "asset_tasks_count": 7
  },
  "next_action": "run_asset_tasks"
}
```

### POST /coze/project/{project_id}/run-asset-tasks

用途：

- 批量执行该项目下 `queued / needs_retry` 的 asset tasks

响应示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "Asset tasks executed",
  "data": {
    "succeeded_count": 7,
    "failed_count": 0,
    "needs_human_revision_count": 0
  },
  "next_action": "check_summary"
}
```

### POST /coze/project/{project_id}/publish-record

用途：

- 创建发布记录
- 发布后将项目状态更新为 `published`

请求示例：

```json
{
  "platform": "douyin",
  "title": "Episode 1",
  "published_at": "2026-04-25T10:00:00+08:00",
  "url": "https://example.com/video/1"
}
```

响应示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "Publish record created",
  "data": {
    "publish_record_id": 1,
    "project_id": 1
  },
  "next_action": "completed"
}
```

### GET /coze/project/{project_id}/summary

用途：

- 查询项目当前阶段
- 返回下一步动作建议

响应示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "Project summary fetched",
  "data": {
    "project_id": 1,
    "project_status": "published",
    "episodes_count": 1,
    "scenes_count": 1,
    "shots_count": 2,
    "asset_tasks_count": 7,
    "assets_count": 7,
    "succeeded_tasks_count": 7,
    "failed_tasks_count": 0,
    "needs_human_revision_count": 0,
    "publish_records_count": 1,
    "next_action": "create_publish_record"
  },
  "next_action": "completed"
}
```

## next_action 说明

- `confirm_character_reference`
  - 还没有任何已确认的角色主参考

- `create_storyboard`
  - 还没有 storyboard / shots

- `create_asset_tasks`
  - 已有 shots，但还没有 asset tasks

- `run_asset_tasks`
  - 还有 queued 或 needs_retry 的任务未执行

- `review_failed_tasks`
  - 存在 failed 或 needs_human_revision 的任务

- `ready_to_publish`
  - 所有任务都已成功

- `completed`
  - 已创建 publish record，且项目状态为 `published`
