# V0.2 升级计划

## 目标

v0.1 的 `full-demo-flow` 已经证明整条 Coze-first MVP 链路可跑通，但当前 payload 更偏固定演示数据。  
v0.2 的目标不是接真实图片或视频服务，而是先把这条链路升级成“可以稳定承接 Coze 真实生成内容”的形态。

## 从固定 demo payload 到真实 Coze payload 的路线

### Phase A：保持接口不变，放宽内容来源

- 保留 `POST /coze/project/full-demo-flow`
- 不要求 Coze 一定传固定示例文本
- 允许 Coze 将真实生成的：
  - `project_card_json`
  - `characters_json`
  - `script_card_json`
  - `storyboard_json`
  直接传给后端
- 后端继续只负责落库、任务编排、summary 返回

这一步的核心不是“生成”，而是“接受真实生成结果”。

### Phase B：标准化字段约束

真实 Coze payload 通常会逐渐变复杂，所以需要先统一字段语义：

- `project_card_json`
  - 保持项目元信息
- `characters_json`
  - 保持角色设定、口癖、视觉约束
- `script_card_json`
  - 保持剧情结构，不要求完整自然语言长文
- `storyboard_json`
  - 强制每个 shot 都带四类 prompt
  - `shot_id` 作为 Coze 侧稳定引用键

目标是让 Coze 生成结果“结构化优先”，而不是“自由文本优先”。

### Phase C：预留真实 provider 输入输出

在 v0.2 中先只定义接口契约：

- image provider 输入：
  - `prompt`
  - `character_reference_url`
  - `shot_id`
  - `style`
- video provider 输入：
  - `image_url`
  - `prompt`
  - `duration`
  - `aspect_ratio`
  - `resolution`
- 输出统一：
  - `ProviderResult(url, metadata)`

这样后续接真实模型时，不需要推翻现有 `asset_task_service`。

## v0.2 交付边界

本阶段只做这些：

- 补文档
- 更新 full demo payload 示例
- 预留真实 provider stub
- 定义更清晰的输入输出 schema

本阶段不做这些：

- 不接真实 API key
- 不产生真实费用
- 不调用真实图片或视频生成服务
- 不新增 n8n
- 不新增 Retrospective
- 不做前端
- 不做多租户 SaaS
