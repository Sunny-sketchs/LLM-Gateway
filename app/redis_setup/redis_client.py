from os import getenv

import redis

redis_url = getenv(key="REDIS_URL")

redis_client = redis.from_url(redis_url, decode_responses=True)

