# VISUAL_ASSET_CANDIDATES

## 什么是 Visual Asset Candidates

Visual Asset Candidates 是“候选参考资产”，不是正式素材库条目。

它们的作用是：

- 从项目里已经写好的内容中，先自动发现可能需要长期复用的角色、场景、道具
- 让人工确认后，再决定是否正式入库

## 为什么不能直接强制入库

自动提取只能看到“像是重要素材”的东西，但不能替代人工判断：

- 名称是否准确
- `asset_key` 是否统一
- 这个对象是否真的值得做长期参考包
- `main_reference_url` 是否已经准备好
- `must_keep / avoid` 是否已经想清楚

所以 candidates 只做“建议”，不直接改正式库。

## 手动导入 vs 自动提取

### 手动导入

适合：

- 你已经准备好了角色图、场景图、道具图
- 只想直接登记到项目库

接口：

- `POST /projects/{project_id}/visual-asset-library/manual-import`

### 自动提取

适合：

- 你先写了角色、剧本、分镜
- 还没来得及系统整理素材库
- 想先让系统找出候选角色 / 场景 / 道具

接口：

- `POST /projects/{project_id}/visual-asset-candidates/extract`

## 自动提取规则

### 角色候选

来自：

- Character records
- `storyboard.character`
- `storyboard.character_asset_keys`

### 场景候选

来自：

- `storyboard.location`
- `storyboard.scene_asset_key`

### 道具候选

来自：

- `storyboard.prop_asset_keys`
- `core_action / image_prompt / dialogue` 的轻量关键词规则

当前内置的常见道具关键词包括：

- smartphone / phone / 手机
- peephole / 猫眼
- door lock / 门锁
- badge / 工牌
- folder / 文件夹
- contract / 合同
- invitation / 邀请函
- champagne / 香槟

## 推荐流程

1. `POST /projects/{project_id}/visual-asset-candidates/extract`
2. review candidates
3. 补 `main_reference_url`
4. 调整 `asset_key / name / must_keep / avoid`
5. `POST /projects/{project_id}/visual-asset-library/import-candidates`
6. `GET /projects/{project_id}/visual-asset-library`
7. 再进入 `image-prompts`

## 示例：提取 candidates

请求：

```text
POST /projects/{project_id}/visual-asset-candidates/extract
```

响应：

```json
{
  "project_id": 1,
  "characters": [
    {
      "asset_key": "shen_zhixia",
      "name": "沈知夏",
      "asset_type": "character",
      "reason": "character appears in storyboard shots",
      "source": "storyboard.character",
      "suggested_main_reference_url": "",
      "must_keep": [],
      "avoid": [],
      "already_in_library": false
    }
  ],
  "scenes": [],
  "props": [],
  "next_action": "review_candidates_before_import"
}
```

## 示例：导入 candidates

请求：

```json
{
  "characters": [
    {
      "asset_key": "shen_zhixia",
      "name": "沈知夏",
      "main_reference_url": "file:///D:/AI漫剧角色库/ShenZhixia_main.png",
      "must_keep": ["same face shape", "same hairstyle"],
      "avoid": ["celebrity likeness", "known anime character"]
    }
  ],
  "scenes": [],
  "props": [],
  "merge_mode": "upsert"
}
```

响应：

```json
{
  "project_id": 1,
  "characters_count": 1,
  "scenes_count": 0,
  "props_count": 0,
  "imported_count": 1,
  "updated_count": 0,
  "next_action": "ready_for_reference_guided_image_generation"
}
```
