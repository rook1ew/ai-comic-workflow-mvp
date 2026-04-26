# Coze-first AI Comic Workflow MVP

这是一个面向 AI 漫剧生产流程验证的 Coze-first 后端 MVP。

当前目标不是完整 SaaS，而是先把内部生产链路跑通，并为后续真实图片 / 视频 provider 接入准备可调试、可校验、可收敛的底座。

当前最小链路已经覆盖：

`立项 -> 角色设定 -> 剧本卡 -> 分镜 / 镜头 -> 素材任务 -> mock provider -> 发布记录 -> Coze summary`

## 当前阶段

### v0.1 已完成

- Coze 固定 demo payload
- `POST /coze/project/full-demo-flow`
- mock provider 执行闭环
- publish record

### v0.2 已完成

v0.2 的重点是 Provider Readiness：

- 校验 Coze 真实 payload 是否合格
- 为 image task 生成 `enhanced_prompt`
- 透传 `storyboard_context`
- 为 video task 补齐 `image_url` 和 `duration`
- 提供 task 级和 project 级 provider debug 接口
- 提供 project 级 provider readiness 检查

当前仍然只使用 mock / stub 能力：

- 不接真实 Image2 API
- 不接真实 Seedance API
- 不读取真实计费接口
- 不会产生真实生成费用

### v0.3 当前状态

v0.3 的重点是为真实 `Image2Provider` 接入做准备，但当前仍然停在真实调用前的准备阶段。

已完成内容包括：

- v0.3-A：配置项和安全开关
- v0.3-B：`Image2Provider` 适配骨架
- v0.3-C：preflight / dry-run 保护层
- v0.3-D：`provider_audit` 审计结构
- v0.3-D.5：本地 API key 安全配置 SOP
- v0.3-E-Plan：第一次真实单 task 调用 runbook

当前明确结论：

- 真实 Image2 调用尚未开启
- 没有 billing / credits 前，不要进入真实调用
- 默认配置下不会发出真实请求
- `.env` 必须保留在本地，不能提交到 GitHub

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
- `POST /characters`
- `POST /characters/{character_id}/confirm-reference`
- `POST /episodes`
- `POST /scenes`
- `POST /shots`
- `POST /asset-tasks`
- `GET /asset-tasks/{asset_task_id}`
- `POST /asset-tasks/{asset_task_id}/run`
- `GET /asset-tasks/{asset_task_id}/provider-debug`
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

## 推荐演示流程

推荐按这条顺序演示：

1. `POST /coze/project/validate-payload`
2. `POST /coze/project/full-demo-flow`
3. `GET /projects/{project_id}/provider-debug-summary`
4. `GET /projects/{project_id}/provider-readiness`

如果你想分步演示，也可以按这条链路：

1. `POST /coze/project/init`
2. `POST /characters/{character_id}/confirm-reference`
3. `POST /coze/project/{project_id}/generate-script`
4. `POST /coze/project/{project_id}/storyboard`
5. `POST /coze/project/{project_id}/create-asset-tasks`
6. `POST /coze/project/{project_id}/run-asset-tasks`
7. `GET /coze/project/{project_id}/summary`
8. `POST /coze/project/{project_id}/publish-record`

## 示例 payload

示例文件位于 [examples](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples)：

- [coze_project_init_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_project_init_payload.json)
- [coze_script_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_script_payload.json)
- [coze_storyboard_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_storyboard_payload.json)
- [coze_create_asset_tasks_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_create_asset_tasks_payload.json)
- [coze_publish_record_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_publish_record_payload.json)
- [coze_full_demo_flow_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_full_demo_flow_payload.json)

## Image2 安全准备文档

在真实 provider 真正接入前，先看这些文档：

- [docs/REAL_PROVIDER_PLAN.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/REAL_PROVIDER_PLAN.md)
- [docs/V0_2_SUMMARY.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/V0_2_SUMMARY.md)
- [docs/V0_3_SUMMARY.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/V0_3_SUMMARY.md)
- [docs/IMAGE2_API_KEY_SETUP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_API_KEY_SETUP.md)
- [docs/IMAGE2_FIRST_REAL_CALL_RUNBOOK.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_FIRST_REAL_CALL_RUNBOOK.md)

当前默认安全配置应保持为：

- `IMAGE_PROVIDER_MODE=mock`
- `ENABLE_REAL_IMAGE_PROVIDER=false`
- `IMAGE2_DRY_RUN=true`

## 当前还没有实现的内容

- 真实 Image2 HTTP 调用
- 真实 SeedanceVideoProvider 调用
- 真实 usage / cost 落库
- 真实计费验证链路
- n8n
- Retrospective
- 前端
- 多租户 / SaaS 权限系统

## 测试

```powershell
cd C:\Users\29964\Documents\GitHub\ai-comic-workflow-mvp-git
C:\Users\29964\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest
```
