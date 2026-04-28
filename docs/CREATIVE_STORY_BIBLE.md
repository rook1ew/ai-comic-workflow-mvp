# CREATIVE_STORY_BIBLE

## 1. AI漫剧不是单张图生产

AI漫剧更接近“连续内容生产”：

- 角色要跨镜头稳定
- 场景要跨镜头稳定
- 道具要跨镜头稳定
- 情绪、冲突和信息揭示要逐镜头推进

所以 Creative Bible 的作用，不是把一句简介写漂亮，而是给后续：

- storyboard
- image-prompts
- editing-shot-board
- editing-timeline
- editing-cue-sheet

提供长期可复用的创作约束。

## 2. 学结构，不模仿具体 IP

学习市场优秀作品时，只学习这些东西：

- 钩子节奏
- 信息揭示顺序
- 误导和反转手法
- 恐惧升级节奏
- 镜头功能分配

不要直接模仿：

- 具体电影
- 具体电视剧
- 具体动漫
- 具体恐怖角色
- 明星或公众人物脸

## 3. 常见爆款惊悚悬疑结构

适合 30–60 秒都市怪谈 / 恐怖惊悚悬疑短剧的基础结构：

1. 3秒钩子
2. 深夜异常
3. 规则提示
4. 恐惧升级
5. 误导信息
6. 反常细节
7. 悬疑反转
8. 结尾钩子

## 4. 角色设定如何写得更丰满

建议至少补这些维度：

- public mask：别人以为她是什么样
- inner truth：她真正是什么样
- fear：她最怕什么
- desire：她最想得到什么
- secret：她隐藏了什么
- stress reaction：遇到压力怎么反应
- arc_start / arc_end：她怎么变化

这些字段不一定都会进画面，但会影响：

- 表情设计
- 镜头焦点
- 台词风格
- 提示词的心理气质

## 5. 惊悚短剧如何设计恐惧节奏

优先做这些恐惧来源：

- 低光
- 狭窄空间
- 沉默
- 反常细节
- 视野之外的威胁
- 错位身份
- 规则提示
- 看似安全但突然失效的日常秩序

尽量少做：

- 大量血腥
- 露骨伤害
- 怪物堆砌
- 单纯靠 jump scare

## 6. 分镜如何服务剪辑

一个好分镜，不只是“画面好看”，还要回答：

- 这个 shot 的剧情功能是什么
- 冲突点在哪里
- 视觉焦点是什么
- 字幕要留在哪里
- 镜头运动怎么配合节奏
- 人物微动要不要做

推荐在 shot 中补这些 creative fields：

- `shot_purpose`
- `conflict_beat`
- `emotion_shift`
- `visual_focus`
- `image_prompt_intent`
- `composition`
- `lighting`
- `subtitle_position`
- `negative_constraints`

## 7. 如何避免海报式画面

分镜图不是海报。要主动避免：

- 站桩摆拍
- 纯概念海报构图
- 空间关系不清
- 人物动作不清
- 表情不够读得懂
- 一张图塞太多信息

推荐在 prompt 中明确：

- one clear narrative moment only
- not a poster
- not a character sheet
- not a collage
- not a multi-panel comic page

## 8. 如何把参考包接入分镜图生成

Visual Asset Library 负责三类参考：

- characters
- scenes
- props

shot 里再通过：

- `character_asset_keys`
- `scene_asset_key`
- `prop_asset_keys`

绑定到具体镜头。

这样 `image-prompts` 就能自动给出：

- Recommended character reference
- Recommended scene reference
- Recommended prop reference
- Must keep
- Avoid

## 9. 恐怖题材安全边界

当前推荐边界：

- 不依赖血腥
- 不做露骨伤害
- 不模仿具体影视 IP / 恐怖角色
- 不做名人脸
- 用氛围、空间、声音和反常细节制造恐惧

## 10. 推荐工作流

1. 先写角色与故事 bible
2. 再准备 visual asset library
3. 再写 storyboard creative fields
4. 导出 `image-prompts`
5. 人工生图并回填
6. 再进入 `editing-shot-board / editing-timeline / editing-cue-sheet`
## 11. core_action 的写法建议

`core_action` 最好写成“一个主动作”。

推荐：

- `沈知夏被急促敲门声惊醒`
- `她从猫眼向外看去`
- `沈知夏盯着物业消息僵住`

不推荐把太多次要动作都塞进同一个 `core_action`：

- `被敲门声惊醒，抓起手机看时间，又抬头看向门口`

更好的拆法是：

- 主动作留在 `core_action`
- 次要动作、镜头节奏、信息焦点放到：
  - `visual_focus`
  - `editing_notes`
  - `pacing_note`
  - `image_prompt_intent`

当前系统不会因为复合动作描述而硬阻塞 `full-demo-flow`。
如果 `core_action` 看起来包含多个动作，`validate-payload` 只会给：

- warning: `core_action_may_contain_multiple_actions`
- suggestion: 鎶婃瑕佺粏鑺傜Щ鍒?`editing_notes / visual_focus / pacing_note`

## 12. v0.5-A Story Source and Narrative Structure Lite

当前创作前段已经补了一个 Lite 结构层，适合 3–10 镜头、30–60 秒的
AI 短漫剧：

- `story-source`
  - 保存原始故事输入
- `narrative-structure-lite`
  - 保存 `segments / beats / storyboard_groups`
- `storyboard-package`
  - 把这些 key 绑定到具体 shot

这样可以先把创作结构补厚，再进入：

- `visual-asset-library`
- `reference-coverage-report`
- `image-prompts`
- `storyboard-production-board`

FastAPI 在这一层只负责保存和回显结构，不直接调用 AI 生成 narrative。
- suggestion: 把次要细节移到 `editing_notes / visual_focus / pacing_note`
