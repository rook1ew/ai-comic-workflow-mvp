# Editing Timeline Export SOP

## 目的

`GET /projects/{project_id}/editing-timeline` 用于把项目级 `editing-shot-board` 转成更适合人工剪辑的软件时间线执行清单。

它适合以下场景：
- 剪映 / CapCut 人工剪辑
- Premiere 时间线施工
- Coze 视频创作前的镜头顺序整理
- 拼帧图片漫剧 / 静态图伪动态剪辑

这个接口不会调用真实 Image2 API，也不会调用真实 Seedance API，不会产生任何 API 费用。

## 什么时候使用

推荐在以下条件满足后使用：
1. `storyboard` 已导入
2. 关键 `editing storyboard fields` 已填写
3. 每个 shot 已有可用图片素材，或至少已知道哪些 shot 缺图
4. 需要把 shot 直接转成按时间顺序排列的剪辑施工单

如果图片还没有补齐，仍然可以先调用这个接口，用来定位哪些镜头缺素材。

## 接口

```http
GET /projects/{project_id}/editing-timeline
```

## 返回核心字段

顶层字段：
- `project_id`
- `shots_count`
- `total_duration`
- `ready_for_timeline`
- `items`
- `blocking_issues`
- `next_action`

每个 `item` 包含：
- `order`
- `internal_shot_id`
- `source_shot_id`
- `start_time`
- `end_time`
- `duration`
- `image_asset_url`
- `subtitle_text`
- `sfx`
- `camera_motion`
- `subject_motion`
- `transition`
- `editing_notes`
- `ready_for_editing`
- `blocking_issues`
- `warnings`

## 时间线计算规则

1. 按 shot 顺序输出。
2. `start_time` 和 `end_time` 由前一个镜头的结束时间累加计算。
3. `duration` 优先读取 `Shot.metadata_json.duration_sec`。
4. 如果没有 `duration_sec`，系统会默认使用 `3` 秒，并在该 item 的 `warnings` 中写入 `duration_defaulted`。
5. 如果某个 shot 缺图片素材，则：
   - `ready_for_editing = false`
   - `blocking_issues` 包含 `missing_image_asset`
6. 如果任一 item 不 ready，则整个 timeline 的 `ready_for_timeline = false`。

## 素材选择规则

如果同一个 shot 下同时存在：
- mock 图片素材
- 人工回填图片素材 `manual_upload = true`

读取时会优先选择人工回填图片素材。

也就是说，`image_asset_url` 会优先返回人工确认后的正式图片，而不是旧的 mock 图片 URL。

## next_action 说明

- `continue_image_generation`
  仍有 shot 缺图片，先继续补图。
- `review_editing_fields`
  图片齐了，但部分剪辑字段仍不完整，先补充镜头运动、转场、字幕或音效提示。
- `ready_for_manual_timeline_editing`
  可以把返回结果直接当成时间线施工单，进入人工剪辑。

## 推荐操作流程

### 1. 先准备图片素材

如果项目还没有图片，先走：
- `GET /projects/{project_id}/image-prompts`
- 手动生图
- `POST /asset-tasks/{asset_task_id}/manual-asset`
- `GET /projects/{project_id}/manual-image-progress`

### 2. 再查看 shot board

调用：

```http
GET /projects/{project_id}/editing-shot-board
```

先确认：
- 哪些 shot 已有图
- 哪些 shot 缺图
- 剪辑字段是否完整

### 3. 导出 timeline

调用：

```http
GET /projects/{project_id}/editing-timeline
```

把每个 shot 的这些信息整理到剪辑工作流中：
- 起止时间
- 持续时长
- 图片素材
- 字幕
- 音效
- 镜头运动
- 人物微动
- 转场
- 剪辑备注

### 4. 在剪辑软件中执行

在剪映 / CapCut / Premiere 中，可以按 `items` 逐条施工：
- 将 `image_asset_url` 对应图片按顺序排入时间线
- 依据 `start_time` / `end_time` 设置镜头持续时间
- 根据 `camera_motion` 设置缓推、拉远、平移等镜头运动
- 根据 `subject_motion` 做人物眨眼、口型、轻微点头等伪动态
- 根据 `subtitle_text` 加字幕
- 根据 `sfx` 补门声、脚步声、惊讶声等音效
- 根据 `transition` 处理切换方式
- 根据 `editing_notes` 做局部节奏微调

### 5. 进入视频阶段或交付阶段

如果你还要手动生成视频，可以继续结合：
- `GET /projects/{project_id}/video-prompts`
- `GET /projects/{project_id}/video-readiness`
- `POST /asset-tasks/{asset_task_id}/manual-video-asset`
- `GET /projects/{project_id}/manual-video-progress`

如果整条人工生产链路已经完成，再看：
- `GET /projects/{project_id}/manual-production-summary`
- `GET /projects/{project_id}/publish-readiness`
- `GET /projects/{project_id}/manual-final-checklist`

## 示例理解

假设 timeline 中有三条：
- SH01: `0 -> 3`
- SH02: `3 -> 7`
- SH03: `7 -> 12`

那就意味着：
- 第 1 镜头放在 0 秒开始，3 秒结束
- 第 2 镜头紧接着从 3 秒开始，7 秒结束
- 第 3 镜头从 7 秒开始，12 秒结束

这样你就可以直接把它当成时间线排版参考。

## 当前限制

当前 `editing-timeline` 只是时间线施工单导出，不会：
- 自动调用真实 Image2 API
- 自动调用真实 Seedance API
- 自动生成视频
- 自动写入剪映 / CapCut / Premiere 工程文件

它的职责是：
- 帮你把 shot 转成一份清晰、可执行、可人工落地的时间线清单

## 相关文档

- [EDITING_SHOT_BOARD_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/EDITING_SHOT_BOARD_SOP.md)
- [EDITING_CUE_SHEET_EXPORT_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/EDITING_CUE_SHEET_EXPORT_SOP.md)
- [EDITING_STORYBOARD_FIELDS.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/EDITING_STORYBOARD_FIELDS.md)
- [MANUAL_PRODUCTION_WORKFLOW.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/MANUAL_PRODUCTION_WORKFLOW.md)
- [API.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/API.md)
