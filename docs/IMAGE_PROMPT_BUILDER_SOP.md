# IMAGE_PROMPT_BUILDER_SOP

## 1. 这份 SOP 解决什么问题

`GET /projects/{project_id}/image-prompts` 导出的 `copy_ready_prompt` 是给
“单镜头分镜图 / storyboard keyframe”准备的，不是海报、不是角色设定图、也不是
场景参考板。

它的目标是：

- 生成一个清晰的单镜头叙事关键帧
- 让后续字幕、轻动效、剪辑和图生视频更容易衔接
- 保持角色、场景、道具在连续镜头里的统一性

## 2. 标准结构

当前分镜图 prompt 重点包含：

1. Task type
2. Output goal
3. Anti-poster rules
4. Shot clarity rules
5. Visual asset refs
6. Creative shot fields
7. Editing fields
8. Shot-type tuning
9. Genre atmosphere rules
10. Negative prompt

## 3. 分镜图和参考资产图的区别

`image-prompts`：

- 用于 `storyboard keyframe`
- 要承载剧情动作、情绪、视觉焦点、镜头目的
- 要考虑字幕空间、镜头可读性、后续剪辑

`visual-asset-prompts`：

- 用于角色 / 场景 / 道具参考图
- 不承载剧情动作
- 更强调稳定、可复用、统一性

简化理解：

- `visual-asset-prompts` 先做“素材库参考图”
- `image-prompts` 再做“单镜头分镜图”

## 4. 分镜图必须强调什么

建议至少明确这些意思：

- `storyboard keyframe`
- `single-shot storyboard frame`
- `not a character sheet`
- `not an environment plate`
- `not a poster`
- `one clear narrative moment only`
- `readable acting and expression`
- `clean composition for later subtitle placement`

## 5. 如何使用 visual asset refs

如果 shot 已经绑定角色 / 场景 / 道具参考，prompt 会自动整合：

- Recommended character reference
- Recommended scene reference
- Recommended prop reference
- Must keep
- Avoid

它们的作用是：

- 让角色身份稳定
- 让场景布局稳定
- 让道具外观稳定

## 6. Creative 字段如何进入 prompt

如果存在，这些字段会被自然合并进 `copy_ready_prompt`：

- `visual_focus`
- `image_prompt_intent`
- `pacing_note`
- `shot_purpose`
- `conflict_beat`
- `emotion_shift`
- `composition`
- `lighting`
- `subtitle_position`
- `negative_constraints`

## 7. Editing 字段如何进入 prompt

如果存在，这些字段也会进入分镜图 prompt：

- `shot_type`
- `camera_motion`
- `subject_motion`
- `transition`
- `subtitle_text`
- `sfx`
- `editing_notes`

其中：

- `camera_motion` 主要用于给后续剪辑留余量
- `subject_motion` 主要用于提示动作倾向，不是要求模型直接做视频
- `subtitle_text` 会帮助模型留出字幕安全区
- `transition` 是上下镜衔接提示，不是单独画一个转场特效

## 8. 惊悚悬疑题材建议

这类题材建议优先强调：

- low light
- narrow space
- silence
- unease
- off-screen threat
- suspenseful pause
- psychological fear
- cinematic horror atmosphere without gore

不要依赖：

- 露骨血腥
- 极端怪物化设计
- 对具体影视 / 动漫 / 恐怖角色的模仿

## 9. Storyboard Production Board 的关系

`GET /projects/{project_id}/storyboard-production-board` 复用了同一套
production-grade image prompt builder，但把 `copy_ready_image_prompt` 放进了
更完整的分镜制作表里。

适合这样理解：

- `image-prompts`
  - 当你主要需要完整分镜图 prompt
- `storyboard-production-board`
  - 当你还需要同时看：
    - shot timing
    - human-readable shot description
    - reference assets
    - motion prompt
    - editing notes

## 10. 示例

```text
Task type: storyboard keyframe.
Output goal: generate one single-shot storyboard frame for this scene, not a character sheet and not an environment plate.
Shot ID: SH02
Story function: suspense escalation
Character(s): 沈知夏
Location: 公寓门口
Core action: 沈知夏从猫眼向外看去
Visual focus: 猫眼视角外那张和她相同的脸
Continuity anchors: use the referenced character, scene, and prop assets as continuity anchors.
Subtitle-safe space: leave clean subtitle-safe space near the lower frame when possible.
Style: anime-comic realism.
Negative prompt: no poster layout, no character sheet, no environment plate, no gore.
```
