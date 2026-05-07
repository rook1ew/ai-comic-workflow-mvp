# 《瓦酒馆 EP01》逐镜头生图计划

## 1. 执行目标

- episode_id：`VG-EP01`
- 标题：《瓦酒馆 EP01：单摸芮娜，赢了战绩输了全队》
- 目标：将 EP01 拆成 8 个可直接进入生图环节的 shot。
- 资产原则：优先使用当前已确认推荐资产，不新增缺失资产。
- 角色范围：老瓦、皮蛋、贤者、芮娜、捷风、幽影。
- 本版不加入评论引导字幕。

## 2. 关键资产接入

| 角色/场景/道具 | 推荐文件 |
| --- | --- |
| 老瓦 | `asset_library/val_tavern/generated/anchors/washu/VG_CHAR_WASHU_fullbody_default_v2.png` |
| 皮蛋 | `asset_library/val_tavern/generated/anchors/pidan/VG_CHAR_PIDAN_action_delivery_v2.png` |
| 贤者 | `asset_library/val_tavern/generated/characters_batch2/sage/VG_CHAR_SAGE_halfbody_tiredsmile_v1.png` |
| 芮娜 | `asset_library/val_tavern/generated/characters_batch4/reyna/VG_CHAR_REYNA_fullbody_purpletoast_v1.png` |
| 捷风 | `asset_library/val_tavern/generated/anchors/jett/VG_CHAR_JETT_halfbody_datacomment_v1.png` |
| 幽影 | `asset_library/val_tavern/generated/characters_batch2/omen/VG_CHAR_OMEN_halfbody_coldstare_v1.png` |
| 吧台全景 | `asset_library/val_tavern/generated/anchors/bar_fullview/VG_SCENE_bar_fullview_v2.png` |
| 吧台中景对话位 | `asset_library/val_tavern/generated/batch3/scenes/bar_dialogue_midshot/VG_SCENE_bar_dialogue_midshot_v2.png` |
| 角落阴影座位 | `asset_library/val_tavern/generated/batch3/scenes/corner_seat/VG_SCENE_corner_omen_seat_v2.png` |
| 皮蛋举牌板 | `asset_library/val_tavern/generated/batch3/props/pidan_sign/VG_PROP_pidan_sign_blank_v2.png` |

## 3. Shot 生图计划

| shot_id | 时间 | 标题 | 画面目标 | 推荐资产 |
| --- | --- | --- | --- | --- |
| SHOT-001 | 0.0–0.5s | 开场视觉钩子 | 酒馆招牌亮起，皮蛋端饮料跑过，圆桌上有排位结算界面。 | 吧台全景、皮蛋 |
| SHOT-002 | 0.5–1.2s | 老瓦固定开场 | 老瓦在吧台后举杯，说“要来一杯吗？”。 | 老瓦、吧台中景 |
| SHOT-003 | 1.2–2.2s | 皮蛋举牌 | 皮蛋举牌，牌面用于后期加“今日特调：单摸战神”。 | 皮蛋、皮蛋举牌板 |
| SHOT-004 | 2.2–6.5s | 贤者吐槽 | 贤者拍桌或指结算界面，委屈又生气。 | 贤者、吧台中景 |
| SHOT-005 | 6.5–12.0s | 芮娜 vs 捷风 | 芮娜自信强调 20-10，捷风冷脸拆台。 | 芮娜、捷风、吧台中景 |
| SHOT-006 | 12.0–18.0s | 芮娜反驳 + 幽影补刀 | 芮娜继续解释拉扯，幽影在角落冷幽默补刀。 | 芮娜、幽影、角落阴影座位 |
| SHOT-007 | 18.0–22.5s | 众人争吵升级 | 四人同场争吵，酒馆复盘气氛热闹但不乱。 | 贤者、芮娜、捷风、幽影、吧台中景 |
| SHOT-008 | 22.5–25.0s | 老瓦叫停 + 皮蛋收尾 | 老瓦叫停，皮蛋举牌 KSKBL 收尾。 | 老瓦、皮蛋、皮蛋举牌板、吧台中景 |

## 4. 生图统一要求

- Q版 / chibi，二次元卡通，赛博酒馆，暖色霓虹。
- 角色轮廓清晰，表情可读，适合抖音竖屏短视频。
- 不使用真实官方 LOGO，不生成大段不可控中文文字。
- 字幕、数字、举牌文字建议后期添加，生图时保留可读留白。
- 芮娜必须使用正式角色资产参考，不再作为缺失资产处理。

## 5. 下一步

- 根据 `data/val_tavern/episodes/ep01_shot_image_generation.seed.json` 逐镜头生成候选图。
- 每个 shot 建议先生成 2 张候选，再人工选择推荐版本。
- 优先检查 SHOT-005 与 SHOT-006，因为这两个镜头直接承载芮娜核心冲突。
