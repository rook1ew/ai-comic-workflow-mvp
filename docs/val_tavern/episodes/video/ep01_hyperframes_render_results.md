# 《炼狱酒馆 EP01》HyperFrames 对照渲染结果

## 1. 执行概览

- 本轮目标：使用 HyperFrames 生成一版 EP01 对照视频，检查是否比纯 FFmpeg 拼接更适合后续视频工程。
- 输入素材：6 段 SeedDance 视频片段。
- 输入音频：`VG_EP01_voiceover_reference_v2.wav`
- 输出视频：`asset_library/val_tavern/generated/episodes/ep01/edit/exports/VG_EP01_hyperframes_first_cut_voice_ref_v1.mp4`
- 工程目录：`video_projects/hyperframes/ep01_first_cut_hyperframes/`
- 是否重新生图：否
- 是否修改原始视频片段：否

## 2. 输出规格

| 项目 | 结果 |
| --- | --- |
| 分辨率 | 1080×1920 |
| 帧率 | 30fps |
| 时长 | 41.02s |
| 音频 | AAC 双声道 |
| 渲染工具 | HyperFrames 0.5.5 |

## 3. 检查结果

- `npx hyperframes lint`：通过，0 errors，0 warnings。
- `npx hyperframes inspect --samples 8 --json`：通过，0 issues。
- 输出视频存在。
- 输出视频包含音频轨。
- 未修改原始图片。
- 未修改原始 SeedDance 视频片段。

## 4. 与 FFmpeg 版本的差异

HyperFrames 版本的优势：

- 可以把视频、音频、字幕、图层动画统一写进 HTML 时间线。
- 后续适合做片头、动态标题、弹幕式梗字、角色名牌、转场和包装动画。
- 有 lint / inspect，可提前发现布局和文本溢出问题。

当前版本的限制：

- 本轮只做对照渲染，没有新增字幕或包装图层，因此视觉内容基本继承原 6 段 SeedDance clip。
- 渲染速度比 FFmpeg 慢，因为需要浏览器逐帧捕获。
- 如果只是无特效拼接，FFmpeg 仍然更快。

## 5. 后续建议

- 保留 FFmpeg 作为快速拼接和批处理方案。
- 用 HyperFrames 处理需要更强包装控制的版本，例如片头、卡点字、角色名牌、字幕动效和社媒封面版。
- 如果下一版需要更像“成片”，建议在 HyperFrames 工程中加入：开场标题卡、关键台词高亮、轻微镜头边框、音效卡点和结尾品牌标识。
