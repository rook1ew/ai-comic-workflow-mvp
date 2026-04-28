# Character Appearance Layer Lite

v0.5-B adds a lightweight layer for managing multiple visual versions of the same character.

## Three Layers

`Character` means who the person is: name, role, personality, voice, and core profile.

`CharacterAppearance` means what this character looks like in one visual version, such as a design sheet, clean main reference, fullbody front, face detail, outfit detail, expression reference, costume version, special state, or mirror double.

`Visual Asset Library` character assets are the prompt-facing visual anchors used by image generation and production boards.

## Why One URL Is Not Enough

Longer AI comic drama production needs stable character continuity. A single `main_reference_url` is useful, but it cannot represent every production need:

- design sheet for the full appearance bible
- clean main reference for storyboard image generation
- face detail for close-ups
- fullbody reference for body proportion
- outfit detail for consistent clothing
- special state or mirror double variants

The Character Appearance Layer organizes these references without file upload, automatic cropping, gallery UI, or real provider calls.

## Data Structure

`CharacterAppearance` stores:

- `project_id`
- `character_id`
- `appearance_key`
- `appearance_type`
- `title`
- `description`
- `image_url`
- `is_selected`
- `order_index`
- `change_reason`
- `must_keep_json`
- `avoid_json`
- `metadata_json`

Recommended `appearance_type` values:

- `design_sheet`
- `main_reference`
- `fullbody_front`
- `fullbody_side`
- `fullbody_back`
- `face_detail`
- `outfit_detail`
- `expression`
- `action_pose`
- `costume_version`
- `special_state`
- `mirror_double`

## Selecting the Main Appearance

Selecting an appearance:

- sets the selected appearance to `is_selected=true`
- sets other appearances under the same character to `is_selected=false`
- updates `Character.main_reference_url`
- updates the matching Visual Asset Library character asset when found

The Visual Asset Library character entry can then include:

- `selected_appearance_key`
- `selected_appearance_url`
- `appearances_count`

## API Flow

1. Create or upsert appearances with `POST /projects/{project_id}/characters/{character_id}/appearances`.
2. Read appearances with `GET /projects/{project_id}/characters/{character_id}/appearances`.
3. Select the active appearance with `POST /projects/{project_id}/characters/{character_id}/appearances/{appearance_key}/select`.
4. Review project readiness with `GET /projects/{project_id}/character-appearance-summary`.

## Shen Zhixia Example

```json
{
  "appearance_key": "shen_zhixia_design_sheet",
  "appearance_type": "design_sheet",
  "title": "Shen Zhixia design sheet",
  "description": "Multi-view master design with front, side, back, face, and outfit details.",
  "image_url": "file:///D:/AI-comic-characters/ShenZhixia_design_sheet.png",
  "is_selected": false,
  "order_index": 1,
  "change_reason": "initial character design sheet",
  "must_keep": [
    "straight black hair",
    "soft homewear silhouette",
    "tired sensitive eyes"
  ],
  "avoid": [
    "changed hairstyle",
    "celebrity likeness",
    "known anime character"
  ]
}
```

## Production Notes

- This layer does not upload files.
- This layer does not crop design sheets automatically.
- If a design sheet contains multiple views, crop or export the useful parts externally, then register each result as a separate `CharacterAppearance`.
- No real Image2, Seedance, or LLM call is made.
