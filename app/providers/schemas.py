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
