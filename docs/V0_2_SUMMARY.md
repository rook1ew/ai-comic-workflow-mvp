# V0_2_SUMMARY

## v0.2 目标

v0.2 的核心目标是把 v0.1 的固定 demo 演示链路，升级为“可承接 Coze 真实结构化内容、并为真实 provider 接入做准备”的阶段。

这一阶段仍然不接真实图片/视频 provider，不产生真实调用和费用。

## v0.2-A 到 v0.2-H 已完成内容

### v0.2-A

- 增加真实 provider 接口设计文档
- 预留 `Image2ProviderStub`
- 预留 `SeedanceVideoProviderStub`
- 统一 provider 输入输出 schema

### v0.2-B

- image task 执行时按统一 schema 组装 `ImageProviderInput`
- video task 执行时按统一 schema 组装 `VideoProviderInput`
- metadata 中记录：
  - `provider_name`
  - `modality`
  - `input_payload`
  - `mock = true`

### v0.2-C

- storyboard 导入时保存 `duration_sec`
- `full-demo-flow` 也会落库 `duration_sec`
- video task 优先从 `Shot.metadata_json` 读取 `duration_sec`

### v0.2-D

- image task 开始透传 `storyboard_context`
- 包含：
  - `source_shot_id`
  - `duration_sec`
  - `character`
  - `location`
  - `emotion`
  - `camera`
  - `dialogue`

### v0.2-E

- 新增 `build_image_enhanced_prompt`
- 组合：
  - `image_prompt`
  - `visual_style`
  - `character_reference_url`
  - `storyboard_context`
- image asset metadata 中已可查看 `enhanced_prompt`

### v0.2-F

- 新增 `GET /asset-tasks/{asset_task_id}/provider-debug`
- 支持查看：
  - `input_payload`
  - `enhanced_prompt`
  - `storyboard_context`
  - `asset_url`
  - `error_message`

### v0.2-G

- 新增 `GET /projects/{project_id}/provider-debug-summary`
- 支持项目级查看所有 asset tasks 的 provider 输入快照摘要
- 支持聚合统计：
  - `image_tasks_count`
  - `video_tasks_count`
  - `succeeded_count`
  - `failed_count`
  - `needs_human_revision_count`
  - `missing_enhanced_prompt_count`
  - `missing_image_url_for_video_count`

### v0.2-H

- 新增 `POST /coze/project/validate-payload`
- 新增 `GET /projects/{project_id}/provider-readiness`
- 在接真实 provider 前，先完成：
  - payload 结构校验
  - 项目级 readiness 检查

## 当前不会做什么

当前阶段仍然不会做：

- 真实 Image2 API 调用
- 真实 Seedance API 调用
- 真实 API key 读取
- 真实费用产生
- n8n
- Retrospective
- 前端
- 多租户 SaaS

## 进入 v0.3 前的建议检查流程

推荐严格按这条顺序走：

1. `POST /coze/project/validate-payload`
   - 检查 Coze 真实 payload 是否完整
2. `POST /coze/project/full-demo-flow`
   - 跑通整条 mock 演示链路
3. `GET /projects/{project_id}/provider-debug-summary`
   - 检查项目级 provider 输入摘要
4. `GET /projects/{project_id}/provider-readiness`
   - 判断是否满足切真实 provider 的最低条件

## 当前阶段结论

v0.2 已经把“真实 provider 接入前最容易踩坑的输入问题”尽量前置成了可读、可测、可调试的接口能力。

这意味着进入 v0.3 时，可以优先专注于：

- 真实 `Image2Provider` 的请求适配
- 真实错误处理
- 成本与耗时记录

而不用再回头重做 Coze payload 校验、shot 元信息透传、prompt 增强和项目级调试能力。
