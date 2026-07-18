from fastapi import FastAPI
from src.app.config import settings
from src.app.routers.proxy import router
from src.app.redis_setup.redis_client import redis_client


app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(router)


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    redis_ok = True
    try:
        pong = redis_client.ping()
        if not pong:
            redis_ok = False
    except Exception:
        redis_ok = False
    return {"status": "ok", "redis": "ok" if redis_ok else "unreachable"}
