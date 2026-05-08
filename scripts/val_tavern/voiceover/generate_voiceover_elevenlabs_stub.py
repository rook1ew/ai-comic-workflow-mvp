"""Generate a voiceover manifest from the EP01 line seed.

This is a stub only. It does not call ElevenLabs or any other TTS API, does not
require an API key, and does not generate audio. Later, this file can be
extended to call ElevenLabs TTS per line using a voice_id and model_id.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SEED_PATH = ROOT / "data/val_tavern/voiceover/ep01_voiceover_lines.seed.json"
MANIFEST_PATH = ROOT / "data/val_tavern/voiceover/ep01_voiceover_generation_manifest.json"


def main() -> None:
    lines = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    manifest = []

    seen = set()
    for item in lines:
        line_id = item.get("line_id")
        text = item.get("text")
        character = item.get("character")
        output_filename = item.get("output_filename")

        if not line_id or line_id in seen:
            raise ValueError(f"Invalid or duplicated line_id: {line_id!r}")
        seen.add(line_id)
        if not text:
            raise ValueError(f"{line_id} is missing text")
        if not character:
            raise ValueError(f"{line_id} is missing character")
        if not output_filename:
            raise ValueError(f"{line_id} is missing output_filename")

        manifest.append(
            {
                "line_id": line_id,
                "episode_id": item.get("episode_id"),
                "clip_id": item.get("clip_id"),
                "character": character,
                "voice_profile": item.get("voice_profile"),
                "text": text,
                "target_duration_seconds": item.get("target_duration_seconds"),
                "recommended_speed": item.get("recommended_speed"),
                "provider": "elevenlabs_stub",
                "model_id": "TODO_MODEL_ID",
                "voice_id": "TODO_VOICE_ID",
                "request_payload_preview": {
                    "text": text,
                    "model_id": "TODO_MODEL_ID",
                    "voice_settings": {
                        "stability": "TODO",
                        "similarity_boost": "TODO"
                    }
                },
                "output_path": f"asset_library/val_tavern/generated/episodes/ep01/voiceover/{output_filename}",
                "status": "pending_tts"
            }
        )

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(manifest)} manifest items to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
