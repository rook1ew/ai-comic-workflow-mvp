# NARRATIVE_STRUCTURE_LITE

## Why Lite first

For a 30–60 second AI short comic episode, the common shot count is only about:

- 3 shots
- 5 shots
- 8 shots

If we immediately introduce heavy formal tables such as:

- `Segment`
- `ScriptScene`
- `ScriptBeat`
- `StoryboardGroup`

the workflow becomes too heavy for short-form production.

So v0.5-A uses a Lite structure first.

## Lite storage model

This version does **not** introduce formal new narrative tables.

Instead it stores lightweight JSON in:

- `Episode.metadata_json.story_source`
- `Episode.metadata_json.source_text_hash`
- `Episode.metadata_json.narrative_structure`
- `Shot.metadata_json.segment_key`
- `Shot.metadata_json.beat_key`
- `Shot.metadata_json.storyboard_group_key`

This keeps the production path backward-compatible and cheap to evolve.

## Story Source

Use:

- `POST /projects/{project_id}/episodes/{episode_id}/story-source`
- `GET /projects/{project_id}/episodes/{episode_id}/story-source`

Purpose:

- save the raw story intake
- save genre / audience / tone / manual notes
- mark that the project has entered creative preproduction

The backend also stores:

- `source_text_hash`
- `analysis_status = story_source_added`

FastAPI does not generate the story. It only stores it.

## Narrative Structure Lite

Use:

- `POST /projects/{project_id}/episodes/{episode_id}/narrative-structure-lite`
- `GET /projects/{project_id}/episodes/{episode_id}/narrative-structure-lite`

Purpose:

- accept lightweight structure from Coze, manual work, or another upstream AI
- save:
  - `segments`
  - `beats`
  - `storyboard_groups`
  - `source`
  - `manual_notes`

FastAPI does not generate the structure. It only stores and returns it.

## Storyboard Package

Use:

- `POST /coze/project/{project_id}/storyboard-package`

This is a lightweight alias of storyboard import and now supports shot-level
linkage fields:

- `segment_key`
- `beat_key`
- `storyboard_group_key`

These keys are saved into `Shot.metadata_json`.

If the key cannot be resolved inside the saved narrative structure:

- the import still succeeds
- the response returns soft warnings

## Three complexity levels

### Lite

- `Episode`
- `Shot`
- shot-level `segment_key / beat_key / storyboard_group_key`

Best for:

- 3–10 shot short episodes
- fast iteration
- manual production workflows

### Standard

- `Episode`
- `Segment`
- `Shot`

Useful when segments start to matter operationally.

### Pro

- `Episode`
- `Segment`
- `ScriptScene`
- `Beat`
- `StoryboardGroup`
- `Shot`

Best when the project becomes large enough to justify heavier formal structure.

## Coze vs FastAPI responsibilities

### Coze / upstream AI

Can generate:

- story ideas
- story source text
- segment ideas
- beat ideas
- storyboard group ideas
- storyboard shot packages

### FastAPI

Handles:

- storage
- validation
- soft warnings
- project-level status
- production exports

FastAPI does **not** directly call a real LLM in this Lite flow.

## How it connects to the existing production pipeline

Recommended flow:

1. add `story-source`
2. save `narrative-structure-lite`
3. import `storyboard-package`
4. prepare `visual-asset-library`
5. run `reference-coverage-report`
6. export `image-prompts`
7. generate storyboard images manually
8. use `storyboard-production-board`
9. continue into editing / manual delivery flow

## Example structure

```json
{
  "segments": [
    {
      "segment_key": "opening_hook",
      "title": "深夜敲门",
      "segment_type": "opening_hook",
      "summary": "沈知夏在旧公寓卧室被急促敲门声惊醒。",
      "target_duration_sec": 10,
      "shot_ids": ["SH01"]
    }
  ],
  "beats": [
    {
      "beat_key": "urgent_knock",
      "title": "急促敲门",
      "beat_type": "fear_trigger",
      "summary": "门外敲门声打破深夜安全感。",
      "emotion": "alarm",
      "conflict": "安全睡眠被未知入侵打破",
      "shot_ids": ["SH01"]
    }
  ],
  "storyboard_groups": [
    {
      "group_key": "opening_group",
      "title": "开场钩子分镜组",
      "summary": "用一个镜头建立深夜敲门恐惧。",
      "segment_key": "opening_hook",
      "beat_key": "urgent_knock",
      "shot_ids": ["SH01"]
    }
  ],
  "manual_notes": "",
  "source": "coze"
}
```
