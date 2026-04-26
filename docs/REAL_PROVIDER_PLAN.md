# REAL_PROVIDER_PLAN

## 目标

当前系统已经具备完整的 mock provider 演示链路，也已经把真实 provider 接入前需要的 payload 校验、输入调试、readiness 检查和安全开关准备好了。

这份文档的目标是明确：

- v0.2 做了哪些 provider readiness 能力
- v0.3 做了哪些真实 Image2 接入前准备
- 当前为什么仍然停在真实调用前
- 后续 v0.3-E / v0.4 应该如何推进

## 总体路线

- v0.2：完成 Provider Readiness 底座
- v0.3：完成真实 `Image2Provider` 调用前准备
- v0.4：再考虑真实 `SeedanceVideoProvider` 接入

当前明确状态：

- v0.2 已完成
- v0.3 已完成到真实调用前准备阶段
- 真实 Image2 调用尚未开启
- 真实 Seedance 调用尚未开始

## v0.2 已完成的 Provider Readiness 能力

### 1. 统一 provider 输入输出契约

当前已经定义并落地：

- `ImageProviderInput`
- `VideoProviderInput`
- `ProviderResult(url, metadata)`

其中：

- image provider 输入重点包含：
  - `prompt`
  - `character_reference_url`
  - `shot_id`
  - `style`
  - `storyboard_context`
- video provider 输入重点包含：
  - `image_url`
  - `prompt`
  - `duration`
  - `aspect_ratio`
  - `resolution`

### 2. storyboard 元信息透传

`storyboard_json` 导入后，会把以下信息保存到 `Shot.metadata_json`：

- `source_shot_id`
- `duration_sec`
- `character`
- `location`
- `emotion`
- `camera`
- `dialogue`

这些信息后续会透传到：

- image provider input
- image asset metadata
- video task 的 `duration` 组装逻辑

### 3. enhanced_prompt

当前 image task 已支持 `enhanced_prompt` 生成。

增强来源包括：

- 原始 `image_prompt`
- `visual_style`
- `character_reference_url`
- storyboard context

同时保持安全约束：

- 不直接模仿具体 IP
- 不直接模仿明星
- 不直接模仿影视角色
- 不直接模仿已知动漫角色

### 4. provider debug

当前已提供：

- `GET /asset-tasks/{asset_task_id}/provider-debug`
- `GET /projects/{project_id}/provider-debug-summary`

用途包括：

- 查看最终送给 provider 的 `input_payload`
- 检查 image task 是否已有 `enhanced_prompt`
- 检查 storyboard context 是否正确透传
- 检查 video task 是否已有 `image_url` 和 `duration`
- 在接真实 provider 前做 task 级和 project 级联调排查

### 5. provider readiness

当前已提供：

- `POST /coze/project/validate-payload`
- `GET /projects/{project_id}/provider-readiness`

它们的作用是：

- 在 `full-demo-flow` 之前检查 Coze payload 是否完整
- 在 mock 流程跑完之后检查项目是否满足切换真实 provider 的最低条件

## v0.3 已完成内容

### v0.3-A 配置和安全开关

已增加配置项：

- `IMAGE_PROVIDER_MODE`
- `IMAGE2_API_KEY`
- `IMAGE2_BASE_URL`
- `IMAGE2_MODEL`
- `ENABLE_REAL_IMAGE_PROVIDER`

默认仍然保持：

- `IMAGE_PROVIDER_MODE=mock`
- `ENABLE_REAL_IMAGE_PROVIDER=false`

即使配置切到 `image2_real`，没有满足条件也不会真实调用。

### v0.3-B Image2Provider 适配骨架

已实现：

- `Image2Provider` 类骨架
- `build_request_payload(...)`
- `parse_response(...)`
- `map_error(...)`
- factory 对 `image2_real` 的识别

当前仍然不会：

- 发送真实 HTTP 请求
- 调用真实 Image2 API
- 产生真实费用

### v0.3-C preflight / dry-run

已增加保护配置：

- `IMAGE2_MAX_REAL_CALLS_PER_RUN`
- `IMAGE2_ALLOW_TASK_IDS`
- `IMAGE2_DRY_RUN`

并增加了 image2_real preflight 检查逻辑。

只有在未来同时满足这些条件时，系统才应该进入真实调用路径：

- `provider_name = image2_real`
- `IMAGE_PROVIDER_MODE = image2_real`
- `ENABLE_REAL_IMAGE_PROVIDER = true`
- `IMAGE2_API_KEY` 存在
- `IMAGE2_BASE_URL` 存在
- `IMAGE2_DRY_RUN = false`
- 当前 task 在 `IMAGE2_ALLOW_TASK_IDS` 中
- 不超过 `IMAGE2_MAX_REAL_CALLS_PER_RUN`
- `task.modality = image`
- task 已有 `enhanced_prompt`

但当前版本即使满足条件，也仍不会发真实请求。

### v0.3-D provider_audit

已标准化真实 provider 调用前后的审计结构：

- `provider_audit`

关键字段包括：

- `request_payload`
- `response_payload`
- `error_body`
- `job_id`
- `usage`
- `latency_ms`
- `real_call`
- `dry_run`
- `blocked_reason`
- `preflight_passed`
- `preflight_checks`

这套结构当前已经会在 image2_real 的 blocked / dry-run 场景下落到 task 输出中，用于未来真实调用排查。

### v0.3-D.5 API key setup

已补充本地安全配置说明：

- [IMAGE2_API_KEY_SETUP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_API_KEY_SETUP.md)

重点包括：

- OpenAI API key 的基本概念
- ChatGPT Plus 不等于 API 免费额度
- billing / credits 检查
- `.env` 本地配置方式
- key 泄露后的处理方式

### v0.3-E-Plan first real call runbook

已补充第一次真实单 task 调用前的 runbook：

- [IMAGE2_FIRST_REAL_CALL_RUNBOOK.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_FIRST_REAL_CALL_RUNBOOK.md)

它定义了：

- 前置条件
- 第一次真实调用前检查
- 临时 `.env` 配置
- 执行步骤
- 成功判断
- 失败处理
- 回滚步骤

## 当前停在哪里

v0.3 当前明确停在：

- 真实 Image2 调用前准备阶段

这意味着：

- 还没有发送真实 HTTP 请求
- 还没有真实 `job_id / usage / latency / error_body`
- 还没有产生任何真实费用
- 还没有进入 v0.3-E 的第一次真实单 task 调用

## 为什么现在还不能进入 v0.3-E

在进入 v0.3-E 之前，至少需要先满足：

- OpenAI API key 已创建
- billing / credits 已确认
- 本地 `.env` 已安全配置
- `.env` 没有被 Git 追踪
- 已选定单个允许真实调用的 `asset_task_id`

如果这些条件没准备好，就不应该放开第一次真实调用。

## 进入 v0.3-E 前的建议流程

建议严格按这条顺序推进：

1. `POST /coze/project/validate-payload`
2. `POST /coze/project/full-demo-flow`
3. `GET /projects/{project_id}/provider-debug-summary`
4. `GET /projects/{project_id}/provider-readiness`
5. 阅读并执行 [IMAGE2_API_KEY_SETUP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_API_KEY_SETUP.md)
6. 阅读并预演 [IMAGE2_FIRST_REAL_CALL_RUNBOOK.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_FIRST_REAL_CALL_RUNBOOK.md)

## v0.4 以后再做什么

### v0.3-E

等 API key 和 billing 准备好后，才进入：

- 第一次真实 `Image2Provider` 单 task 调用

### v0.4

等 image 路径稳定后，再考虑：

- 真实 `SeedanceVideoProvider` 接入

## 当前明确不做的内容

当前阶段仍然不做：

- 真实 Seedance 接入
- n8n
- Retrospective
- 前端
- 多租户 / SaaS 权限系统
