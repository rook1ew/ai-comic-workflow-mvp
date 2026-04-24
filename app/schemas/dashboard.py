from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_projects: int
    total_episodes: int
    total_characters: int
    total_scenes: int
    total_shots: int
    total_asset_tasks: int
    total_assets: int
    total_reviews: int
    total_publish_records: int
