# Editing Cue Sheet Export SOP

## 目的

`GET /projects/{project_id}/editing-cue-sheet` 用于把项目级 `editing-timeline`
转成更适合人工阅读、复制和分发的 shot-by-shot 剪辑清单。

它适合以下场景：
- 复制到 Coze 视频创作
- 粘贴到剪映 / CapCut 备注
- 发给 Premiere 剪辑师
- 贴进 Notion、飞书表格或 Excel
- 作为拼帧图片漫剧的人工施工单

这个接口不会调用真实 Image2 API，也不会调用真实 Seedance API，不会产生任何 API 费用。

## 三层视图怎么用

当前推荐这样理解三层导出：

1. `editing-shot-board`
- 适合按 shot 检查素材、字段、字幕、音效和卡点

2. `editing-timeline`
- 适合系统化时间线
- 看每个镜头的 `start_time / end_time / duration`

3. `editing-cue-sheet`
- 适合人类直接阅读和复制
- 每个 shot 会变成一条 `cue_line`
- 整个项目会输出一段 `plain_text`

## 接口

```http
GET /projects/{project_id}/editing-cue-sheet
```

## 返回核心字段

顶层字段：
- `project_id`
- `shots_count`
- `total_duration`
- `ready_for_cue_sheet`
- `items`
- `plain_text`
- `blocking_issues`
- `next_action`

每个 `item` 包含：
- `order`
- `source_shot_id`
- `time_range`
- `duration`
- `image_asset_url`
- `subtitle_text`
- `sfx`
- `camera_motion`
- `subject_motion`
- `transition`
- `editing_notes`
- `cue_line`
- `ready_for_editing`
- `blocking_issues`
- `warnings`

## cue_line 是什么

`cue_line` 是给人直接看的单行剪辑说明。

例如：

```text
SH01 | 0.0s-3.0s | 图片: file:///D:/AI-comic-assets/SH01.png | 字幕: 不好意思，我走错了。 | 音效: door_open | 镜头: slow_push_in | 人物微动: blink, slight_body_shift | 转场: cut | 备注: Use slight zoom-in and nervous pause.
```

这行文本可以直接：
- 复制给剪辑师
- 粘贴到 Coze 视频创作
- 粘贴到剪映 / CapCut 镜头备注
- 贴进 Premiere 时间线笔记
- 贴进 Notion / Excel 做执行清单

## plain_text 是什么

`plain_text` 是所有 `cue_line` 拼接后的多行文本。

你可以直接整段复制，用于：
- 发给剪辑师
- 贴进 Coze
- 存档到项目文档
- 发到群里做施工说明

## 规则

1. 按 `editing-timeline` 的顺序输出。
2. 如果缺图片素材：
- `ready_for_cue_sheet = false`
- `blocking_issues` 包含 `missing_image_asset`
3. 如果缺 `subtitle_text`：
- 不阻塞
- `warnings` 包含 `missing_subtitle_text`
4. 如果缺 `sfx`：
- 不阻塞
- `warnings` 包含 `missing_sfx`
5. 如果缺 `camera_motion / subject_motion / transition / editing_notes`：
- 不阻塞
- 但会在 `warnings` 中提示
6. 如果所有 shot 都具备基本条件：
- `ready_for_cue_sheet = true`
- `next_action = ready_for_manual_editing`
7. 如果存在阻塞项：
- `ready_for_cue_sheet = false`
- `next_action = fix_editing_inputs`

## 推荐操作流程

### 1. 先准备图片素材

如果图片还没补齐，先走：
- `GET /projects/{project_id}/image-prompts`
- 手动生图
- `POST /asset-tasks/{asset_task_id}/manual-asset`
- `GET /projects/{project_id}/manual-image-progress`

### 2. 再检查 shot board

调用：

```http
GET /projects/{project_id}/editing-shot-board
```

确认：
- 图片是否到位
- shot_type / camera_motion / subject_motion / transition 是否有值
- subtitle / sfx / editing_notes 是否基本可用

### 3. 生成 timeline

调用：

```http
GET /projects/{project_id}/editing-timeline
```

先确认每个 shot 的：
- 起止时间
- 持续时间
- 图片素材

### 4. 导出 cue sheet

调用：

```http
GET /projects/{project_id}/editing-cue-sheet
```

然后：
- 逐条查看 `cue_line`
- 需要时复制整个 `plain_text`

### 5. 按 cue_line 执行拼帧剪辑

可以按下面方式施工：
- 根据 `time_range` 在时间线上摆放图片
- 根据 `camera_motion` 设定缓推、拉远、平移
- 根据 `subject_motion` 做眨眼、口型、轻微身体移动
- 根据 `subtitle_text` 加字幕
- 根据 `sfx` 加音效
- 根据 `transition` 处理镜头切换
- 根据 `editing_notes` 做节奏和重点强调

## next_action 说明

- `fix_editing_inputs`
说明还缺图片或关键输入，先修正

- `ready_for_manual_editing`
说明 cue sheet 已可直接交给人工剪辑或复制到 Coze / 剪映 / CapCut / Premiere

## 当前限制

当前 `editing-cue-sheet` 只是导出执行清单，不会：
- 自动调用真实 Image2 API
- 自动调用真实 Seedance API
- 自动生成视频
- 自动写入剪映 / CapCut / Premiere 工程文件

它的职责是：
- 帮你把 `editing-timeline` 转成人类可读的施工单

## 相关文档

- [EDITING_SHOT_BOARD_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/EDITING_SHOT_BOARD_SOP.md)
- [EDITING_TIMELINE_EXPORT_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/EDITING_TIMELINE_EXPORT_SOP.md)
- [EDITING_STORYBOARD_FIELDS.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/EDITING_STORYBOARD_FIELDS.md)
- [MANUAL_PRODUCTION_WORKFLOW.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/MANUAL_PRODUCTION_WORKFLOW.md)
- [API.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/API.md)
