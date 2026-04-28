# VISUAL_ASSET_LIBRARY

## What it is

Visual Asset Library is the lightweight project-level reference library for:

- characters
- scenes
- props

It lives in:

- `Project.visual_asset_library_json`

The goal is not file hosting or gallery UI. The goal is reference consistency
for long-form AI comic drama production.

## Core structure

The library is grouped into:

- `characters`
- `scenes`
- `props`

Each item can include:

- `asset_key`
- `name`
- `main_reference_url`
- `selected_appearance_key`
- `selected_appearance_url`
- `appearances_count`
- `must_keep`
- `avoid`

Characters may also carry extra role or profile notes when available. Scenes
and props may carry more specific structure fields, but the minimum stable
contract is still the same: key, name, reference URL, keep rules, avoid rules.

## Character Appearance compatibility

v0.5-B adds a lightweight `CharacterAppearance` layer. Visual Asset Library character assets remain the prompt-facing visual anchors, but they can now be linked to the currently selected character appearance.

When an appearance is selected through `POST /projects/{project_id}/characters/{character_id}/appearances/{appearance_key}/select`, the system updates:

- `Character.main_reference_url`
- matching `visual_asset_library_json.characters[].main_reference_url`
- `selected_appearance_key`
- `selected_appearance_url`
- `appearances_count`

This keeps old projects compatible while allowing richer character reference management.

## How shots reference the library

Shots can bind library entries through `Shot.metadata_json`:

- `character_asset_keys`
- `scene_asset_key`
- `prop_asset_keys`

These references are then consumed by:

- `reference-coverage-report`
- `image-prompts`
- `editing-shot-board`
- `storyboard-production-board`

## Read and maintenance endpoints

### `GET /projects/{project_id}/visual-asset-library`

Read the current library and summary counts.

Enhanced fields include:

- `missing_reference_url_count`
- `assets_without_reference_url`
- `next_action`

Typical `next_action` values:

- `extract_or_manual_import_assets`
- `complete_reference_urls`
- `ready_for_reference_guided_image_generation`

### `POST /projects/{project_id}/visual-asset-library/manual-import`

Manually upsert one character, scene, or prop entry.

Use this when:

- you already have local reference images
- you want to register `main_reference_url`
- you want to fix or enrich one asset without touching the whole library

### `POST /projects/{project_id}/visual-asset-candidates/extract`

Extract candidate visual assets from:

- character records
- storyboard character fields
- storyboard location fields
- prop keys and lightweight prop keyword detection

Candidates are returned for review only. They are not auto-imported into the
formal library.

### `POST /projects/{project_id}/visual-asset-library/import-candidates`

Import reviewed candidates into the formal library with `upsert` behavior.

## Relationship to prompt builders

Two prompt systems now sit on top of the same library:

### `visual-asset-prompts`

Use this to generate:

- character reference images
- scene reference plates
- prop single-object reference images

These prompts are for building the asset library itself.

### `image-prompts`

Use this to generate:

- single-shot storyboard frames

These prompts are for actual episode shots, and they reuse the library as
continuity anchors.

## Recommended production flow

For the current manual production route:

1. `story-source`
2. `narrative-structure-lite`
3. `storyboard-package`
4. `visual-asset-candidates/extract`
5. `visual-asset-library/manual-import` or `import-candidates`
6. `visual-asset-prompts`
7. generate reference images manually
8. update `main_reference_url`
9. `reference-coverage-report`
10. `image-prompts`
11. generate storyboard images

This keeps reference preparation clearly separated from storyboard image
generation, while still letting both stages share one consistent asset library.
