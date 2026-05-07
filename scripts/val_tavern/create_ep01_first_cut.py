#!/usr/bin/env python3
"""Create Val Tavern EP01 first cut from still shot images.

This script intentionally uses only repository-relative paths and FFmpeg.
It writes:
- first cut MP4
- SRT subtitle file
- timeline JSON
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WIDTH = 1080
HEIGHT = 1920
FPS = 30

VIDEO_DIR = ROOT / "asset_library/val_tavern/generated/episodes/ep01/video"
SUBTITLE_DIR = VIDEO_DIR / "subtitles"
PROJECT_DIR = VIDEO_DIR / "project_files"
SHOT_DIR = ROOT / "asset_library/val_tavern/generated/episodes/ep01/shot_images"

OUTPUT_MP4 = VIDEO_DIR / "VG_EP01_first_cut_v1.mp4"
OUTPUT_SRT = SUBTITLE_DIR / "VG_EP01_first_cut_v1.srt"
OUTPUT_TIMELINE = PROJECT_DIR / "VG_EP01_timeline_v1.json"


TIMELINE = [
    {
        "shot_id": "SHOT-001",
        "start": 0.0,
        "end": 0.5,
        "image": "VG_EP01_SHOT_001_opening_v2.png",
        "caption": "",
        "motion": "slow_push_in",
        "note": "Uses corrected v2 so the bartender is Washu, not Brimstone.",
    },
    {
        "shot_id": "SHOT-002",
        "start": 0.5,
        "end": 1.2,
        "image": "VG_EP01_SHOT_002_washu_opening_v1.png",
        "caption": "要来一杯吗？",
        "motion": "slow_push_in",
        "note": "Fixed opening line.",
    },
    {
        "shot_id": "SHOT-003",
        "start": 1.2,
        "end": 2.2,
        "image": "VG_EP01_SHOT_003_pidan_special_v1.png",
        "caption": "今日特调：单摸战神",
        "motion": "slow_push_in",
        "note": "Plate text is added in video, not generated in the image.",
    },
    {
        "shot_id": "SHOT-004",
        "start": 2.2,
        "end": 6.5,
        "image": "VG_EP01_SHOT_004_sage_complain_v1.png",
        "caption": "打 A 点喊半天让你跟团，\n你非要一个人摸 B 通！\n我们正面进点永远少一个，\n捷风 E 进去就没了，你人呢？",
        "motion": "slow_push_in",
        "note": "Sage complaint beat.",
    },
    {
        "shot_id": "SHOT-005",
        "start": 6.5,
        "end": 12.0,
        "image": "VG_EP01_SHOT_005_reyna_jett_conflict_v1.png",
        "caption": "芮娜：我 20-10，全队最高战绩。\n你们自己打不进点，怪我？\n捷风：你这 20-10 挺好看的。\n就是和赢游戏没什么关系。",
        "motion": "slow_push_in",
        "note": "Reyna vs Jett conflict. 20-10 is subtitle text.",
    },
    {
        "shot_id": "SHOT-006",
        "start": 12.0,
        "end": 18.0,
        "image": "VG_EP01_SHOT_006_reyna_omen_roast_v2.png",
        "caption": "芮娜：我在拉扯，给对面压力。\n我偷人把机会都做出来了，\n是你们自己接不住。\n幽影：不怪你。\n你只是和队伍不在一个地图。\n确实给到我们四个压力了。",
        "motion": "slow_push_in",
        "note": "Uses corrected Reyna reference v2.",
    },
    {
        "shot_id": "SHOT-007",
        "start": 18.0,
        "end": 22.5,
        "image": "VG_EP01_SHOT_007_group_argument_v1.png",
        "caption": "芮娜：那我不单摸，\n你们正面就一定打得进去吗？\n贤者：至少你人在，我们还能补枪！\n捷风：你来得比残局结算还晚。\n幽影：她不是单摸，她是单机。",
        "motion": "slow_pan",
        "note": "Group argument beat.",
    },
    {
        "shot_id": "SHOT-008",
        "start": 22.5,
        "end": 25.0,
        "image": "VG_EP01_SHOT_008_pidan_ending_v1.png",
        "caption": "老瓦：别吵了。皮蛋，你怎么看？\n皮蛋举牌：\nKSKBL",
        "motion": "slow_push_in",
        "note": "No comment CTA subtitle.",
    },
]


def seconds_to_srt_time(value: float) -> str:
    ms_total = int(round(value * 1000))
    hours = ms_total // 3_600_000
    ms_total %= 3_600_000
    minutes = ms_total // 60_000
    ms_total %= 60_000
    seconds = ms_total // 1000
    millis = ms_total % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def write_srt() -> None:
    entries = []
    index = 1
    for item in TIMELINE:
        caption = item["caption"].strip()
        if not caption:
            continue
        entries.append(
            f"{index}\n"
            f"{seconds_to_srt_time(item['start'])} --> {seconds_to_srt_time(item['end'])}\n"
            f"{caption}\n"
        )
        index += 1
    OUTPUT_SRT.write_text("\n".join(entries), encoding="utf-8")


def write_timeline() -> None:
    def rel(path: Path) -> str:
        return path.relative_to(ROOT).as_posix()

    data = {
        "episode_id": "VG-EP01",
        "title": "《瓦酒馆 EP01：单摸芮娜，赢了战绩输了全队》",
        "video_spec": {
            "width": WIDTH,
            "height": HEIGHT,
            "fps": FPS,
            "duration_seconds": 25.0,
            "format": "mp4",
            "codec": "H.264",
            "audio": "silent",
        },
        "outputs": {
            "video": rel(OUTPUT_MP4),
            "srt": rel(OUTPUT_SRT),
        },
        "shots": [
            {
                **item,
                "duration": round(item["end"] - item["start"], 3),
                "image_path": rel(SHOT_DIR / item["image"]),
            }
            for item in TIMELINE
        ],
    }
    OUTPUT_TIMELINE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ffmpeg_subtitle_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build_ffmpeg_command() -> list[str]:
    inputs: list[str] = []
    filters: list[str] = []
    labels: list[str] = []

    for idx, item in enumerate(TIMELINE):
        image_path = SHOT_DIR / item["image"]
        duration = item["end"] - item["start"]
        frames = max(1, int(round(duration * FPS)))
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{duration:.3f}", "-i", str(image_path)]

        if item["motion"] == "slow_pan":
            x_expr = f"iw/2-(iw/zoom/2)+(on/{frames}-0.5)*24"
            y_expr = "ih/2-(ih/zoom/2)"
        else:
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        # Scale larger than the output first so zoom/pan has enough pixels.
        filters.append(
            f"[{idx}:v]"
            f"scale={WIDTH + 160}:{HEIGHT + 284}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH + 160}:{HEIGHT + 284},"
            f"zoompan=z='min(1.0+on*0.00055,1.045)':"
            f"x='{x_expr}':y='{y_expr}':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
            f"trim=duration={duration:.3f},setpts=PTS-STARTPTS,format=yuv420p[v{idx}]"
        )
        labels.append(f"[v{idx}]")

    subtitle_file = ffmpeg_subtitle_path(OUTPUT_SRT)
    force_style = (
        "FontName=Microsoft YaHei,"
        "FontSize=48,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BackColour=&H99000000,"
        "BorderStyle=3,"
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=120"
    )
    filters.append(
        f"{''.join(labels)}concat=n={len(TIMELINE)}:v=1:a=0,"
        f"subtitles=filename='{subtitle_file}':charenc=UTF-8:force_style='{force_style}',"
        f"format=yuv420p[vout]"
    )

    return [
        "ffmpeg",
        "-y",
        "-hide_banner",
        *inputs,
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[vout]",
        "-an",
        "-r",
        str(FPS),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(OUTPUT_MP4),
    ]


def main() -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is not available on PATH")

    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    SUBTITLE_DIR.mkdir(parents=True, exist_ok=True)
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    missing = [str(SHOT_DIR / item["image"]) for item in TIMELINE if not (SHOT_DIR / item["image"]).exists()]
    if missing:
        raise FileNotFoundError("Missing input shot images:\n" + "\n".join(missing))

    write_srt()
    write_timeline()

    cmd = build_ffmpeg_command()
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(f"ffmpeg failed with exit code {result.returncode}")

    print(f"Wrote video: {OUTPUT_MP4.relative_to(ROOT).as_posix()}")
    print(f"Wrote subtitles: {OUTPUT_SRT.relative_to(ROOT).as_posix()}")
    print(f"Wrote timeline: {OUTPUT_TIMELINE.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
