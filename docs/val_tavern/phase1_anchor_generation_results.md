# 《瓦酒馆》第一阶段锚点资产生成结果

## 1. 执行概览

- 本批次目标：为第一阶段第一批 5 个锚点资产生成候选图，并选择每类资产 1 张作为推荐锚点。
- 生成资产数量：5
- 候选图总数：10
- 推荐锚点数量：5
- 生成方式：使用内置 imagegen 工具生成，不使用真实官方 LOGO，不声称官方授权。

## 2. 各资产结果

### 2.1 瓦叔

- 生成文件：
  - `asset_library/val_tavern/generated/anchors/washu/VG_CHAR_WASHU_fullbody_default_v1.png`
  - `asset_library/val_tavern/generated/anchors/washu/VG_CHAR_WASHU_fullbody_default_v2.png`
- 推荐文件：`asset_library/val_tavern/generated/anchors/washu/VG_CHAR_WASHU_fullbody_default_v2.png`
- 选择原因：
  - 角色轮廓清晰，Q版比例更适合作为锚点。
  - 机械义手和发光酒杯辨识度高。
  - 暖色赛博酒馆气质明确。
  - 背景相对简洁，便于后续统一参考。
- 备注：可作为瓦叔后续半身表情、今日特调动作和封面主视觉参考。

### 2.2 皮蛋

- 生成文件：
  - `asset_library/val_tavern/generated/anchors/pidan/VG_CHAR_PIDAN_action_delivery_v1.png`
  - `asset_library/val_tavern/generated/anchors/pidan/VG_CHAR_PIDAN_action_delivery_v2.png`
- 推荐文件：`asset_library/val_tavern/generated/anchors/pidan/VG_CHAR_PIDAN_action_delivery_v2.png`
- 选择原因：
  - 更接近参考图的圆滚滚原创吉祥物方向。
  - 黄色主体、护目镜和小围裙辨识度清晰。
  - 托盘、发光饮品和空白账单区域更适合复用。
  - 背景不抢主体，适合作为后续跑堂动作参考。
- 备注：本次已按参考图重生成皮蛋候选，后续可继续派生举牌、递账单和右下角封面小图标版本。

### 2.3 捷风

- 生成文件：
  - `asset_library/val_tavern/generated/anchors/jett/VG_CHAR_JETT_halfbody_datacomment_v1.png`
  - `asset_library/val_tavern/generated/anchors/jett/VG_CHAR_JETT_halfbody_datacomment_v2.png`
- 推荐文件：`asset_library/val_tavern/generated/anchors/jett/VG_CHAR_JETT_halfbody_datacomment_v2.png`
- 选择原因：
  - 更贴近参考图的夜色赛博酒馆坐姿氛围。
  - 白发、冷饮杯和数据平板同时保留，角色定位清晰。
  - 冷色风效与粉橙霓虹形成稳定视觉语言。
  - 适合作为数据拆台、封面和对话镜头锚点。
- 备注：本次已按参考图重生成捷风候选，可作为靠窗位、数据拆台、平板 UI 交互镜头的角色参考。

### 2.4 今日特调牌

- 生成文件：
  - `asset_library/val_tavern/generated/anchors/specialdrink_sign/VG_PROP_specialdrink_sign_v1.png`
  - `asset_library/val_tavern/generated/anchors/specialdrink_sign/VG_PROP_specialdrink_sign_v2.png`
- 推荐文件：`asset_library/val_tavern/generated/anchors/specialdrink_sign/VG_PROP_specialdrink_sign_v2.png`
- 选择原因：
  - 中心可替换文字区域更干净。
  - 霓虹边框和道具轮廓清晰。
  - 装饰信息较少，复用性更强。
  - 适合放入吧台场景和金句卡模板。
- 备注：适合后续做“今日特调”结尾金句图和瓦叔手持版二次生成参考。

### 2.5 瓦酒馆吧台全景

- 生成文件：
  - `asset_library/val_tavern/generated/anchors/bar_fullview/VG_SCENE_bar_fullview_v1.png`
  - `asset_library/val_tavern/generated/anchors/bar_fullview/VG_SCENE_bar_fullview_v2.png`
- 推荐文件：`asset_library/val_tavern/generated/anchors/bar_fullview/VG_SCENE_bar_fullview_v2.png`
- 选择原因：
  - 竖屏构图更清晰，吧台视觉中心稳定。
  - 前景留白更大，适合后续角色合成。
  - 今日特调菜单、吧台、酒瓶和墙面装饰齐全。
  - 暖色赛博酒馆氛围统一且不过度杂乱。
- 备注：后续可作为开场、群像互怼和角色站位的主场景参考。

## 3. 当前确定的正式锚点

| 资产名称 | 推荐文件 | 后续用途 |
| --- | --- | --- |
| 瓦叔 | `asset_library/val_tavern/generated/anchors/washu/VG_CHAR_WASHU_fullbody_default_v2.png` | 主角色参考、今日特调收尾、封面主视觉 |
| 皮蛋 | `asset_library/val_tavern/generated/anchors/pidan/VG_CHAR_PIDAN_action_delivery_v2.png` | 吉祥物参考、跑堂动作、举牌动作派生 |
| 捷风 | `asset_library/val_tavern/generated/anchors/jett/VG_CHAR_JETT_halfbody_datacomment_v2.png` | 数据拆台角色参考、靠窗复盘镜头 |
| 今日特调牌 | `asset_library/val_tavern/generated/anchors/specialdrink_sign/VG_PROP_specialdrink_sign_v2.png` | 收尾金句道具、模板角标、吧台常驻装饰 |
| 瓦酒馆吧台全景 | `asset_library/val_tavern/generated/anchors/bar_fullview/VG_SCENE_bar_fullview_v2.png` | 主场景锚点、竖屏分镜背景、角色合成参考 |

## 4. 下一批扩展建议

建议下一批扩展：

- 火男
- 奶妈
- 奇乐
- 幽影
- 吧台中景
- 靠窗位
- 角落位
- 账单
- 皮蛋举牌板
- 捷风数据平板
