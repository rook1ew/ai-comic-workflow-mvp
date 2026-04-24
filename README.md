# Coze AI Comic MVP

一个面向 AI 漫剧早期验证的 Coze-first 后端 MVP。

当前目标不是做完整 SaaS，而是把下面这条内部生产线跑通：

`立项 -> 角色设定 -> 剧本卡 -> 分镜/镜头 -> 素材任务 -> mock provider -> 审核记录 -> 发布记录 -> Coze summary`

## 当前项目状态

当前仓库已经完成这些能力：

- FastAPI + SQLAlchemy + SQLite + Alembic 基础底座
- `Project / Episode / Character / Scene / Shot / AssetTask / Asset / Review / PublishRecord` 数据模型
- 基础 REST API
- mock provider 执行闭环
- 项目级批量 asset task 创建与执行
- Coze 编排接口最小闭环
- pytest 自动化测试

当前测试状态：

- `55 passed`

## 本地启动

```powershell
cd C:\Users\29964\Documents\Codex\ai-comic-workflow-mvp-main
Copy-Item .env.example .env
C:\Users\29964\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip install -r requirements.txt
C:\Users\29964\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m alembic upgrade head
C:\Users\29964\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m uvicorn app.main:app --reload
```

启动后访问：

- OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 当前可用接口列表

### 基础 REST API

- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/summary`
- `POST /characters`
- `POST /characters/{character_id}/confirm-reference`
- `POST /episodes`
- `POST /scenes`
- `POST /shots`
- `POST /asset-tasks`
- `GET /asset-tasks/{asset_task_id}`
- `POST /asset-tasks/{asset_task_id}/run`
- `GET /projects/{project_id}/asset-tasks`
- `GET /projects/{project_id}/assets`
- `POST /projects/{project_id}/asset-tasks/bulk`
- `POST /projects/{project_id}/asset-tasks/run-bulk`
- `POST /reviews`
- `POST /publish-records`
- `GET /dashboard/summary`

### Coze 编排接口

- `POST /coze/project/init`
- `POST /coze/project/{project_id}/generate-script`
- `POST /coze/project/{project_id}/storyboard`
- `POST /coze/project/{project_id}/create-asset-tasks`
- `POST /coze/project/{project_id}/run-asset-tasks`
- `POST /coze/project/{project_id}/publish-record`
- `GET /coze/project/{project_id}/summary`

## Coze-first MVP 手动测试流程

建议按这个顺序手动演示：

1. `POST /coze/project/init`
   - 创建项目和角色
   - 返回 `project_id`、`character_ids`
   - `next_action = confirm_character_reference`

2. `POST /characters/{character_id}/confirm-reference`
   - 确认角色主参考
   - `next_action = create_storyboard`

3. `POST /coze/project/{project_id}/generate-script`
   - 写入 Coze 已生成好的剧本卡
   - 若项目下还没有 Episode，会自动创建默认 Episode
   - `next_action = create_storyboard`

4. `POST /coze/project/{project_id}/storyboard`
   - 导入 Coze 已生成好的 storyboard JSON
   - 创建 Episode / Scene / Shot
   - `next_action = create_asset_tasks`

5. `POST /coze/project/{project_id}/create-asset-tasks`
   - 创建默认 `image + voice + bgm`
   - 重点镜头可额外创建 `video`
   - `next_action = run_asset_tasks`

6. `POST /coze/project/{project_id}/run-asset-tasks`
   - 运行 mock provider
   - 写回 `Asset`
   - `next_action = check_summary`

7. `GET /coze/project/{project_id}/summary`
   - 查看项目进度、任务状态、下一步动作

8. `POST /coze/project/{project_id}/publish-record`
   - 写入发布记录
   - 项目状态更新为 `published`
   - `next_action = completed`

## 示例 payload

示例文件位于 [examples](</C:/Users/29964/Documents/Codex/ai-comic-workflow-mvp-main/examples>)：

- [coze_project_init_payload.json](</C:/Users/29964/Documents/Codex/ai-comic-workflow-mvp-main/examples/coze_project_init_payload.json>)
- [coze_script_payload.json](</C:/Users/29964/Documents/Codex/ai-comic-workflow-mvp-main/examples/coze_script_payload.json>)
- [coze_storyboard_payload.json](</C:/Users/29964/Documents/Codex/ai-comic-workflow-mvp-main/examples/coze_storyboard_payload.json>)
- [coze_create_asset_tasks_payload.json](</C:/Users/29964/Documents/Codex/ai-comic-workflow-mvp-main/examples/coze_create_asset_tasks_payload.json>)
- [coze_publish_record_payload.json](</C:/Users/29964/Documents/Codex/ai-comic-workflow-mvp-main/examples/coze_publish_record_payload.json>)

## 当前还没有实现的内容

- Retrospective
- n8n 工作流
- 前端
- 多租户 / SaaS 权限系统
- 真实 provider 接入
- 更完整的任务生命周期管理
- 更完整的项目状态自动推进

## 开发说明

当前实现强调两件事：

- Coze 编排层只做薄封装，不复制底层业务逻辑
- 本地默认可运行，不依赖真实付费模型服务
