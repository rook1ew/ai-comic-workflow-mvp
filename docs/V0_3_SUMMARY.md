# V0_3_SUMMARY

## v0.3 目标

v0.3 的目标不是立刻放开真实图片 / 视频 provider，而是把两条路径都准备完整：

1. 真实 Image2Provider 接入前准备
2. 无 billing 的人工图视频生产闭环

当前 v0.3 已经明确包含这两条路线。

## 路线 A：Image2 real provider preparation

### v0.3-A 配置和安全开关

已完成：

- `IMAGE_PROVIDER_MODE`
- `IMAGE2_API_KEY`
- `IMAGE2_BASE_URL`
- `IMAGE2_MODEL`
- `ENABLE_REAL_IMAGE_PROVIDER`

默认仍保持安全值：

- `IMAGE_PROVIDER_MODE=mock`
- `ENABLE_REAL_IMAGE_PROVIDER=false`
- `IMAGE2_DRY_RUN=true`

### v0.3-B Image2Provider 适配骨架

已完成：

- `Image2Provider` 骨架
- `build_request_payload(...)`
- `parse_response(...)`
- `map_error(...)`
- factory 识别 `image2_real`

当前仍不发真实请求。

### v0.3-C preflight / dry-run

已完成：

- `IMAGE2_MAX_REAL_CALLS_PER_RUN`
- `IMAGE2_ALLOW_TASK_IDS`
- `IMAGE2_DRY_RUN`
- 真实调用前 preflight 检查
- dry-run 阻断逻辑

这保证即使配置误改，默认也不会直接产生真实费用。

### v0.3-D provider_audit

已完成：

- `provider_audit`
- `request_payload`
- `response_payload`
- `error_body`
- `job_id`
- `usage`
- `latency_ms`
- `real_call`
- `dry_run`
- `blocked_reason`
- `preflight_checks`

这为未来第一次真实调用提供了完整审计结构。

### v0.3-D.5 API key setup

已新增：

- [IMAGE2_API_KEY_SETUP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_API_KEY_SETUP.md)

重点说明：

- OpenAI API key 是什么
- ChatGPT Plus 不等于 API 免费额度
- 如何确认 billing / credits
- 如何写入本地 `.env`
- 为什么 `.env` 不能提交到 GitHub

### v0.3-E-Plan first real call runbook

已新增：

- [IMAGE2_FIRST_REAL_CALL_RUNBOOK.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_FIRST_REAL_CALL_RUNBOOK.md)

它定义了：

- 前置条件
- dry-run 预演检查
- 第一次真实单 task 调用前的临时配置
- 执行步骤
- 成功判断
- 失败处理
- 回滚步骤

## 路线 B：Manual image/video production workflow

这条路线用于当前没有 OpenAI API billing、也不想接真实 Image2 / Seedance API 的阶段。

### v0.3-E-alt 手动生图提示词导出

已完成：

- `GET /projects/{project_id}/image-prompts`

能力：

- 返回所有 image tasks 的 `enhanced_prompt`
- 返回 `copy_ready_prompt`
- 适合直接复制到 ChatGPT / 图片工具

### v0.3-E-alt.1 手动图片回填

已完成：

- `POST /asset-tasks/{asset_task_id}/manual-asset`

能力：

- 手动把图片 URL 或本地路径登记回 image task
- 自动创建 `provider_name = manual` 的 Asset
- 把 image task 标记为 `succeeded`

### v0.3-E-alt.2 手动图片进度检查

已完成：

- `GET /projects/{project_id}/manual-image-progress`

能力：

- 查看哪些 image tasks 已回填
- 查看哪些 image tasks 还缺图片

### v0.3-E-alt.3 视频就绪检查

已完成：

- `GET /projects/{project_id}/video-readiness`

能力：

- 检查 video task 是否已有 image asset
- 检查 duration 是否存在
- 判断是否可以进入视频生成阶段

### v0.3-E-alt.4 手动视频回填

已完成：

- `POST /asset-tasks/{asset_task_id}/manual-video-asset`

能力：

- 手动把视频 URL 或本地路径登记回 video task
- 自动创建 `provider_name = manual` 的视频 Asset
- 把 video task 标记为 `succeeded`

### v0.3-E-alt.5 手动视频进度检查

已完成：

- `GET /projects/{project_id}/manual-video-progress`

能力：

- 查看哪些 video tasks 已回填
- 查看哪些 video tasks 还缺视频

### v0.3-E-alt.6 人工生产总览

已完成：

- `GET /projects/{project_id}/manual-production-summary`

能力：

- 汇总 image progress
- 汇总 video readiness
- 汇总 manual video progress
- 判断当前阶段：
  - `manual_image_generation`
  - `video_input_fixing`
  - `manual_video_generation`
  - `manual_production_completed`

### v0.3-E-alt.7 发布前就绪检查

已完成：

- `GET /projects/{project_id}/publish-readiness`

能力：

- 检查图视频素材是否齐全
- 检查是否有 failed tasks
- 检查是否有 needs_human_revision tasks
- 检查 publish record 是否存在

### v0.3-E-alt.8 最终交付检查

已完成：

- `GET /projects/{project_id}/manual-final-checklist`

能力：

- 汇总 `manual-production-summary`
- 汇总 `publish-readiness`
- 汇总 publish record / project status
- 判断是否已具备最终合成 / 发布 / 交付条件

## 当前 v0.3 的明确边界

截至当前版本，v0.3 仍然没有做这些事：

- 真实 Image2 HTTP 调用
- 真实 Seedance API 调用
- 真实 usage / cost 落库
- 真实 billing 计费链路
- n8n
- Retrospective
- 前端
- 多租户 / SaaS 权限系统

## 当前结论

当前 v0.3 已经有两条明确可用的路线：

### A. 真实 Image2Provider 接入前准备

适合：

- 先把真实调用前的配置、安全、dry-run、审计和 runbook 准备好
- 但暂时不真正发请求

### B. Manual image/video production workflow

适合：

- 当前没有 billing
- 不想走真实 API
- 需要程序出提示词、人工生图 / 生视频、再回填素材

这意味着即使现在不接任何真实 provider，也已经能把项目从提示词导出一路推到人工图视频回填、发布前检查和最终交付检查。
