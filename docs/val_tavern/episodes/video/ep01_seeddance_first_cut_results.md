# 《炼狱酒馆 EP01》SeedDance First Cut 剪辑结果

## 1. 执行概览

- 本轮目标：将 6 段 SeedDance 视频按剪辑计划拼接，并加入占位中文配音。
- 是否重新生图：否。
- 是否重新生成 SeedDance 视频：否。
- 是否修改 `D:\1.mp4` 到 `D:\6.mp4` 原始视频：否。
- 剪辑方式：硬切为主，Clip 01 裁掉前段冗余，其余片段按计划时长轻裁。
- 配音方式：本机 `Microsoft Huihui Desktop` 中文 TTS，占位单声道配音，已合成为 AAC 音轨。

## 2. 输出文件

| 类型 | 路径 |
| --- | --- |
| 最终带配音 first cut | `asset_library/val_tavern/generated/episodes/ep01/edit/exports/VG_EP01_seeddance_first_cut_vo_v1.mp4` |
| 无声拼接版 | `asset_library/val_tavern/generated/episodes/ep01/edit/exports/VG_EP01_seeddance_first_cut_silent_v1.mp4` |
| 整段配音 WAV | `asset_library/val_tavern/generated/episodes/ep01/edit/project_files/VG_EP01_voiceover_v1.wav` |
| 工程记录 JSON | `asset_library/val_tavern/generated/episodes/ep01/edit/project_files/VG_EP01_seeddance_edit_project_v1.json` |

## 3. 视频规格

- 画幅：9:16
- 分辨率：720 x 1280
- 帧率：30 fps
- 视频编码：H.264
- 音频编码：AAC
- 实际时长：约 40.88 秒

## 4. 使用片段

| clip_id | 仓库内视频路径 | 时间线 |
| --- | --- | --- |
| EP01-CLIP-01 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_01_opening.mp4` | 0-5s |
| EP01-CLIP-02 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_02_sage_complain.mp4` | 5-12s |
| EP01-CLIP-03 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_03_reyna_jett.mp4` | 12-19s |
| EP01-CLIP-04 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_04_reyna_omen.mp4` | 19-28s |
| EP01-CLIP-05 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_05_group_argument.mp4` | 28-36s |
| EP01-CLIP-06 | `asset_library/val_tavern/generated/episodes/ep01/seeddance_clips/EP01_CLIP_06_pidan_ending.mp4` | 36-41s |

## 5. 当前版本说明

- 当前配音是占位版本，不是最终角色分声线版本。
- 若字幕在 SeedDance 输出中仍有模糊，可在剪映中覆盖同文案字幕。
- 若需要正式发布版，建议替换为多角色配音，并补充轻微酒馆 BGM、碰杯、拍桌、pop、whoosh 等音效。

## 6. 下一步

- 人工观看 `VG_EP01_seeddance_first_cut_vo_v1.mp4`。
- 标记字幕不清晰或角色变形严重的片段。
- 根据观看结果决定是否重跑单个 SeedDance 片段。
- 替换正式多角色配音和 BGM。
- 输出 final cut v1。
