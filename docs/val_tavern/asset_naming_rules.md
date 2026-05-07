# 《瓦酒馆》资产统一命名规则

## 命名格式

```text
[PROJECT]_[CATEGORY]_[SUBJECT]_[TYPE]_[VERSION]
```

## 字段说明

| 字段 | 说明 | 示例 |
| --- | --- | --- |
| PROJECT | 项目缩写，固定使用 `VG` | `VG` |
| CATEGORY | 资产分类缩写 | `CHAR`、`PROP`、`SCENE` |
| SUBJECT | 资产主体，使用英文或拼音关键词 | `WASHU`、`specialdrink`、`bar` |
| TYPE | 资产类型、动作、镜头或用途 | `fullbody_default`、`action_delivery`、`fullview` |
| VERSION | 版本号，从 `v1` 开始 | `v1` |

## 分类缩写

| 缩写 | 含义 | 用途 |
| --- | --- | --- |
| CHAR | character | 角色资产 |
| PROP | prop | 道具资产 |
| SCENE | scene | 场景资产 |
| TEMPLATE | template | 模板资产 |
| GAG | gag asset | 梗道具或梗图形资产 |
| DECOR | decoration asset | 背景装饰资产 |

> 当前推荐优先使用 `PROP_gag_*` 和 `PROP_decor_*` 表达梗道具与装饰道具，便于统一归入 props 目录；如后续资产管理系统支持更多分类，再拆分为 `GAG`、`DECOR` 独立分类。

## 示例

| 资产 | 命名示例 |
| --- | --- |
| 瓦叔默认全身 | `VG_CHAR_WASHU_fullbody_default_v1` |
| 皮蛋送酒动作 | `VG_CHAR_PIDAN_action_delivery_v1` |
| 今日特调牌 | `VG_PROP_specialdrink_sign_v1` |
| 嘴硬检测器 | `VG_PROP_gag_hardmouthmeter_v1` |
| 酒馆吧台全景 | `VG_SCENE_bar_fullview_v1` |

## 书写规则

- 使用半角英文下划线 `_` 分隔字段。
- 版本号使用小写 `v` 加数字，例如 `v1`、`v2`。
- 角色主体建议使用稳定英文代号：`WASHU`、`PIDAN`、`JETT`、`PHOENIX`、`SAGE`、`KILLJOY`、`OMEN`。
- 道具与场景主体使用小写英文关键词，多个词用下划线连接。
- 不在文件名中使用中文、空格、特殊符号或真实官方 LOGO 名称。
- 文件名只描述资产内容，不写生产状态；状态交给任务系统维护。
