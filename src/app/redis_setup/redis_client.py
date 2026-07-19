from os import getenv
from fastapi.exceptions import HTTPException

import redis

redis_url = getenv(key="REDIS_URL")

redis_client = redis.from_url(
    redis_url,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)

