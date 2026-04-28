# VISUAL_ASSET_PROMPT_BUILDER

## v0.5-B Character Appearance note

For character assets, `visual-asset-prompts` now checks whether the matching `Character` has a selected `CharacterAppearance`.

If a selected appearance exists, the character reference prompt includes:

- `Selected appearance reference: ...`
- `Use this selected appearance as the primary identity anchor.`

The endpoint still does not generate images, upload files, crop images, or call any real provider. It only builds copy-ready prompts for external/manual use.

## 什么是 Visual Asset Prompt Builder

`GET /projects/{project_id}/visual-asset-prompts` 用来生成三类“参考资产图 prompt”：

1. 角色参考图 prompt
2. 场景参考图 prompt
3. 道具参考图 prompt

它的重点不是剧情镜头，而是素材库参考图。

## 它和 image-prompts 的区别

`visual-asset-prompts`：

- 用于 reusable library assets
- 用于 canonical character references
- 用于 scene reference plates
- 用于 prop single-object references
- 不承载剧情动作

`image-prompts`：

- 用于 storyboard shot
- 承载剧情动作、情绪、视觉焦点、镜头目的

一句话区分：

- 先做 reference assets
- 再做 storyboard shots

## 三类 prompt 的定位

### 1. Character

角色参考图 prompt 更强调：

- canonical character reference
- not a storyboard shot
- not a scene frame
- clean background
- stable face / hair / outfit / vibe

适合生成：

- main reference
- 定妆图
- 后续 front / side / expression / mouth shape 的基础参考

### 2. Scene

场景参考图 prompt 更强调：

- scene reference plate
- environment reference image
- no characters
- clear spatial layout
- reusable background consistency

适合生成：

- 固定场景主参考
- 统一空间布局和光线氛围

### 3. Prop

道具参考图 prompt 更强调：

- prop reference image
- single object only
- centered presentation
- no characters
- no hands
- reusable object consistency

## 为什么需要它

很多项目在开始时还没有真实参考图，例如：

- `ShenZhixia_main.png`
- `old_apartment_bedroom_main.png`
- `smartphone_main.png`

这时系统虽然知道“缺参考图”，但如果没有 prompt builder，用户仍然要手写参考图提示词。

这个接口的作用就是：

- 先自动生成参考图 prompt
- 再让人工去外部工具生成参考图
- 再把生成后的 URL 回填进 Visual Asset Library

## 推荐流程

1. `extract candidates`
2. `import/manual-import assets`
3. `visual-asset-prompts`
4. 生成 reference images
5. `manual-import` 更新 URL
6. `reference-coverage-report`
7. `image-prompts`
8. 生成 shot images
9. `storyboard-production-board`

## 和 Storyboard Production Board 的关系

`storyboard-production-board` 会消费这些资产引用结果，但它本身不负责生成参考资产图 prompt。

推荐职责分工：

- `visual-asset-prompts`
  - 先做角色 / 场景 / 道具参考图
- `reference-coverage-report`
  - 再检查哪些 shot 已经吃到参考资产
- `image-prompts`
  - 再做分镜图 prompt
- `storyboard-production-board`
  - 最后把参考资产、分镜图 prompt、运动提示和剪辑信息汇总成制作表

## 示例

### Character prompt

```text
Task type: character reference image.
Output goal: create one canonical character reference portrait for later storyboard generation, not a storyboard shot.
Character: 沈知夏
Role: lead
Framing: clean half-body or three-quarter portrait.
Background: simple, neutral, non-narrative background.
Style: anime-comic realism.
Continuity requirement: keep face shape, hairstyle, outfit silhouette, and character vibe stable for future shots.
```

### Scene prompt

```text
Task type: scene reference plate.
Output goal: create one environment reference image for later storyboard consistency, not a storyboard shot.
Scene: 旧公寓卧室
Characters: no characters.
Layout anchors: clearly show spatial layout and fixed elements.
Style: anime-comic realism.
```

## v0.5-A 衔接说明

在新的 Lite 创作前段里，推荐先走：

1. `story-source`
2. `narrative-structure-lite`
3. `storyboard-package`
4. `visual-asset-candidates / manual-import`
5. `visual-asset-prompts`

这样做的好处是：

- 先明确故事结构
- 再准备角色 / 场景 / 道具参考资产
- 最后再进入 `image-prompts` 的单镜头分镜图生成

### Prop prompt

```text
Task type: prop reference image.
Output goal: create one reusable prop reference image, not a storyboard shot.
Prop: 猫眼
Presentation: single object only, centered, clearly visible.
Characters: none.
Hands: none.
Style: anime-comic realism.
```
