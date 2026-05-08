# 《炼狱酒馆 EP01》SeedDance 视频剪辑计划

## 1. 当前剪辑目标

本阶段目标是制作 EP01 的 first cut：只拼接 6 段已生成的 SeedDance 视频片段，验证剧情顺序、字幕可读性、角色节奏和整体观看流畅度。

本阶段不重新生图，不重新生成视频，不修改原始视频，不扩展剧情。

## 2. 视频片段顺序

| 顺序 | clip_id | 片段内容 | 占位源视频 |
| --- | --- | --- | --- |
| 1 | EP01-CLIP-01 | 开场 + 老瓦 + 皮蛋举牌 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_01_opening.mp4` |
| 2 | EP01-CLIP-02 | 贤者吐槽 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_02_sage_complain.mp4` |
| 3 | EP01-CLIP-03 | 芮娜嘴硬 + 捷风阴阳 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_03_reyna_jett.mp4` |
| 4 | EP01-CLIP-04 | 芮娜反驳 + 幽影补刀 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_04_reyna_omen.mp4` |
| 5 | EP01-CLIP-05 | 众人争吵 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_05_group_argument.mp4` |
| 6 | EP01-CLIP-06 | 老瓦叫停 + 皮蛋收尾 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_06_pidan_ending.mp4` |

## 3. 推荐时间线

| 片段 | 时间段 | 时长 | 内容 |
| --- | --- | --- | --- |
| Clip 01 | 0-5s | 5s | 开场 + 老瓦 + 皮蛋举牌 |
| Clip 02 | 5-12s | 7s | 贤者吐槽 |
| Clip 03 | 12-19s | 7s | 芮娜嘴硬 + 捷风阴阳 |
| Clip 04 | 19-28s | 9s | 芮娜反驳 + 幽影补刀 |
| Clip 05 | 28-36s | 8s | 众人争吵 |
| Clip 06 | 36-41s | 5s | 老瓦叫停 + 皮蛋收尾 |

## 4. 剪辑注意事项

- 只拼接 6 段视频，不拼静态帧。
- 每段前后裁掉不稳定废帧，尤其是字幕变形、角色脸部漂移、手部明显崩坏的部分。
- 转场以硬切为主，避免过度转场影响短视频节奏。
- 字幕已经烘焙进视频，不重复加字幕。
- 如果字幕糊了，再用剪映覆盖同文案字幕。
- 当前版本不添加结尾评论引导字幕。
- 不使用官方角色原音频，不使用酒桶古拉加斯原音频。

## 5. 音频建议

- 角色配音：老瓦、皮蛋、贤者、芮娜、捷风、幽影。
- 背景音乐：轻微酒馆 BGM，音量低于对白。
- 环境声：酒馆底噪、杯子碰撞声、轻微霓虹电流声。
- 重点音效：碰杯、拍桌、pop、whoosh。
- 幽影补刀处可加低频氛围音，但不要做恐怖化处理。

## 6. First Cut 检查清单

- 6 个片段是否按正确顺序拼接。
- 每段开头和结尾是否裁掉不稳定废帧。
- 字幕是否清楚可读。
- 字幕是否和画面情绪大致同步。
- 角色脸部是否稳定。
- 老瓦、皮蛋、贤者、芮娜、捷风、幽影是否均能被识别。
- `KSKBL` 收尾是否清楚。
- 是否没有重复添加字幕。
- 是否没有评论引导字幕。
- 全片节奏是否适合 41 秒 first cut。

## 7. Final Cut 下一步计划

- 将 6 个 SeedDance 片段按本时间线导入剪辑软件。
- 完成 first cut 粗剪并人工观看。
- 如果某段字幕不可读，优先用剪映覆盖字幕。
- 如果某段角色形变严重，再单独重跑对应 SeedDance 片段。
- 录制或生成角色配音。
- 添加酒馆 BGM、环境声和关键音效。
- 调整整体音量、节奏和结尾停顿。
- 输出 EP01 final cut v1。
