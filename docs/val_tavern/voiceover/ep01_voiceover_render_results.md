# 《炼狱酒馆 EP01》参考音色配音渲染结果

## 1. 执行概览

- 本轮目标：基于用户确认的参考视频提取角色声音，并重新合成 EP01 配音版。
- 输入参考视频：`D:\瓦酒馆视频素材\EP01_first_cut_v1.mp4`
- 输入静音剪辑：`asset_library/val_tavern/generated/episodes/ep01/edit/exports/VG_EP01_seeddance_first_cut_silent_v1.mp4`
- 输出视频：`asset_library/val_tavern/generated/episodes/ep01/edit/exports/VG_EP01_seeddance_first_cut_voice_ref_v2.mp4`
- 输出总配音轨：`asset_library/val_tavern/generated/episodes/ep01/edit/project_files/VG_EP01_voiceover_reference_v2.wav`
- 单句配音数量：18
- 输出视频时长：41 秒

## 2. 音色处理说明

- 老瓦、皮蛋、贤者、捷风、幽影：从用户确认参考视频中按台词切句，做基础响度统一和压缩处理。
- 芮娜：使用用户确认的 V3 方向，向更自信、更亮、更有攻击性的芮娜音色靠近。
- 本轮未使用官方游戏角色原声。
- 本轮未使用 LOL 酒桶古拉加斯原音频。
- 本轮未重新生成图片或视频片段，只替换配音轨并输出新 mp4。

## 3. 输出文件

| 类型 | 路径 |
| --- | --- |
| 配音版视频 | `asset_library/val_tavern/generated/episodes/ep01/edit/exports/VG_EP01_seeddance_first_cut_voice_ref_v2.mp4` |
| 总配音 WAV | `asset_library/val_tavern/generated/episodes/ep01/edit/project_files/VG_EP01_voiceover_reference_v2.wav` |
| 单句配音目录 | `asset_library/val_tavern/generated/episodes/ep01/voiceover_lines/reference_v2/` |
| 渲染结果 JSON | `data/val_tavern/voiceover/ep01_voiceover_render_results.json` |
| 可复用渲染脚本 | `scripts/val_tavern/voiceover/render_ep01_reference_voiceover.py` |

## 4. HyperFrames 状态

本轮尝试检查 HyperFrames CLI，但当前本机 PATH 中缺少 `npm` / `npx`，因此暂时无法执行 `npx hyperframes render` 或 `npx hyperframes tts`。后续补齐 Node/npm 环境后，可以用 HyperFrames 制作更强的分层字幕、动画和音频时间线对照版。

## 5. 后续检查建议

- 观看 `VG_EP01_seeddance_first_cut_voice_ref_v2.mp4`，重点检查台词是否压到字幕节奏。
- 如果某句配音进入太早或太晚，优先调整 `render_ep01_reference_voiceover.py` 中对应 `target_start`。
- 如果某句切音不完整，优先调整对应 `source_start` 和 `source_duration`。
- 如果芮娜仍不够接近目标音色，可继续在 V3 基础上微调 EQ、语速和压缩参数。
