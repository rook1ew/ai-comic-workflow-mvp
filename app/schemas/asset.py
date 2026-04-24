from app.models.enums import AssetModality
from app.schemas.common import TimestampedResponse


class AssetResponse(TimestampedResponse):
    shot_id: int
    asset_task_id: int
    asset_type: AssetModality
    url: str
    metadata_json: dict
