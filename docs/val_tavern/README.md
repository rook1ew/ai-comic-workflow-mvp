# 《瓦酒馆》第一阶段资产库

## 项目概览

- **项目名称**：《瓦酒馆》
- **项目定位**：Q版无畏契约赛后酒馆轻喜剧栏目
- **核心结构**：固定酒馆场景 + 角色互怼 + 每集一个瓦圈梗 + 今日特调收尾
- **第一阶段目标**：先搭建角色、道具、场景三类资产库，并预留模板目录，方便后续接入分镜、生成图、短视频包装等工作流。

## 第一阶段核心角色

| 角色 | 栏目定位 |
| --- | --- |
| 瓦叔 | 原创酒馆老板，今日特调收尾位 |
| 皮蛋 | 酒馆吉祥物 / 小跑堂 / 送酒递账单 |
| 捷风 | 冷静毒舌 / 数据拆台 |
| 火男 | 嘴硬上头 / 白给制造机 |
| 奶妈 | 温柔补刀 / 被甩锅专业户 |
| 奇乐 | 可爱道具位 / 兼职服务员 / 设备维修员 |
| 幽影 | 阴间金句 / 冷幽默 |

## 第一阶段资产分类

| 分类 | 目录 | 说明 |
| --- | --- | --- |
| characters | `asset_library/val_tavern/characters/` | 角色全身、半身、表情、动作资产 |
| props | `asset_library/val_tavern/props/` | 栏目道具、角色专属道具、梗道具、背景装饰 |
| scenes | `asset_library/val_tavern/scenes/` | 固定酒馆场景与镜头位 |
| templates | `asset_library/val_tavern/templates/` | 封面、今日特调卡、字幕包装等模板 |
| references | `asset_library/val_tavern/references/` | 风格参考、情绪板、后续人工整理资料 |

## 文档索引

- [角色资产卡](./phase1_character_assets.md)
- [道具资产卡](./phase1_prop_assets.md)
- [场景资产卡](./phase1_scene_assets.md)
- [统一命名规则](./asset_naming_rules.md)
- [第一阶段制作优先级](./phase1_asset_priority.md)
- [第四批角色资产导入结果](./phase1_character_batch4_results.md)
- [固定开场白框架](./opening_formula_framework.md)
- [固定开场白 1.0](./opening_formula_v1.md)
- [EP01 脚本](./episodes/ep01_duelist_problem_script.md)
- [EP01 分镜](./episodes/ep01_duelist_problem_storyboard.md)
- [EP01 shot generation plan](./episodes/ep01_shot_generation_plan.md)
- [EP01 shot image generation seed](../../data/val_tavern/episodes/ep01_shot_image_generation.seed.json)
- [EP01 first cut 视频制作说明](./episodes/video/ep01_video_first_cut_notes.md)
- [EP01 剪辑计划](./episodes/video/ep01_editing_plan.md)
- [EP01 SeedDance first cut 剪辑结果](./episodes/video/ep01_seeddance_first_cut_results.md)
- [EP01 SeedDance2 带字输入图与提示词](./episodes/ep01_seeddance_prompt_pack.md)
- [任务种子文件](../../data/val_tavern/phase1_asset_tasks.seed.json)

## 任务种子文件位置

当前仓库未发现会忽略 `data/` 的 `.gitignore` 规则，因此第一阶段结构化任务种子文件放置在：

`data/val_tavern/phase1_asset_tasks.seed.json`

## 非官方粉丝二创说明

《瓦酒馆》是基于无畏契约玩家社区语境创作的粉丝二创短视频栏目设定，非官方内容，仅用于娱乐交流。资产库不得使用真实官方 LOGO 文件、官方素材原图或误导观众认为本项目为官方出品的表述。
