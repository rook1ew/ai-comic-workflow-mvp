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
    must_keep: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    main_reference_confirmed: bool = False


class CozeCharactersPayload(BaseModel):
    characters: list[CozeCharacterItem] = Field(default_factory=list)


class CozeProjectInitRequest(BaseModel):
    project_card_json: CozeProjectCard
    characters_json: CozeCharactersPayload


class ConfirmCharacterReferenceRequest(BaseModel):
    main_reference_url: str | None = None


class CozeScriptCard(BaseModel):
    opening_hook: str | None = None
    conflict: str | None = None
    escalation: str | None = None
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
