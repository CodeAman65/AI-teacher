import os
import hashlib
import warnings
import logging
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
logging.getLogger("redis").setLevel(logging.ERROR)

load_dotenv()

UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
CACHE_EXPIRY_DAYS = 30
CACHE_EXPIRY_SEC  = CACHE_EXPIRY_DAYS * 24 * 60 * 60  # 30 days in seconds

# Single Redis client — created once, reused
_redis_client = None


def get_redis():
    """
    Returns Redis client. Creates it once and reuses.
    Returns None if Redis is unavailable — never crashes the app.
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    if not UPSTASH_REDIS_URL:
        print("⚠️  UPSTASH_REDIS_URL not in .env — caching disabled")
        return None

    try:
        import redis
        client = redis.from_url(
            UPSTASH_REDIS_URL,
            decode_responses=True,      # Return strings not bytes
            socket_timeout=5,           # 5 second timeout
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        # Test connection
        client.ping()
        _redis_client = client
        return _redis_client

    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("   App will work without cache — just slower")
        return None


def make_cache_key(topic: str) -> str:
    """
    Creates a consistent MD5 hash key from topic string.
    Normalizes topic before hashing so
    'Osmosis', 'osmosis', 'OSMOSIS' all map to same key.

    Args:
        topic: Topic string e.g. "Osmosis"

    Returns:
        Cache key string e.g. "video:a1b2c3d4..."
    """
    normalized = topic.strip().lower()
    hash_key   = hashlib.md5(normalized.encode()).hexdigest()
    return f"video:{hash_key}"


def get_cached_video(topic: str) -> str | None:
    """
    Checks Redis for a cached video URL for the given topic.

    Args:
        topic: Topic string e.g. "Osmosis"

    Returns:
        Video URL string if found in cache
        None if not found or Redis unavailable
    """
    client = get_redis()
    if client is None:
        return None

    try:
        cache_key = make_cache_key(topic)
        value     = client.get(cache_key)

        if value:
            print(f"  ✓ Cache HIT for '{topic}' → {value}")
            return value
        else:
            print(f"  - Cache MISS for '{topic}'")
            return None

    except Exception as e:
        # Never crash the app because of cache failure
        print(f"  ⚠️  Cache read error: {e} — continuing without cache")
        return None


def cache_video(topic: str, video_url: str) -> bool:
    """
    Saves a video URL to Redis with 30-day expiry.
    Same topic asked by 100 students = generate once, serve 99 from cache.

    Args:
        topic:     Topic string e.g. "Osmosis"
        video_url: Public URL to the generated MP4 video

    Returns:
        True if cached successfully, False if failed
    """
    client = get_redis()
    if client is None:
        return False

    try:
        cache_key = make_cache_key(topic)
        client.setex(
            name=cache_key,
            time=CACHE_EXPIRY_SEC,
            value=video_url
        )
        print(f"  ✓ Cached video for '{topic}' (expires in {CACHE_EXPIRY_DAYS} days)")
        return True

    except Exception as e:
        print(f"  ⚠️  Cache write error: {e} — video generated but not cached")
        return False


def delete_cached_video(topic: str) -> bool:
    """
    Deletes a cached video for a topic.
    Useful when you regenerate better quality videos.

    Args:
        topic: Topic string e.g. "Osmosis"

    Returns:
        True if deleted, False if not found or error
    """
    client = get_redis()
    if client is None:
        return False

    try:
        cache_key = make_cache_key(topic)
        result    = client.delete(cache_key)
        if result:
            print(f"  ✓ Deleted cache for '{topic}'")
            return True
        else:
            print(f"  - No cache found for '{topic}'")
            return False

    except Exception as e:
        print(f"  ⚠️  Cache delete error: {e}")
        return False


def get_cache_stats() -> dict:
    """
    Returns basic cache statistics.
    Useful for monitoring how many videos are cached.
    """
    client = get_redis()
    if client is None:
        return {"status": "unavailable", "cached_videos": 0}

    try:
        keys  = client.keys("video:*")
        count = len(keys)
        return {
            "status":         "connected",
            "cached_videos":  count,
            "expiry_days":    CACHE_EXPIRY_DAYS
        }
    except Exception as e:
        return {"status": f"error: {e}", "cached_videos": 0}


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Cache")
    print("=" * 60)

    # Test 1: Stats
    print("\n[TEST 1] Cache connection")
    stats = get_cache_stats()
    print(f"  Status: {stats['status']}")
    print(f"  Cached videos: {stats['cached_videos']}")

    # Test 2: Cache miss
    print("\n[TEST 2] Cache miss")
    result = get_cached_video("Osmosis Test Topic")
    print(f"  Result: {result}")  # Should be None

    # Test 3: Cache write
    print("\n[TEST 3] Cache write")
    success = cache_video("Osmosis Test Topic", "https://example.com/osmosis.mp4")
    print(f"  Written: {success}")

    # Test 4: Cache hit
    print("\n[TEST 4] Cache hit")
    result = get_cached_video("Osmosis Test Topic")
    print(f"  Result: {result}")  # Should return URL

    # Test 5: Case insensitive
    print("\n[TEST 5] Case insensitive — 'osmosis test topic' == 'Osmosis Test Topic'")
    result = get_cached_video("osmosis test topic")
    print(f"  Result: {result}")  # Should still return URL

    # Test 6: Cleanup
    print("\n[TEST 6] Delete test entry")
    delete_cached_video("Osmosis Test Topic")
    result = get_cached_video("Osmosis Test Topic")
    print(f"  After delete: {result}")  # Should be None

    print("\n" + "=" * 60)
    print("✓ Cache testing complete!")
    print("=" * 60)