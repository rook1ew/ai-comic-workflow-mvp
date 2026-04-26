# MANUAL_IMAGE_GENERATION_SOP

## 目标

当前用户还没有 OpenAI API billing，因此暂时不进入真实 `Image2Provider` 调用。

这份 SOP 负责说明“人工图片阶段”的完整流程，并与视频前检查阶段衔接。

## 人工图片阶段完整流程

1. 先用现有工作流生成 image tasks
2. 通过 `GET /projects/{project_id}/image-prompts` 导出可复制提示词
3. 手动粘贴到 ChatGPT 或其他图片生成工具
4. 保存生成图片
5. 通过 `POST /asset-tasks/{asset_task_id}/manual-asset` 回填图片 Asset
6. 通过 `GET /asset-tasks/{asset_task_id}/provider-debug` 检查单任务回填结果
7. 通过 `GET /projects/{project_id}/manual-image-progress` 检查整体图片进度
8. 通过 `GET /projects/{project_id}/video-readiness` 检查是否可以进入视频阶段

## 当前方案特点

- 不调用真实 Image2 API
- 不读取真实 API key
- 不产生真实 API 费用
- 不影响现有 full-demo-flow 的 mock 演示链路

## 生成 image tasks

你可以用两种方式准备 image tasks。

### 方式 A：直接跑 full-demo-flow

推荐调用：

- `POST /coze/project/full-demo-flow`

### 方式 B：分步流程

按顺序调用：

1. `POST /coze/project/init`
2. `POST /characters/{character_id}/confirm-reference`
3. `POST /coze/project/{project_id}/generate-script`
4. `POST /coze/project/{project_id}/storyboard`
5. `POST /coze/project/{project_id}/create-asset-tasks`

## 导出手动生图提示词

调用：

- `GET /projects/{project_id}/image-prompts`

重点使用字段：

- `asset_task_id`
- `source_shot_id`
- `enhanced_prompt`
- `copy_ready_prompt`

## 复制到 ChatGPT / 图片生成工具

拿到 `copy_ready_prompt` 后，可以手动复制到：

- ChatGPT 图片生成
- 其他不需要在本项目里接 API 的图片生成工具

推荐做法：

1. 一次只处理一个 image task
2. 保留 `source_shot_id`
3. 保留 `asset_task_id`
4. 生成后把图片文件按 shot 对应关系存好

## 回填图片 Asset

当图片已经手动生成并保存好后，调用：

- `POST /asset-tasks/{asset_task_id}/manual-asset`

请求示例：

```json
{
  "asset_url": "file:///D:/ai-comic-assets/SH01.png",
  "asset_type": "image",
  "notes": "手动用 ChatGPT 生成，已确认角色一致"
}
```

回填后：

- 会创建新的 `Asset`
- `provider_name = manual`
- `metadata_json.source = manual_image_generation`
- 对应 image task 会变成 `succeeded`

## 检查单个图片任务结果

调用：

- `GET /asset-tasks/{asset_task_id}/provider-debug`

重点检查：

- `asset_url`
- `status`
- `error_message`

## 检查项目级图片进度

调用：

- `GET /projects/{project_id}/manual-image-progress`

它会告诉你：

- 总共有多少个 image tasks
- 已完成多少个
- 还缺多少个
- 其中有多少个是手动回填
- 下一步是否应继续人工生图

规则：

- 如果所有 image tasks 都已有图片，`next_action = manual_images_completed`
- 如果还有缺失，`next_action = continue_manual_image_generation`

## 进入视频前检查

当图片阶段基本完成后，继续调用：

- `GET /projects/{project_id}/video-readiness`

只有当返回：

- `next_action = ready_for_video_generation`

时，才建议进入视频阶段。

## 安全与内容提醒

- 不要模仿具体 IP
- 不要模仿明星
- 不要模仿影视角色
- 不要模仿已知动漫角色
- 当前不会产生 API 费用
- 当前不会触发真实 Image2 调用
- 当前不需要真实 API key
