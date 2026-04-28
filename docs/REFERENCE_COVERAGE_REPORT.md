# Reference Coverage Report

## 什么是 Reference Coverage Report

`GET /projects/{project_id}/reference-coverage-report` 是项目级的柔性巡检接口。

它的目标不是阻塞流程，而是在人工生图或 reference-guided image generation 之前，快速回答这些问题：

1. 哪些 shot 已经绑定了角色 / 场景 / 道具参考
2. 哪些 shot 还没有绑定参考
3. 哪些 shot 绑定了不存在的 `asset_key`
4. 哪些已绑定资产还缺 `main_reference_url`
5. 哪些 shot 已经适合进入 reference-guided image generation

## 为什么要在生图前检查

长篇 AI 漫剧最容易失控的不是单张图质量，而是一致性：

- 角色脸型、发型、服装漂移
- 场景布局忽然变化
- 关键道具前后不一致

Reference Coverage Report 的作用，就是在生图前先做一轮“参考素材覆盖巡检”。

## 哪些问题只是 warning

这个接口默认走 soft-check，不会因为这些问题直接阻塞：

- 缺 `character_asset_keys`
- 缺 `scene_asset_key`
- 缺 `prop_asset_keys`
- 绑定了不存在的 `asset_key`
- 资产存在但缺 `main_reference_url`

这些问题会以：

- `warnings`
- `suggestions`

的形式返回，方便人工决定是否先补齐。

## 如何根据 report 修补资产库

### 如果库为空

优先做：

1. `POST /projects/{project_id}/visual-asset-candidates/extract`
2. review candidates
3. `POST /projects/{project_id}/visual-asset-library/import-candidates`

### 如果资产存在但缺 reference URL

用：

- `POST /projects/{project_id}/visual-asset-library/manual-import`

补充：

- `main_reference_url`
- `must_keep`
- `avoid`

### 如果 shot 绑定了不存在的 asset_key

说明：

- 要么 storyboard 里写错了 key
- 要么资产还没真正导入 library

可以回到：

- `manual-import`
- `import-candidates`

修正。

## 推荐流程

推荐顺序：

1. `extract candidates`
2. `import candidates`
3. `manual-import` 补 `main_reference_url`
4. `reference-coverage-report`
5. `image-prompts`
6. manual image generation

## 示例返回关注点

重点字段：

- `character_refs_found`
- `scene_ref_found`
- `prop_refs_found`
- `missing_character_asset_keys`
- `missing_scene_asset_key`
- `missing_prop_asset_keys`
- `assets_missing_reference_url`
- `ready_for_reference_guided_image`
- `warnings`
- `suggestions`
- `next_action`

## next_action 含义

- `extract_or_manual_import_assets`
  - 资产库基本还是空的
- `review_missing_asset_keys`
  - shot 绑定了不存在的 key
- `complete_reference_urls`
  - 资产存在，但还缺 `main_reference_url`
- `bind_reference_assets_to_shots`
  - 资产库已有内容，但大量 shot 还没真正绑定
- `ready_for_reference_guided_image_generation`
  - 可以安全进入带参考素材的手动生图或后续 reference-guided 生成
