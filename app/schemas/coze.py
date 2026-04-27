from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus, ShotStatus


class CozeResponse(BaseModel):
    success: bool = True
    code: str = "OK"
    message: str = ""
    data: dict = Field(default_factory=dict)
    next_action: str = ""


class CozeProjectCard(BaseModel):
    project_title: str
    genre: str | None = None
    platform: str | None = None
    target_duration: int | None = None
    target_audience: str | None = None
    visual_style: str | None = None
    core_conflict: str | None = None
    hook: str | None = None
    ending_hook: str | None = None
    selling_points: list[str] = Field(default_factory=list)
    visual_asset_library_json: dict[str, Any] | None = None
    status: ProjectStatus = ProjectStatus.DRAFT


class CozeCharacterItem(BaseModel):
    name: str
    role: str
    age_vibe: str | None = None
    appearance: str | None = None
    hair: str | None = None
    outfit: str | None = None
    personality: str | None = None
    speaking_style: str | None = None
    main_reference_url: str | None = None
    must_keep: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    main_reference_confirmed: bool = False
    gender: str | None = None
    age: str | None = None
    appearance_summary: str | None = None
    social_identity: str | None = None
    first_impression: str | None = None
    public_mask: str | None = None
    inner_truth: str | None = None
    core_keywords: list[str] = Field(default_factory=list)
    personality_contradiction: str | None = None
    habits: list[str] = Field(default_factory=list)
    language_style: str | None = None
    decision_style: str | None = None
    stress_reaction: str | None = None
    values: list[str] = Field(default_factory=list)
    fear: str | None = None
    desire: str | None = None
    trauma: str | None = None
    secret: str | None = None
    family_background: str | None = None
    growth_environment: str | None = None
    economic_status: str | None = None
    education_background: str | None = None
    key_events: list[str] = Field(default_factory=list)
    current_status: str | None = None
    core_problem: str | None = None
    relationship_status: str | None = None
    closest_person: str | None = None
    enemy_person: str | None = None
    complex_relationships: list[str] = Field(default_factory=list)
    emotional_bond: str | None = None
    arc_start: str | None = None
    arc_end: str | None = None
    arc_type: str | None = None
    catalyst: str | None = None
    turning_point: str | None = None
    growth_theme: str | None = None
    catchphrase: str | None = None
    signature_action: str | None = None


class CozeCharactersPayload(BaseModel):
    characters: list[CozeCharacterItem] = Field(default_factory=list)


class CozeProjectInitRequest(BaseModel):
    project_card_json: CozeProjectCard
    characters_json: CozeCharactersPayload
    visual_asset_library_json: dict[str, Any] | None = None


class ConfirmCharacterReferenceRequest(BaseModel):
    main_reference_url: str | None = None


class CozeScriptCard(BaseModel):
    logline: str | None = None
    genre_tags: list[str] = Field(default_factory=list)
    audience_profile: str | None = None
    audience_emotion: str | None = None
    commercial_positioning: str | None = None
    core_hook: str | None = None
    opening_hook: str | None = None
    conflict: str | None = None
    escalation: str | None = None
    fear_beat: str | None = None
    suspense_beat: str | None = None
    misdirection_beat: str | None = None
    reveal_beat: str | None = None
    payoff_beat: str | None = None
    cliffhanger: str | None = None
    episode_theme: str | None = None
    emotional_curve: str | None = None
    conflict_chain: str | None = None
    power_dynamic: str | None = None
    secret_reveal_plan: str | None = None
    next_episode_hook: str | None = None
    turning_point: str | None = None
    ending_hook: str | None = None


class CozeStoryboardShot(BaseModel):
    shot_id: str
    duration_sec: int | None = None
    character: str | None = None
    location: str | None = None
    core_action: str
    emotion: str | None = None
    camera: str | None = None
    dialogue: str | None = None
    shot_type: str | None = None
    camera_motion: str | None = None
    subject_motion: str | None = None
    transition: str | None = None
    subtitle_text: str | None = None
    sfx: str | None = None
    editing_notes: str | None = None
    shot_purpose: str | None = None
    conflict_beat: str | None = None
    emotion_shift: str | None = None
    visual_focus: str | None = None
    image_prompt_intent: str | None = None
    storyboard_clarity: str | None = None
    pacing_note: str | None = None
    audience_feeling: str | None = None
    reference_priority: str | None = None
    composition: str | None = None
    lighting: str | None = None
    subtitle_position: str | None = None
    negative_constraints: list[str] = Field(default_factory=list)
    character_asset_keys: list[str] = Field(default_factory=list)
    scene_asset_key: str | None = None
    prop_asset_keys: list[str] = Field(default_factory=list)
    image_prompt: str
    video_prompt: str
    voice_prompt: str
    bgm_prompt: str
    status: ShotStatus = ShotStatus.PROMPT_READY


class CozeStoryboardPayload(BaseModel):
    shots: list[CozeStoryboardShot] = Field(default_factory=list)


class CozeStoryboardRequest(BaseModel):
    script_card_json: CozeScriptCard
    storyboard_json: CozeStoryboardPayload


class CozeCreateAssetTasksRequest(BaseModel):
    video_shot_ids: list[str] = Field(default_factory=list)


class CozeGenerateScriptRequest(BaseModel):
    script_card_json: CozeScriptCard


class CozePublishRecordRequest(BaseModel):
    platform: str
    title: str
    published_at: str
    url: str


class CozeFullDemoFlowRequest(BaseModel):
    project_card_json: CozeProjectCard
    characters_json: CozeCharactersPayload
    visual_asset_library_json: dict[str, Any] | None = None
    script_card_json: CozeScriptCard
    storyboard_json: CozeStoryboardPayload
    video_shot_ids: list[str] = Field(default_factory=list)
    publish_record_json: CozePublishRecordRequest


class CozePayloadValidationRequest(BaseModel):
    project_card_json: dict[str, Any] = Field(default_factory=dict)
    characters_json: dict[str, Any] = Field(default_factory=dict)
    visual_asset_library_json: Any | None = None
    script_card_json: dict[str, Any] = Field(default_factory=dict)
    storyboard_json: dict[str, Any] = Field(default_factory=dict)
    video_shot_ids: list[str] = Field(default_factory=list)
    publish_record_json: dict[str, Any] = Field(default_factory=dict)
