# STORYBOARD_PRODUCTION_BOARD

## 什么是 Storyboard Production Board

`GET /projects/{project_id}/storyboard-production-board` 是一个项目级的专业分镜制作表。

它把现有系统里的几类信息汇总成按 shot 顺序展开的人类可读生产视图：

- shot 基础字段
- 时长与时间范围
- 角色 / 场景 / 道具参考资产
- 分镜图提示词
- 轻运动提示词
- 剪辑备注

它适合创作者、剪辑师、Coze、Codex 或人工运营直接查看每个镜头的完整生产信息。

## 它和其他接口的区别

- `image-prompts`
  - 重点是单镜头分镜图 prompt
- `editing-shot-board`
  - 重点是镜头字段和图片是否到位
- `editing-timeline`
  - 重点是时间线顺序和时间范围
- `editing-cue-sheet`
  - 重点是人类可复制的逐镜头剪辑清单
- `storyboard-production-board`
  - 重点是把上面这些内容整合成一份更像专业分镜制作表的总览

## 为什么需要专业分镜制作表

在“拼帧图片漫剧 / 静态图伪动态剪辑”路线下，团队通常需要同时看到：

- 这个镜头要讲什么
- 这个镜头用哪个角色参考
- 这个镜头用哪个场景参考
- 这个镜头的视觉重点是什么
- 这张图生成完之后，后续要怎么轻动效或剪辑

单独看 `image-prompts`、`editing-shot-board` 或 `editing-cue-sheet` 都能解决局部问题，
但 storyboard production board 更像一张完整施工单。

## 主要字段

- `source_shot_id`
- `time_range`
- `duration`
- `human_shot_description`
- `story_function`
- `conflict_beat`
- `emotion_shift`
- `visual_focus`
- `character_asset_refs`
- `scene_asset_ref`
- `prop_asset_refs`
- `copy_ready_image_prompt`
- `copy_ready_motion_prompt`
- `editing_notes`
- `ready_for_image_generation`
- `ready_for_editing`

## 轻运动提示词说明

`copy_ready_motion_prompt` 不是实际 provider 调用。

它是给这些场景复制使用的轻量运动说明：

- Coze 视频创作
- 剪映
- CapCut
- Premiere
- Seedance 网页端
- 静态图轻动效工具

它会强调：

- use the generated storyboard image as a still frame
- keep movement subtle
- do not change face / hairstyle / outfit
- do not change scene layout
- no face morphing
- no extra limbs

## 推荐使用方式

1. 先准备 storyboard 和 visual asset refs
2. 用 `image-prompts` 生成分镜图提示词
3. 用 `storyboard-production-board` 做最终生图前检查
4. 生图后回填图片
5. 再进入 `editing-shot-board` / `editing-timeline` / `editing-cue-sheet`

## 示例响应片段

```json
{
  "project_id": 18,
  "items_count": 1,
  "total_duration": 4,
  "items": [
    {
      "order": 1,
      "source_shot_id": "SH01",
      "time_range": "0.0s-4.0s",
      "human_shot_description": "深夜旧公寓卧室内，沈知夏被急促敲门声惊醒，手机冷光照亮她疲惫的脸。",
      "story_function": "three-second horror hook",
      "character_asset_refs": [
        {
          "asset_key": "shen_zhixia",
          "name": "沈知夏",
          "main_reference_url": "file:///D:/AI漫剧角色库/ShenZhixia_main.png"
        }
      ],
      "copy_ready_image_prompt": "...",
      "copy_ready_motion_prompt": "...",
      "ready_for_image_generation": true,
      "ready_for_editing": false
    }
  ],
  "next_action": "generate_storyboard_images"
}
```

## v0.5-A Lite narrative linkage

Storyboard Production Board now echoes lightweight narrative structure fields
per shot:

- `segment_key`
- `segment_title`
- `segment_type`
- `beat_key`
- `beat_title`
- `beat_type`
- `storyboard_group_key`
- `storyboard_group_title`

Resolution order:

1. read linkage keys from `Shot.metadata_json`
2. resolve titles and types from `Episode.metadata_json.narrative_structure`

If a linkage key cannot be resolved:

- the board still returns successfully
- unresolved title / type fields stay `null`

`plain_text` may also include lightweight narrative lines such as:

- `段落: 开场钩子`
- `节拍: 急促敲门`
