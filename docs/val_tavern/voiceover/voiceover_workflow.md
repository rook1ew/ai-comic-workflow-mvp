# 《炼狱酒馆》AI 配音工作流

## 1. 工作流目标

- 为《炼狱酒馆》建立固定角色配音流程。
- 第一阶段优先使用剪映 / CapCut 的 AI 文本朗读完成配音。
- Codex 负责生成配音台词、分轨表、音色说明和时间轴。
- 剪辑软件负责实际生成音频并对齐视频。
- 中后期可接入 ElevenLabs 或其他 TTS API。
- 不使用任何官方游戏角色原声。
- 不使用 LOL 酒桶古拉加斯原音频。
- 所有声音必须是原创 AI 配音或授权音色。

## 2. 标准流程

1. 根据 episode 脚本拆分台词。
2. 按角色生成 voiceover line seed。
3. 每一句单独生成音频，不整集一次性生成。
4. 每个角色使用固定音色方向。
5. 导出分轨音频。
6. 放入剪辑时间线。
7. 调整音量、语速和停顿。
8. 加 BGM 和音效。
9. 导出 first cut。
10. 记录使用音色和音频路径。

## 3. 剪映 / CapCut 手动配音流程

- 打开剪映。
- 导入 6 段 SeedDance 视频。
- 按时间线排列。
- 使用“文本 → 新建文本 → 文本朗读 / AI 配音”。
- 每句单独生成，不要整集一次性生成。
- 生成后把音频拖到对应视频段下。
- 如果文本框影响画面，可以隐藏文本或移出画面。
- 配音完成后再加 BGM 和音效。

## 4. ElevenLabs 可选自动配音流程

- ElevenLabs 可作为中后期 TTS provider。
- 使用 `voice_id` 指定每个角色音色。
- 使用 `model_id` 选择 TTS 模型。
- 每条 line 单独请求生成。
- 输出 mp3 或 wav。
- 记录 request 参数。
- 不在仓库提交 API key。
- API key 只能放在 `.env`。
- 当前阶段只保留接口结构，不真实调用。

## 5. 配音文件命名规范

建议命名：

```text
EP01_CLIP01_WASHU_001_opening.wav
EP01_CLIP01_PIDAN_001_special.wav
EP01_CLIP02_SAGE_001_complain.wav
EP01_CLIP03_REYNA_001_kda_reply.wav
EP01_CLIP03_JETT_001_roast.wav
EP01_CLIP04_OMEN_001_roast.wav
```

字段说明：

- `episode`：集数，例如 `EP01`。
- `clip`：对应视频片段，例如 `CLIP03`。
- `role`：角色英文代号，例如 `REYNA`。
- `line number`：该角色或该 clip 内的台词序号。
- `semantic label`：台词语义标签，例如 `kda_reply`。

## 6. 混音建议

- 人声最大。
- BGM 只做氛围。
- 音效用于卡点和强化笑点。
- 手机外放必须听清人声。

建议音量：

- 角色配音：100%
- BGM：20%–30%
- 音效：50%–70%
- 环境声：10%–20%
