from fastapi import FastAPI
from app.config import settings
from app.routers.proxy import router
import redis

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(router)


@app.on_event('startup')
async def startup_event():
    keys = Keys()
    await initialize_redis(keys)



@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
