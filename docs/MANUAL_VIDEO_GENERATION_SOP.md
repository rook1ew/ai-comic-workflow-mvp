# MANUAL_VIDEO_GENERATION_SOP

## 目标

当前项目在没有 Seedance API billing 的前提下，先走“视频就绪检查 + 人工生成视频 + 手动回填”的执行流程。

这份 SOP 说明：

1. 如何确认视频任务是否已具备生成条件
2. 如何手动生成视频
3. 如何回填视频 Asset
4. 如何检查单任务和项目级视频进度
5. 如何结合 `manual-production-summary` 判断是否已进入发布或合成阶段

## 总览接口优先

推荐先调用：

- `GET /projects/{project_id}/manual-production-summary`
- `GET /projects/{project_id}/publish-readiness`
- `GET /projects/{project_id}/manual-final-checklist`

如果返回：

- `stage = manual_video_generation`

说明图片阶段已经完成、视频输入已经准备好，可以继续人工视频生产。

如果返回：

- `stage = video_input_fixing`

说明还不能进入视频生成，应该先修正图片缺口或 duration 等输入问题。

`manual-production-summary` 用于看当前生产阶段，`publish-readiness` 用于在视频全部完成后做发布前放行检查，`manual-final-checklist` 用于最终交付总检查。

## 视频前检查

调用：

- `GET /projects/{project_id}/video-readiness`

前提说明：

- 只有在 `video_shot_ids` 中列出的 storyboard shot，系统才会创建 `video` 类型 asset task
- `video_shot_ids` 使用的是 storyboard 里的源镜头编号，例如 `SH01`
- 没有出现在 `video_shot_ids` 里的 shot，默认不会进入视频阶段

重点看每个 video task：

- `has_image_asset`
- `image_asset_url`
- `has_duration`
- `duration`
- `ready_for_video`
- `blocking_issues`

规则：

- 缺图片时会有 `missing_image_asset`
- 缺 duration 时会有 `missing_duration`
- 所有 video tasks 都 ready 时：`next_action = ready_for_video_generation`

## 人工生成视频

当某个 video task 已 ready 后，可以手动在这些地方生成视频：

- Seedance 网页端
- 其他外部视频工具

建议记录：

- `asset_task_id`
- `source_shot_id`
- 使用的图片 URL 或本地文件
- 使用的 `duration`
- 使用的 `video_prompt`
- 导出视频路径或 URL

## 回填视频 Asset

调用：

- `POST /asset-tasks/{asset_task_id}/manual-video-asset`

示例：

```json
{
  "asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4",
  "asset_type": "video",
  "notes": "手动用 Seedance 网页端生成，已确认画面可用"
}
```

回填后：

- 会创建 `provider_name = manual` 的视频 Asset
- 对应 video task 会更新为 `succeeded`

## 检查单个视频任务

调用：

- `GET /asset-tasks/{asset_task_id}/provider-debug`

重点检查：

- `asset_url`
- `status`
- `error_message`

## 检查项目级视频进度

调用：

- `GET /projects/{project_id}/manual-video-progress`

它会告诉你：

- 总共有多少 video tasks
- 已完成多少
- 还缺多少
- 有多少是手动回填

规则：

- 如果全部完成：`next_action = manual_videos_completed`
- 如果还有缺失：`next_action = continue_manual_video_generation`

## 与总览接口配合使用

建议顺序：

1. 先看 `GET /projects/{project_id}/manual-production-summary`
2. 如果 `stage = manual_video_generation`
   - 再看 `GET /projects/{project_id}/video-readiness`
   - 手动生成视频
   - 调 `POST /asset-tasks/{asset_task_id}/manual-video-asset`
3. 用 `GET /asset-tasks/{asset_task_id}/provider-debug` 检查单任务
4. 用 `GET /projects/{project_id}/manual-video-progress` 看项目级视频进度
5. 再回到 `manual-production-summary` 看是否已经完成整个手动生产链路

## 完成判定

当：

- `GET /projects/{project_id}/manual-video-progress` 返回 `next_action = manual_videos_completed`
- 并且 `GET /projects/{project_id}/manual-production-summary` 返回：
  - `stage = manual_production_completed`
  - `next_action = ready_for_publish_or_composition`
- 并且 `GET /projects/{project_id}/publish-readiness` 返回：
  - `ready_for_publish = true`
- 并且 `GET /projects/{project_id}/manual-final-checklist` 返回：
  - `ready_for_delivery = true`

就可以进入：

- 发布前整理
- 合成阶段
- 最终审核阶段

## 当前限制

- 不调用真实 Seedance API
- 不调用真实 Image2 API
- 不读取真实 API key
- 不产生真实 API 费用
- 不影响现有 mock / dry-run / provider_audit 逻辑
