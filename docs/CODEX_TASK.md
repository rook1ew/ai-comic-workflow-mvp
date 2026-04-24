# Codex Task: Build Coze-first AI Comic MVP

你是我的技术合伙人和自动化工程师。请从 0 开始为一个“AI漫剧自动化生产线”创建第一阶段 MVP 仓库代码。

## 项目方向
这是一个 Coze-first 的 AI 漫剧生产流程系统，用于先跑通早期流程。
目标不是完整 SaaS，而是内部生产线底座。

## 当前要求
请基于当前空仓库，从零搭建一个可运行的 FastAPI 项目。

## 第一阶段范围
仅实现：
- Project
- Episode
- Character
- Scene
- Shot
- AssetTask
- Asset
- Review
- PublishRecord

不实现：
- Retrospective
- n8n 相关功能
- 前端
- 多租户
- 真实付费 provider 接入

## 技术栈
- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Alembic
- pytest

## 必须完成的能力
1. 项目管理
2. 角色管理
3. 分镜/镜头管理
4. 素材任务管理
5. 审核记录
6. 发布记录
7. Coze 集成接口
8. Mock provider

## 新增 Coze 高层 API
请实现：
- POST /coze/project/init
- POST /coze/project/{project_id}/generate-script
- POST /coze/project/{project_id}/generate-storyboard
- POST /coze/project/{project_id}/create-asset-tasks
- POST /coze/project/{project_id}/publish-record
- GET /coze/project/{project_id}/summary

## 统一返回格式
所有 Coze 接口统一返回：

```json
{
  "success": true,
  "code": "OK",
  "message": "...",
  "data": {},
  "next_action": "..."
}
```

## 状态要求
Project:
- draft
- approved
- scripting
- storyboard
- producing
- reviewing
- ready_to_publish
- published
- archived

Shot:
- pending
- prompt_ready
- generating
- generated
- review_failed
- approved
- locked

AssetTask:
- queued
- running
- succeeded
- failed
- needs_retry
- cancelled
- needs_human_revision

## 业务规则
1. 一个镜头只允许一个核心动作描述。
2. 同一镜头默认最多重试 3 次。
3. 超过最大重试次数后状态变为 needs_human_revision。
4. 未确认角色主参考前，不允许批量生成镜头素材。
5. 每个镜头都必须包含：
   - image_prompt
   - video_prompt
   - voice_prompt
   - bgm_prompt

## 文档要求
请生成并维护：
- README.md
- docs/API.md
- docs/DATA_MODEL.md
- docs/STATUS_MACHINE.md
- docs/PROMPT_TEMPLATES.md
- docs/COZE_INTEGRATION.md
- docs/DEPLOYMENT.md
- docs/SOP.md

## 测试要求
至少覆盖：
- project creation
- shot creation
- asset task creation
- Coze init endpoint
- Coze storyboard endpoint
- retry limit behavior
- dashboard summary

## 交付顺序
Phase 1:
- 先输出实施计划
- 输出目录结构
- 输出数据模型草案

Phase 2:
- 再开始编码基础项目骨架

Phase 3:
- 完成 API、状态机、mock provider、测试

Phase 4:
- 完成文档与示例

请不要一次性大改。先输出计划和数据模型草案，等我确认后再开始第一阶段实现。
