# EDITING_STORYBOARD_FIELDS

## 目标

这份文档说明 v0.4-A 新增的轻量剪辑分镜字段。

这些字段的定位是：

- 不改变现有核心数据结构
- 优先保存在 `Shot.metadata_json`
- 让 storyboard 不只用于出图和视频 prompt，还能直接指导拼帧漫剧剪辑

## 当前支持的字段

这些字段都可以出现在 `storyboard_json.shots[]` 中：

- `shot_type`
- `camera_motion`
- `subject_motion`
- `transition`
- `subtitle_text`
- `sfx`
- `editing_notes`

它们都是可选字段。

如果没有这些字段：

- 旧 storyboard import 仍然可用
- 旧 full-demo-flow 仍然可用
- 旧 payload 不需要修改

## 字段含义

### `shot_type`

镜头类型。

常见值：

- `dialogue`
- `reaction`
- `close_up`
- `transition`
- `reveal`
- `action`

用途：

- 帮助后续判断这个 shot 更偏对白镜头、反应镜头、转场镜头还是动作镜头

### `camera_motion`

镜头运动方式。

常见值：

- `static`
- `slow_push_in`
- `pull_out`
- `pan_left`
- `pan_right`
- `shake`
- `zoom_in`

用途：

- 用于拼帧剪辑时决定镜头怎么动
- 用于 video prompt 中指导镜头移动

### `subject_motion`

主体微动方式。

常见值：

- `blink`
- `mouth_move`
- `slight_body_shift`
- `turn_head`
- `nod`
- `hand_move`

用途：

- 用于静态图伪动态剪辑
- 指导人物微动作，不一定意味着完整动作镜头

### `transition`

镜头转场方式。

常见值：

- `cut`
- `fade`
- `flash`
- `zoom_cut`
- `whip_pan`

用途：

- 给剪辑软件或人工剪辑做转场提示

### `subtitle_text`

字幕提示文本。

用途：

- 用于强调对白、羞辱语句、反转信息
- 可作为后期字幕 cue

### `sfx`

音效提示。

常见值：

- `door_open`
- `chair_scrape`
- `crowd_gasp`
- `flash_hit`

用途：

- 给后期音效或视频 prompt 做提示

### `editing_notes`

自由备注。

用途：

- 补充说明节奏、镜头感、压迫感、反转点或后期注意事项

## 哪些字段更适合拼帧剪辑

最直接服务拼帧图片漫剧 / 静态图伪动态剪辑的字段：

- `camera_motion`
- `subject_motion`
- `transition`
- `subtitle_text`
- `sfx`
- `editing_notes`

## 哪些字段会进入 video prompt

当前会进入 `GET /projects/{project_id}/video-prompts` 返回中的：

- `shot_type`
- `camera_motion`
- `subject_motion`
- `transition`
- `subtitle_text`
- `sfx`
- `editing_notes`

并且会组合进 `copy_ready_video_prompt`。

## payload 填写方式

示例：

```json
{
  "shot_id": "SH01",
  "duration_sec": 3,
  "character": "林夏",
  "location": "会议室门口",
  "core_action": "林夏推门进入会议室",
  "emotion": "紧张",
  "camera": "medium close-up",
  "shot_type": "dialogue",
  "camera_motion": "slow_push_in",
  "subject_motion": "blink",
  "transition": "cut",
  "subtitle_text": "对不起，我走错了。",
  "sfx": "door_open",
  "editing_notes": "镜头轻微推进，营造误入压迫感。",
  "dialogue": "对不起，我走错了。",
  "image_prompt": "都市职场，女主推门进入会议室，紧张表情",
  "video_prompt": "女主推门进入会议室，气氛尴尬",
  "voice_prompt": "紧张地说：对不起，我走错了。",
  "bgm_prompt": "轻微尴尬感的都市职场背景音乐",
  "status": "prompt_ready"
}
```

## 与当前接口的关系

这些字段当前会影响或出现在：

- `POST /coze/project/{project_id}/storyboard`
- `POST /coze/project/full-demo-flow`
- `GET /projects/{project_id}/image-prompts`
- `GET /projects/{project_id}/video-prompts`
- `GET /projects/{project_id}/video-readiness`

## 兼容性说明

- 不新增复杂表结构
- 不要求数据库新增专门字段
- 不影响旧 payload
- 不接真实 Image2 API
- 不接真实 Seedance API
