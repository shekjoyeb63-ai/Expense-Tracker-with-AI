import redis
import os

redis_client = redis.from_url(
    os.environ.get("REDIS_URL"),
    decode_responses=True
)
def test_connection():
    try:
        redis_client.ping()
        print("Redis connected ✅")
    except redis.ConnectionError:
        print("Redis connection failed ❌")