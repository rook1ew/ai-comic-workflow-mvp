# MANUAL_IMAGE_GENERATION_SOP

## 目标

当前项目在没有 Image2 API billing 的前提下，先走“人工生图 + 手动回填”的可执行流程。

这份 SOP 说明：

1. 如何导出可复制提示词
2. 如何手动生成图片
3. 如何回填图片 Asset
4. 如何检查图片阶段进度
5. 如何用 `manual-production-summary` 决定下一步

## 总览接口优先

推荐先调用：

- `GET /projects/{project_id}/manual-production-summary`
- `GET /projects/{project_id}/publish-readiness`
- `GET /projects/{project_id}/manual-final-checklist`

它会告诉你当前项目处于哪一个阶段：

- `manual_image_generation`
- `video_input_fixing`
- `manual_video_generation`
- `manual_production_completed`

如果当前 `stage = manual_image_generation`，说明还需要继续导出提示词、生成图片并回填图片。

`manual-production-summary` 用于看当前生产阶段，`publish-readiness` 用于发布前最终放行检查，`manual-final-checklist` 用于最终交付 / 发布总检查。

## 人工生图完整流程

1. 先生成项目和镜头任务
2. 调用 `GET /projects/{project_id}/image-prompts`
3. 复制 `copy_ready_prompt` 到 ChatGPT 或其他图片工具
4. 保存生成图片
5. 调用 `POST /asset-tasks/{asset_task_id}/manual-asset` 回填图片
6. 调用 `GET /asset-tasks/{asset_task_id}/provider-debug` 检查单任务结果
7. 调用 `GET /projects/{project_id}/manual-image-progress` 检查项目图片进度
8. 再调用 `GET /projects/{project_id}/manual-production-summary` 看总阶段是否推进

## 如何生成 image tasks

可以用两种方式：

1. 直接跑 `POST /coze/project/full-demo-flow`
2. 或按分步流程：
   - `POST /coze/project/init`
   - `POST /characters/{character_id}/confirm-reference`
   - `POST /coze/project/{project_id}/generate-script`
   - `POST /coze/project/{project_id}/storyboard`
   - `POST /coze/project/{project_id}/create-asset-tasks`

## 导出手动生图提示词

调用：

- `GET /projects/{project_id}/image-prompts`

重点字段：

- `asset_task_id`
- `source_shot_id`
- `base_prompt`
- `enhanced_prompt`
- `copy_ready_prompt`

其中 `copy_ready_prompt` 已经组合了：

- 增强后的剧情提示词
- 竖屏漫剧构图要求
- 角色一致性要求
- negative prompt

## 手动生成图片

把 `copy_ready_prompt` 粘贴到：

- ChatGPT 图片生成
- 其他不需要在本项目里接 API 的图片工具

建议：

1. 一次只处理一个 `asset_task_id`
2. 保留 `source_shot_id`
3. 记录最终保存路径或 URL
4. 不要模仿具体 IP、明星、影视角色或已知动漫角色

## 回填图片 Asset

调用：

- `POST /asset-tasks/{asset_task_id}/manual-asset`

示例：

```json
{
  "asset_url": "file:///D:/ai-comic-assets/SH01.png",
  "asset_type": "image",
  "notes": "手动用 ChatGPT 生成，已确认角色一致"
}
```

回填后：

- 会创建一个 `provider_name = manual` 的图片 Asset
- 对应 image task 会更新为 `succeeded`

## 检查单任务结果

调用：

- `GET /asset-tasks/{asset_task_id}/provider-debug`

重点看：

- `asset_url`
- `status`
- `error_message`

## 检查图片阶段进度

调用：

- `GET /projects/{project_id}/manual-image-progress`

它会告诉你：

- 总共有多少 image tasks
- 已完成多少
- 还缺多少
- 有多少是手动回填

规则：

- 如果所有 image tasks 都已有图片：`next_action = manual_images_completed`
- 如果还有缺失：`next_action = continue_manual_image_generation`

## 与总览接口配合使用

建议顺序：

1. 先看 `GET /projects/{project_id}/manual-production-summary`
2. 如果 `stage = manual_image_generation`
   - 调 `GET /projects/{project_id}/image-prompts`
   - 手动生图
   - 调 `POST /asset-tasks/{asset_task_id}/manual-asset`
3. 再看 `GET /projects/{project_id}/manual-image-progress`
4. 再回到 `manual-production-summary` 看是否进入下一阶段

## 下一步：进入视频前检查

当图片阶段基本完成后，继续调用：

- `GET /projects/{project_id}/video-readiness`

如果视频侧所有输入都齐全，`manual-production-summary` 会推进到：

- `stage = manual_video_generation`

这时再进入视频 SOP：

- [MANUAL_VIDEO_GENERATION_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/MANUAL_VIDEO_GENERATION_SOP.md)

## 发布前最终检查

当图片和视频都完成后，继续调用：

- `GET /projects/{project_id}/publish-readiness`
- `GET /projects/{project_id}/manual-final-checklist`

只有当：

- `ready_for_publish = true`
- `ready_for_delivery = true`

时，才建议：

- 创建 publish record
- 进入合成阶段
- 进入最终发布阶段

## 当前限制

- 不调用真实 Image2 API
- 不读取真实 API key
- 不产生真实 API 费用
- 不影响现有 mock / dry-run / provider_audit 逻辑
