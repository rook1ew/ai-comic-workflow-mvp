# Visual Asset Prompt Builder

## 什么是 Visual Asset Prompt Builder

`GET /projects/{project_id}/visual-asset-prompts` 用来生成三类“参考图 prompt”：

1. 角色参考图 prompt
2. 场景参考图 prompt
3. 道具参考图 prompt

它和 `image-prompts` 不同：

- `visual-asset-prompts`
  - 生成可复用参考图
  - 不带剧情动作
  - 不带 shot 叙事目的
- `image-prompts`
  - 生成 storyboard shot 分镜图
  - 带剧情动作、情绪、镜头、剪辑目的

## 为什么需要它

很多项目在开始时还没有真实参考图，例如：

- `ShenZhixia_main.png`
- `old_apartment_bedroom_main.png`
- `smartphone_main.png`

这时系统虽然知道“缺参考图”，但还需要一层自动 prompt builder，帮用户快速生成这些参考图提示词。

## 角色参考图 prompt 规则

character prompt 会强调：

- `character main reference image for an AI comic drama`
- `create a stable reusable character reference image, not a storyboard shot`
- `not a poster`
- `not a multi-panel comic page`
- `not a dramatic action frame`

并自动整合：

- `name`
- `role`
- `must_keep`
- `avoid`
- richer character fields（如存在）
- `visual_style`
- `genre`

## 场景参考图 prompt 规则

scene prompt 会强调：

- `scene main reference image for an AI comic drama`
- `create a stable reusable scene reference image, not a storyboard shot`
- `no characters`
- `show spatial layout`
- `clean reusable background`

惊悚悬疑题材会额外强调：

- low light
- narrow space
- silence
- unease
- realistic old apartment texture
- no gore

## 道具参考图 prompt 规则

prop prompt 会强调：

- `prop main reference image for an AI comic drama`
- `single object only`
- `simple background`
- `no brand logo`
- `no readable copyrighted text`
- `no watermark`

## 推荐流程

1. `extract candidates`
2. `import/manual-import assets`
3. `visual-asset-prompts`
4. 生成 reference images
5. `manual-import` 更新 URL
6. `reference-coverage-report`
7. `image-prompts`
8. 生成 shot images

## 示例

角色参考图 prompt 应该像这样：

- 这是角色定妆参考图，不是剧情镜头
- 画面干净，可复用
- 面部、发型、服装轮廓清晰
- 背景简单，方便后续作为 identity anchor
