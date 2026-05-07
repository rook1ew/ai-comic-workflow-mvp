# 《瓦酒馆 EP01》SeedDance2 带字输入图与提示词

## 1. 流程说明

本流程采用“字幕前置烘焙”：先把 EP01 的核心对白、牌面文字和结尾梗写入输入图，再交给 SeedDance2 做图生视频。后续不再逐句添加字幕，SeedDance2 需要尽量保持输入图中的中文文字清晰、稳定、不可改写。

本轮只制作 6 张带字输入图，不生成视频，不重新生图，不修改原始 shot 图片。

## 2. 统一负面提示词

不要乱码文字，不要改写中文字，不要水印，不要新增角色，不要角色脸崩，不要大幅旋转，不要大幅推拉，不要战斗场景，不要写实真人，不要改变服装和发型。

## 3. Clip 输入图与提示词

### VG-EP01-SD-CLIP-01｜开场与今日特调

- 输入图：`asset_library/val_tavern/generated/episodes/ep01/seeddance_inputs/VG_EP01_SD_CLIP_01_opening_text_v1.png`
- 来源图：`asset_library/val_tavern/generated/episodes/ep01/shot_images/VG_EP01_SHOT_001_opening_v1.png`
- 建议时长：4s
- 烘焙文字：
  - 老瓦：要来一杯吗？
  - 皮蛋：今日特调：单摸战神

SeedDance2 提示词：

Q版二次元赛博酒馆短视频镜头，9:16 竖屏，暖色霓虹，轻微镜头运动，保持原图角色设计，严格保持画面中的中文对白气泡和牌面文字清晰可读，不要改写文字，不要生成新文字，不要让文字变形，不要新增角色，不要变成战斗场景。

### VG-EP01-SD-CLIP-02｜贤者吐槽

- 输入图：`asset_library/val_tavern/generated/episodes/ep01/seeddance_inputs/VG_EP01_SD_CLIP_02_sage_complain_text_v1.png`
- 来源图：`asset_library/val_tavern/generated/episodes/ep01/shot_images/VG_EP01_SHOT_004_sage_complain_v1.png`
- 建议时长：4s
- 烘焙文字：
  - 贤者：
  - 打 A 让你跟团，
  - 你非要摸 B！
  - 捷风 E 进去就没了，
  - 你人呢？

SeedDance2 提示词：

Q版二次元赛博酒馆短视频镜头，9:16 竖屏，暖色霓虹，轻微镜头运动，保持原图角色设计，严格保持画面中的中文对白气泡和牌面文字清晰可读，不要改写文字，不要生成新文字，不要让文字变形，不要新增角色，不要变成战斗场景。

### VG-EP01-SD-CLIP-03｜芮娜与捷风

- 输入图：`asset_library/val_tavern/generated/episodes/ep01/seeddance_inputs/VG_EP01_SD_CLIP_03_reyna_jett_text_v1.png`
- 来源图：`asset_library/val_tavern/generated/episodes/ep01/shot_images/VG_EP01_SHOT_005_reyna_jett_conflict_v1.png`
- 建议时长：4s
- 烘焙文字：
  - 芮娜：
  - 我 20-10，全队最高，
  - 怪我？
  - 捷风：
  - 你这 20-10 挺好看，
  - 就是和赢游戏没关系。

SeedDance2 提示词：

Q版二次元赛博酒馆短视频镜头，9:16 竖屏，暖色霓虹，轻微镜头运动，保持原图角色设计，严格保持画面中的中文对白气泡和牌面文字清晰可读，不要改写文字，不要生成新文字，不要让文字变形，不要新增角色，不要变成战斗场景。

### VG-EP01-SD-CLIP-04｜芮娜与幽影

- 输入图：`asset_library/val_tavern/generated/episodes/ep01/seeddance_inputs/VG_EP01_SD_CLIP_04_reyna_omen_text_v1.png`
- 来源图：`asset_library/val_tavern/generated/episodes/ep01/shot_images/VG_EP01_SHOT_006_reyna_omen_roast_v2.png`
- 建议时长：4s
- 烘焙文字：
  - 芮娜：
  - 我在拉扯，给压力！
  - 幽影：
  - 不怪你。
  - 你只是和队伍不在一个地图。

SeedDance2 提示词：

Q版二次元赛博酒馆短视频镜头，9:16 竖屏，暖色霓虹，轻微镜头运动，保持原图角色设计，严格保持画面中的中文对白气泡和牌面文字清晰可读，不要改写文字，不要生成新文字，不要让文字变形，不要新增角色，不要变成战斗场景。

### VG-EP01-SD-CLIP-05｜众人争吵

- 输入图：`asset_library/val_tavern/generated/episodes/ep01/seeddance_inputs/VG_EP01_SD_CLIP_05_group_argument_text_v1.png`
- 来源图：`asset_library/val_tavern/generated/episodes/ep01/shot_images/VG_EP01_SHOT_007_group_argument_v1.png`
- 建议时长：4s
- 烘焙文字：
  - 贤者：至少你人在，我们还能补枪！
  - 捷风：你来得比残局结算还晚。
  - 幽影：她不是单摸，她是单机。

SeedDance2 提示词：

Q版二次元赛博酒馆短视频镜头，9:16 竖屏，暖色霓虹，轻微镜头运动，保持原图角色设计，严格保持画面中的中文对白气泡和牌面文字清晰可读，不要改写文字，不要生成新文字，不要让文字变形，不要新增角色，不要变成战斗场景。

### VG-EP01-SD-CLIP-06｜皮蛋结尾

- 输入图：`asset_library/val_tavern/generated/episodes/ep01/seeddance_inputs/VG_EP01_SD_CLIP_06_pidan_ending_text_v1.png`
- 来源图：`asset_library/val_tavern/generated/episodes/ep01/shot_images/VG_EP01_SHOT_008_pidan_ending_v1.png`
- 建议时长：4s
- 烘焙文字：
  - 都别吵了，
  - KSKBL

SeedDance2 提示词：

Q版二次元赛博酒馆短视频镜头，9:16 竖屏，暖色霓虹，轻微镜头运动，保持原图角色设计，严格保持画面中的中文对白气泡和牌面文字清晰可读，不要改写文字，不要生成新文字，不要让文字变形，不要新增角色，不要变成战斗场景。

## 4. 使用建议

- 每个 clip 建议生成 4 秒图生视频。
- 输入图已经包含核心文字，SeedDance2 阶段不要再要求模型新增字幕。
- 如果文字在视频中漂移、乱码或变形，应降低镜头运动幅度，优先使用更稳定的轻微推近。
- 如果某个 clip 需要更长台词，建议重新制作更少字、更大字的输入图，而不是在 SeedDance2 提示词里追加文字。
