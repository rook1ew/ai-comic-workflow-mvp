from pydantic import BaseModel, Field


class ProviderRequest(BaseModel):
    shot_id: int
    modality: str
    payload: dict = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    provider_name: str
    asset_type: str
    url: str
    metadata: dict = Field(default_factory=dict)


class ProviderResult(BaseModel):
    url: str
    metadata: dict = Field(default_factory=dict)


class ImageProviderInput(BaseModel):
    prompt: str
    character_reference_url: str | None = None
    shot_id: int
    style: str | None = None
    storyboard_context: dict = Field(default_factory=dict)


class VideoProviderInput(BaseModel):
    image_url: str
    prompt: str
    duration: int | float
    aspect_ratio: str
    resolution: str
