# REAL_PROVIDER_PLAN

## 目标

当前系统已经具备完整的 mock provider 演示链路，可以用于 Coze-first MVP 验证。

本阶段的目标不是直接接真实 provider，而是先把真实 provider 接入前的输入、调试、校验和 readiness 检查准备好。

当前规划：

- v0.2：完成 Provider Readiness 底座
- v0.3：开始接真实 `Image2Provider`
- v0.4：开始接真实 `SeedanceVideoProvider`

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

`storyboard_json` 导入后，当前会把以下信息保存到 `Shot.metadata_json`：

- `source_shot_id`
- `duration_sec`
- `character`
- `location`
- `emotion`
- `camera`
- `dialogue`

这些信息会继续透传到：

- image provider input
- image asset metadata
- video duration 组装逻辑

### 3. enhanced_prompt

当前 image task 已支持生成 `enhanced_prompt`。

增强策略包括：

- 保留原始 `image_prompt`
- 追加 `visual_style`
- 如果存在 `character_reference_url`，增加角色一致性提示
- 追加 storyboard 上下文：
  - `source_shot_id`
  - `character`
  - `location`
  - `emotion`
  - `camera`
  - `dialogue`

同时明确约束：

- 不直接模仿具体 IP
- 不直接模仿明星
- 不直接模仿影视角色
- 不直接模仿已知动漫角色

### 4. provider debug 能力

当前已经提供两层只读调试接口：

- `GET /asset-tasks/{asset_task_id}/provider-debug`
- `GET /projects/{project_id}/provider-debug-summary`

用途：

- 检查最终送给 provider 的 `input_payload`
- 检查 image task 是否已有 `enhanced_prompt`
- 检查 storyboard context 是否正确透传
- 检查 video task 是否已有 `image_url` 和 `duration`
- 在接真实 provider 前先做项目级调试

### 5. provider readiness 检查

当前已经提供：

- `POST /coze/project/validate-payload`
- `GET /projects/{project_id}/provider-readiness`

用途：

- 在 full-demo-flow 前检查 Coze payload 是否完整
- 在 mock 工作流跑完后检查项目是否已经满足切真实 provider 的最低条件

当前 readiness 重点检查：

- 至少存在 image task
- image task 应有 `enhanced_prompt`
- 如果存在 video task：
  - 应有 `image_url`
  - 应有 `duration`
- 不应存在 `failed`
- 不应存在 `needs_human_revision`

## v0.3 计划：接真实 Image2Provider

v0.3 才开始接真实 `Image2Provider`。

推荐接入顺序：

1. 保持现有 `asset_task_service` 编排不变
2. 让 image task 在 provider factory 中支持切换到真实 `Image2Provider`
3. 优先使用 `enhanced_prompt`
4. 保留 provider-debug 接口用于排查真实输入
5. 增加真实 provider 的错误处理、请求 ID、耗时和成本记录

v0.3 的目标不是一次做完全部多模态，而是先把 image 路径打通。

## v0.4 计划：接真实 SeedanceVideoProvider

v0.4 才开始接真实 `SeedanceVideoProvider`。

前置条件：

- image 路径已经稳定
- video task 已可靠拿到 `image_url`
- `duration`、`aspect_ratio`、`resolution` 已经稳定

推荐接入顺序：

1. 复用当前 video input 组装逻辑
2. 将 provider factory 中的 video provider 从 mock 切到真实 provider
3. 记录真实 provider task id、轮询状态、失败原文
4. 继续复用 project 级 provider-readiness 做联调前检查

## 当前明确不做的事

当前阶段仍然不做：

- 真实 API key 读取
- 真实费用调用
- n8n
- Retrospective
- 前端
- 多租户 SaaS

## v0.3-A 当前范围

v0.3-A 只完成真实 `Image2Provider` 接入前的配置和安全开关准备：

- 增加 `IMAGE_PROVIDER_MODE`
- 增加 `IMAGE2_API_KEY`
- 增加 `IMAGE2_BASE_URL`
- 增加 `IMAGE2_MODEL`
- 增加 `ENABLE_REAL_IMAGE_PROVIDER`
- 支持 `image2_stub`
- 对 `image2_real` 做明确阻断

默认行为仍然是：

- 使用 `mock`
- 不发真实请求
- 不读取真实费用接口
- 不产生真实生成费用

真实 image provider 在未来只有同时满足以下条件时才允许启用：

- `IMAGE_PROVIDER_MODE=image2_real`
- `ENABLE_REAL_IMAGE_PROVIDER=true`
- `IMAGE2_API_KEY` 存在

并且 `.env` 必须继续留在本地，不允许提交到 GitHub。

## v0.3-B 当前范围

v0.3-B 只实现真实 `Image2Provider` 的适配结构，不启用真实 HTTP 调用。

本轮已补齐：

- `Image2Provider` 类骨架
- `build_request_payload(...)`
- `parse_response(...)`
- `map_error(...)`
- factory 对 `image2_real` 的识别

当前仍然不会做：

- 发送真实 HTTP 请求
- 调用真实 Image2 API
- 读取真实费用接口
- 产生真实生成费用

进入 v0.3-C 之前，`image2_real` 仍应被视为“结构已就绪、调用未放开”的状态。

## v0.3-C 当前范围

v0.3-C 继续不做真实 Image2 HTTP 调用。

这一轮新增的是“第一次受控真实图片调用”前的保护层：

- preflight 检查
- dry-run 阻断
- allow-task-id 白名单
- 单次运行最大真实调用次数限制

当前新增的关键配置：

- `IMAGE2_MAX_REAL_CALLS_PER_RUN`
- `IMAGE2_ALLOW_TASK_IDS`
- `IMAGE2_DRY_RUN`

必须同时满足以下条件，未来才允许进入真实调用路径：

- `provider_name = image2_real`
- `IMAGE_PROVIDER_MODE = image2_real`
- `ENABLE_REAL_IMAGE_PROVIDER = true`
- `IMAGE2_API_KEY` 存在
- `IMAGE2_BASE_URL` 存在
- `IMAGE2_DRY_RUN = false`
- 当前 `asset_task_id` 在 `IMAGE2_ALLOW_TASK_IDS` 中
- 本次运行真实调用次数不超过 `IMAGE2_MAX_REAL_CALLS_PER_RUN`
- `task.modality = image`
- 当前 task 已有 `enhanced_prompt`

即便以上都满足，v0.3-C 仍然不会真正发请求，只会：

- 构造 `request_payload`
- 记录 preflight 结果
- 写入 `blocked_reason`
- 返回受控失败

这样可以在真正放开第一次真实调用前，先把所有执行保护链路验证完整。

## v0.3-D 当前范围

v0.3-D 新增的是“真实 provider 调用审计记录层”。

当前会在 image2_real 的 dry-run / blocked 场景下统一写入：

- `provider_audit`

其目标是为未来第一次真实 Image2 调用提前准备统一审计结构，包括：

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

当前 v0.3-D 仍然不会发送真实请求，这个审计结构只是先把未来真实调用需要落库和排查的字段标准化。

## v0.3 前建议流程

在切真实 provider 前，建议始终按这条顺序检查：

1. `POST /coze/project/validate-payload`
2. `POST /coze/project/full-demo-flow`
3. `GET /projects/{project_id}/provider-debug-summary`
4. `GET /projects/{project_id}/provider-readiness`

只有当 payload 合格、mock 流程跑通、provider debug 正常、provider readiness 通过后，再进入真实 provider 接入。
