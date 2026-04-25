# Coze-first AI Comic Workflow MVP

这是一个面向 AI 漫剧生产流程验证的 Coze-first 后端 MVP。

当前目标不是做完整 SaaS，而是先把这条内部生产链路跑通：

`立项 -> 角色设定 -> 剧本卡 -> 分镜/镜头 -> 素材任务 -> mock provider -> 发布记录 -> Coze summary`

## 当前项目状态

v0.1 已跑通：

- Coze 固定 demo payload
- `full-demo-flow`
- mock provider 执行闭环
- publish record

v0.2 当前重点是 Provider Readiness：

- 校验 Coze 真实 payload 是否合格
- 为 image task 生成 `enhanced_prompt`
- 透传 `storyboard_context`
- 为 video task 补齐 `image_url` 和 `duration`
- 提供 task 级和 project 级 provider debug 读取接口
- 提供 project 级 provider readiness 检查

当前仍然只使用 mock provider：

- 不接真实 Image2 API
- 不接真实 Seedance API
- 不读取真实 API key
- 不会产生真实费用

## v0.3-A Provider 配置开关

当前 v0.3-A 只做真实 Image2Provider 接入前的配置和安全开关准备。

新增配置项：

- `IMAGE_PROVIDER_MODE`
  - 默认 `mock`
  - 可选：`mock / image2_stub / image2_real`
- `IMAGE2_API_KEY`
  - 默认空
  - 本轮只预留，不实际调用
- `IMAGE2_BASE_URL`
  - 默认空
- `IMAGE2_MODEL`
  - 默认 `image2`
- `ENABLE_REAL_IMAGE_PROVIDER`
  - 默认 `false`

真实 image provider 在未来只有同时满足以下条件才允许调用：

- `IMAGE_PROVIDER_MODE=image2_real`
- `ENABLE_REAL_IMAGE_PROVIDER=true`
- `IMAGE2_API_KEY` 存在

当前版本即使设置为 `image2_real`，也不会发出真实请求；系统会返回清晰错误并阻止调用。

v0.3-C 新增的保护配置：

- `IMAGE2_MAX_REAL_CALLS_PER_RUN`
  - 默认 `1`
- `IMAGE2_ALLOW_TASK_IDS`
  - 默认空
  - 只有显式列出的 `asset_task_id` 才允许进入未来真实调用路径
- `IMAGE2_DRY_RUN`
  - 默认 `true`
  - 为 `true` 时只构造 request payload，不发真实请求

注意：

- `.env` 不允许提交到 GitHub
- API key 只能放本地环境变量或本地 `.env`

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

## Coze-first MVP 手动测试流程

推荐按这个顺序演示：

1. `POST /coze/project/validate-payload`
   - 先检查 Coze 真实 payload 是否合格
   - 如果有 errors，先修 payload 再继续
2. `POST /coze/project/full-demo-flow`
   - 一次性跑完整条 mock 演示闭环
3. `GET /projects/{project_id}/provider-debug-summary`
   - 查看整个项目的 provider 输入快照摘要
4. `GET /projects/{project_id}/provider-readiness`
   - 判断项目是否已经满足切换真实 provider 的最低条件

如果你想分步演示，也可以用：

1. `POST /coze/project/init`
2. `POST /characters/{character_id}/confirm-reference`
3. `POST /coze/project/{project_id}/generate-script`
4. `POST /coze/project/{project_id}/storyboard`
5. `POST /coze/project/{project_id}/create-asset-tasks`
6. `POST /coze/project/{project_id}/run-asset-tasks`
7. `GET /coze/project/{project_id}/summary`
8. `POST /coze/project/{project_id}/publish-record`

## v0.2 Provider Readiness 当前能力

当前已经具备的 provider readiness 能力：

- `POST /coze/project/validate-payload`
  - 校验 Coze full-demo-flow payload 是否完整
- `GET /asset-tasks/{asset_task_id}/provider-debug`
  - 查看单个任务最终送入 provider 的输入快照
- `GET /projects/{project_id}/provider-debug-summary`
  - 查看整个项目下所有任务的 provider 输入摘要
- `GET /projects/{project_id}/provider-readiness`
  - 判断项目是否满足切换真实 Image2 / Seedance 前的最低条件

## 示例 payload

示例文件位于 [examples](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples)：

- [coze_project_init_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_project_init_payload.json)
- [coze_script_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_script_payload.json)
- [coze_storyboard_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_storyboard_payload.json)
- [coze_create_asset_tasks_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_create_asset_tasks_payload.json)
- [coze_publish_record_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_publish_record_payload.json)
- [coze_full_demo_flow_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_full_demo_flow_payload.json)

## 当前还没有实现的内容

- 真实 Image2Provider 接入
- 真实 SeedanceVideoProvider 接入
- 真实 API key 管理
- 真实费用调用
- n8n
- Retrospective
- 前端
- 多租户 / SaaS 权限系统

## 测试

```powershell
cd C:\Users\29964\Documents\GitHub\ai-comic-workflow-mvp-git
C:\Users\29964\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest
```
