# V0_3_SUMMARY

## v0.3 目标

v0.3 的目标不是直接放开真实图片生成，而是把真实 `Image2Provider` 接入前的配置、安全、调试、审计和执行清单全部准备好。

这意味着在 v0.3 结束时，系统应该已经具备：

- 可切换的 provider 配置结构
- 严格的真实调用安全开关
- dry-run 与 preflight 检查
- provider 级调试与审计记录
- API key 配置 SOP
- 第一次真实单 task 调用的执行 / 回滚 runbook

但当前仍然：

- 没有真实 API 调用
- 没有真实费用产生
- 没有放开真实 Image2 单 task 生成

## v0.3-A 配置和安全开关

本阶段完成了真实 `Image2Provider` 接入前的基础配置：

- `IMAGE_PROVIDER_MODE`
- `IMAGE2_API_KEY`
- `IMAGE2_BASE_URL`
- `IMAGE2_MODEL`
- `ENABLE_REAL_IMAGE_PROVIDER`

同时保留默认安全值：

- `IMAGE_PROVIDER_MODE=mock`
- `ENABLE_REAL_IMAGE_PROVIDER=false`
- 不读取真实 key 也能正常运行测试与 mock 流程

这一阶段的重点是先把“是否允许走真实图片 provider”这件事收口到显式配置里，而不是隐式切换。

## v0.3-B Image2Provider 适配骨架

本阶段新增了真实 `Image2Provider` 的适配结构，但没有真实发请求。

已完成：

- `Image2Provider` 类骨架
- `build_request_payload(...)`
- `parse_response(...)`
- `map_error(...)`
- factory 能识别 `image2_real`

目的不是现在就调用真实 Image2，而是先把未来真实请求的：

- 输入结构
- 响应解析
- 错误映射

都标准化，避免后面在真实接入时一边连 API 一边改接口契约。

## v0.3-C preflight / dry-run

本阶段新增了真实调用前的执行保护层。

新增关键配置：

- `IMAGE2_MAX_REAL_CALLS_PER_RUN`
- `IMAGE2_ALLOW_TASK_IDS`
- `IMAGE2_DRY_RUN`

当前即使 task 使用 `image2_real`，也必须通过 preflight 检查才可能进入未来真实调用路径。检查重点包括：

- provider 是否是 `image2_real`
- mode 是否切到 `image2_real`
- 是否显式开启真实 provider
- 是否存在 API key
- 是否存在 base URL
- 是否关闭 dry run
- 当前 task 是否在 allow-list 里
- 是否在单次调用数量限制内
- modality 是否是 image
- 是否存在 `enhanced_prompt`

当前版本结论：

- 默认仍然是 dry-run
- 默认不会真实调用
- 没有 allow-list task id 不能进入未来真实调用路径

## v0.3-D provider_audit

本阶段把未来真实 provider 调用需要的审计结构标准化了。

当前 `image2_real` 在 blocked / dry-run 场景下，会统一记录：

- `provider_audit`

核心字段包括：

- `request_payload`
- `response_payload`
- `error_body`
- `job_id`
- `usage`
- `latency_ms`
- `real_call`
- `dry_run`
- `blocked_reason`
- `preflight_passed`
- `preflight_checks`

这样做的价值是：未来第一次真实调用前，task 的调试、审计、回滚字段已经提前准备好，不用等真实调用出问题后再补。

## v0.3-D.5 API key setup

本阶段没有改代码，只新增了本地安全配置 SOP：

- [IMAGE2_API_KEY_SETUP.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_API_KEY_SETUP.md)

重点说明了：

- OpenAI API key 是什么
- ChatGPT Plus 不等于 API 免费额度
- 如何确认 billing / credits
- 如何安全写入本地 `.env`
- 为什么 `.env` 不能提交 GitHub
- 泄露 key 后如何立即作废并重建

这一步的目的是避免后面一旦真的准备接真实 provider，就在最基础的密钥管理上出错。

## v0.3-E-Plan first real call runbook

本阶段仍然没有改业务逻辑，只新增了第一次真实调用前的执行清单：

- [IMAGE2_FIRST_REAL_CALL_RUNBOOK.md](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/docs/IMAGE2_FIRST_REAL_CALL_RUNBOOK.md)

它定义了：

- 前置条件
- 第一次真实调用前检查
- 临时 `.env` 配置
- 执行步骤
- 成功判断
- 失败处理
- 回滚步骤

这意味着即使未来进入 v0.3-E，也不会一上来就批量调用，而是只允许：

- 单个 task
- 明确 allow-list
- 明确 max calls
- 明确可回滚

## 当前没有做什么

截至 v0.3 当前阶段，依然没有做这些事：

- 没有真实 Image2 HTTP 调用
- 没有真实费用产生
- 没有真实 usage / billing 落库
- 没有真实 Seedance 接入
- 没有 n8n
- 没有 Retrospective
- 没有前端
- 没有多租户 / SaaS 权限系统

## 进入 v0.3-E 前的建议检查流程

在真正进入第一次真实 `Image2Provider` 单 task 调用前，建议严格按这条顺序检查：

1. `POST /coze/project/validate-payload`
2. `POST /coze/project/full-demo-flow`
3. `GET /projects/{project_id}/provider-debug-summary`
4. `GET /projects/{project_id}/provider-readiness`
5. 检查本地 API key、billing / credits、`.env`
6. 对照 `IMAGE2_FIRST_REAL_CALL_RUNBOOK.md` 做一次 dry-run 预演

## 当前阶段结论

v0.3 当前已经把“真实调用前最容易出问题的部分”基本都前置准备好了：

- 配置项
- 安全开关
- dry-run
- preflight
- provider-debug
- provider-debug-summary
- provider-readiness
- provider_audit
- API key setup
- first real call runbook

但它依然明确停在：

- 真实调用前准备阶段

只有在确认：

- API key 已准备好
- billing / credits 已确认
- 本地 `.env` 已正确配置
- allow-list task 已选定

之后，才应该进入真正的 v0.3-E 单 task 真实调用实现。
