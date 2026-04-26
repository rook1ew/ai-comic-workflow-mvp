# MANUAL_VIDEO_GENERATION_SOP

## 目标

当项目已经完成人工图片阶段，但暂时不接真实 Seedance API 时，这份 SOP 说明如何手动生成视频并回填到系统。

## 前置条件

先确保这些步骤已经完成：

1. `GET /projects/{project_id}/image-prompts`
2. 手动生成图片
3. `POST /asset-tasks/{asset_task_id}/manual-asset`
4. `GET /projects/{project_id}/manual-image-progress`
5. `GET /projects/{project_id}/video-readiness`

只有当：

- `GET /projects/{project_id}/video-readiness`

返回：

- `next_action = ready_for_video_generation`

时，才建议进入手动视频阶段。

## 第一步：检查视频就绪状态

调用：

- `GET /projects/{project_id}/video-readiness`

重点看每个 video task：

- `has_image_asset`
- `image_asset_url`
- `has_duration`
- `duration`
- `ready_for_video`
- `blocking_issues`

如果缺图片：

- 先回到人工图片阶段

如果缺 duration：

- 先修正 storyboard / task 输入

## 第二步：手动生成视频

当某个 video task 已 ready 后，可以手动在：

- Seedance 网页端
- 或其他外部视频工具

中生成视频。

建议至少记录：

- `asset_task_id`
- `source_shot_id`
- 使用的 image source
- 使用的 duration
- 使用的 video prompt
- 导出视频文件名
- 视频最终本地路径或 URL

## 第三步：回填视频 Asset

当视频已经手动生成并保存好后，调用：

- `POST /asset-tasks/{asset_task_id}/manual-video-asset`

请求示例：

```json
{
  "asset_url": "file:///D:/ai-comic-assets/SH01_video.mp4",
  "asset_type": "video",
  "notes": "手动用 Seedance 网页端生成，已确认画面可用"
}
```

回填后：

- 会创建新的 video `Asset`
- `provider_name = manual`
- `metadata_json.source = manual_video_generation`
- 对应 video task 会变成 `succeeded`

## 第四步：检查视频回填结果

回填完成后，调用：

- `GET /asset-tasks/{asset_task_id}/provider-debug`

重点检查：

- `asset_url`
- `status`
- `error_message`

这样可以确认视频回填是否已经被后端正确接收。

## 当前限制

当前阶段明确：

- 不调用真实 Seedance API
- 不调用真实 Image2 API
- 不读取真实 API key
- 不产生真实 API 费用

## 推荐人工视频流程

1. `GET /projects/{project_id}/video-readiness`
2. 找到 `ready_for_video = true` 的 video tasks
3. 手动在 Seedance 网页端或其他工具生成视频
4. 保存视频
5. `POST /asset-tasks/{asset_task_id}/manual-video-asset`
6. `GET /asset-tasks/{asset_task_id}/provider-debug`

这样就能在没有 billing 的阶段，把视频资产也闭环回填到系统中。
