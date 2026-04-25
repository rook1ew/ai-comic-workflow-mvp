# IMAGE2_FIRST_REAL_CALL_RUNBOOK

## 目的

这份 runbook 用来指导“第一次真实 Image2 单 task 调用”前的准备、执行、判断、失败处理和回滚。

当前强调：

- 本文档是执行清单
- 当前代码默认仍然不会真实调用
- 在真正进入 v0.3-E 前，先把这份 runbook 准备好

## 1. 前置条件

在考虑第一次真实调用前，必须先确认：

- OpenAI API key 已创建
- billing / credits 已确认可用
- 本地 `.env` 已配置 `IMAGE2_API_KEY`
- `.env` 没有被 Git 追踪
- `IMAGE2_DRY_RUN` 默认仍为 `true`

建议额外确认：

- `.env.example` 中没有真实 key
- README / docs / examples / 代码中没有真实 key

## 2. 第一次真实调用前检查

在切到真实调用前，先按这条顺序检查：

1. `POST /coze/project/validate-payload`
   - 确认 payload 结构无阻断错误
2. `POST /coze/project/full-demo-flow`
   - 先让默认 mock 路径完整跑通
3. `GET /projects/{project_id}/provider-debug-summary`
   - 确认 image task 的 `enhanced_prompt`、storyboard context 正常
4. `GET /projects/{project_id}/provider-readiness`
   - 确认项目满足切真实 provider 的最低条件
5. 找到一个明确的 image `asset_task_id`

第一轮只允许选：

- 一个 task
- 一个 image task

不要第一次就跑批量任务。

## 3. 第一次真实调用前的 .env 临时配置

只有在准备执行第一次真实调用时，才临时修改本地 `.env`：

```env
IMAGE_PROVIDER_MODE=image2_real
ENABLE_REAL_IMAGE_PROVIDER=true
IMAGE2_DRY_RUN=false
IMAGE2_ALLOW_TASK_IDS=某个单独 asset_task_id
IMAGE2_MAX_REAL_CALLS_PER_RUN=1
```

说明：

- `IMAGE2_ALLOW_TASK_IDS` 只放一个 task id
- `IMAGE2_MAX_REAL_CALLS_PER_RUN=1` 保持单次只允许一个真实调用
- 如果还没准备好，不要关闭 dry-run

## 4. 执行步骤

推荐执行顺序：

1. 修改本地 `.env`
2. 重启 FastAPI
3. 只运行指定 image task
4. 检查 `provider_audit`
5. 检查 `Asset.url`
6. 检查 `provider-debug`

建议操作方式：

- 只调用单个：
  - `POST /asset-tasks/{asset_task_id}/run`
- 不要调用：
  - bulk run
  - full-demo-flow
  - 批量任务接口

## 5. 成功判断

第一次真实调用成功时，理想上应满足：

- `task.status = succeeded`
- `Asset.url` 是真实图片 URL
- `provider_audit.real_call = true`
- `provider_audit.job_id` 有记录
- `provider_audit.usage` 有记录
- `provider_audit.latency_ms` 有记录

同时建议确认：

- `provider-debug` 中的 `request_payload` 与预期一致
- 返回结果没有落回 mock / stub URL

## 6. 失败处理

如果第一次真实调用失败：

1. 先看 `error_message`
2. 再看 `provider_audit.error_body`
3. 不要立刻重复批量运行
4. 先把配置改回 dry-run

排查重点：

- API key 是否可用
- billing / credits 是否足够
- `IMAGE2_ALLOW_TASK_IDS` 是否正确
- `IMAGE_PROVIDER_MODE` 是否正确
- `IMAGE2_BASE_URL` 是否正确
- `request_payload` 是否完整

## 7. 回滚步骤

如果第一次真实调用后需要立即回滚，修改本地 `.env`：

```env
IMAGE_PROVIDER_MODE=mock
ENABLE_REAL_IMAGE_PROVIDER=false
IMAGE2_DRY_RUN=true
IMAGE2_ALLOW_TASK_IDS=
```

然后：

1. 重启 FastAPI
2. 再次确认默认 mock 路径可用
3. 再次用 `provider-debug-summary` / `provider-readiness` 检查状态

## 8. 安全提醒

务必遵守：

- 不要提交 `.env`
- 不要截图 API key
- 不要把 key 写入 README
- 不要把 key 写入 docs
- 不要把 key 写入 examples
- 第一次只跑一个 task

如果怀疑 key 泄露：

1. 立刻删除旧 key
2. 重新创建新 key
3. 更新本地 `.env`
4. 检查是否有误提交或误传播

## 推荐配套文档

在执行前，建议同时参考：

- [IMAGE2_API_KEY_SETUP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_API_KEY_SETUP.md)
- [REAL_PROVIDER_PLAN.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/REAL_PROVIDER_PLAN.md)
