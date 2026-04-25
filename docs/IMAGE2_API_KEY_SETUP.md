# IMAGE2_API_KEY_SETUP

## 这份文档的用途

这份 SOP 用来说明，未来如果要从当前的 mock / dry-run 阶段切到真实 `Image2Provider`，应该如何在本地安全准备 API Key、billing 和运行配置。

当前结论先放前面：

- 现在默认仍然不会调用真实 Image2
- 现在默认不会产生任何费用
- 在真正准备好前，不要修改默认安全配置

## OpenAI API Key 是什么

OpenAI API Key 是给程序调用 OpenAI Platform API 用的密钥。

它和你在 ChatGPT 网页或 App 里使用的账号登录不是一回事，也不能直接互换。

这个项目未来接真实 `Image2Provider` 时，需要的是：

- OpenAI Platform API Key

而不是单纯的 ChatGPT 登录状态。

## ChatGPT Plus 不等于 API 免费额度

需要特别注意：

- ChatGPT Plus 是 ChatGPT 产品订阅
- OpenAI API 是单独计费体系

也就是说：

- 你开了 ChatGPT Plus
- 不代表 API 一定免费
- 不代表 API 一定已经有可用 credits

所以在准备真实 provider 前，一定要先确认：

- OpenAI Platform 账号可正常使用
- API billing / credits 已准备好

## 如何创建 OpenAI API Key

标准流程：

1. 打开 OpenAI Platform 控制台
2. 进入 API Keys 页面
3. 创建一个新的 secret key
4. 只在创建当下复制并保存
5. 不要把 key 发到聊天、文档、截图、代码、README、examples 或 GitHub

建议：

- 为本项目单独创建一把 key
- 不要复用其它生产系统的 key

## 如何确认 billing / credits

在第一次准备真实调用前，建议确认：

1. billing 是否已启用
2. 当前账号是否还有 credits 或可计费额度
3. 是否设置了合理的 usage limit

建议先把额度限制设得很低，避免第一次联调时产生意外费用。

## 如何写入本地 .env

复制一份本地配置：

```powershell
Copy-Item .env.example .env
```

然后只在本地 `.env` 中填写：

```env
IMAGE_PROVIDER_MODE=image2_real
IMAGE2_API_KEY=你的真实key
IMAGE2_BASE_URL=你的真实provider地址
IMAGE2_MODEL=image2
ENABLE_REAL_IMAGE_PROVIDER=true
IMAGE2_MAX_REAL_CALLS_PER_RUN=1
IMAGE2_ALLOW_TASK_IDS=123
IMAGE2_DRY_RUN=false
```

注意：

- 这里只能写到本地 `.env`
- 不要把真实 key 写入 `.env.example`
- 不要把真实 key 写入代码
- 不要把真实 key 写入 README
- 不要把真实 key 写入 docs
- 不要把真实 key 写入 examples

## .env 不允许提交到 GitHub

本项目要求：

- `.env` 必须继续被 `.gitignore` 忽略
- 真实 API key 不允许进入 Git 历史

在提交前建议手动检查：

```powershell
git status
```

确认没有把 `.env`、包含 key 的临时文件、截图或日志一起提交。

## 当前安全默认配置

当前默认安全配置应该保持为：

```env
IMAGE_PROVIDER_MODE=mock
ENABLE_REAL_IMAGE_PROVIDER=false
IMAGE2_DRY_RUN=true
```

这代表：

- 默认走 mock
- 默认关闭真实 provider
- 默认即使走 image2_real 路径也只 dry-run

## 只有准备真实调用前才改成下面这样

只有当你已经准备好 API key、billing、额度和单任务 allow list 时，才考虑临时改成：

```env
IMAGE_PROVIDER_MODE=image2_real
ENABLE_REAL_IMAGE_PROVIDER=true
IMAGE2_DRY_RUN=false
IMAGE2_ALLOW_TASK_IDS=某个单独 task id
IMAGE2_MAX_REAL_CALLS_PER_RUN=1
```

建议始终坚持：

- 一次只放开一个 task id
- 一次只允许 1 次真实调用

## 如何先用 provider-debug 检查 request_payload

在切真实 provider 之前，先用：

- `GET /asset-tasks/{asset_task_id}/provider-debug`

重点检查：

- `input_payload`
- `enhanced_prompt`
- `storyboard_context`
- `provider_audit`
- `blocked_reason`
- `preflight_checks`

确认最终送入 provider 的输入结构已经正确，再考虑关闭 dry run。

## 如何用 provider-readiness 检查项目是否可切真实 provider

在项目级别，先用：

- `GET /projects/{project_id}/provider-debug-summary`
- `GET /projects/{project_id}/provider-readiness`

重点检查：

- image task 是否都有 `enhanced_prompt`
- video task 是否已有 `image_url` 和 `duration`
- 是否还有 `failed`
- 是否还有 `needs_human_revision`
- provider summary 里是否还有明显阻断项

推荐流程：

1. `POST /coze/project/validate-payload`
2. `POST /coze/project/full-demo-flow`
3. `GET /projects/{project_id}/provider-debug-summary`
4. `GET /projects/{project_id}/provider-readiness`
5. 只有确认没问题后，再考虑真实调用

## 如果 API key 泄露怎么办

如果你怀疑 key 已泄露，立即做这几步：

1. 立刻在 OpenAI Platform 删除旧 key
2. 创建新的 key
3. 替换本地 `.env`
4. 检查最近是否把 key 写进：
   - 代码
   - 文档
   - examples
   - README
   - 截图
   - shell 历史
5. 如果已经提交到 Git 历史，必须进一步处理 Git 历史和仓库凭据风险

## 最后强调

不要把真实 API key 写入以下任何位置：

- README
- docs
- examples
- 代码
- `.env.example`
- 测试文件

真实 key 只能保留在本地安全环境中。
