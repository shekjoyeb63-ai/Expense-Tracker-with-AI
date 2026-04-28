import redis
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

def test_connection():
    try:
        redis_client.ping()
        print("Redis connected ✅")
    except redis.ConnectionError:
        print("Redis connection failed ❌")