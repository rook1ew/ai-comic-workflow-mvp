# Coze-first AI Comic Workflow MVP

这是一个面向 AI 漫剧生产流程验证的 Coze-first 后端 MVP。

当前目标不是完整 SaaS，而是先把内部生产链路跑通，并为后续真实图片 / 视频 provider 接入准备一个可追踪、可调试、可收口的底座。

当前最小闭环已经覆盖：

`立项 -> 角色设定 -> 剧本卡 -> 分镜 / 镜头 -> 素材任务 -> mock provider / 人工素材回填 -> 发布记录 -> Coze summary`

## 当前阶段

### v0.1

- Coze 固定 demo payload
- `POST /coze/project/full-demo-flow`
- mock provider 执行闭环
- publish record

### v0.2 Provider Readiness

v0.2 的重点是为未来真实 provider 接入做输入和调试准备：

- 校验 Coze payload 是否合格
- image task 生成 `enhanced_prompt`
- 透传 `storyboard_context`
- video task 补齐 `image_url` 和 `duration`
- 提供 task 级和 project 级 provider debug
- 提供 provider readiness 检查

当前仍然：

- 不接真实 Image2 API
- 不接真实 Seedance API
- 不读取真实计费接口
- 不会产生真实生成费用

### v0.3 当前状态

v0.3 当前已经分成两条路线：

1. 真实 Image2Provider 接入前准备
2. 无 billing 的人工图 / 视频生产闭环

#### A. Image2 real provider preparation

已完成：

- 配置和安全开关
- `Image2Provider` 适配骨架
- preflight / dry-run 保护
- `provider_audit` 审计结构
- API key 本地安全配置文档
- 第一次真实单 task 调用 runbook

当前仍然：

- 没有开启真实 Image2 调用
- 没有真实 billing / credits 前不要进入真实调用
- 默认配置下不会发出真实请求

#### B. Manual Production Workflow

当前已经支持一条完全不依赖 OpenAI API billing 的人工生产链路：

- 程序导出可复制提示词
- 人工用 ChatGPT / 图片工具生成图片
- 手动回填图片 Asset
- 检查图片进度
- 检查视频就绪情况
- 人工用 Seedance 网页端或其他工具生成视频
- 手动回填视频 Asset
- 检查项目整体视频进度
- 检查生产总览、发布前就绪和最终交付清单

这条链路当前明确：

- 不需要 OpenAI API billing
- 不调用真实 Image2 API
- 不调用真实 Seedance API
- 不读取真实 API key
- 不产生真实 API 费用

适合当前阶段：

- 程序出提示词
- 人工生图 / 生视频
- 再把素材 URL 或本地路径回填到系统

## 本地启动

```powershell
cd C:\Users\29964\Documents\GitHub\ai-comic-workflow-mvp-git
Copy-Item .env.example .env
C:\Users\29964\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip install -r requirements.txt
C:\Users\29964\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m alembic upgrade head
C:\Users\29964\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m uvicorn app.main:app --reload
```

启动后访问：

- OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 当前可用接口

### 基础 REST API

- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/summary`
- `GET /projects/{project_id}/provider-readiness`
- `GET /projects/{project_id}/image-prompts`
- `GET /projects/{project_id}/manual-image-progress`
- `GET /projects/{project_id}/video-readiness`
- `GET /projects/{project_id}/manual-video-progress`
- `GET /projects/{project_id}/manual-production-summary`
- `GET /projects/{project_id}/publish-readiness`
- `GET /projects/{project_id}/manual-final-checklist`
- `POST /characters`
- `POST /characters/{character_id}/confirm-reference`
- `POST /episodes`
- `POST /scenes`
- `POST /shots`
- `POST /asset-tasks`
- `GET /asset-tasks/{asset_task_id}`
- `POST /asset-tasks/{asset_task_id}/run`
- `GET /asset-tasks/{asset_task_id}/provider-debug`
- `POST /asset-tasks/{asset_task_id}/manual-asset`
- `POST /asset-tasks/{asset_task_id}/manual-video-asset`
- `GET /projects/{project_id}/asset-tasks`
- `GET /projects/{project_id}/assets`
- `GET /projects/{project_id}/provider-debug-summary`
- `POST /projects/{project_id}/asset-tasks/bulk`
- `POST /projects/{project_id}/asset-tasks/run-bulk`
- `POST /reviews`
- `POST /publish-records`
- `GET /dashboard/summary`

### Coze 编排接口

- `POST /coze/project/init`
- `POST /coze/project/validate-payload`
- `POST /coze/project/{project_id}/generate-script`
- `POST /coze/project/{project_id}/storyboard`
- `POST /coze/project/{project_id}/create-asset-tasks`
- `POST /coze/project/{project_id}/run-asset-tasks`
- `POST /coze/project/{project_id}/publish-record`
- `GET /coze/project/{project_id}/summary`
- `POST /coze/project/full-demo-flow`

## 推荐演示路径

### 路线 A：Coze / mock 演示

1. `POST /coze/project/validate-payload`
2. `POST /coze/project/full-demo-flow`
3. `GET /projects/{project_id}/provider-debug-summary`
4. `GET /projects/{project_id}/provider-readiness`

### 路线 B：人工图视频生产演示

1. `POST /coze/project/full-demo-flow` 或分步生成 project / shots / tasks
2. `GET /projects/{project_id}/image-prompts`
3. 手动生图
4. `POST /asset-tasks/{asset_task_id}/manual-asset`
5. `GET /projects/{project_id}/manual-image-progress`
6. `GET /projects/{project_id}/video-readiness`
7. 手动生成视频
8. `POST /asset-tasks/{asset_task_id}/manual-video-asset`
9. `GET /projects/{project_id}/manual-video-progress`
10. `GET /projects/{project_id}/manual-production-summary`
11. `GET /projects/{project_id}/publish-readiness`
12. `GET /projects/{project_id}/manual-final-checklist`

## 示例 payload

示例文件位于 [examples](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples)：

- [coze_project_init_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_project_init_payload.json)
- [coze_script_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_script_payload.json)
- [coze_storyboard_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_storyboard_payload.json)
- [coze_create_asset_tasks_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_create_asset_tasks_payload.json)
- [coze_publish_record_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_publish_record_payload.json)
- [coze_full_demo_flow_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_full_demo_flow_payload.json)

## 关键文档

### 真实 provider 准备

- [docs/REAL_PROVIDER_PLAN.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/REAL_PROVIDER_PLAN.md)
- [docs/V0_2_SUMMARY.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/V0_2_SUMMARY.md)
- [docs/V0_3_SUMMARY.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/V0_3_SUMMARY.md)
- [docs/IMAGE2_API_KEY_SETUP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_API_KEY_SETUP.md)
- [docs/IMAGE2_FIRST_REAL_CALL_RUNBOOK.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_FIRST_REAL_CALL_RUNBOOK.md)

### 人工生产闭环

- [docs/MANUAL_IMAGE_GENERATION_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/MANUAL_IMAGE_GENERATION_SOP.md)
- [docs/MANUAL_VIDEO_GENERATION_SOP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/MANUAL_VIDEO_GENERATION_SOP.md)
- [docs/MANUAL_PRODUCTION_WORKFLOW.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/MANUAL_PRODUCTION_WORKFLOW.md)

## 当前默认安全配置

在没有真实 billing / credits 前，建议保持：

- `IMAGE_PROVIDER_MODE=mock`
- `ENABLE_REAL_IMAGE_PROVIDER=false`
- `IMAGE2_DRY_RUN=true`

## 当前还没有实现的内容

- 真实 Image2 HTTP 调用
- 真实 SeedanceVideoProvider 调用
- 真实 usage / cost 落库
- 真实 billing 验证链路
- n8n
- Retrospective
- 前端
- 多租户 / SaaS 权限系统

## 测试

```powershell
cd C:\Users\29964\Documents\GitHub\ai-comic-workflow-mvp-git
C:\Users\29964\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest
```
