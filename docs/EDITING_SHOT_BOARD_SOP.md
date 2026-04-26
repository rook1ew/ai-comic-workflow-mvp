# EDITING_SHOT_BOARD_SOP

## 目标

`editing-shot-board` 是当前“拼帧图片漫剧 / 静态图伪动态剪辑”路线下的项目级剪辑施工单接口。

它的作用不是生成素材，而是把每个 shot 当前是否具备剪辑条件一次性展示出来。

## 什么时候使用

推荐在这些步骤之后使用：

1. `full-demo-flow` 或分步 storyboard 导入完成
2. `image-prompts` 已导出
3. 关键图片已经手动生成并回填

这时可以调用：

- `GET /projects/{project_id}/editing-shot-board`

## 它会告诉你什么

每个 shot 会回显：

- `source_shot_id`
- `image_asset_url`
- `duration`
- `shot_type`
- `camera_motion`
- `subject_motion`
- `transition`
- `subtitle_text`
- `sfx`
- `editing_notes`
- `ready_for_editing`
- `blocking_issues`

## 如何把它当作剪辑施工单

### 1. 先看项目级 next_action

- `continue_image_generation`
  - 说明还有 shot 缺图片，先不要进入剪辑
- `review_editing_fields`
  - 说明图片已经有了，但镜头运动、字幕、音效或备注还不够
- `ready_for_manual_editing`
  - 说明已经可以交给人工剪辑

### 2. 再按 shot 逐条执行

对每个 item：

- 如果 `has_image_asset = false`
  - 先回去补图
- 如果 `ready_for_editing = false`
  - 看 `blocking_issues`
  - 补齐图片或剪辑字段
- 如果 `ready_for_editing = true`
  - 可以直接把这一条作为剪辑施工单

### 3. 剪辑时优先关注这些字段

- `camera_motion`
  - 决定镜头推拉摇移
- `subject_motion`
  - 决定人物是否轻微眨眼、点头、转头、嘴动
- `transition`
  - 决定镜头切换方式
- `subtitle_text`
  - 决定字幕重点
- `sfx`
  - 决定音效 cue
- `editing_notes`
  - 决定节奏、压迫感、停顿点、反转点

## 当前推荐流程

1. `GET /projects/{project_id}/image-prompts`
2. 手动生图
3. `POST /asset-tasks/{asset_task_id}/manual-asset`
4. `GET /projects/{project_id}/manual-image-progress`
5. `GET /projects/{project_id}/editing-shot-board`
6. `GET /projects/{project_id}/editing-timeline`
7. `GET /projects/{project_id}/editing-cue-sheet`
8. 根据 shot board、timeline 和 cue sheet 进入人工剪辑
9. 如需视频辅助，再看 `video-prompts` 或 `manual-video-progress`
10. 最后看 `manual-production-summary` / `publish-readiness` / `manual-final-checklist`

## 当前限制

- 不调用真实 Image2 API
- 不调用真实 Seedance API
- 不读取真实 API key
- 不产生真实费用
