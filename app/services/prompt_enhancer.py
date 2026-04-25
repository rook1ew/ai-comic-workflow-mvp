def build_image_enhanced_prompt(
    base_prompt: str,
    visual_style: str | None,
    character_reference_url: str | None,
    storyboard_context: dict | None,
) -> str:
    lines: list[str] = []

    cleaned_base_prompt = (base_prompt or "").strip()
    if cleaned_base_prompt:
        lines.append(f"Base image prompt: {cleaned_base_prompt}")

    if visual_style:
        lines.append(f"Visual style: {visual_style}")

    if character_reference_url:
        lines.append(
            "Character consistency: keep the main character visually consistent with the provided reference image "
            f"({character_reference_url})."
        )

    context = storyboard_context or {}
    if context.get("source_shot_id"):
        lines.append(f"Storyboard shot id: {context['source_shot_id']}")
    if context.get("character"):
        lines.append(f"Character in frame: {context['character']}")
    if context.get("location"):
        lines.append(f"Location: {context['location']}")
    if context.get("emotion"):
        lines.append(f"Emotion: {context['emotion']}")
    if context.get("camera"):
        lines.append(f"Camera framing: {context['camera']}")
    if context.get("dialogue"):
        lines.append(f"Dialogue cue: {context['dialogue']}")

    lines.append(
        "Safety and originality: do not imitate specific copyrighted IP, celebrities, film characters, or known anime characters."
    )

    return "\n".join(lines)
