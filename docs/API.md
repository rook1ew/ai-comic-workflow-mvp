# API Design

Phase 1 target endpoints:

- POST /coze/project/init
- POST /characters/{character_id}/confirm-reference
- POST /coze/project/{project_id}/storyboard
- POST /coze/project/{project_id}/create-asset-tasks
- POST /coze/project/{project_id}/run-asset-tasks
- GET /coze/project/{project_id}/summary

Current core REST endpoints also include:

- POST /projects
- GET /projects
- GET /projects/{project_id}
- GET /projects/{project_id}/summary
- POST /characters
- POST /episodes
- POST /scenes
- POST /shots
- POST /asset-tasks
- GET /asset-tasks/{asset_task_id}
- POST /asset-tasks/{asset_task_id}/run
- GET /projects/{project_id}/asset-tasks
- GET /projects/{project_id}/assets
- POST /projects/{project_id}/asset-tasks/bulk
- POST /projects/{project_id}/asset-tasks/run-bulk
- POST /reviews
- POST /publish-records
- GET /dashboard/summary
