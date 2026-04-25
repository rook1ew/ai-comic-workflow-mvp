# REAL_PROVIDER_PLAN

## 目标

当前系统已经有 mock provider，可用于工作流演示。  
下一阶段要做的是在不破坏现有任务执行链路的前提下，逐步接入真实 provider。

本文件先定义两类真实 provider 的接入设计：

- `Image2Provider`
- `SeedanceVideoProvider`

当前只提供 stub，不会调用真实 API。

## 统一输出模型

真实 provider 的统一输出应为：

```python
ProviderResult(
  url="https://...",
  metadata={}
)
```

约束：

- `url`
  - 生成结果的可访问地址
  - 可以是对象存储地址、CDN 地址或中转文件地址
- `metadata`
  - provider 返回的附加信息
  - 例如耗时、尺寸、seed、provider request id、token 用量等

## Image2Provider 设计

### 输入

`ImageProviderInput`

- `prompt`
- `character_reference_url`
- `shot_id`
- `style`

### 预期职责

- 接收镜头图像 prompt
- 可选读取角色主参考图
- 输出首帧图或关键视觉图
- 为后续视频生成提供稳定图片输入

### 接入建议

后续真实接入时，建议 provider 内部负责：

1. 参数映射
2. 请求重试
3. provider 原始响应解析
4. 输出统一成 `ProviderResult`

不要把这些逻辑散落到 `asset_task_service` 中。

## SeedanceVideoProvider 设计

### 输入

`VideoProviderInput`

- `image_url`
- `prompt`
- `duration`
- `aspect_ratio`
- `resolution`

### 预期职责

- 接收首帧图片和视频 prompt
- 生成视频片段
- 输出统一的媒体 URL 和 metadata

### 接入建议

后续真实接入时，建议额外记录：

- provider task id
- 异步轮询状态
- 失败原因原文
- 实际生成时长和分辨率

## 当前 stub 约束

v0.2 中新增的：

- `Image2ProviderStub`
- `SeedanceVideoProviderStub`

只用于表达未来接入边界：

- 不读取 API key
- 不发真实请求
- 不产生真实费用
- 被调用时直接抛出明确异常，提示当前仍是占位实现

## 推荐接入顺序

1. 先接 `Image2Provider`
2. 再让 `video` 任务可读取 `image` 任务产物 URL
3. 最后接 `SeedanceVideoProvider`

这样能避免视频 provider 在缺少稳定首帧输入时直接进入高耦合状态。
