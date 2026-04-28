# Visual Asset Library

## 什么是 Visual Asset Library

Visual Asset Library 是项目级的轻量参考素材库，用来管理三类长期复用的视觉参考：

1. 角色参考包 `character reference packs`
2. 场景参考包 `scene reference packs`
3. 道具参考包 `prop reference packs`

当前版本只做 JSON 数据结构和导出，不做：
- 文件上传
- 图库 UI
- 真实 Image2 API 调用
- 真实 Seedance API 调用

它的目标是：在长篇漫剧、多集连载、多人协作时，尽量保证角色、场景、道具的一致性。

## 为什么三类都需要参考包

### 角色参考包

用于约束：
- 脸型
- 发型
- 服装
- 体型比例
- 表情参考
- 口型参考

适合：
- 手动生图
- 拼帧剪辑
- 后续真实图像生成前的角色一致性约束

### 场景参考包

用于约束：
- 固定空间布局
- 门口角度 / 桌面角度 / 反打角度
- 灯光和环境风格

适合：
- 办公室
- 会议室
- 家庭客厅
- 医院走廊
- 校园教室

### 道具参考包

用于约束：
- 工牌
- 文件夹
- 手机
- 电脑
- 茶杯

适合避免同一个道具在不同镜头中形状、颜色、风格反复漂移。

## 数据结构

当前存储在：

- `Project.visual_asset_library_json`

推荐结构：

```json
{
  "characters": [
    {
      "asset_key": "lin_wan",
      "name": "林晚",
      "role": "lead",
      "main_reference_url": "file:///D:/AI漫剧角色库/LinWan_main.png",
      "turnaround_urls": {
        "front": "file:///D:/AI漫剧角色库/LinWan_front.png",
        "three_quarter": "file:///D:/AI漫剧角色库/LinWan_3q.png",
        "side": "file:///D:/AI漫剧角色库/LinWan_side.png"
      },
      "expression_urls": {
        "calm": "file:///D:/AI漫剧角色库/LinWan_calm.png",
        "nervous": "file:///D:/AI漫剧角色库/LinWan_nervous.png",
        "shocked": "file:///D:/AI漫剧角色库/LinWan_shocked.png"
      },
      "mouth_shape_urls": {
        "closed": "file:///D:/AI漫剧角色库/LinWan_mouth_closed.png",
        "talking": "file:///D:/AI漫剧角色库/LinWan_talking.png"
      },
      "must_keep": [
        "same face shape",
        "same hairstyle",
        "same outfit",
        "same body proportion"
      ],
      "avoid": [
        "celebrity likeness",
        "known anime character",
        "changed hairstyle",
        "changed outfit"
      ]
    }
  ],
  "scenes": [
    {
      "asset_key": "meeting_room_a",
      "name": "会议室A",
      "main_reference_url": "file:///D:/AI漫剧场景库/meeting_room_a_main.png",
      "angle_urls": {
        "door_angle": "file:///D:/AI漫剧场景库/meeting_room_a_door.png",
        "table_angle": "file:///D:/AI漫剧场景库/meeting_room_a_table.png",
        "reverse_angle": "file:///D:/AI漫剧场景库/meeting_room_a_reverse.png"
      },
      "must_keep": [
        "long conference table",
        "gray glass wall",
        "black office chairs",
        "modern corporate lighting"
      ],
      "avoid": [
        "luxury palace style",
        "classroom layout",
        "fantasy background"
      ]
    }
  ],
  "props": [
    {
      "asset_key": "employee_badge",
      "name": "员工工牌",
      "main_reference_url": "file:///D:/AI漫剧道具库/employee_badge_main.png",
      "variant_urls": {
        "close_up": "file:///D:/AI漫剧道具库/employee_badge_closeup.png",
        "on_chest": "file:///D:/AI漫剧道具库/employee_badge_chest.png"
      },
      "must_keep": [
        "blue strap",
        "white ID card",
        "corporate badge style"
      ],
      "avoid": [
        "school badge",
        "fantasy medal",
        "random logo"
      ]
    }
  ]
}
```

## shot 如何引用 reference assets

在 storyboard shot 中，可以使用这些可选字段：

- `character_asset_keys: string[]`
- `scene_asset_key: string`
- `prop_asset_keys: string[]`

示例：

```json
{
  "shot_id": "SH01",
  "character": "林晚",
  "location": "会议室A",
  "character_asset_keys": ["lin_wan"],
  "scene_asset_key": "meeting_room_a",
  "prop_asset_keys": ["employee_badge"]
}
```

这些字段会保存到：

- `Shot.metadata_json`

它们不会替代已有字段，只是补充引用关系。

## image-prompts 如何使用这些 reference assets

`GET /projects/{project_id}/image-prompts` 现在会返回：

- `character_asset_keys`
- `scene_asset_key`
- `prop_asset_keys`
- `visual_asset_refs`

同时，`copy_ready_prompt` 会追加简短参考说明，例如：

- Recommended character reference
- Recommended scene reference
- Recommended prop reference
- Must keep
- Avoid

目的是让人工生图时更容易复制到 ChatGPT 或其他工具中使用。

## editing-shot-board 如何使用这些 reference assets

`GET /projects/{project_id}/editing-shot-board` 会回显：

- `character_asset_keys`
- `scene_asset_key`
- `prop_asset_keys`
- `visual_asset_refs`

这样在剪辑阶段，执行人员能一眼看到当前镜头应该参考哪套角色、场景、道具素材。

## 拼帧漫剧中如何使用

推荐工作流：

1. 先在项目级准备 `visual_asset_library_json`
2. 在 storyboard shot 中引用 `character_asset_keys / scene_asset_key / prop_asset_keys`
3. 用 `image-prompts` 导出带参考说明的手动生图提示词
4. 回填图片素材
5. 用 `editing-shot-board / editing-timeline / editing-cue-sheet` 做剪辑施工

这样能显著降低：
- 角色脸漂移
- 场景角度乱变
- 道具造型不一致

## 当前校验规则

在 `POST /coze/project/validate-payload` 中：

- `visual_asset_library_json` 如果存在，必须是 object
- `characters / scenes / props` 如果存在，必须是 array
- `shot.character_asset_keys` 如果存在，必须是 array
- `shot.scene_asset_key` 如果存在，必须是 string
- `shot.prop_asset_keys` 如果存在，必须是 array
- 如果 shot 引用了不存在的 `asset_key`，当前只给 warning，不直接阻塞 full-demo-flow

## 示例文件

- [coze_urban_reversal_3shot_visual_assets_payload.json](/C:/Users/29964/Documents/GitHub/ai-comic-workflow-mvp-git/examples/coze_urban_reversal_3shot_visual_assets_payload.json)

## 相关接口

- `GET /projects/{project_id}/visual-asset-library`
- `GET /projects/{project_id}/image-prompts`
- `GET /projects/{project_id}/editing-shot-board`
- `GET /projects/{project_id}/editing-cue-sheet`

## 与 Creative Bible 和 image prompt builder 的关系

在 v0.4-F 之后，Visual Asset Library 不再只是“参考图清单”，而是直接参与：

- `image-prompts` 的 production-grade `copy_ready_prompt`
- `editing-shot-board` 的镜头执行信息
- 惊悚悬疑题材下的角色、场景、道具一致性约束

`image-prompts` 会自动提取：

- Recommended character reference
- Recommended scene reference
- Recommended prop reference
- Must keep
- Avoid

建议把 Visual Asset Library 和 Creative Bible 一起维护：

- Creative Bible 负责角色内核、恐惧节奏、镜头功能
- Visual Asset Library 负责视觉一致性
- storyboard shot 负责把两者绑定到具体镜头

## 新增：手动导入与候选提取

当前 Visual Asset Library 支持两种来源：

1. 手动导入
2. 自动提取候选资产，再人工确认导入

### 手动导入

接口：

- `POST /projects/{project_id}/visual-asset-library/manual-import`

适合场景：

- 你已经有人物、场景、道具参考图
- 只想把 URL 和一致性规则登记进项目库

### 自动提取候选资产

接口：

- `POST /projects/{project_id}/visual-asset-candidates/extract`

适合场景：

- 你先写了角色、剧本、分镜
- 还没系统整理素材库
- 想让系统先提取候选角色 / 场景 / 道具，再人工筛选

注意：

- candidates 不会直接强制入库
- 需要人工 review 后，再调用：
  - `POST /projects/{project_id}/visual-asset-library/import-candidates`

### 推荐流程

1. 先 `extract candidates`
2. `import candidates`
3. 用 `manual-import` 补 `main_reference_url / must_keep / avoid`
4. 跑 `reference-coverage-report`
5. 再进入 `image-prompts`

## Reference Coverage Report

新增：

- `GET /projects/{project_id}/reference-coverage-report`

用途：

- 在生图前检查每个 shot 的角色 / 场景 / 道具参考覆盖情况
- 检查绑定的 `asset_key` 是否真实存在
- 检查资产是否缺 `main_reference_url`
- 判断哪些 shot 已经适合进入 `reference-guided image generation`

注意：

- 它默认只返回 `warnings / suggestions`
- 不会因为缺参考就直接阻塞旧流程
- 更适合做长篇漫剧的一致性巡检
2. 人工 review candidates
3. 补 `main_reference_url`
4. 再 `import candidates`
5. 最后去跑 `image-prompts`
