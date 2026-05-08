from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

REFERENCE_VIDEO = Path(r"D:\瓦酒馆视频素材\EP01_first_cut_v1.mp4")
SILENT_VIDEO = REPO_ROOT / "asset_library/val_tavern/generated/episodes/ep01/edit/exports/VG_EP01_seeddance_first_cut_silent_v1.mp4"
VOICE_SEED = REPO_ROOT / "data/val_tavern/voiceover/ep01_voiceover_lines.seed.json"

LINE_DIR = REPO_ROOT / "asset_library/val_tavern/generated/episodes/ep01/voiceover_lines/reference_v2"
VOICEOVER_WAV = REPO_ROOT / "asset_library/val_tavern/generated/episodes/ep01/edit/project_files/VG_EP01_voiceover_reference_v2.wav"
OUTPUT_VIDEO = REPO_ROOT / "asset_library/val_tavern/generated/episodes/ep01/edit/exports/VG_EP01_seeddance_first_cut_voice_ref_v2.mp4"
RESULT_JSON = REPO_ROOT / "data/val_tavern/voiceover/ep01_voiceover_render_results.json"

TOTAL_DURATION = 41.0

# Source windows are cut from the user-approved reference video. Target starts
# follow the 6-clip edit plan currently used by the EP01 silent first cut.
LINE_TIMINGS = {
    "EP01-VO-001": {"source_start": 2.20, "source_duration": 1.65, "target_start": 0.70},
    "EP01-VO-002": {"source_start": 5.10, "source_duration": 2.30, "target_start": 2.35},
    "EP01-VO-003": {"source_start": 15.05, "source_duration": 2.40, "target_start": 5.30},
    "EP01-VO-004": {"source_start": 17.35, "source_duration": 3.55, "target_start": 7.75},
    "EP01-VO-005": {"source_start": 8.15, "source_duration": 2.65, "target_start": 12.15},
    "EP01-VO-006": {"source_start": 12.05, "source_duration": 1.10, "target_start": 14.95},
    "EP01-VO-007": {"source_start": 13.05, "source_duration": 2.05, "target_start": 16.05},
    "EP01-VO-008": {"source_start": 22.05, "source_duration": 2.20, "target_start": 19.35},
    "EP01-VO-009": {"source_start": 24.55, "source_duration": 2.30, "target_start": 21.55},
    "EP01-VO-010": {"source_start": 27.05, "source_duration": 1.05, "target_start": 23.95},
    "EP01-VO-011": {"source_start": 29.55, "source_duration": 2.45, "target_start": 25.10},
    "EP01-VO-012": {"source_start": 27.85, "source_duration": 1.95, "target_start": 27.20},
    "EP01-VO-013": {"source_start": 34.05, "source_duration": 2.35, "target_start": 28.35},
    "EP01-VO-014": {"source_start": 36.70, "source_duration": 1.95, "target_start": 30.80},
    "EP01-VO-015": {"source_start": 38.10, "source_duration": 1.90, "target_start": 32.80},
    "EP01-VO-016": {"source_start": 39.00, "source_duration": 2.10, "target_start": 34.55},
    "EP01-VO-017": {"source_start": 40.75, "source_duration": 1.50, "target_start": 36.60},
    "EP01-VO-018": {"source_start": 42.35, "source_duration": 1.80, "target_start": 38.45},
}

DEFAULT_FILTER = (
    "highpass=f=80,"
    "lowpass=f=14000,"
    "acompressor=threshold=-18dB:ratio=1.8:attack=5:release=80,"
    "loudnorm=I=-18:TP=-1.8:LRA=10"
)

# User selected Reyna V3: more confident, brighter, stronger attack.
REYNA_V3_FILTER = (
    "asetrate=48000*0.93,aresample=48000,atempo=1.156,"
    "highpass=f=90,"
    "equalizer=f=260:t=q:w=1:g=1.5,"
    "equalizer=f=3600:t=q:w=1:g=2.2,"
    "acompressor=threshold=-17dB:ratio=2.0:attack=5:release=80,"
    "loudnorm=I=-17:TP=-1.5:LRA=9"
)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def ffprobe_duration(path: Path) -> float:
    output = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        cwd=REPO_ROOT,
        text=True,
    )
    return float(output.strip())


def main() -> None:
    if not REFERENCE_VIDEO.exists():
        raise FileNotFoundError(f"Missing reference video: {REFERENCE_VIDEO}")
    if not SILENT_VIDEO.exists():
        raise FileNotFoundError(f"Missing silent video: {SILENT_VIDEO}")
    if not VOICE_SEED.exists():
        raise FileNotFoundError(f"Missing voice seed: {VOICE_SEED}")

    LINE_DIR.mkdir(parents=True, exist_ok=True)
    VOICEOVER_WAV.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    RESULT_JSON.parent.mkdir(parents=True, exist_ok=True)

    seed_lines = json.loads(VOICE_SEED.read_text(encoding="utf-8"))
    seed_by_id = {line["line_id"]: line for line in seed_lines}

    rendered_lines = []
    for line_id in sorted(LINE_TIMINGS):
        seed = seed_by_id[line_id]
        timing = LINE_TIMINGS[line_id]
        out_path = LINE_DIR / seed["output_filename"]
        afilter = REYNA_V3_FILTER if seed["character"] == "芮娜" else DEFAULT_FILTER

        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-ss",
                f'{timing["source_start"]:.3f}',
                "-t",
                f'{timing["source_duration"]:.3f}',
                "-i",
                str(REFERENCE_VIDEO),
                "-vn",
                "-ac",
                "2",
                "-ar",
                "48000",
                "-af",
                afilter,
                str(out_path),
            ]
        )

        rendered_lines.append(
            {
                "line_id": line_id,
                "character": seed["character"],
                "text": seed["text"],
                "source_video": str(REFERENCE_VIDEO),
                "source_start": timing["source_start"],
                "source_duration": timing["source_duration"],
                "target_start": timing["target_start"],
                "output_file": str(out_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "voice_filter": "reyna_v3_official_direction" if seed["character"] == "芮娜" else "reference_loudnorm",
            }
        )

    inputs: list[str] = []
    filter_parts = ["[0:a]volume=0.0[base]"]
    mix_labels = ["[base]"]
    for index, item in enumerate(rendered_lines, start=1):
        wav_path = REPO_ROOT / item["output_file"]
        inputs.extend(["-i", str(wav_path)])
        delay_ms = int(round(item["target_start"] * 1000))
        label = f"a{index}"
        filter_parts.append(f"[{index}:a]adelay={delay_ms}|{delay_ms},volume=1.0[{label}]")
        mix_labels.append(f"[{label}]")

    filter_complex = (
        ";".join(filter_parts)
        + ";"
        + "".join(mix_labels)
        + f"amix=inputs={len(mix_labels)}:duration=longest:normalize=0,"
        + f"atrim=0:{TOTAL_DURATION},asetpts=N/SR/TB,loudnorm=I=-16:TP=-1.5:LRA=10[out]"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-f",
            "lavfi",
            "-t",
            str(TOTAL_DURATION),
            "-i",
            "anullsrc=r=48000:cl=stereo",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            "[out]",
            "-ar",
            "48000",
            str(VOICEOVER_WAV),
        ]
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-i",
            str(SILENT_VIDEO),
            "-i",
            str(VOICEOVER_WAV),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(OUTPUT_VIDEO),
        ]
    )

    result = {
        "render_id": "EP01-VOICEOVER-REF-V2",
        "episode_id": "EP01",
        "source_reference_video": str(REFERENCE_VIDEO),
        "silent_video": str(SILENT_VIDEO.relative_to(REPO_ROOT)).replace("\\", "/"),
        "output_voiceover_wav": str(VOICEOVER_WAV.relative_to(REPO_ROOT)).replace("\\", "/"),
        "output_video": str(OUTPUT_VIDEO.relative_to(REPO_ROOT)).replace("\\", "/"),
        "line_count": len(rendered_lines),
        "video_duration_seconds": round(ffprobe_duration(OUTPUT_VIDEO), 3),
        "audio_duration_seconds": round(ffprobe_duration(VOICEOVER_WAV), 3),
        "reyna_voice_direction": "V3 selected by user: confident, brighter, stronger attack, closer to Reyna reference direction",
        "lines": rendered_lines,
        "status": "completed",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
