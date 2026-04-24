from fastapi import FastAPI

app = FastAPI(
    title="Coze AI Comic MVP",
    description="Coze-first MVP backend for AI comic-drama workflow validation.",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {
        "success": True,
        "code": "OK",
        "message": "Coze AI Comic MVP is running",
        "data": {"docs": "/docs"},
        "next_action": "open_api_docs",
    }
