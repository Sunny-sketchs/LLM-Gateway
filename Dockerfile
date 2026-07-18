FROM python:3.12-slim

# build-essential is needed for a couple of presidio/spacy transitive deps to compile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# presidio-analyzer requires a spaCy model to be present at runtime - it is not
# pulled in automatically by pip. en_core_web_sm keeps the image smaller; swap
# to en_core_web_lg later if you need better PII/entity recall.
RUN python -m spacy download en_core_web_sm

COPY src ./src

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# $PORT is injected by Render/Railway/Fly; falls back to 8000 for local `docker run`
CMD ["sh", "-c", "uvicorn src.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]