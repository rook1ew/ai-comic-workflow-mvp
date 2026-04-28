from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse


class CharacterCreate(BaseModel):
    project_id: int
    name: str = Field(min_length=1, max_length=255)
    role_type: str = Field(min_length=1, max_length=100)
    profile: str = Field(min_length=1)
    visual_notes: str = Field(min_length=1)
    voice_style: str = Field(min_length=1)
    main_reference_url: str | None = None
    main_reference_confirmed: bool = False


class CharacterResponse(TimestampedResponse):
    project_id: int
    name: str
    role_type: str
    profile: str
    visual_notes: str
    voice_style: str
    main_reference_url: str | None
    main_reference_confirmed: bool


class CharacterAppearanceUpsertRequest(BaseModel):
    appearance_key: str = Field(min_length=1, max_length=255)
    appearance_type: str = Field(min_length=1, max_length=100)
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    image_url: str = Field(min_length=1, max_length=1000)
    is_selected: bool = False
    order_index: int = 0
    change_reason: str | None = None
    must_keep: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)


class CharacterAppearanceResponse(TimestampedResponse):
    project_id: int
    character_id: int
    appearance_key: str
    appearance_type: str
    title: str | None = None
    description: str | None = None
    image_url: str
    is_selected: bool
    order_index: int
    change_reason: str | None = None
    must_keep: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)


class CharacterAppearanceSelectResponse(BaseModel):
    project_id: int
    character_id: int
    selected_appearance: CharacterAppearanceResponse
    character_main_reference_url: str | None = None
    synced_visual_asset: dict | None = None


class ProjectCharacterAppearanceSummaryItem(BaseModel):
    character_id: int
    name: str
    role_type: str
    main_reference_url: str | None = None
    selected_appearance_key: str | None = None
    selected_appearance_url: str | None = None
    appearances_count: int
    has_design_sheet: bool
    has_main_reference: bool
    has_face_detail: bool
    has_fullbody: bool
    warnings: list[str] = Field(default_factory=list)
    next_action: str


class ProjectCharacterAppearanceSummary(BaseModel):
    project_id: int
    characters_count: int
    items: list[ProjectCharacterAppearanceSummaryItem] = Field(default_factory=list)
    next_action: str
