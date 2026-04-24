from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectSummary
from app.services.project_service import create_project, get_project_or_404, get_project_summary, list_projects

router = APIRouter()


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project_route(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectResponse:
    return create_project(db, payload)


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects_route(db: Session = Depends(get_db)) -> list[ProjectResponse]:
    return list_projects(db)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project_route(project_id: int, db: Session = Depends(get_db)) -> ProjectResponse:
    return get_project_or_404(db, project_id)


@router.get("/projects/{project_id}/summary", response_model=ProjectSummary)
def get_project_summary_route(project_id: int, db: Session = Depends(get_db)) -> ProjectSummary:
    return get_project_summary(db, project_id)
