from fastapi import APIRouter

from app.api.routes import asset_tasks, characters, coze, dashboard, episodes, projects, publish_records, reviews, scenes, shots

api_router = APIRouter()
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(characters.router, tags=["characters"])
api_router.include_router(episodes.router, tags=["episodes"])
api_router.include_router(scenes.router, tags=["scenes"])
api_router.include_router(shots.router, tags=["shots"])
api_router.include_router(asset_tasks.router, tags=["asset_tasks"])
api_router.include_router(reviews.router, tags=["reviews"])
api_router.include_router(publish_records.router, tags=["publish_records"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(coze.router, tags=["coze"])
