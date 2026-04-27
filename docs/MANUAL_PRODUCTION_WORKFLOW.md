# MANUAL_PRODUCTION_WORKFLOW

## 目标

这份文档用一页说明当前“无 billing 的人工图视频生产闭环”。

适用场景：

- 当前没有 OpenAI API billing
- 不接真实 Image2 API
- 不接真实 Seedance API
- 程序负责提示词、结构化任务和项目进度追踪
- 人工在外部工具中完成图片 / 视频生成，再把素材回填

## 当前流程总览

完整人工生产链路如下：

1. `POST /coze/project/full-demo-flow`
2. `GET /projects/{project_id}/visual-asset-library`
3. `GET /projects/{project_id}/image-prompts`
4. `POST /asset-tasks/{asset_task_id}/manual-asset`
5. `GET /projects/{project_id}/manual-image-progress`
6. `GET /projects/{project_id}/video-readiness`
7. `GET /projects/{project_id}/video-prompts`
8. `POST /asset-tasks/{asset_task_id}/manual-video-asset`
9. `GET /projects/{project_id}/manual-video-progress`
10. `GET /projects/{project_id}/editing-shot-board`
11. `GET /projects/{project_id}/editing-timeline`
12. `GET /projects/{project_id}/editing-cue-sheet`
13. `GET /projects/{project_id}/manual-production-summary`
14. `GET /projects/{project_id}/publish-readiness`
15. `GET /projects/{project_id}/manual-final-checklist`

## 推荐操作顺序

### 1. 先准备项目和素材任务

可以直接使用：

- `POST /coze/project/full-demo-flow`

或者分步创建 project、storyboard 和 asset tasks。

### 2. 导出图片提示词

调用：

- `GET /projects/{project_id}/image-prompts`

拿到：

- `enhanced_prompt`
- `copy_ready_prompt`

然后人工复制到 ChatGPT 或其他图片工具生成图片。

### 3. 回填图片

调用：

- `POST /asset-tasks/{asset_task_id}/manual-asset`

然后再看：

- `GET /projects/{project_id}/manual-image-progress`

确认图片是否都已回填。

### 4. 检查视频是否就绪

调用：

- `GET /projects/{project_id}/video-readiness`

注意：

- 只有 `video_shot_ids` 中列出的 storyboard shot 才会创建 `video` asset task
- `video_shot_ids` 使用 storyboard 原始 shot 编号，例如 `SH01`

### 5. 导出视频提示词

调用：

- `GET /projects/{project_id}/video-prompts`

返回会自动带出：

- `image_asset_url`
- `duration`
- `base_video_prompt`
- `copy_ready_video_prompt`
- `shot_type`
- `camera_motion`
- `subject_motion`
- `transition`
- `subtitle_text`
- `sfx`
- `editing_notes`

这组字段特别适合当前的“拼帧图片漫剧 / 静态图伪动态剪辑”路线。

### 6. 手动生成并回填视频

在 Seedance 网页端或其他工具生成视频后，调用：

- `POST /asset-tasks/{asset_task_id}/manual-video-asset`

然后再看：

- `GET /projects/{project_id}/manual-video-progress`

确认视频是否都已回填。

### 7. 把 storyboard 当作剪辑施工单

调用：

- `GET /projects/{project_id}/editing-shot-board`

用途：

- 按 shot 维度查看图片是否就位
- 查看 `shot_type / camera_motion / subject_motion / transition`
- 查看 `subtitle_text / sfx / editing_notes`
- 判断每个 shot 是否已经 `ready_for_editing`

### 8. 把 shot board 转成时间线施工单

调用：

- `GET /projects/{project_id}/editing-timeline`

用途：

- 自动计算每个 shot 的 `start_time / end_time`
- 输出字幕、音效、镜头运动、人物微动和转场
- 作为剪映 / CapCut / Premiere / Coze 视频创作的时间线执行清单

### 9. 导出人类可读的 cue sheet

调用：

- `GET /projects/{project_id}/editing-cue-sheet`

用途：

- 把 `editing-timeline` 转成更适合人工阅读和复制的单行清单
- 直接复制到 Coze 视频创作、剪映备注、CapCut、Premiere、Notion 或 Excel
- 给剪辑师一个逐镜头、逐时间段的施工单

## 三层总览接口

### manual-production-summary

调用：

- `GET /projects/{project_id}/manual-production-summary`

用途：

- 看当前生产阶段卡在哪一步

阶段包括：

- `manual_image_generation`
- `video_input_fixing`
- `manual_video_generation`
- `manual_production_completed`

### publish-readiness

调用：

- `GET /projects/{project_id}/publish-readiness`

用途：

- 看当前项目是否满足发布前最低条件

重点检查：

- 图片是否齐
- 视频是否齐
- 是否存在 failed tasks
- 是否存在 needs_human_revision tasks
- 是否已有 publish record

### manual-final-checklist

调用：

- `GET /projects/{project_id}/manual-final-checklist`

用途：

- 作为最终交付 / 发布总检查接口
- 只看这一份就知道项目能不能进入最终发布或合成

## 如何决定下一步

### 如果 `manual-production-summary.stage = manual_image_generation`

继续：

- 导出 prompts
- 手动生图
- 回填图片

### 如果 `manual-production-summary.stage = video_input_fixing`

继续：

- 修图片缺口
- 修 duration 缺口
- 重新检查 `video-readiness`

### 如果 `manual-production-summary.stage = manual_video_generation`

继续：

- 先看 `video-prompts`
- 再看 `editing-shot-board`
- 最后看 `editing-timeline`
- 根据镜头运动、人物微动、字幕和音效字段生成视频
- 回填视频

### 如果 `manual-final-checklist.ready_for_delivery = true`

说明项目已经具备：

- 进入 publish record
- 进入最终合成
- 进入最终发布

## 剪辑字段的作用

当前 v0.4-A 已支持在 storyboard shot 中保存并回显这些剪辑字段：

- `shot_type`
- `camera_motion`
- `subject_motion`
- `transition`
- `subtitle_text`
- `sfx`
- `editing_notes`

用途：

- 指导拼帧图片漫剧中的镜头运动
- 指导人物微动和镜头节奏
- 作为字幕、音效和转场的剪辑备注
- 自动进入 `video-prompts` 的 `copy_ready_video_prompt`
- 自动进入 `editing-shot-board` 和 `editing-timeline`

## 当前明确不做的事

当前这条链路明确：

- 不调用真实 Image2 API
- 不调用真实 Seedance API
- 不读取真实 API key
- 不产生真实 API 费用

## 配套文档

- [MANUAL_IMAGE_GENERATION_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/MANUAL_IMAGE_GENERATION_SOP.md)
- [MANUAL_VIDEO_GENERATION_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/MANUAL_VIDEO_GENERATION_SOP.md)
- [EDITING_SHOT_BOARD_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/EDITING_SHOT_BOARD_SOP.md)
- [EDITING_TIMELINE_EXPORT_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/EDITING_TIMELINE_EXPORT_SOP.md)
- [EDITING_CUE_SHEET_EXPORT_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/EDITING_CUE_SHEET_EXPORT_SOP.md)
- [EDITING_STORYBOARD_FIELDS.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/EDITING_STORYBOARD_FIELDS.md)
- [VISUAL_ASSET_LIBRARY.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/VISUAL_ASSET_LIBRARY.md)
- [CREATIVE_STORY_BIBLE.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/CREATIVE_STORY_BIBLE.md)
- [IMAGE_PROMPT_BUILDER_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE_PROMPT_BUILDER_SOP.md)
- [API.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/API.md)

## v0.4-F 创作层增强

当前手动生产闭环已经补上 Creative Bible 与 production-grade image prompt builder：

- richer character profile
- story bible / episode bible
- creative shot fields
- reference-guided image prompt export
- suspense / horror friendly storyboard keyframe prompts

推荐顺序：

1. 先整理 `visual_asset_library_json`
   - 如果还没有整理好，可先用 `POST /projects/{project_id}/visual-asset-candidates/extract`
   - 再用 `POST /projects/{project_id}/visual-asset-library/import-candidates`
2. 再写 richer `characters_json`
3. 再写 richer `script_card_json`
4. 在 storyboard shot 中补：
   - editing fields
   - creative fields
   - asset key references
5. 最后导出 `image-prompts`

这样程序输出的已经不是“普通生图提示词”，而是适合拼帧漫剧生产的单镜头分镜图提示词。

## v0.4-G Visual Asset Candidate workflow

当前素材库准备可以走两条路：

1. 手动导入
   - `POST /projects/{project_id}/visual-asset-library/manual-import`
2. 自动候选提取
   - `POST /projects/{project_id}/visual-asset-candidates/extract`
   - review
   - `POST /projects/{project_id}/visual-asset-library/import-candidates`

推荐顺序：

1. 先看 `GET /projects/{project_id}/visual-asset-library`
2. 如果库为空：
   - `next_action = extract_or_manual_import_assets`
3. 如果有资产但缺 URL：
   - `next_action = complete_reference_urls`
4. 资产完整后，再进入：
   - `image-prompts`
   - `editing-shot-board`
   - `editing-cue-sheet`
