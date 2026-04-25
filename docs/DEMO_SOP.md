# DEMO_SOP

## 1. 如何启动 FastAPI

在项目根目录打开终端：

```powershell
cd C:\Users\29964\Documents\GitHub\ai-comic-workflow-mvp-git
Copy-Item .env.example .env
C:\Users\29964\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m uvicorn app.main:app --reload
```

启动成功后，默认本地地址是：

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

## 2. 如何启动 ngrok

在另一个单独终端中执行：

```powershell
ngrok http 8000
```

启动后，ngrok 会生成一个公网地址，例如：

- `https://xxxx-xx-xx-xx-xx.ngrok-free.app`

这个地址会转发到本地 FastAPI 的 `8000` 端口。

## 3. 如何确认公网 /docs 可访问

拿到 ngrok 地址后，直接在浏览器打开：

```text
https://你的-ngrok-地址/docs
```

如果页面能正常打开 FastAPI Swagger 文档，说明公网访问已经打通。

建议同时确认：

- `https://你的-ngrok-地址/docs`
- `https://你的-ngrok-地址/openapi.json`

都能正常返回。

## 4. Coze 工作流使用的接口地址

当前演示最推荐使用这个单接口：

- `POST https://你的-ngrok-地址/coze/project/full-demo-flow`

如果要分步调试，也可以使用这些接口：

- `POST https://你的-ngrok-地址/coze/project/init`
- `POST https://你的-ngrok-地址/characters/{character_id}/confirm-reference`
- `POST https://你的-ngrok-地址/coze/project/{project_id}/generate-script`
- `POST https://你的-ngrok-地址/coze/project/{project_id}/storyboard`
- `POST https://你的-ngrok-地址/coze/project/{project_id}/create-asset-tasks`
- `POST https://你的-ngrok-地址/coze/project/{project_id}/run-asset-tasks`
- `POST https://你的-ngrok-地址/coze/project/{project_id}/publish-record`
- `GET https://你的-ngrok-地址/coze/project/{project_id}/summary`

## 5. Coze 快捷指令名称

当前建议在 Coze 里使用的演示快捷指令名称：

- `/run_demo`

建议让这个指令内部直接触发：

- `POST /coze/project/full-demo-flow`

这样 Coze 只需要发一次请求，就能跑完整个 MVP 演示闭环。

## 6. 成功返回示例

接口：

- `POST /coze/project/full-demo-flow`

成功返回示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "Full demo flow completed",
  "data": {
    "project_id": 1,
    "character_ids": [1],
    "episode_id": 1,
    "shots_count": 1,
    "asset_tasks_count": 4,
    "assets_count": 4,
    "publish_record_id": 1,
    "final_summary": {
      "project_id": 1,
      "project_status": "published",
      "episodes_count": 1,
      "scenes_count": 1,
      "shots_count": 1,
      "asset_tasks_count": 4,
      "assets_count": 4,
      "succeeded_tasks_count": 4,
      "failed_tasks_count": 0,
      "needs_human_revision_count": 0,
      "publish_records_count": 1,
      "next_action": "completed"
    }
  },
  "next_action": "completed"
}
```

## 7. 常见问题

### ngrok 关闭后地址会失效

ngrok 免费地址通常不是永久固定的。  
如果关闭 ngrok 进程，再次启动后大概率会得到一个新的公网地址。

### FastAPI 窗口不能关闭

如果运行 FastAPI 的终端窗口被关闭，本地服务就会停止。  
这时即使 ngrok 还开着，公网请求也会失败。

### 如果 ngrok 地址变化，需要更新 Coze HTTP 请求 URL

Coze 工作流里的 HTTP 请求节点如果还指向旧的 ngrok 地址，会直接调用失败。  
每次 ngrok 地址变化后，都要把 Coze 里的请求 URL 更新成新的公网地址。
