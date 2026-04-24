# Coze AI Comic MVP

一个面向 AI 漫剧早期创业验证的最小可行系统（MVP）。

当前版本目标：
- 用 Coze 跑通前期工作流
- 用后端 API 承接项目、角色、分镜、素材任务和发布记录
- 不包含复盘模块
- 不依赖真实付费生成服务即可本地演示

## Phase 1 Scope
- Project management
- Character management
- Shot / storyboard management
- Asset task management
- Review records
- Publish records
- Coze integration endpoints
- Mock providers

## Not in Phase 1
- Retrospective module
- Full frontend
- Multi-tenant SaaS
- Real provider integrations
- n8n-specific workflow

## Proposed Stack
- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Alembic
- pytest

## Planned Structure
- `app/` application code
- `docs/` documentation
- `examples/` sample payloads
- `tests/` automated tests
- `scripts/` helper scripts

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Status
Scaffolding stage. Next step: ask Codex to implement Phase 1 backend.
