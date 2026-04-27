# IMAGE_PROMPT_BUILDER_SOP

## 1. 分镜图提示词标准结构

当前 `GET /projects/{project_id}/image-prompts` 导出的 `copy_ready_prompt` 是给
“单镜头分镜图 / storyboard keyframe”准备的，不是海报提示词。

标准结构包括：

1. Task type
2. Output goal
3. Anti-poster rules
4. Shot clarity rules
5. Visual asset refs
6. Creative shot fields
7. Editing fields
8. Shot-type tuning
9. Horror / suspense atmosphere rules
10. Negative prompt

## 2. 角色参考图提示词 vs 分镜图提示词

角色参考图提示词更关注：

- 正脸稳定
- 发型稳定
- 服装稳定
- 表情包和转面

分镜图提示词更关注：

- 单一叙事时刻
- 动作与空间关系
- 剪辑可读性
- 字幕留位
- 镜头节奏

所以分镜图提示词必须明确：

- storyboard shot image
- single-shot storyboard keyframe
- suitable for later editing

## 3. storyboard shot image 必须包含哪些规则

建议一定包含：

- one clear narrative moment only
- readable acting and expression
- clear action and spatial relationship
- clean composition for later subtitle placement
- suitable for storyboard-based short-drama editing

## 4. 哪些词用于避免海报化

至少建议包含：

- not a poster
- not a character sheet
- not a collage
- not a multi-panel comic page

## 5. 如何使用 visual asset refs

程序会自动加入：

- Recommended character reference
- Recommended scene reference
- Recommended prop reference
- Must keep
- Avoid

使用原则：

- Recommended reference 用来提醒应该优先参考哪套素材
- Must keep 用来保持一致性
- Avoid 用来压制走偏方向

## 6. 如何根据 shot_type 调整提示词

- `dialogue`
  - 强调表情可读、口型、字幕空间
- `reaction`
  - 强调情绪反应和脸部清晰度
- `reveal`
  - 强调反转、异常线索、认知改变
- `close_up`
  - 强调面部细节与干净构图
- `transition`
  - 强调切点友好和构图稳定
- `action`
  - 强调动作清晰和调度可读
- `suspense`
  - 强调沉默、留白、压迫、视觉不确定性

## 7. 惊悚悬疑题材如何强调氛围

推荐优先强调：

- low light
- narrow space
- silence
- unease
- off-screen threat
- suspenseful pause
- psychological fear
- cinematic horror atmosphere without gore

## 8. 示例 copy_ready_prompt

```text
Task type: storyboard shot image for a vertical AI comic drama.
Output goal: generate one single-shot storyboard keyframe for later editing.
Base image prompt: a woman wakes up from urgent knocking in a dim apartment bedroom
Visual style: anime-comic realism
Shot clarity: show one clear narrative moment only; focus on readable acting and expression; make the character action and spatial relationship clear; maintain clean composition for later subtitle placement; suitable for storyboard-based short-drama editing.
Do not create a poster, character sheet, collage, or multi-panel comic page. not a poster. not a character sheet. not a collage. not a multi-panel comic page.
Reveal focus: emphasize a disturbing clue, changed understanding of the scene, and suspenseful reveal.
Shot purpose: opening horror hook
Conflict beat: safety of room vs unknown outside threat
Visual focus: phone time and dark doorway
Lighting: low light with cold phone glow
Recommended character reference: 沈知夏: file:///D:/refs/shen.png
Recommended scene reference: Apartment Entry Door: file:///D:/refs/door.png
Recommended prop reference: Peephole: file:///D:/refs/peephole.png
Must keep: same face shape, same hairstyle, same outfit
Avoid: celebrity likeness, known anime character
Negative prompt: 不要模仿具体IP、明星、影视角色或已知动漫角色；不要水印；不要乱码文字；不要多余肢体；不要低清晰度。
```
