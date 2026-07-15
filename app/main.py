from fastapi import FastAPI
from app.config import settings
from app.routers.proxy import router
import logging
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(router)


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
