# COZE_INTEGRATION

## 概述

当前项目是 Coze-first 的后端底座。

设计原则：

- Coze 负责生成前期结构化内容
- 后端负责落库、状态管理、任务执行和 summary
- `/coze/*` 接口只做薄编排，底层逻辑复用现有 services

## 调用顺序

推荐顺序如下：

1. `POST /coze/project/init`
2. `POST /characters/{character_id}/confirm-reference`
3. `POST /coze/project/{project_id}/generate-script`
4. `POST /coze/project/{project_id}/storyboard`
5. `POST /coze/project/{project_id}/create-asset-tasks`
6. `POST /coze/project/{project_id}/run-asset-tasks`
7. `GET /coze/project/{project_id}/summary`
8. `POST /coze/project/{project_id}/publish-record`
9. `GET /coze/project/{project_id}/summary`

## 每一步 payload 与返回

### 1. 初始化项目

接口：

- `POST /coze/project/init`

payload：

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

返回重点：

- `project_id`
- `character_ids`
- `next_action = confirm_character_reference`

### 2. 确认角色主参考

接口：

- `POST /characters/{character_id}/confirm-reference`

payload：

```json
{
  "main_reference_url": "mock://character/reference.png"
}
```

返回重点：

- `main_reference_confirmed = true`
- `next_action = create_storyboard`

### 3. 写入剧本卡

接口：

- `POST /coze/project/{project_id}/generate-script`

payload：

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

返回重点：

- 自动创建默认 Episode（如果没有）
- `next_action = create_storyboard`

### 4. 写入 storyboard

接口：

- `POST /coze/project/{project_id}/storyboard`

payload：

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

返回重点：

- `episode_id`
- `shots_count`
- `next_action = create_asset_tasks`

### 5. 创建素材任务

接口：

- `POST /coze/project/{project_id}/create-asset-tasks`

payload：

```json
{
  "video_shot_ids": ["SH01", "SH07"]
}
```

返回重点：

- `created_count`
- `asset_tasks_count`
- `next_action = run_asset_tasks`

### 6. 运行素材任务

接口：

- `POST /coze/project/{project_id}/run-asset-tasks`

payload：

```json
{}
```

返回重点：

- `succeeded_count`
- `failed_count`
- `needs_human_revision_count`
- `next_action = check_summary`

### 7. 查询项目进度

接口：

- `GET /coze/project/{project_id}/summary`

返回重点：

- 任务数量
- 成功 / 失败 / 需人工修订数量
- `next_action`

### 8. 写入发布记录

接口：

- `POST /coze/project/{project_id}/publish-record`

payload：

```json
{
  "platform": "douyin",
  "title": "Episode 1",
  "published_at": "2026-04-25T10:00:00+08:00",
  "url": "https://example.com/video/1"
}
```

返回重点：

- `publish_record_id`
- `project_id`
- 项目状态更新为 `published`
- `next_action = completed`

## next_action 如何引导下一步

- `confirm_character_reference`
  - 先确认角色主参考，再继续

- `create_storyboard`
  - 已有项目和角色，但还没有可执行分镜

- `create_asset_tasks`
  - 已有 shots，但还没创建素材任务

- `run_asset_tasks`
  - 已创建任务，但还没全部执行

- `review_failed_tasks`
  - 有失败任务或人工修订任务，需要回到人工检查

- `ready_to_publish`
  - 所有任务执行成功，可以写发布记录

- `completed`
  - 已经发布完成

## 联网调用注意事项

Coze 不能直接访问你本机的 `http://127.0.0.1:8000`。

如果要让 Coze 调用本项目，需要提供公网 URL，例如：

- `ngrok`
- `Cloudflare Tunnel`
- 已部署的测试环境服务

本地调试方式通常是：

1. 本地运行 FastAPI
2. 用 `ngrok http 8000` 或 Cloudflare Tunnel 暴露公网地址
3. 在 Coze 工作流中配置该公网 URL
