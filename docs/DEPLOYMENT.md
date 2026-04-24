# Deployment

Phase 1 local development:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Production deployment is out of scope for Phase 1.
