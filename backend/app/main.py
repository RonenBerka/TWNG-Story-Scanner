from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.candidates import router as candidates_router
from app.api.routes.ingest_facebook import router as fb_ingest_router
from app.api.routes.records import router as records_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.viewer import router as viewer_router

app = FastAPI(title="TWNG Story Scanner", version="0.1.0")

app.include_router(auth_router)
app.include_router(candidates_router)
app.include_router(records_router)
app.include_router(tasks_router)
app.include_router(fb_ingest_router)
app.include_router(viewer_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
