# Coze Integration

Coze should orchestrate the early workflow and call this backend through high-level APIs.

Recommended flow:

1. Coze collects project inputs from the user.
2. Coze calls `POST /coze/project/init`.
3. Coze generates or requests a script through `generate-script`.
4. Coze generates storyboard data through `generate-storyboard`.
5. Coze triggers `create-asset-tasks`.
6. Backend executes mock providers and returns structured results.
7. Coze shows next action to the user.

Phase 1.6-A minimal endpoints:

- `POST /coze/project/init`
- `POST /characters/{character_id}/confirm-reference`
- `POST /coze/project/{project_id}/storyboard`
- `POST /coze/project/{project_id}/create-asset-tasks`
- `POST /coze/project/{project_id}/run-asset-tasks`
- `GET /coze/project/{project_id}/summary`

All `/coze/*` endpoints return:

```json
{
  "success": true,
  "code": "OK",
  "message": "",
  "data": {},
  "next_action": ""
}
```
