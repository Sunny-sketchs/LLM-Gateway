# main.py

from fastapi import FastAPI
from app.config import settings


app = FastAPI(title=settings.app_name, version=settings.app_version)

@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status" : "ok"}


